"""
Simple static site generator using DuckDB (no Polars dependency)
"""

import duckdb
import json
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime
import shutil


def calculate_hit_rate(values, threshold, over=True):
    """Calculate what % of games hit a threshold"""
    if not values:
        return 0.0
    if over:
        hits = sum(1 for v in values if v > threshold)
    else:
        hits = sum(1 for v in values if v < threshold)
    return hits / len(values)


def collect_players_data():
    """Collect player analysis data using DuckDB"""
    conn = duckdb.connect('data/superbowl.db')

    # Load 2025 player data
    player_data = conn.execute("""
        SELECT * FROM player_game_logs WHERE season = 2025
    """).fetchdf()

    if len(player_data) == 0:
        return {'summaries': []}

    # Load Super Bowl history
    sb_history_path = Path("data/superbowl_player_history.parquet")
    sb_benchmarks = {}
    if sb_history_path.exists():
        sb_data = conn.execute(f"""
            SELECT position,
                   AVG(passing_yards) as avg_pass_yds,
                   AVG(passing_tds) as avg_pass_td,
                   AVG(rushing_yards) as avg_rush_yds,
                   AVG(rushing_tds) as avg_rush_td,
                   AVG(receptions) as avg_rec,
                   AVG(receiving_yards) as avg_rec_yds,
                   AVG(receiving_tds) as avg_rec_td
            FROM read_parquet('{sb_history_path}')
            GROUP BY position
        """).fetchall()

        for row in sb_data:
            pos = row[0]
            sb_benchmarks[pos] = {
                'passing_yards': row[1],
                'passing_tds': row[2],
                'rushing_yards': row[3],
                'rushing_tds': row[4],
                'receptions': row[5],
                'receiving_yards': row[6],
                'receiving_tds': row[7]
            }

    # Load player config
    config_path = Path("players_to_track.json")
    if not config_path.exists():
        return {'summaries': []}

    with open(config_path) as f:
        config = json.load(f)

    summaries = []
    for player_config in config["players"]:
        player_name = player_config["name"]
        position = player_config["position"]

        # Skip placeholders
        if player_name.startswith("Player Name"):
            continue

        # Get player's games
        player_games = player_data[player_data['player_name'] == player_name]

        if len(player_games) == 0:
            continue

        # Calculate stats - separate metadata from stats for template
        player_summary = {
            'name': player_name,
            'position': position,
            'team': player_games.iloc[0]['team'],
            'games_played': len(player_games),
            'stats': {}
        }

        stats = player_summary['stats']

        # Key stats based on position
        if position == 'QB':
            pass_yds = player_games['passing_yards'].tolist()
            pass_tds = player_games['passing_tds'].tolist()

            stats['avg_pass_yds'] = sum(pass_yds) / len(pass_yds)
            stats['pass_250_rate'] = calculate_hit_rate(pass_yds, 250, over=True)
            stats['pass_2td_rate'] = calculate_hit_rate(pass_tds, 1.5, over=True)

            # Super Bowl benchmark comparison
            if 'QB' in sb_benchmarks:
                stats['sb_avg_pass_yds'] = sb_benchmarks['QB']['passing_yards']
                stats['sb_avg_pass_tds'] = sb_benchmarks['QB']['passing_tds']

        elif position == 'RB':
            rush_yds = player_games['rushing_yards'].tolist()

            stats['avg_rush_yds'] = sum(rush_yds) / len(rush_yds)
            stats['rush_75_rate'] = calculate_hit_rate(rush_yds, 75, over=True)

            if 'RB' in sb_benchmarks:
                stats['sb_avg_rush_yds'] = sb_benchmarks['RB']['rushing_yards']

        elif position in ['WR', 'TE']:
            rec = player_games['receptions'].tolist()
            rec_yds = player_games['receiving_yards'].tolist()

            stats['avg_rec'] = sum(rec) / len(rec)
            stats['avg_rec_yds'] = sum(rec_yds) / len(rec_yds)
            stats['rec_5_rate'] = calculate_hit_rate(rec, 4.5, over=True)
            stats['rec_60_rate'] = calculate_hit_rate(rec_yds, 60, over=True)

            if position in sb_benchmarks:
                stats['sb_avg_rec'] = sb_benchmarks[position]['receptions']
                stats['sb_avg_rec_yds'] = sb_benchmarks[position]['receiving_yards']

        summaries.append(player_summary)

    conn.close()
    return {'summaries': summaries}


def generate_pages(data, output_dir):
    """Generate HTML pages"""
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

    # Generate players page
    if (template_dir / 'players.html').exists():
        template = env.get_template('players.html')
        output = template.render(data=data)
        with open(output_dir / 'players.html', 'w') as f:
            f.write(output)
        print("✅ Generated players.html")

    # Generate index page (simple version)
    index_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Super Bowl LIX Player Props Analysis</title>
    <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
    <h1>Super Bowl LIX Player Props Analysis</h1>
    <h2>Seattle Seahawks vs New England Patriots</h2>

    <nav>
        <a href="players.html">Player Analysis</a>
    </nav>

    <div>
        <h3>Data Summary</h3>
        <ul>
            <li>{len(data['players']['summaries'])} players analyzed</li>
            <li>2025 season data</li>
            <li>Super Bowl historical benchmarks</li>
        </ul>
        <p>Last updated: {data['timestamp']}</p>
    </div>
</body>
</html>
"""
    with open(output_dir / 'index.html', 'w') as f:
        f.write(index_html)
    print("✅ Generated index.html")


def generate_site():
    """Generate static site"""
    print("🏈 Generating static site...\n")

    print("📊 Collecting player data...")
    data = {
        'players': collect_players_data(),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    print("📝 Generating HTML pages...")
    output_dir = Path("static_site")
    generate_pages(data, output_dir)

    print(f"\n✅ Site generated at {output_dir}/")
    print("   Open static_site/index.html in your browser")


if __name__ == "__main__":
    generate_site()
