import duckdb
from pathlib import Path

conn = duckdb.connect('data/superbowl.db')

print("="*80)
print("DATABASE CONTENTS SUMMARY")
print("="*80)

# Overall stats
print("\n📊 OVERALL DATABASE STATS")
print("-" * 80)
result = conn.execute("SELECT COUNT(*) FROM player_game_logs").fetchone()
print(f"Total game logs: {result[0]}")

# By season
print("\n📅 BY SEASON")
print("-" * 80)
results = conn.execute("""
    SELECT season, COUNT(*) as games, COUNT(DISTINCT player_name) as players
    FROM player_game_logs
    GROUP BY season
    ORDER BY season
""").fetchall()

for season, games, players in results:
    print(f"{season}: {games} games across {players} players")

# Player breakdown
print("\n👥 PLAYER BREAKDOWN (2025 Season)")
print("-" * 80)
results = conn.execute("""
    SELECT
        player_name,
        COUNT(*) as games,
        SUM(passing_yards) as pass_yd,
        SUM(passing_tds) as pass_td,
        SUM(rushing_yards) as rush_yd,
        SUM(rushing_tds) as rush_td,
        SUM(receptions) as rec,
        SUM(receiving_yards) as rec_yd,
        SUM(receiving_tds) as rec_td
    FROM player_game_logs
    WHERE season = 2025
    GROUP BY player_name
    ORDER BY player_name
""").fetchall()

for row in results:
    name, games, pass_yd, pass_td, rush_yd, rush_td, rec, rec_yd, rec_td = row
    print(f"\n{name}: {games} games")
    if pass_yd > 0:
        print(f"  Passing: {pass_yd:,} yards, {pass_td} TDs")
    if rush_yd > 0:
        print(f"  Rushing: {rush_yd:,} yards, {rush_td} TDs")
    if rec > 0:
        print(f"  Receiving: {rec} catches, {rec_yd:,} yards, {rec_td} TDs")

# Check for Super Bowl history data
print("\n🏆 SUPER BOWL HISTORY DATA")
print("-" * 80)
sb_file = Path("data/superbowl_player_history.parquet")
if sb_file.exists():
    try:
        result = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{sb_file}')").fetchone()
        print(f"✅ Super Bowl player history: {result[0]} player games")

        # Show breakdown
        results = conn.execute(f"""
            SELECT position, COUNT(*) as games
            FROM read_parquet('{sb_file}')
            GROUP BY position
            ORDER BY position
        """).fetchall()
        print("\nBreakdown by position:")
        for pos, count in results:
            print(f"  {pos}: {count} games")
    except Exception as e:
        print(f"❌ Error reading Super Bowl history: {str(e)[:100]}")
else:
    print("❌ No Super Bowl history data found")
    print("   Run: python scrapers/superbowl_player_stats.py")

print("\n" + "="*80)
print("WHAT'S NEEDED FOR ANALYSIS")
print("="*80)
print("\n✅ HAVE: 2025 season player data (94 games for 5 Seattle players)")
print("❌ NEED: Historical Super Bowl player data for position benchmarks")
print("\nTo populate Super Bowl history:")
print("  python scrapers/superbowl_player_stats.py")
print("\nThen generate the site:")
print("  python generate_site.py")
print("="*80)

conn.close()
