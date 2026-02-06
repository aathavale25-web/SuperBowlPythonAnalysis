"""
Generate game progression data for conditional probability calculations
"""

import json
from pathlib import Path
from analysis.squares import load_superbowl_games, apply_recency_weighting

def filter_games_by_type(games, game_type):
    """Filter games by type"""
    if game_type == 'all':
        return games
    elif game_type == 'championship':
        return [g for g in games if g.get('game_type') in ['afc_championship', 'nfc_championship']]
    else:
        return [g for g in games if g.get('game_type') == game_type]


def build_game_progressions(games):
    """
    Build game progression data showing score evolution quarter by quarter

    Returns:
        dict mapping quarter pairs to conditional probabilities
    """
    quarters = ['q1', 'q2', 'q3', 'q4', 'final']

    # For each quarter pair (e.g., q1 -> q2), build conditional probabilities
    progressions = {}

    for i in range(len(quarters) - 1):
        prev_quarter = quarters[i]
        next_quarter = quarters[i + 1]

        pair_key = f"{prev_quarter}_to_{next_quarter}"
        progressions[pair_key] = {}

        # For each game, record the progression
        for game in games:
            prev_winner = game.get(f'winner_{prev_quarter}', 0)
            prev_loser = game.get(f'loser_{prev_quarter}', 0)

            next_winner = game.get(f'winner_{next_quarter}', 0)
            next_loser = game.get(f'loser_{next_quarter}', 0)

            # Get last digits
            prev_key = f"{prev_winner % 10}-{prev_loser % 10}"
            next_key = f"{next_winner % 10}-{next_loser % 10}"

            if prev_key not in progressions[pair_key]:
                progressions[pair_key][prev_key] = {}

            if next_key not in progressions[pair_key][prev_key]:
                progressions[pair_key][prev_key][next_key] = 0

            progressions[pair_key][prev_key][next_key] += 1

    # Convert counts to probabilities
    for pair_key in progressions:
        for prev_key in progressions[pair_key]:
            total = sum(progressions[pair_key][prev_key].values())
            for next_key in progressions[pair_key][prev_key]:
                progressions[pair_key][prev_key][next_key] = {
                    'count': progressions[pair_key][prev_key][next_key],
                    'probability': progressions[pair_key][prev_key][next_key] / total if total > 0 else 0
                }

    return progressions


def generate_progression_data():
    """Generate full progression data for all filters"""
    all_games = load_superbowl_games()

    filters = {
        'all': 'All Games',
        'superbowl': 'Super Bowl Only',
        'championship': 'Championship Games',
        'afc_championship': 'AFC Championship',
        'nfc_championship': 'NFC Championship'
    }

    results = {}

    for filter_key, filter_name in filters.items():
        print(f"\n📊 Generating progressions for: {filter_name}")

        filtered_games = filter_games_by_type(all_games, filter_key)

        if not filtered_games:
            continue

        weighted_games = apply_recency_weighting(filtered_games)

        print(f"   {len(filtered_games)} games, {len(weighted_games)} weighted samples")

        progressions = build_game_progressions(weighted_games)

        results[filter_key] = {
            'name': filter_name,
            'game_count': len(filtered_games),
            'sample_count': len(weighted_games),
            'progressions': progressions
        }

    return results


if __name__ == "__main__":
    print("🎲 Generating Game Progression Data...\n")

    data = generate_progression_data()

    # Save to JSON
    output_path = Path("data/game_progressions.json")
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Saved to {output_path}")

    # Show example
    print("\n📊 Example: Q1 7-3 -> Q2 in All Games")
    if 'all' in data and 'q1_to_q2' in data['all']['progressions']:
        q1_to_q2 = data['all']['progressions']['q1_to_q2']
        if '7-3' in q1_to_q2:
            print(f"   Found {len(q1_to_q2['7-3'])} different Q2 outcomes")
            # Show top 3
            sorted_outcomes = sorted(q1_to_q2['7-3'].items(),
                                    key=lambda x: x[1]['count'], reverse=True)
            for next_square, stats in sorted_outcomes[:3]:
                print(f"     {next_square}: {stats['probability']*100:.1f}% ({stats['count']} games)")

    print("\n🎉 Done!")
