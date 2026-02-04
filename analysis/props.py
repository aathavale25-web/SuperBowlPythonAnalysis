"""
Playoff props analysis
"""

import polars as pl


def calculate_game_prop_hit_rates(games, prop_type, lines=None, buckets=None):
    """Calculate hit rates for game props"""
    if prop_type == "total_points":
        return _calculate_total_points_hit_rates(games, lines)
    elif prop_type == "winning_margin":
        return _calculate_winning_margin_hit_rates(games, buckets)
    elif prop_type == "defensive_td":
        return _calculate_defensive_td_hit_rates(games)
    return {}


def _calculate_total_points_hit_rates(games, lines):
    """Calculate hit rates for total points lines"""
    hit_rates = {}

    for line in lines:
        over_count = (games["total_points"] > line).sum()
        under_count = (games["total_points"] <= line).sum()
        total = len(games)

        hit_rates[line] = {
            "over": over_count,
            "under": under_count,
            "hit_rate_over": over_count / total if total > 0 else 0.0,
            "hit_rate_under": under_count / total if total > 0 else 0.0
        }

    return hit_rates


def _calculate_winning_margin_hit_rates(games, buckets):
    """Calculate hit rates for winning margin buckets"""
    # Calculate margin for each game
    margins = games["winner_score"] - games["loser_score"]

    hit_rates = {}
    total = len(games)

    for bucket in buckets:
        if bucket == "1-6":
            count = ((margins >= 1) & (margins <= 6)).sum()
        elif bucket == "7-12":
            count = ((margins >= 7) & (margins <= 12)).sum()
        elif bucket == "13-18":
            count = ((margins >= 13) & (margins <= 18)).sum()
        elif bucket == "19+":
            count = (margins >= 19).sum()
        else:
            count = 0

        hit_rates[bucket] = {
            "count": count,
            "percentage": count / total if total > 0 else 0.0
        }

    return hit_rates


def _calculate_defensive_td_hit_rates(games):
    """Calculate hit rates for defensive/special teams TDs"""
    occurred = games["defensive_td"].sum()
    total = len(games)

    return {
        "occurred": {
            "count": occurred,
            "percentage": occurred / total if total > 0 else 0.0
        },
        "no_occurrence": {
            "count": total - occurred,
            "percentage": (total - occurred) / total if total > 0 else 0.0
        }
    }


def calculate_player_prop_hit_rates(player_stats, prop_type, line):
    """Calculate hit rates for player props"""
    if prop_type == "qb_passing_yards":
        stat_column = "passing_yards"
    elif prop_type == "qb_passing_tds":
        stat_column = "passing_tds"
    elif prop_type == "qb_interceptions":
        stat_column = "interceptions"
    elif prop_type == "rb_rushing_yards":
        stat_column = "rushing_yards"
    elif prop_type == "wr_receiving_yards":
        stat_column = "receiving_yards"
    else:
        return {}

    # Calculate over/under for the line
    values = player_stats[stat_column]
    over_count = (values > line).sum()
    under_count = (values <= line).sum()
    total = len(values)

    return {
        "over": over_count,
        "under": under_count,
        "hit_rate_over": over_count / total if total > 0 else 0.0,
        "hit_rate_under": under_count / total if total > 0 else 0.0
    }


def breakdown_by_round(games, prop_type, line):
    """Break down prop hit rates by playoff round"""
    breakdown = {}

    # Get unique rounds
    rounds = games["round"].unique().to_list()

    for round_name in rounds:
        # Filter games for this round
        round_games = games.filter(pl.col("round") == round_name)

        if prop_type == "total_points":
            over_count = (round_games["total_points"] > line).sum()
            under_count = (round_games["total_points"] <= line).sum()
            total = len(round_games)

            breakdown[round_name] = {
                "over": over_count,
                "under": under_count,
                "hit_rate_over": over_count / total if total > 0 else 0.0,
                "hit_rate_under": under_count / total if total > 0 else 0.0
            }

    return breakdown


def identify_best_playoff_props(all_props, threshold=0.60):
    """Identify best playoff props above threshold"""
    best_props = {}

    for prop_name, data in all_props.items():
        # Check if it's an over/under prop
        if "hit_rate_over" in data:
            if data["hit_rate_over"] >= threshold:
                best_props[prop_name] = data
        # Check if it's a percentage-based prop (like margin buckets)
        elif "percentage" in data:
            if data["percentage"] >= threshold:
                best_props[prop_name] = data

    return best_props


def load_playoff_data(parquet_path="data/playoff_games.parquet"):
    """Load playoff games data from parquet file"""
    from pathlib import Path

    path = Path(parquet_path)
    if not path.exists():
        return None

    return pl.read_parquet(parquet_path)


