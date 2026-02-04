"""
Analysis for Super Bowl squares betting
"""

import duckdb
from pathlib import Path
from collections import defaultdict
import plotly.graph_objects as go


def calculate_digit_frequency(games, quarter):
    """
    Calculate frequency of last digits in scores

    Args:
        games: List of game dicts with score data
        quarter: Which quarter to analyze ("q1", "q2", "q3", "q4", or "final")

    Returns:
        dict with "winner" and "loser" digit frequencies
    """
    winner_digits = defaultdict(int)
    loser_digits = defaultdict(int)

    winner_key = f"winner_{quarter}"
    loser_key = f"loser_{quarter}"

    for game in games:
        if winner_key in game and loser_key in game:
            winner_score = game[winner_key]
            loser_score = game[loser_key]

            # Get last digit (0-9)
            winner_digit = winner_score % 10
            loser_digit = loser_score % 10

            winner_digits[winner_digit] += 1
            loser_digits[loser_digit] += 1

    return {
        "winner": dict(winner_digits),
        "loser": dict(loser_digits)
    }


def apply_recency_weighting(games, current_year=2024):
    """
    Apply recency weighting to games

    Args:
        games: List of game dicts with year field
        current_year: Current year for calculating recency

    Returns:
        List of games with recency weighting applied (duplicated entries)
    """
    weighted_games = []

    for game in games:
        year = game.get("year", current_year)
        years_ago = current_year - year

        # Determine weight
        if years_ago < 5:
            weight = 3  # Last 5 years: 3x
        elif years_ago < 15:
            weight = 2  # Last 15 years: 2x
        else:
            weight = 1  # Older: 1x

        # Add game multiple times based on weight
        for _ in range(weight):
            weighted_games.append(game)

    return weighted_games


def calculate_probability_matrix(frequencies):
    """
    Calculate 10x10 probability matrix from digit frequencies

    Args:
        frequencies: Dict with "winner" and "loser" digit frequency dicts

    Returns:
        10x10 matrix of probabilities
    """
    winner_freq = frequencies["winner"]
    loser_freq = frequencies["loser"]

    # Calculate total counts
    total_winner = sum(winner_freq.values()) or 1
    total_loser = sum(loser_freq.values()) or 1

    # Create 10x10 matrix
    matrix = []
    for winner_digit in range(10):
        row = []
        for loser_digit in range(10):
            # Probability = P(winner digit) * P(loser digit)
            # (assuming independence)
            p_winner = winner_freq.get(winner_digit, 0) / total_winner
            p_loser = loser_freq.get(loser_digit, 0) / total_loser
            prob = p_winner * p_loser
            row.append(prob)
        matrix.append(row)

    # Normalize to ensure sum = 1.0
    total_prob = sum(sum(row) for row in matrix)
    if total_prob > 0:
        matrix = [[prob / total_prob for prob in row] for row in matrix]

    return matrix


def rank_squares(matrix):
    """
    Rank all 100 squares by probability

    Args:
        matrix: 10x10 probability matrix

    Returns:
        List of (winner_digit, loser_digit, probability) tuples, sorted descending
    """
    squares = []

    for winner_digit in range(10):
        for loser_digit in range(10):
            prob = matrix[winner_digit][loser_digit]
            squares.append((winner_digit, loser_digit, prob))

    # Sort by probability (descending)
    squares.sort(key=lambda x: x[2], reverse=True)

    return squares


def load_superbowl_games():
    """
    Load Super Bowl games from database

    Returns:
        List of game dicts
    """
    db_path = Path("data/superbowl.db")
    if not db_path.exists():
        return []

    conn = duckdb.connect(str(db_path))

    try:
        result = conn.execute("""
            SELECT year, winner, loser,
                   winner_q1, winner_q2, winner_q3, winner_q4, winner_final,
                   loser_q1, loser_q2, loser_q3, loser_q4, loser_final
            FROM superbowl_games
            ORDER BY year DESC
        """).fetchall()

        games = []
        for row in result:
            games.append({
                "year": row[0],
                "winner": row[1],
                "loser": row[2],
                "winner_q1": row[3],
                "winner_q2": row[4],
                "winner_q3": row[5],
                "winner_q4": row[6],
                "winner_final": row[7],
                "loser_q1": row[8],
                "loser_q2": row[9],
                "loser_q3": row[10],
                "loser_q4": row[11],
                "loser_final": row[12]
            })

        return games

    finally:
        conn.close()


