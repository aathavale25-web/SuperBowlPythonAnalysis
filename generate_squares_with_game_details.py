"""
Generate squares analysis with game details for each combination
"""

import json
from pathlib import Path
from analysis.squares import (
    load_superbowl_games,
    apply_recency_weighting
)

def filter_games_by_type(games, game_type):
    """Filter games by type"""
    if game_type == 'all':
        return games
    elif game_type == 'championship':
        return [g for g in games if g.get('game_type') in ['afc_championship', 'nfc_championship']]
    else:
        return [g for g in games if g.get('game_type') == game_type]


def get_game_details_for_combinations(games, quarter):
    """
    Get game details for each (winner_digit, loser_digit) combination

    Args:
        games: List of game dicts
        quarter: Which quarter

    Returns:
        dict mapping (winner_digit, loser_digit) to list of game details
    """
    combinations = {}

    winner_key = f"winner_{quarter}"
    loser_key = f"loser_{quarter}"

    for game in games:
        if winner_key in game and loser_key in game:
            winner_score = game[winner_key]
            loser_score = game[loser_key]

            winner_digit = winner_score % 10
            loser_digit = loser_score % 10

            key = f"{winner_digit}-{loser_digit}"

            if key not in combinations:
                combinations[key] = []

            combinations[key].append({
                'year': game['year'],
                'game_type': game.get('game_type', 'superbowl'),
                'winner': game['winner'],
                'loser': game['loser'],
                'winner_score': winner_score,
                'loser_score': loser_score,
                'winner_final': game.get('winner_final', winner_score),
                'loser_final': game.get('loser_final', loser_score)
            })

    return combinations


def calculate_probability_matrix(games, quarter):
    """Calculate probability matrix from games"""
    from collections import Counter

    winner_key = f"winner_{quarter}"
    loser_key = f"loser_{quarter}"

    combinations = Counter()

    for game in games:
        if winner_key in game and loser_key in game:
            winner_digit = game[winner_key] % 10
            loser_digit = game[loser_key] % 10
            combinations[(winner_digit, loser_digit)] += 1

    total_count = sum(combinations.values())

    if total_count == 0:
        uniform_prob = 1.0 / 100
        return [[uniform_prob for _ in range(10)] for _ in range(10)]

    matrix = []
    for winner_digit in range(10):
        row = []
        for loser_digit in range(10):
            count = combinations.get((winner_digit, loser_digit), 0)
            prob = count / total_count
            row.append(prob)
        matrix.append(row)

    return matrix


def rank_squares(matrix):
    """Rank squares by probability"""
    squares = []
    for winner_digit in range(10):
        for loser_digit in range(10):
            prob = matrix[winner_digit][loser_digit]
            squares.append((winner_digit, loser_digit, prob))

    squares.sort(key=lambda x: x[2], reverse=True)
    return squares


def generate_squares_data():
    """Generate squares data with game details for each combination"""
    all_games = load_superbowl_games()

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

        filtered_games = filter_games_by_type(all_games, filter_key)

        if not filtered_games:
            print(f"   ⚠️  No games found for {filter_name}")
            continue

        weighted_games = apply_recency_weighting(filtered_games)

        print(f"   {len(filtered_games)} games, {len(weighted_games)} weighted samples")

        filter_data = {
            'name': filter_name,
            'game_count': len(filtered_games),
            'sample_count': len(weighted_games),
            'matrices': {},
            'ranked': {},
            'game_details': {}  # Add game details
        }

        for quarter in quarters:
            # Get game details for each combination
            game_details = get_game_details_for_combinations(filtered_games, quarter)
            filter_data['game_details'][quarter] = game_details

            # Calculate probability matrix
            matrix = calculate_probability_matrix(weighted_games, quarter)
            filter_data['matrices'][quarter] = matrix

            # Rank squares
            ranked_squares = rank_squares(matrix)
            filter_data['ranked'][quarter] = [
                {
                    'winner': w,
                    'loser': l,
                    'probability': prob
                }
                for w, l, prob in ranked_squares[:10]
            ]

        results[filter_key] = filter_data

    return results


if __name__ == "__main__":
    print("🎲 Generating Squares Analysis with Game Details...\n")

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
