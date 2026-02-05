"""
Show detailed playoff summary with all player stats
"""

import duckdb
from pathlib import Path

db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

# Get total counts
result = conn.execute("SELECT COUNT(*) FROM playoff_games").fetchone()
total_games = result[0]

result = conn.execute("SELECT COUNT(*) FROM player_game_logs WHERE game_type = 'playoff'").fetchone()
total_stats = result[0]

print(f"📊 PLAYOFF SCRAPING SUMMARY")
print(f"=" * 80)
print(f"\n✅ Total playoff games scraped: {total_games}")
print(f"✅ Total player game logs: {total_stats}\n")

# Show playoff games
print(f"🏈 Playoff Games:")
print(f"=" * 80)

games = conn.execute("""
    SELECT season, round, date, winner, loser, winner_score, loser_score, total_points
    FROM playoff_games
    ORDER BY date DESC
""").fetchall()

for season, round, date, winner, loser, winner_score, loser_score, total_points in games:
    print(f"\n{round} ({season}) - {date}")
    print(f"   {winner} {winner_score}, {loser} {loser_score}")
    print(f"   Total Points: {total_points}")

# Show player stats grouped by game
print(f"\n\n📊 Player Stats from Playoff Games:")
print(f"=" * 80)

# Get all player stats
player_stats = conn.execute("""
    SELECT player_name, team, season,
           passing_yards, passing_tds, interceptions,
           rushing_yards, rushing_tds,
           receptions, receiving_yards, receiving_tds
    FROM player_game_logs
    WHERE game_type = 'playoff'
    ORDER BY (passing_yards + rushing_yards + receiving_yards) DESC
""").fetchall()

print(f"\nTop {min(len(player_stats), 10)} Player Performances:\n")

for i, (pname, team, season, pass_yds, pass_tds, ints, rush_yds, rush_tds, recs, rec_yds, rec_tds) in enumerate(player_stats[:10], 1):
    stats_parts = []

    # Passing stats
    if pass_yds > 0:
        stats_parts.append(f"{pass_yds} pass yds")
        if pass_tds > 0:
            stats_parts.append(f"{pass_tds} pass TD")
        if ints > 0:
            stats_parts.append(f"{ints} INT")

    # Rushing stats
    if rush_yds > 0:
        stats_parts.append(f"{rush_yds} rush yds")
        if rush_tds > 0:
            stats_parts.append(f"{rush_tds} rush TD")

    # Receiving stats
    if recs > 0:
        stats_parts.append(f"{recs} rec")
    if rec_yds > 0:
        stats_parts.append(f"{rec_yds} rec yds")
        if rec_tds > 0:
            stats_parts.append(f"{rec_tds} rec TD")

    total_yds = pass_yds + rush_yds + rec_yds
    print(f"{i:2d}. {pname:25s} ({team:3s}) - {', '.join(stats_parts)}")
    print(f"    Total Yards: {total_yds}")

print(f"\n" + "=" * 80)
print(f"\n✅ All data stored in DuckDB and exported to data/playoff_games.parquet")

conn.close()
