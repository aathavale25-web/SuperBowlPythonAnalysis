"""
Player prop betting analysis
"""

import polars as pl


def calculate_player_stats(games, player_name):
    """Calculate statistics for a player"""
    # Filter to player
    player_games = games.filter(pl.col("player_name") == player_name)

    stats = {}

    # Calculate for all numeric columns
    stat_columns = [
        "passing_yards", "passing_tds", "interceptions",
        "rushing_yards", "rushing_tds",
        "receptions", "receiving_yards", "receiving_tds"
    ]

    for col in stat_columns:
        if col in player_games.columns:
            values = player_games[col]
            stats[f"avg_{col}"] = values.mean()
            stats[f"median_{col}"] = values.median()
            stats[f"high_{col}"] = values.max()
            stats[f"low_{col}"] = values.min()

    return stats


def calculate_position_benchmarks(sb_history, position):
    """
    Calculate Super Bowl position benchmarks

    Args:
        sb_history: Polars DataFrame with Super Bowl player history
        position: Position to calculate benchmarks for (e.g., "QB", "RB", "WR", "TE")

    Returns:
        dict with average stats for the position, or None if no data
    """
    # Filter to position
    position_players = sb_history.filter(pl.col("position") == position)

    if len(position_players) == 0:
        return None

    benchmarks = {}

    # Calculate averages for all stat columns
    stat_columns = [
        "passing_yards", "passing_tds", "interceptions",
        "rushing_yards", "rushing_tds",
        "receptions", "receiving_yards", "receiving_tds"
    ]

    for col in stat_columns:
        if col in position_players.columns:
            avg_value = position_players[col].mean()
            benchmarks[f"avg_{col}"] = avg_value

    return benchmarks


def calculate_combined_hit_rate(season_hit_rate, sb_position_hit_rate, season_weight=0.7):
    """
    Calculate combined hit rate from season and Super Bowl position data

    Args:
        season_hit_rate: Hit rate from player's season data (0.0 to 1.0)
        sb_position_hit_rate: Hit rate from SB position benchmark (0.0 to 1.0)
        season_weight: Weight for season data (default 0.7 for 70/30 split)

    Returns:
        Combined hit rate (0.0 to 1.0)
    """
    sb_weight = 1.0 - season_weight
    combined = (season_hit_rate * season_weight) + (sb_position_hit_rate * sb_weight)
    return combined


def calculate_hit_rates(games, player_name, stat_column, lines, player_filter=True):
    """Calculate hit rates for betting lines"""
    # Filter to player if player_filter is True
    if player_filter:
        player_games = games.filter(pl.col("player_name") == player_name)
        values = player_games[stat_column]
    else:
        # Use all games (for position benchmarks)
        values = games[stat_column]

    hit_rates = {}

    for line in lines:
        over_count = (values > line).sum()
        under_count = (values <= line).sum()
        total = len(values)

        hit_rates[line] = {
            "over": over_count,
            "under": under_count,
            "hit_rate_over": over_count / total if total > 0 else 0.0,
            "hit_rate_under": under_count / total if total > 0 else 0.0
        }

    return hit_rates


def identify_best_bets(hit_rates, threshold=0.65):
    """Identify best bets above threshold"""
    best_bets = {}

    for line, data in hit_rates.items():
        if data["hit_rate_over"] >= threshold:
            best_bets[line] = data

    return best_bets


def analyze_last_n_games_trend(games, player_name, stat_column, n=5):
    """Analyze trend in last N games"""
    # Filter to player and sort by week
    player_games = games.filter(pl.col("player_name") == player_name)
    player_games = player_games.sort("week")

    # Get values
    values = player_games[stat_column]

    if len(values) < n * 2:
        return {
            "direction": "insufficient_data",
            "last_n_avg": None,
            "previous_n_avg": None
        }

    # Last N games
    last_n = values[-n:]
    last_n_avg = last_n.mean()

    # Previous N games
    previous_n = values[-n*2:-n]
    previous_n_avg = previous_n.mean()

    # Determine direction
    if last_n_avg > previous_n_avg:
        direction = "improving"
    elif last_n_avg < previous_n_avg:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "direction": direction,
        "last_n_avg": last_n_avg,
        "previous_n_avg": previous_n_avg
    }


def load_player_data(parquet_path="data/player_stats_2024.parquet"):
    """Load player data from parquet file"""
    from pathlib import Path

    path = Path(parquet_path)
    if not path.exists():
        return None

    return pl.read_parquet(parquet_path)


def get_betting_lines_for_position(position):
    """Get common betting lines for a position"""
    lines = {
        "QB": {
            "passing_yards": [224.5, 249.5, 274.5, 299.5],
            "passing_tds": [1.5, 2.5],
            "interceptions": [0.5]
        },
        "RB": {
            "rushing_yards": [49.5, 74.5, 99.5],
            "rushing_tds": [0.5],
            "receptions": [2.5, 3.5]
        },
        "WR": {
            "receptions": [3.5, 4.5, 5.5],
            "receiving_yards": [49.5, 74.5, 99.5],
            "receiving_tds": [0.5]
        },
        "TE": {
            "receptions": [3.5, 4.5, 5.5],
            "receiving_yards": [49.5, 74.5, 99.5],
            "receiving_tds": [0.5]
        }
    }
    return lines.get(position, {})