def print_prop_results(prop_name, hit_rates):
    """Print prop hit rate results"""
    if "hit_rate_over" in hit_rates:
        over_pct = hit_rates["hit_rate_over"] * 100
        under_pct = hit_rates["hit_rate_under"] * 100
        total = hit_rates["over"] + hit_rates["under"]
        print(f"   {prop_name}:")
        print(f"      OVER:  {over_pct:>5.1f}% ({hit_rates['over']:>2}/{total})")
        print(f"      UNDER: {under_pct:>5.1f}% ({hit_rates['under']:>2}/{total})")
    elif "percentage" in hit_rates:
        pct = hit_rates["percentage"] * 100
        print(f"   {prop_name}: {pct:>5.1f}% ({hit_rates['count']} games)")


def analyze_playoff_props():
    """
    Analyze playoff props across multiple seasons
    """
    print("🏈 Starting Playoff Props Analysis...\\n")

    # Load playoff data
    games = load_playoff_data()
    if games is None:
        print("❌ No playoff data found at data/playoff_games.parquet")
        print("   Run load_sample_playoff_props_data.py first to load sample data")
        return

    print(f"✅ Loaded {len(games)} playoff games")
    print(f"   Seasons: {games['season'].min()}-{games['season'].max()}")
    print(f"   Rounds: {', '.join(games['round'].unique().sort().to_list())}\\n")

    # === GAME PROPS ===
    print("="*80)
    print("📊 GAME PROPS ANALYSIS")
    print("="*80)

    # Total Points
    print("\\n🎯 Total Points:")
    total_points_lines = [43.5, 47.5, 51.5]
    total_points_hr = calculate_game_prop_hit_rates(
        games, "total_points", lines=total_points_lines
    )
    for line in total_points_lines:
        print_prop_results(f"O/U {line}", total_points_hr[line])

    # Winning Margin
    print("\\n🎯 Winning Margin:")
    margin_buckets = ["1-6", "7-12", "13-18", "19+"]
    margin_hr = calculate_game_prop_hit_rates(
        games, "winning_margin", buckets=margin_buckets
    )
    for bucket in margin_buckets:
        print_prop_results(f"Margin {bucket} points", margin_hr[bucket])

    # Defensive TD
    print("\\n🎯 Defensive/Special Teams TD:")
    def_td_hr = calculate_game_prop_hit_rates(games, "defensive_td")
    print(f"   Occurred:     {def_td_hr['occurred']['percentage']*100:>5.1f}% ({def_td_hr['occurred']['count']} games)")
    print(f"   Did Not Occur: {def_td_hr['no_occurrence']['percentage']*100:>5.1f}% ({def_td_hr['no_occurrence']['count']} games)")

    # === BREAKDOWN BY ROUND ===
    print("\\n" + "="*80)
    print("📊 BREAKDOWN BY PLAYOFF ROUND")
    print("="*80)

    print("\\n🏆 Total Points O47.5 by Round:")
    round_breakdown = breakdown_by_round(games, "total_points", 47.5)
    for round_name in sorted(round_breakdown.keys()):
        data = round_breakdown[round_name]
        over_pct = data["hit_rate_over"] * 100
        total = data["over"] + data["under"]
        print(f"   {round_name:15s}: {over_pct:>5.1f}% over ({data['over']}/{total})")

    # === BEST PROPS ===
    print("\\n" + "="*80)
    print("🎯 BEST HISTORICAL PLAYOFF PROPS (>60% Hit Rate)")
    print("="*80)

    # Collect all props
    all_props = {}

    # Add total points props
    for line in total_points_lines:
        all_props[f"Total Points O{line}"] = total_points_hr[line]

    # Add margin props
    for bucket in margin_buckets:
        all_props[f"Margin {bucket}"] = margin_hr[bucket]

    # Identify best props
    best_props = identify_best_playoff_props(all_props, threshold=0.60)

    if best_props:
        print("\\n✅ Props with >60% hit rate:")
        for prop_name in sorted(best_props.keys(), key=lambda x: best_props[x].get("hit_rate_over", best_props[x].get("percentage", 0)), reverse=True):
            data = best_props[prop_name]
            if "hit_rate_over" in data:
                pct = data["hit_rate_over"] * 100
                total = data["over"] + data["under"]
                print(f"   {prop_name:25s} - {pct:>5.1f}% ({data['over']}/{total})")
            else:
                pct = data["percentage"] * 100
                print(f"   {prop_name:25s} - {pct:>5.1f}% ({data['count']} games)")
    else:
        print("\\n⚠️  No props found with >60% hit rate")

    # === KEY INSIGHTS ===
    print("\\n" + "="*80)
    print("💡 KEY INSIGHTS")
    print("="*80)

    # Super Bowl specific
    sb_games = games.filter(pl.col("round") == "Super Bowl")
    if len(sb_games) > 0:
        sb_avg_total = sb_games["total_points"].mean()
        all_avg_total = games["total_points"].mean()

        print(f"\\n🏆 Super Bowl Trends:")
        print(f"   Average Total Points: {sb_avg_total:.1f} (All Playoffs: {all_avg_total:.1f})")

        sb_high_scoring = (sb_games["total_points"] > 47.5).sum() / len(sb_games) * 100
        print(f"   High Scoring (O47.5): {sb_high_scoring:.1f}%")

    print("\\n✅ Analysis complete!")


if __name__ == "__main__":
    analyze_playoff_props()
