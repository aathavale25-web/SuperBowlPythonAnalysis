"""
Generate betting prop lines with probabilities and recommendations
"""

import json
from pathlib import Path
from analysis.player_props_model import (
    generate_player_props,
    get_prop_recommendation,
    analyze_alternate_lines
)


# Typical Super Bowl prop lines (these would normally come from sportsbooks)
TYPICAL_LINES = {
    'QB': {
        'passing_yards': [225.5, 249.5, 274.5],
        'passing_tds': [1.5, 2.5],
        'interceptions': [0.5, 1.5],
        'rushing_yards': [19.5, 29.5]
    },
    'RB': {
        'rushing_yards': [49.5, 69.5, 89.5],
        'rushing_tds': [0.5],
        'receptions': [2.5, 3.5],
        'receiving_yards': [19.5, 29.5]
    },
    'WR': {
        'receptions': [4.5, 5.5, 6.5],
        'receiving_yards': [49.5, 69.5, 89.5],
        'receiving_tds': [0.5]
    },
    'TE': {
        'receptions': [3.5, 4.5, 5.5],
        'receiving_yards': [39.5, 49.5, 59.5],
        'receiving_tds': [0.5]
    }
}


STAT_INDEX_MAP = {
    'passing_yards': 3,
    'passing_tds': 4,
    'interceptions': 5,
    'rushing_yards': 6,
    'rushing_tds': 7,
    'receptions': 8,
    'receiving_yards': 9,
    'receiving_tds': 10
}


def generate_all_props():
    """Generate props for all players"""

    # Load player config
    config_path = Path("players_to_track.json")
    with open(config_path) as f:
        config = json.load(f)

    all_props = {}

    print("🎲 Generating Player Prop Lines...\n")

    for player in config['players']:
        name = player['name']
        position = player['position']

        if name.startswith("Player Name"):
            continue

        print(f"📊 Analyzing {name} ({position})...")

        # Generate base props
        props = generate_player_props(name, position)

        # Analyze alternate lines
        alternate_analysis = {}
        typical_lines = TYPICAL_LINES.get(position, {})

        for stat_name, lines in typical_lines.items():
            if stat_name in props:
                stat_index = STAT_INDEX_MAP[stat_name]
                alternates = analyze_alternate_lines(
                    name, position, stat_name, stat_index, lines
                )
                alternate_analysis[stat_name] = [
                    {
                        'line': alt.line,
                        'over_prob': alt.over_prob,
                        'under_prob': alt.under_prob,
                        'recommendation': get_prop_recommendation(alt),
                        'trend': alt.recent_trend
                    }
                    for alt in alternates
                ]

        all_props[name] = {
            'position': position,
            'base_props': {
                stat: {
                    'line': prop.line,
                    'mean': prop.mean,
                    'median': prop.median,
                    'std_dev': prop.std_dev,
                    'confidence_80_low': prop.confidence_80[0],
                    'confidence_80_high': prop.confidence_80[1],
                    'over_prob': prop.over_prob,
                    'under_prob': prop.under_prob,
                    'trend': prop.recent_trend,
                    'recommendation': get_prop_recommendation(prop)
                }
                for stat, prop in props.items()
            },
            'alternate_lines': alternate_analysis
        }

    # Save to JSON
    output_path = Path("data/player_prop_lines.json")
    with open(output_path, 'w') as f:
        json.dump(all_props, f, indent=2)

    print(f"\n✅ Generated prop lines for {len(all_props)} players")
    print(f"📁 Saved to {output_path}")

    return all_props


def print_best_bets(all_props, min_edge=55):
    """Print props with betting edge"""
    print(f"\n🎯 BEST BETS (Edge >= {min_edge}%)\n")
    print("=" * 80)

    best_bets = []

    for player_name, data in all_props.items():
        position = data['position']

        for stat_name, alternates in data['alternate_lines'].items():
            for alt in alternates:
                max_prob = max(alt['over_prob'], alt['under_prob'])
                if max_prob >= min_edge:
                    side = "OVER" if alt['over_prob'] > alt['under_prob'] else "UNDER"
                    edge = max_prob
                    best_bets.append({
                        'player': player_name,
                        'position': position,
                        'stat': stat_name.replace('_', ' ').title(),
                        'line': alt['line'],
                        'side': side,
                        'edge': edge,
                        'trend': alt['trend']
                    })

    # Sort by edge
    best_bets.sort(key=lambda x: x['edge'], reverse=True)

    for bet in best_bets:
        trend_emoji = "📈" if bet['trend'] == "up" else "📉" if bet['trend'] == "down" else "➡️"
        print(f"{bet['player']} ({bet['position']})")
        print(f"  {bet['stat']}: {bet['side']} {bet['line']}")
        print(f"  Edge: {bet['edge']:.1f}% {trend_emoji} {bet['trend']}")
        print()


if __name__ == "__main__":
    props = generate_all_props()
    print_best_bets(props, min_edge=55)