def generate_player_summary(games, player_name, position):
    """Generate complete prop analysis summary for a player"""
    # Calculate basic stats
    stats = calculate_player_stats(games, player_name)

    # Get betting lines for position
    lines = get_betting_lines_for_position(position)

    # Calculate hit rates for each stat
    all_hit_rates = {}
    for stat_column, stat_lines in lines.items():
        if stat_column in games.columns:
            hit_rates = calculate_hit_rates(games, player_name, stat_column, stat_lines)
            all_hit_rates[stat_column] = hit_rates

    # Identify best bets
    best_bets = []
    for stat_column, hit_rates in all_hit_rates.items():
        bets = identify_best_bets(hit_rates, threshold=0.65)
        for line, data in bets.items():
            best_bets.append({
                "stat": stat_column,
                "line": line,
                "hit_rate": data["hit_rate_over"],
                "over_count": data["over"],
                "under_count": data["under"]
            })

    # Analyze trends for key stats
    trends = {}
    for stat_column in lines.keys():
        if stat_column in games.columns and "week" in games.columns:
            trend = analyze_last_n_games_trend(games, player_name, stat_column, n=5)
            trends[stat_column] = trend

    return {
        "player_name": player_name,
        "position": position,
        "stats": stats,
        "hit_rates": all_hit_rates,
        "best_bets": best_bets,
        "trends": trends
    }


def print_player_summary(summary):
    """Print player summary to console"""
    print(f"\n{'='*80}")
    print(f"🏈 {summary['player_name']} ({summary['position']})")
    print(f"{'='*80}\n")

    # Print basic stats
    print("📊 Season Statistics:")
    stats = summary['stats']
    for key, value in sorted(stats.items()):
        if key.startswith('avg_'):
            stat_name = key.replace('avg_', '').replace('_', ' ').title()
            median_key = key.replace('avg_', 'median_')
            high_key = key.replace('avg_', 'high_')
            low_key = key.replace('avg_', 'low_')

            if value and median_key in stats:
                print(f"   {stat_name}:")
                print(f"      Avg: {value:.1f} | Median: {stats[median_key]:.1f}")
                print(f"      High: {stats[high_key]:.0f} | Low: {stats[low_key]:.0f}")

    # Print hit rates
    print(f"\n📈 Betting Line Hit Rates:")
    for stat_column, hit_rates in summary['hit_rates'].items():
        stat_name = stat_column.replace('_', ' ').title()
        print(f"\n   {stat_name}:")
        for line in sorted(hit_rates.keys()):
            data = hit_rates[line]
            over_pct = data['hit_rate_over'] * 100
            under_pct = data['hit_rate_under'] * 100
            print(f"      {line:>5} - Over: {over_pct:>5.1f}% ({data['over']:>2}/{data['over']+data['under']:>2}) | "
                  f"Under: {under_pct:>5.1f}% ({data['under']:>2}/{data['over']+data['under']:>2})")

    # Print best bets
    if summary['best_bets']:
        print(f"\n🎯 Best Bets (>65% hit rate):")
        for bet in sorted(summary['best_bets'], key=lambda x: x['hit_rate'], reverse=True):
            stat_name = bet['stat'].replace('_', ' ').title()
            pct = bet['hit_rate'] * 100
            total = bet['over_count'] + bet['under_count']
            print(f"   {stat_name} OVER {bet['line']} - {pct:.1f}% ({bet['over_count']}/{total})")
    else:
        print(f"\n🎯 No strong betting opportunities (>65% hit rate) found")

    # Print trends
    if summary['trends']:
        print(f"\n📉 Last 5 Games Trend:")
        for stat_column, trend in summary['trends'].items():
            if trend['direction'] != 'insufficient_data':
                stat_name = stat_column.replace('_', ' ').title()
                direction = trend['direction'].upper()
                emoji = "📈" if direction == "IMPROVING" else "📉" if direction == "DECLINING" else "➡️"
                print(f"   {stat_name}: {emoji} {direction}")
                print(f"      Last 5 avg: {trend['last_n_avg']:.1f} | Previous 5 avg: {trend['previous_n_avg']:.1f}")

    print(f"\n{'='*80}\n")


def analyze_player_trends():
    """
    Analyze player performance trends and generate prop betting analysis
    """
    print("🏈 Starting Player Prop Analysis...\n")

    # Load player data
    games = load_player_data()
    if games is None:
        print("❌ No player data found at data/player_stats_2024.parquet")
        print("   Run scrapers/player_stats.py first to scrape player data")
        return

    print(f"✅ Loaded {len(games)} game logs\n")

    # Load player config to get positions
    import json
    from pathlib import Path

    config_path = Path("players_to_track.json")
    if not config_path.exists():
        print("❌ players_to_track.json not found")
        return

    with open(config_path) as f:
        config = json.load(f)

    # Analyze each player
    for player_config in config["players"]:
        player_name = player_config["name"]
        position = player_config["position"]

        # Filter games for this player
        player_games = games.filter(pl.col("player_name") == player_name)

        if len(player_games) == 0:
            print(f"⚠️  No data found for {player_name}")
            continue

        # Generate and print summary
        summary = generate_player_summary(player_games, player_name, position)
        print_player_summary(summary)

    print("✅ Player prop analysis complete!")


if __name__ == "__main__":
    analyze_player_trends()
