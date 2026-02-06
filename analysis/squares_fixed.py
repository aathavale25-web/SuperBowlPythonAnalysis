"""
Fixed squares analysis using actual combination frequencies
"""

import duckdb
from collections import defaultdict, Counter
from pathlib import Path


def load_superbowl_games():
    """Load Super Bowl game scores"""
    conn = duckdb.connect('data/superbowl.db')

    games = conn.execute("""
        SELECT
            year, winner_q1, loser_q1, winner_q2, loser_q2,
            winner_q3, loser_q3, winner_q4, loser_q4,
            winner_final, loser_final
        FROM superbowl_scores
        ORDER BY year DESC
    """).fetchall()

    conn.close()

    return [
        {
            "year": g[0],
            "winner_q1": g[1], "loser_q1": g[2],
            "winner_q2": g[3], "loser_q2": g[4],
            "winner_q3": g[5], "loser_q3": g[6],
            "winner_q4": g[7], "loser_q4": g[8],
            "winner_final": g[9], "loser_final": g[10]
        }
        for g in games
    ]


def apply_recency_weighting(games, current_year=2024):
    """Apply recency weighting to games"""
    weighted_games = []

    for game in games:
        year = game.get("year", current_year)
        years_ago = current_year - year

        # Determine weight
        if years_ago < 5:
            weight = 3
        elif years_ago < 15:
            weight = 2
        else:
            weight = 1

        for _ in range(weight):
            weighted_games.append(game)

    return weighted_games


def calculate_combination_frequency(games, quarter):
    """
    Calculate actual (winner_digit, loser_digit) combination frequencies

    Args:
        games: List of game dicts
        quarter: Which quarter ('q1', 'q2', 'q3', 'q4', 'final')

    Returns:
        Counter of (winner_digit, loser_digit) tuples
    """
    combinations = Counter()
    winner_key = f"winner_{quarter}"
    loser_key = f"loser_{quarter}"

    for game in games:
        if winner_key in game and loser_key in game:
            winner_score = game[winner_key]
            loser_score = game[loser_key]

            winner_digit = winner_score % 10
            loser_digit = loser_score % 10

            combinations[(winner_digit, loser_digit)] += 1

    return combinations


def calculate_probability_matrix(combinations):
    """
    Calculate 10x10 probability matrix from actual combinations

    Args:
        combinations: Counter of (winner_digit, loser_digit) tuples

    Returns:
        10x10 matrix of probabilities
    """
    total_count = sum(combinations.values())

    if total_count == 0:
        # If no data, return uniform distribution
        uniform_prob = 1.0 / 100
        return [[uniform_prob for _ in range(10)] for _ in range(10)]

    # Create 10x10 matrix
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
    """
    Rank all squares by probability

    Args:
        matrix: 10x10 probability matrix

    Returns:
        List of (winner, loser, probability) tuples sorted by probability
    """
    squares = []
    for winner in range(10):
        for loser in range(10):
            prob = matrix[winner][loser]
            squares.append((winner, loser, prob))

    # Sort by probability (highest first)
    squares.sort(key=lambda x: x[2], reverse=True)

    return squares


if __name__ == "__main__":
    print("🎲 Fixed Squares Analysis\n")

    games = load_superbowl_games()
    weighted_games = apply_recency_weighting(games)

    for quarter in ['q1', 'final']:
        combinations = calculate_combination_frequency(weighted_games, quarter)
        matrix = calculate_probability_matrix(combinations)

        total_prob = sum(sum(row) for row in matrix)
        print(f"{quarter.upper()}: Total probability = {total_prob:.6f}")

        ranked = rank_squares(matrix)
        print(f"  Top 3:")
        for i, (w, l, p) in enumerate(ranked[:3], 1):
            print(f"    {i}. {w}-{l}: {p*100:.2f}%")
        print()
