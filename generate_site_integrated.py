"""
Generate full static site with squares and player props (no Polars)
"""

import duckdb
import json
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime
import shutil

# Import analysis modules that don't use Polars
from analysis.squares import (
    load_superbowl_games,
    apply_recency_weighting,
    calculate_combination_frequency,
    calculate_probability_matrix,
    rank_squares
)


def collect_squares_data():
    """Collect squares analysis data"""
    games = load_superbowl_games()
    if not games:
        return {'matrices': {}, 'ranked': {}}

    weighted_games = apply_recency_weighting(games)

    quarters = ["q1", "q2", "q3", "q4", "final"]
    matrices = {}
    ranked = {}

    for quarter in quarters:
        combinations = calculate_combination_frequency(weighted_games, quarter)
        matrix = calculate_probability_matrix(combinations)
        matrices[quarter] = matrix

        ranked_squares = rank_squares(matrix)
        ranked[quarter] = [
            {
                'winner': w,
                'loser': l,
                'probability': prob
            }
            for w, l, prob in ranked_squares
        ]

    return {
        'matrices': matrices,
        'ranked': ranked
    }


def collect_players_data():
    """Collect player props data using DuckDB"""
    conn = duckdb.connect('data/superbowl.db')

    # Load player config
    config_path = Path("players_to_track.json")
    if not config_path.exists():
        return {'summaries': []}

    with open(config_path) as f:
        config = json.load(f)

    positions = {p['name']: p['position'] for p in config['players']}

    # Get player stats
    players = conn.execute("""
        SELECT
            player_name,
            team,
            COUNT(*) as games,
            SUM(passing_yards) as total_pass_yds,
            CAST(AVG(passing_yards) AS INTEGER) as avg_pass_yds,
            SUM(passing_tds) as total_pass_td,
            SUM(rushing_yards) as total_rush_yds,
            CAST(AVG(rushing_yards) AS INTEGER) as avg_rush_yds,
            SUM(rushing_tds) as total_rush_td,
            SUM(receptions) as total_rec,
            CAST(AVG(receptions) AS DECIMAL(4,1)) as avg_rec,
            SUM(receiving_yards) as total_rec_yds,
            CAST(AVG(receiving_yards) AS INTEGER) as avg_rec_yds,
            SUM(receiving_tds) as total_rec_td
        FROM player_game_logs
        WHERE season = 2025
        GROUP BY player_name, team
        ORDER BY player_name
    """).fetchall()

    # Load Super Bowl benchmarks
    sb_benchmarks = {}
    sb_path = Path("data/superbowl_player_history.parquet")
    if sb_path.exists():
        sb_data = conn.execute(f"""
            SELECT position,
                   AVG(passing_yards) as avg_pass_yds,
                   AVG(rushing_yards) as avg_rush_yds,
                   AVG(receptions) as avg_rec,
                   AVG(receiving_yards) as avg_rec_yds
            FROM read_parquet('{sb_path}')
            GROUP BY position
        """).fetchall()

        for row in sb_data:
            sb_benchmarks[row[0]] = {
                'passing_yards': row[1],
                'rushing_yards': row[2],
                'receptions': row[3],
                'receiving_yards': row[4]
            }

    # Get game-by-game stats
    game_by_game = {}
    for row in players:
        player_name = row[0]
        games = conn.execute("""
            SELECT week, game_type, game_result, opponent, opponent_abbr,
                   passing_yards, passing_tds, interceptions,
                   rushing_yards, rushing_tds,
                   receptions, receiving_yards, receiving_tds
            FROM player_game_logs
            WHERE player_name = ? AND season = 2025
            ORDER BY week
        """, [player_name]).fetchall()
        game_by_game[player_name] = games

    # Calculate win/loss splits for each player
    win_loss_splits = {}
    for row in players:
        player_name = row[0]

        # Get stats in wins
        wins = conn.execute("""
            SELECT
                COUNT(*) as games,
                CAST(AVG(passing_yards) AS INTEGER) as avg_pass_yds,
                CAST(AVG(rushing_yards) AS INTEGER) as avg_rush_yds,
                CAST(AVG(receptions) AS DECIMAL(4,1)) as avg_rec,
                CAST(AVG(receiving_yards) AS INTEGER) as avg_rec_yds
            FROM player_game_logs
            WHERE player_name = ? AND season = 2025 AND game_result = 'W'
        """, [player_name]).fetchone()

        # Get stats in losses
        losses = conn.execute("""
            SELECT
                COUNT(*) as games,
                CAST(AVG(passing_yards) AS INTEGER) as avg_pass_yds,
                CAST(AVG(rushing_yards) AS INTEGER) as avg_rush_yds,
                CAST(AVG(receptions) AS DECIMAL(4,1)) as avg_rec,
                CAST(AVG(receiving_yards) AS INTEGER) as avg_rec_yds
            FROM player_game_logs
            WHERE player_name = ? AND season = 2025 AND game_result = 'L'
        """, [player_name]).fetchone()

        win_loss_splits[player_name] = {
            'wins': {
                'games': wins[0],
                'passing_yards': wins[1] or 0,
                'rushing_yards': wins[2] or 0,
                'receptions': float(wins[3] or 0),
                'receiving_yards': wins[4] or 0
            },
            'losses': {
                'games': losses[0],
                'passing_yards': losses[1] or 0,
                'rushing_yards': losses[2] or 0,
                'receptions': float(losses[3] or 0),
                'receiving_yards': losses[4] or 0
            }
        }

    # Build summaries for template
    summaries = []
    for row in players:
        name = row[0]
        if name.startswith("Player Name"):
            continue

        pos = positions.get(name, '?')
        games_list = game_by_game[name]

        # Calculate recent form (last 5 games weighted more)
        recent_games = games_list[-5:] if len(games_list) >= 5 else games_list

        # Calculate projections based on position
        # Note: game tuple is now (week, game_type, game_result, opponent, opponent_abbr,
        #                          passing_yards, passing_tds, interceptions, rushing_yards, rushing_tds,
        #                          receptions, receiving_yards, receiving_tds)
        projection = {}
        if pos == 'QB':
            # Recent average for passing yards (index 5 now)
            recent_pass_yds = [g[5] for g in recent_games]
            recent_avg = sum(recent_pass_yds) / len(recent_pass_yds) if recent_pass_yds else 0
            season_avg = row[4]
            sb_avg = sb_benchmarks.get(pos, {}).get('passing_yards', 0) or 0

            # Weighted projection: 50% recent, 30% season, 20% SB history
            projection['passing_yards'] = int((recent_avg * 0.5) + (season_avg * 0.3) + (sb_avg * 0.2))
            projection['passing_tds'] = round((row[5] / row[2]) * 1.1)  # Slight bump for big game

        elif pos == 'RB':
            recent_rush_yds = [g[8] for g in recent_games]  # rushing_yards at index 8
            recent_avg = sum(recent_rush_yds) / len(recent_rush_yds) if recent_rush_yds else 0
            season_avg = row[7]
            sb_avg = sb_benchmarks.get(pos, {}).get('rushing_yards', 0) or 0

            projection['rushing_yards'] = int((recent_avg * 0.5) + (season_avg * 0.3) + (sb_avg * 0.2))
            projection['rushing_tds'] = round((row[8] / row[2]) * 1.1, 1)

            # Receptions for pass-catching backs (receptions at index 10)
            recent_rec = [g[10] for g in recent_games]
            recent_rec_avg = sum(recent_rec) / len(recent_rec) if recent_rec else 0
            projection['receptions'] = int((recent_rec_avg * 0.6) + (float(row[10]) * 0.4))

        elif pos in ['WR', 'TE']:
            recent_rec = [g[10] for g in recent_games]  # receptions at index 10
            recent_rec_yds = [g[11] for g in recent_games]  # receiving_yards at index 11
            recent_rec_avg = sum(recent_rec) / len(recent_rec) if recent_rec else 0
            recent_yds_avg = sum(recent_rec_yds) / len(recent_rec_yds) if recent_rec_yds else 0

            season_rec_avg = float(row[10])
            season_yds_avg = float(row[12])
            sb_rec_avg = float(sb_benchmarks.get(pos, {}).get('receptions', 0) or 0)
            sb_yds_avg = float(sb_benchmarks.get(pos, {}).get('receiving_yards', 0) or 0)

            projection['receptions'] = round((recent_rec_avg * 0.5) + (season_rec_avg * 0.3) + (sb_rec_avg * 0.2), 1)
            projection['receiving_yards'] = int((recent_yds_avg * 0.5) + (season_yds_avg * 0.3) + (sb_yds_avg * 0.2))
            projection['receiving_tds'] = round((row[13] / row[2]) * 1.1, 1)

        summary = {
            'name': name,
            'position': pos,
            'team': row[1],
            'games_played': row[2],
            'totals': {
                'passing_yards': row[3],
                'passing_tds': row[5],
                'rushing_yards': row[6],
                'rushing_tds': row[8],
                'receptions': row[9],
                'receiving_yards': row[11],
                'receiving_tds': row[13]
            },
            'averages': {
                'passing_yards': row[4],
                'rushing_yards': row[7],
                'receptions': row[10],
                'receiving_yards': row[12]
            },
            'sb_benchmarks': sb_benchmarks.get(pos, {}),
            'projection': projection,
            'win_loss_splits': win_loss_splits.get(name, {}),
            'game_by_game': game_by_game[name]
        }

        summaries.append(summary)

    conn.close()
    return {'summaries': summaries}


