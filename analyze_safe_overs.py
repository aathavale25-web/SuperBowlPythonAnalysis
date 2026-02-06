"""
Analyze player game logs to find safe OVER bets based on consistency
"""

import duckdb
from pathlib import Path
import json

# Common betting lines by position and stat
BETTING_LINES = {
    'QB': {
        'passing_yards': [199.5, 224.5, 249.5, 274.5, 299.5],
        'passing_tds': [1.5, 2.5],
        'interceptions': [0.5, 1.5],
        'rushing_yards': [9.5, 19.5, 29.5]
    },
    'RB': {
        'rushing_yards': [49.5, 59.5, 69.5, 79.5, 89.5],
        'rushing_tds': [0.5],
        'receptions': [2.5, 3.5, 4.5],
        'receiving_yards': [19.5, 29.5, 39.5]
    },
    'WR': {
        'receptions': [3.5, 4.5, 5.5, 6.5],
        'receiving_yards': [49.5, 59.5, 69.5, 79.5, 89.5],
        'receiving_tds': [0.5]
    },
    'TE': {
        'receptions': [2.5, 3.5, 4.5, 5.5],
        'receiving_yards': [39.5, 49.5, 59.5, 69.5],
        'receiving_tds': [0.5]
    }
}

def calculate_over_hit_rate(values, line):
    """Calculate what % of games went OVER the line"""
    if not values:
        return 0, 0

    overs = sum(1 for v in values if v > line)
    hit_rate = (overs / len(values)) * 100
    return hit_rate, overs


def analyze_player_overs(player_name, position):
    """Analyze all betting lines for a player"""
    conn = duckdb.connect('data/superbowl.db')

    # Get player's game logs
    games = conn.execute("""
        SELECT
            week,
            game_result,
            opponent,
            passing_yards,
            passing_tds,
            interceptions,
            rushing_yards,
            rushing_tds,
            receptions,
            receiving_yards,
            receiving_tds
        FROM player_game_logs
        WHERE player_name = ?
        AND season = 2025
        ORDER BY week
    """, [player_name]).fetchall()

    conn.close()

    if not games:
        return None

    # Extract stat values
    stats_data = {
        'passing_yards': [g[3] for g in games if g[3] is not None],
        'passing_tds': [g[4] for g in games if g[4] is not None],
        'interceptions': [g[5] for g in games if g[5] is not None],
        'rushing_yards': [g[6] for g in games if g[6] is not None],
        'rushing_tds': [g[7] for g in games if g[7] is not None],
        'receptions': [g[8] for g in games if g[8] is not None],
        'receiving_yards': [g[9] for g in games if g[9] is not None],
        'receiving_tds': [g[10] for g in games if g[10] is not None]
    }

    # Analyze each relevant stat for this position
    lines_for_position = BETTING_LINES.get(position, {})

    results = []

    for stat, lines in lines_for_position.items():
        values = stats_data.get(stat, [])
        if not values or len(values) < 3:  # Need at least 3 games
            continue

        for line in lines:
            hit_rate, overs = calculate_over_hit_rate(values, line)

            # Only include if hit rate >= 65% (reasonably safe)
            if hit_rate >= 65:
                results.append({
                    'player': player_name,
                    'position': position,
                    'stat': stat,
                    'line': line,
                    'hit_rate': hit_rate,
                    'overs': overs,
                    'games': len(values),
                    'avg': sum(values) / len(values),
                    'recent_avg': sum(values[-5:]) / len(values[-5:]) if len(values) >= 5 else sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'values': values
                })

    return results


def find_safe_overs():
    """Find all safe OVER bets across all players"""
    conn = duckdb.connect('data/superbowl.db')

    # Load player config to get positions
    config_path = Path("players_to_track.json")
    with open(config_path) as f:
        config = json.load(f)

    positions = {p['name']: p['position'] for p in config['players']}

    # Get all players
    players = conn.execute("""
        SELECT DISTINCT player_name
        FROM player_game_logs
        WHERE season = 2025
    """).fetchall()

    conn.close()

    all_safe_overs = []

    print("🎯 Analyzing Safe OVER Bets...\n")

    for player_row in players:
        player_name = player_row[0]
        position = positions.get(player_name, 'UNKNOWN')

        if position == 'UNKNOWN':
            continue

        print(f"Analyzing {player_name} ({position})...")

        results = analyze_player_overs(player_name, position)

        if results:
            all_safe_overs.extend(results)
            print(f"  Found {len(results)} safe overs")

    return all_safe_overs


if __name__ == "__main__":
    safe_overs = find_safe_overs()

    # Sort by hit rate
    safe_overs.sort(key=lambda x: x['hit_rate'], reverse=True)

    print(f"\n{'='*80}")
    print(f"🏆 SAFE OVER BETS (65%+ Hit Rate)")
    print(f"{'='*80}\n")

    # Group by confidence level
    elite = [o for o in safe_overs if o['hit_rate'] >= 85]
    strong = [o for o in safe_overs if 75 <= o['hit_rate'] < 85]
    good = [o for o in safe_overs if 65 <= o['hit_rate'] < 75]

    print(f"🔥 ELITE (85%+ Hit Rate) - {len(elite)} bets")
    print("-" * 80)
    for over in elite[:10]:
        stat_name = over['stat'].replace('_', ' ').title()
        print(f"{over['player']} ({over['position']})")
        print(f"  {stat_name} OVER {over['line']}")
        print(f"  Hit Rate: {over['hit_rate']:.1f}% ({over['overs']}/{over['games']} games)")
        print(f"  Season Avg: {over['avg']:.1f} | Recent Avg: {over['recent_avg']:.1f}")
        print(f"  Range: {over['min']}-{over['max']}")
        print()

    print(f"\n💪 STRONG (75-84% Hit Rate) - {len(strong)} bets")
    print("-" * 80)
    for over in strong[:10]:
        stat_name = over['stat'].replace('_', ' ').title()
        print(f"{over['player']} - {stat_name} OVER {over['line']}: {over['hit_rate']:.1f}% ({over['overs']}/{over['games']})")

    print(f"\n✅ GOOD (65-74% Hit Rate) - {len(good)} bets")
    print("-" * 80)
    for over in good[:10]:
        stat_name = over['stat'].replace('_', ' ').title()
        print(f"{over['player']} - {stat_name} OVER {over['line']}: {over['hit_rate']:.1f}% ({over['overs']}/{over['games']})")

    # Save to JSON
    output_path = Path("data/safe_overs.json")
    with open(output_path, 'w') as f:
        json.dump({
            'elite': elite,
            'strong': strong,
            'good': good,
            'all': safe_overs
        }, f, indent=2)

    print(f"\n✅ Saved to {output_path}")
    print(f"\nTotal Safe Overs Found: {len(safe_overs)}")
