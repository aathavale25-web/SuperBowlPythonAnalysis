"""
Monte Carlo simulation model for player prop betting analysis
Generates probability distributions and over/under recommendations
"""

import numpy as np
import duckdb
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PropLine:
    """Betting prop line with probabilities"""
    stat_name: str
    line: float
    over_prob: float
    under_prob: float
    mean: float
    median: float
    std_dev: float
    confidence_80: Tuple[float, float]  # 80% confidence interval
    recent_trend: str  # "up", "down", "stable"


def load_player_stats(player_name: str, position: str, season: int = 2025) -> Dict:
    """Load player statistics from database"""
    conn = duckdb.connect('data/superbowl.db')

    # Get all games for player
    games = conn.execute("""
        SELECT
            week, game_type, game_result,
            passing_yards, passing_tds, interceptions,
            rushing_yards, rushing_tds,
            receptions, receiving_yards, receiving_tds
        FROM player_game_logs
        WHERE player_name = ? AND season = ?
        ORDER BY week
    """, [player_name, season]).fetchall()

    conn.close()

    return {
        'player_name': player_name,
        'position': position,
        'games': games,
        'num_games': len(games)
    }


def extract_stat_values(games: List, stat_index: int, recent_only: bool = False) -> np.ndarray:
    """Extract specific stat values from games"""
    if recent_only:
        games = games[-5:]  # Last 5 games

    values = [game[stat_index] for game in games if game[stat_index] is not None]
    return np.array(values)


def calculate_trend(values: np.ndarray) -> str:
    """Calculate trend direction for recent games"""
    if len(values) < 3:
        return "stable"

    recent = values[-3:]
    early = values[:-3] if len(values) > 3 else values[:1]

    recent_avg = np.mean(recent)
    early_avg = np.mean(early)

    diff_pct = (recent_avg - early_avg) / early_avg if early_avg > 0 else 0

    if diff_pct > 0.15:
        return "up"
    elif diff_pct < -0.15:
        return "down"
    else:
        return "stable"


def monte_carlo_simulation(historical_values: np.ndarray,
                          n_simulations: int = 10000,
                          weight_recent: bool = True) -> np.ndarray:
    """
    Run Monte Carlo simulation for player prop outcomes

    Uses historical distribution with optional recency weighting
    """
    if len(historical_values) == 0:
        return np.array([0])

    # Calculate mean and std from historical data
    mean = np.mean(historical_values)
    std = np.std(historical_values)

    # If weighting recent games, adjust mean toward recent average
    if weight_recent and len(historical_values) >= 5:
        recent_mean = np.mean(historical_values[-5:])
        mean = 0.7 * recent_mean + 0.3 * mean  # 70% recent, 30% season

    # Add Super Bowl factor (slightly higher variance)
    std = std * 1.1

    # Ensure non-negative values for counting stats
    simulations = np.random.normal(mean, std, n_simulations)
    simulations = np.maximum(simulations, 0)  # No negative stats

    return simulations


def analyze_prop_line(player_data: Dict,
                     stat_name: str,
                     stat_index: int,
                     suggested_line: float = None) -> PropLine:
    """
    Analyze a specific prop bet line using Monte Carlo simulation
    """
    games = player_data['games']
    position = player_data['position']

    # Extract historical values
    historical = extract_stat_values(games, stat_index)

    if len(historical) == 0:
        return None

    # Run Monte Carlo simulation
    simulations = monte_carlo_simulation(historical, n_simulations=10000)

    # Calculate statistics
    mean = np.mean(simulations)
    median = np.median(simulations)
    std_dev = np.std(simulations)

    # 80% confidence interval (10th to 90th percentile)
    conf_80 = (np.percentile(simulations, 10), np.percentile(simulations, 90))

    # Determine suggested line if not provided
    if suggested_line is None:
        suggested_line = median

    # Calculate over/under probabilities
    over_prob = np.mean(simulations > suggested_line) * 100
    under_prob = 100 - over_prob

    # Calculate trend
    trend = calculate_trend(historical)

    return PropLine(
        stat_name=stat_name,
        line=suggested_line,
        over_prob=over_prob,
        under_prob=under_prob,
        mean=mean,
        median=median,
        std_dev=std_dev,
        confidence_80=conf_80,
        recent_trend=trend
    )