def generate_pages(data, output_dir):
    """Generate all HTML pages"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Create assets directory
    assets_dir = output_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)

    # Copy CSS
    static_css = Path('static/styles.css')
    if static_css.exists():
        shutil.copy(static_css, assets_dir / 'styles.css')

    # Setup Jinja2
    template_dir = Path('templates')
    if not template_dir.exists():
        print("⚠️  No templates directory found")
        return

    env = Environment(loader=FileSystemLoader('templates'))

    # Generate each page
    pages = {
        'index': 'index.html',
        'squares': 'squares_filtered.html',
        'players': 'players_simple.html',  # Use simplified template
        'prop_lines': 'prop_lines.html',  # Betting prop lines
        'model_comparison': 'model_comparison.html',  # Model comparison
        'about': 'about.html'
    }

    for page_name, template_file in pages.items():
        output_file = f'{page_name}.html'

        if not (template_dir / template_file).exists():
            continue

        try:
            template = env.get_template(template_file)
            output = template.render(data=data)

            with open(output_dir / output_file, 'w') as f:
                f.write(output)

            print(f"✅ Generated {output_file}")
        except Exception as e:
            print(f"⚠️  Error generating {output_file}: {str(e)[:100]}")


def generate_site():
    """Generate complete static site"""
    print("🏈 Generating complete static site...\n")

    print("📊 Collecting analysis data...")

    # Load prop lines if available
    prop_lines = {}
    prop_lines_path = Path("data/player_prop_lines.json")
    if prop_lines_path.exists():
        with open(prop_lines_path) as f:
            prop_lines = json.load(f)

    # Load model comparison if available
    model_comparison = {}
    comparison_path = Path("data/model_comparison.json")
    if comparison_path.exists():
        with open(comparison_path) as f:
            model_comparison = json.load(f)

    # Load filtered squares data if available
    squares_data = {}
    squares_path = Path("data/squares_with_filters.json")
    if squares_path.exists():
        with open(squares_path) as f:
            squares_data = json.load(f)
    else:
        # Fallback to old method if filtered data not available
        squares_data = {'all': collect_squares_data()}

    data = {
        'squares_data': squares_data,  # Filtered squares data
        'squares': collect_squares_data(),  # Keep for index page
        'players': collect_players_data(),
        'prop_lines': prop_lines,
        'model_comparison': model_comparison,
        'playoffs': {'game_props': {}, 'best_props': {}},  # Legacy, kept for compatibility
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    print(f"   - {len(data['players']['summaries'])} players")
    print(f"   - {len(data['squares']['ranked'])} quarters for squares")
    print(f"   - {len(prop_lines)} players with prop lines")
    print(f"   - {len(model_comparison)} players with model comparisons")

    print("\n📝 Generating HTML pages...")
    output_dir = Path("static_site")
    generate_pages(data, output_dir)

    print(f"\n✅ Site generated at {output_dir}/")
    print("   Main pages:")
    print("   - index.html (overview)")
    print("   - squares.html (squares analysis)")
    print("   - players.html (player props)")


if __name__ == "__main__":
    generate_site()
