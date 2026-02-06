"""
Generate squares analysis with game type filters
"""

import json
from pathlib import Path
from analysis.squares import (
    load_superbowl_games,
    apply_recency_weighting,
    calculate_combination_frequency,
    calculate_probability_matrix,
    rank_squares
)

def filter_games_by_type(games, game_type):
    """
    Filter games by type

    Args:
        games: List of game dicts
        game_type: 'all', 'superbowl', 'championship', 'afc_championship', 'nfc_championship'

    Returns:
        Filtered list of games
    """
    if game_type == 'all':
        return games
    elif game_type == 'championship':
        return [g for g in games if g.get('game_type') in ['afc_championship', 'nfc_championship']]
    else:
        return [g for g in games if g.get('game_type') == game_type]


def generate_squares_data():
    """
    Generate squares data for all filter combinations

    Returns:
        dict with matrices and ranked squares for each filter
    """
    # Load all games
    all_games = load_superbowl_games()

    # Game type filters
    filters = {
        'all': 'All Games',
        'superbowl': 'Super Bowl Only',
        'championship': 'Championship Games',
        'afc_championship': 'AFC Championship',
        'nfc_championship': 'NFC Championship'
    }

    quarters = ['q1', 'q2', 'q3', 'q4', 'final']

    results = {}

    for filter_key, filter_name in filters.items():
        print(f"\n📊 Generating data for: {filter_name}")

        # Filter games
        filtered_games = filter_games_by_type(all_games, filter_key)

        if not filtered_games:
            print(f"   ⚠️  No games found for {filter_name}")
            continue

        # Apply recency weighting
        weighted_games = apply_recency_weighting(filtered_games)

        print(f"   {len(filtered_games)} games, {len(weighted_games)} weighted samples")

        filter_data = {
            'name': filter_name,
            'game_count': len(filtered_games),
            'sample_count': len(weighted_games),
            'matrices': {},
            'ranked': {}
        }

        for quarter in quarters:
            combinations = calculate_combination_frequency(weighted_games, quarter)
            matrix = calculate_probability_matrix(combinations)

            filter_data['matrices'][quarter] = matrix

            ranked_squares = rank_squares(matrix)
            filter_data['ranked'][quarter] = [
                {
                    'winner': w,
                    'loser': l,
                    'probability': prob
                }
                for w, l, prob in ranked_squares[:10]  # Top 10
            ]

        results[filter_key] = filter_data

    return results


if __name__ == "__main__":
    print("🎲 Generating Squares Analysis with Filters...\n")

    data = generate_squares_data()

    # Save to JSON
    output_path = Path("data/squares_with_filters.json")
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Saved to {output_path}")

    # Show summary
    print("\n📊 Summary:")
    for filter_key, filter_data in data.items():
        print(f"   {filter_data['name']}: {filter_data['game_count']} games")

    print("\n🎉 Done!")