def generate_player_props(player_name: str, position: str, season: int = 2025) -> Dict[str, PropLine]:
    """
    Generate all relevant prop lines for a player based on position
    """
    player_data = load_player_stats(player_name, position, season)
    props = {}

    if position == 'QB':
        # Passing yards (index 3)
        props['passing_yards'] = analyze_prop_line(
            player_data, 'Passing Yards', 3
        )

        # Passing TDs (index 4)
        props['passing_tds'] = analyze_prop_line(
            player_data, 'Passing TDs', 4
        )

        # Interceptions (index 5)
        props['interceptions'] = analyze_prop_line(
            player_data, 'Interceptions', 5
        )

        # Rushing yards (index 6)
        props['rushing_yards'] = analyze_prop_line(
            player_data, 'Rushing Yards', 6
        )

    elif position == 'RB':
        # Rushing yards (index 6)
        props['rushing_yards'] = analyze_prop_line(
            player_data, 'Rushing Yards', 6
        )

        # Rushing TDs (index 7)
        props['rushing_tds'] = analyze_prop_line(
            player_data, 'Rushing TDs', 7
        )

        # Receptions (index 8)
        props['receptions'] = analyze_prop_line(
            player_data, 'Receptions', 8
        )

        # Receiving yards (index 9)
        props['receiving_yards'] = analyze_prop_line(
            player_data, 'Receiving Yards', 9
        )

    elif position in ['WR', 'TE']:
        # Receptions (index 8)
        props['receptions'] = analyze_prop_line(
            player_data, 'Receptions', 8
        )

        # Receiving yards (index 9)
        props['receiving_yards'] = analyze_prop_line(
            player_data, 'Receiving Yards', 9
        )

        # Receiving TDs (index 10)
        props['receiving_tds'] = analyze_prop_line(
            player_data, 'Receiving TDs', 10
        )

    return {k: v for k, v in props.items() if v is not None}


def get_prop_recommendation(prop: PropLine) -> str:
    """
    Get betting recommendation based on probability edge
    """
    # Strong edge if probability is 60%+
    if prop.over_prob >= 60:
        return f"✅ OVER (Edge: {prop.over_prob:.1f}%)"
    elif prop.under_prob >= 60:
        return f"✅ UNDER (Edge: {prop.under_prob:.1f}%)"
    # Moderate edge if 55-60%
    elif prop.over_prob >= 55:
        return f"↗️ Lean OVER ({prop.over_prob:.1f}%)"
    elif prop.under_prob >= 55:
        return f"↘️ Lean UNDER ({prop.under_prob:.1f}%)"
    else:
        return f"⚖️ No edge ({prop.over_prob:.1f}% / {prop.under_prob:.1f}%)"


def analyze_alternate_lines(player_name: str, position: str,
                           stat_name: str, stat_index: int,
                           lines: List[float]) -> List[PropLine]:
    """
    Analyze multiple alternate lines for same prop
    """
    player_data = load_player_stats(player_name, position)
    results = []

    for line in lines:
        prop = analyze_prop_line(player_data, stat_name, stat_index, line)
        if prop:
            results.append(prop)

    return results


if __name__ == "__main__":
    # Example usage
    print("🏈 Player Props Model - Monte Carlo Simulation\n")

    # Analyze Drake Maye
    props = generate_player_props("Drake Maye", "QB")

    print("Drake Maye (QB) - Suggested Lines:\n")
    for stat_name, prop in props.items():
        print(f"{prop.stat_name}:")
        print(f"  Suggested Line: {prop.line:.1f}")
        print(f"  Mean: {prop.mean:.1f}, Median: {prop.median:.1f}")
        print(f"  80% Range: {prop.confidence_80[0]:.0f}-{prop.confidence_80[1]:.0f}")
        print(f"  Over: {prop.over_prob:.1f}% | Under: {prop.under_prob:.1f}%")
        print(f"  Trend: {prop.recent_trend}")
        print(f"  Recommendation: {get_prop_recommendation(prop)}")
        print()