def generate_heatmap(matrix, title, output_path):
    """
    Generate Plotly heatmap visualization

    Args:
        matrix: 10x10 probability matrix
        title: Chart title
        output_path: Path to save HTML file
    """
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=list(range(10)),
        y=list(range(10)),
        colorscale='RdYlGn',
        text=[[f'{val:.2%}' for val in row] for row in matrix],
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Probability")
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Loser's Last Digit",
        yaxis_title="Winner's Last Digit",
        width=800,
        height=800
    )

    # Save to HTML
    fig.write_html(output_path)


def adjust_probabilities_for_teams(matrix, team1_fg_heavy=False, team2_fg_heavy=False):
    """
    Adjust probabilities based on team scoring tendencies

    Args:
        matrix: Base 10x10 probability matrix
        team1_fg_heavy: Whether team 1 (winner position) is FG-heavy
        team2_fg_heavy: Whether team 2 (loser position) is FG-heavy

    Returns:
        Adjusted 10x10 probability matrix
    """
    # FG-heavy teams favor digits: 0, 3, 6, 7 (multiples of 3 and common TD+XP combinations)
    fg_digits = {0, 3, 6, 7}

    # Copy matrix
    adjusted = [row[:] for row in matrix]

    # Boost probabilities for FG-heavy team digits
    boost_factor = 1.3
    penalty_factor = 0.7

    for i in range(10):
        for j in range(10):
            # Team 1 (winner/row)
            if team1_fg_heavy:
                if i in fg_digits:
                    adjusted[i][j] *= boost_factor
                else:
                    adjusted[i][j] *= penalty_factor

            # Team 2 (loser/column)
            if team2_fg_heavy:
                if j in fg_digits:
                    adjusted[i][j] *= boost_factor
                else:
                    adjusted[i][j] *= penalty_factor

    # Renormalize
    total = sum(sum(row) for row in adjusted)
    if total > 0:
        adjusted = [[val / total for val in row] for row in adjusted]

    return adjusted


def analyze_squares():
    """
    Analyze quarter score patterns for squares betting
    """
    print("🎲 Starting Super Bowl Squares Analysis...\n")

    # Load games
    games = load_superbowl_games()
    if not games:
        print("❌ No Super Bowl games found in database")
        return

    print(f"✅ Loaded {len(games)} Super Bowl games")

    # Apply recency weighting
    weighted_games = apply_recency_weighting(games)
    print(f"✅ Applied recency weighting ({len(weighted_games)} weighted samples)\n")

    # Analyze each quarter and final
    quarters = ["q1", "q2", "q3", "q4", "final"]

    all_matrices = {}

    for quarter in quarters:
        print(f"📊 Analyzing {quarter.upper()}...")

        # Calculate digit frequencies
        freq = calculate_digit_frequency(weighted_games, quarter)

        # Calculate probability matrix
        matrix = calculate_probability_matrix(freq)

        # Store for later use
        all_matrices[quarter] = matrix

        # Rank squares
        ranked = rank_squares(matrix)

        print(f"   Top 5 squares for {quarter.upper()}:")
        for i, (w, l, prob) in enumerate(ranked[:5], 1):
            print(f"      {i}. {w}-{l}: {prob:.2%}")

    # Generate visualizations
    print(f"\n📈 Generating heatmaps...")

    static_dir = Path("static_site")
    static_dir.mkdir(exist_ok=True)

    for quarter in quarters:
        output_path = static_dir / f"squares_heatmap_{quarter}.html"
        generate_heatmap(
            all_matrices[quarter],
            f"Super Bowl Squares Probability - {quarter.upper()}",
            str(output_path)
        )
        print(f"   ✅ Saved {output_path}")

    # Show overall rankings (final score)
    print(f"\n🏆 TOP 10 BEST SQUARES (Final Score):")
    print(f"=" * 60)

    ranked_final = rank_squares(all_matrices["final"])

    for i, (w, l, prob) in enumerate(ranked_final[:10], 1):
        print(f"{i:2d}. Winner: {w}, Loser: {l}  -  {prob:.3%} probability")

    print(f"\n💀 TOP 10 WORST SQUARES (Final Score):")
    print(f"=" * 60)

    for i, (w, l, prob) in enumerate(ranked_final[-10:][::-1], 1):
        print(f"{i:2d}. Winner: {w}, Loser: {l}  -  {prob:.3%} probability")

    print(f"\n🎉 Analysis complete!")


if __name__ == "__main__":
    analyze_squares()
