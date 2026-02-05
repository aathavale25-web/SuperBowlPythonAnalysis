"""
Show playoff scraping summary with player stats
"""

import duckdb
from pathlib import Path

db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

# Get total playoff games count
result = conn.execute("SELECT COUNT(*) FROM playoff_games").fetchone()
total_games = result[0]

print(f"📊 PLAYOFF SCRAPING SUMMARY")
print(f"=" * 80)
print(f"\n✅ Total playoff games scraped: {total_games}")

# Get total player stats
result = conn.execute("SELECT COUNT(*) FROM player_game_logs WHERE game_type = 'playoff'").fetchone()
total_stats = result[0]
print(f"✅ Total player game logs: {total_stats}\n")

# Show sample of 3 games with player stats
print(f"🎲 Sample of 3 Playoff Games with Player Stats:")
print(f"=" * 80)

games_query = """
SELECT id, season, round, date, winner, loser, winner_score, loser_score
FROM playoff_games
LIMIT 3
"""

games = conn.execute(games_query).fetchall()

for game in games:
    game_id, season, round, date, winner, loser, winner_score, loser_score = game

    print(f"\n🏈 {round} - {season}")
    print(f"   {winner} {winner_score}, {loser} {loser_score}")
    print(f"   Date: {date}")
    print(f"\n   📈 Top Player Performances:")

    # Get player stats for this game
    # Match by team names and season (since we don't have game_id in player_game_logs)
    stats_query = """
    SELECT player_name, team,
           passing_yards, passing_tds, interceptions,
           rushing_yards, rushing_tds,
           receptions, receiving_yards, receiving_tds
    FROM player_game_logs
    WHERE game_type = 'playoff'
      AND season = ?
      AND (team LIKE ? OR team LIKE ?)
    ORDER BY (passing_yards + rushing_yards + receiving_yards) DESC
    LIMIT 5
    """

    # Extract team abbreviations from full names
    winner_abbr = winner.split()[-1][:3].upper()
    loser_abbr = loser.split()[-1][:3].upper()

    player_stats = conn.execute(stats_query, [season, f"%{winner_abbr}%", f"%{loser_abbr}%"]).fetchall()

    for pname, team, pass_yds, pass_tds, ints, rush_yds, rush_tds, recs, rec_yds, rec_tds in player_stats:
        stats_parts = []
        if pass_yds > 0:
            stats_parts.append(f"{pass_yds} pass yds, {pass_tds} pass TD")
        if rush_yds > 0:
            stats_parts.append(f"{rush_yds} rush yds, {rush_tds} rush TD")
        if rec_yds > 0:
            stats_parts.append(f"{recs} rec, {rec_yds} rec yds, {rec_tds} rec TD")

        if stats_parts:
            print(f"      {pname} ({team}): {', '.join(stats_parts)}")

    print(f"   " + "-" * 76)

print(f"\n" + "=" * 80)
print(f"\n✅ Data successfully stored in database and exported to data/playoff_games.parquet")

conn.close()
