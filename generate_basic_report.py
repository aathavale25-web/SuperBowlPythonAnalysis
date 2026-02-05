"""
Generate basic HTML report without Polars
"""

import duckdb
import json
from pathlib import Path
from datetime import datetime


def generate_report():
    """Generate basic HTML report"""
    print("🏈 Generating basic report...\n")

    conn = duckdb.connect('data/superbowl.db')

    # Get 2025 player stats
    players = conn.execute("""
        SELECT
            player_name,
            team,
            COUNT(*) as games,
            CAST(AVG(passing_yards) AS INTEGER) as avg_pass_yds,
            CAST(AVG(passing_tds) AS INTEGER) as avg_pass_td,
            CAST(AVG(rushing_yards) AS INTEGER) as avg_rush_yds,
            CAST(AVG(rushing_tds) AS INTEGER) as avg_rush_td,
            CAST(AVG(receptions) AS INTEGER) as avg_rec,
            CAST(AVG(receiving_yards) AS INTEGER) as avg_rec_yds,
            CAST(AVG(receiving_tds) AS INTEGER) as avg_rec_td
        FROM player_game_logs
        WHERE season = 2025
        GROUP BY player_name, team
        ORDER BY player_name
    """).fetchall()

    # Load config for positions
    with open('players_to_track.json') as f:
        config = json.load(f)

    positions = {p['name']: p['position'] for p in config['players']}

    # Load SB benchmarks
    sb_path = Path("data/superbowl_player_history.parquet")
    sb_benchmarks = {}
    if sb_path.exists():
        sb_data = conn.execute(f"""
            SELECT position,
                   CAST(AVG(passing_yards) AS INTEGER) as avg_pass_yds,
                   CAST(AVG(rushing_yards) AS INTEGER) as avg_rush_yds,
                   CAST(AVG(receptions) AS INTEGER) as avg_rec,
                   CAST(AVG(receiving_yards) AS INTEGER) as avg_rec_yds
            FROM read_parquet('{sb_path}')
            GROUP BY position
        """).fetchall()

        for row in sb_data:
            sb_benchmarks[row[0]] = {
                'pass': row[1],
                'rush': row[2],
                'rec': row[3],
                'rec_yds': row[4]
            }

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Super Bowl LIX Player Props - Seattle Seahawks</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        h1 {{ color: #002244; }}
        h2 {{ color: #69BE28; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; background: white; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #002244; color: white; }}
        .highlight {{ background-color: #fff3cd; }}
        .good {{ color: #28a745; font-weight: bold; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>🏈 Super Bowl LIX Player Props Analysis</h1>
    <h2>Seattle Seahawks vs New England Patriots</h2>
    <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>Seattle Seahawks - 2025 Season Stats</h2>
    <table>
        <tr>
            <th>Player</th>
            <th>Position</th>
            <th>Games</th>
            <th>Pass Yds</th>
            <th>Pass TD</th>
            <th>Rush Yds</th>
            <th>Rush TD</th>
            <th>Receptions</th>
            <th>Rec Yds</th>
            <th>Rec TD</th>
        </tr>
"""

    for row in players:
        name = row[0]
        pos = positions.get(name, '?')
        team = row[1]
        games = row[2]

        # Highlight key stats based on position
        highlight_class = ""

        html += f"""        <tr class="{highlight_class}">
            <td><strong>{name}</strong></td>
            <td>{pos}</td>
            <td>{games}</td>
            <td>{row[3] if row[3] > 0 else '-'}</td>
            <td>{row[4] if row[4] > 0 else '-'}</td>
            <td>{row[5] if row[5] > 0 else '-'}</td>
            <td>{row[6] if row[6] > 0 else '-'}</td>
            <td>{row[7] if row[7] > 0 else '-'}</td>
            <td>{row[8] if row[8] > 0 else '-'}</td>
            <td>{row[9] if row[9] > 0 else '-'}</td>
        </tr>
"""

    html += """    </table>

    <h2>Super Bowl Historical Benchmarks (by Position)</h2>
    <table>
        <tr>
            <th>Position</th>
            <th>Avg Pass Yds</th>
            <th>Avg Rush Yds</th>
            <th>Avg Receptions</th>
            <th>Avg Rec Yds</th>
        </tr>
"""

    for pos in ['QB', 'RB', 'WR', 'TE']:
        if pos in sb_benchmarks:
            b = sb_benchmarks[pos]
            html += f"""        <tr>
            <td><strong>{pos}</strong></td>
            <td>{b['pass'] if b['pass'] > 0 else '-'}</td>
            <td>{b['rush'] if b['rush'] > 0 else '-'}</td>
            <td>{b['rec'] if b['rec'] > 0 else '-'}</td>
            <td>{b['rec_yds'] if b['rec_yds'] > 0 else '-'}</td>
        </tr>
"""

    html += """    </table>

    <h2>Key Insights</h2>
    <ul>
"""

    # Add insights for each player
    for row in players:
        name = row[0]
        pos = positions.get(name, '?')

        if pos == 'QB' and row[3] > 0:
            html += f"        <li><strong>{name} (QB):</strong> Averaging {row[3]} passing yards per game</li>\n"
        elif pos == 'RB' and row[5] > 0:
            html += f"        <li><strong>{name} (RB):</strong> Averaging {row[5]} rushing yards per game</li>\n"
        elif pos in ['WR', 'TE'] and row[7] > 0:
            html += f"        <li><strong>{name} ({pos}):</strong> Averaging {row[7]} receptions, {row[8]} yards per game</li>\n"

    html += """    </ul>

    <p><em>Note: Analysis based on 2025 regular season data and historical Super Bowl performance by position.</em></p>
</body>
</html>
"""

    # Write to file
    output_dir = Path("static_site")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "index.html"
    with open(output_file, 'w') as f:
        f.write(html)

    conn.close()

    print(f"✅ Report generated at {output_file}")
    print(f"   Open in browser: open {output_file}")


if __name__ == "__main__":
    generate_report()
