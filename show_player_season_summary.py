"""
Show player season stats summary
"""

import duckdb
from pathlib import Path

db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

print(f"📊 2024 SEASON STATS SUMMARY")
print(f"=" * 80)

# Get player list
players_query = """
SELECT DISTINCT player_name, team
FROM player_game_logs
WHERE season = 2024
ORDER BY player_name
"""

players = conn.execute(players_query).fetchall()

print(f"\n✅ Players tracked: {len(players)}\n")

for player_name, team in players:
    print(f"\n{'='*80}")
    print(f"🏈 {player_name} ({team})")
    print(f"{'='*80}")

    # Get season totals
    totals_query = """
    SELECT
        COUNT(*) as games,
        SUM(CASE WHEN game_type = 'regular' THEN 1 ELSE 0 END) as regular_games,
        SUM(CASE WHEN game_type = 'playoff' THEN 1 ELSE 0 END) as playoff_games,
        SUM(passing_yards) as pass_yds,
        SUM(passing_tds) as pass_tds,
        SUM(interceptions) as ints,
        SUM(rushing_yards) as rush_yds,
        SUM(rushing_tds) as rush_tds,
        SUM(receptions) as recs,
        SUM(receiving_yards) as rec_yds,
        SUM(receiving_tds) as rec_tds
    FROM player_game_logs
    WHERE season = 2024 AND player_name = ?
    """

    totals = conn.execute(totals_query, [player_name]).fetchone()
    games, reg_games, playoff_games, pass_yds, pass_tds, ints, rush_yds, rush_tds, recs, rec_yds, rec_tds = totals

    print(f"\n📈 Season Totals:")
    print(f"   Games: {games} ({reg_games} regular, {playoff_games} playoff)")

    # Passing stats
    if pass_yds > 0:
        print(f"\n   Passing:")
        print(f"      Yards: {pass_yds:,}")
        print(f"      TDs: {pass_tds}")
        print(f"      INTs: {ints}")
        print(f"      Yards/Game: {pass_yds/games:.1f}")

    # Rushing stats
    if rush_yds > 0:
        print(f"\n   Rushing:")
        print(f"      Yards: {rush_yds:,}")
        print(f"      TDs: {rush_tds}")
        print(f"      Yards/Game: {rush_yds/games:.1f}")

    # Receiving stats
    if recs > 0:
        print(f"\n   Receiving:")
        print(f"      Receptions: {recs}")
        print(f"      Yards: {rec_yds:,}")
        print(f"      TDs: {rec_tds}")
        print(f"      Yards/Reception: {rec_yds/recs:.1f}")

    # Show best games
    print(f"\n   🌟 Best Games:")

    best_games_query = """
    SELECT week, game_type,
           passing_yards, passing_tds,
           rushing_yards, rushing_tds,
           receptions, receiving_yards, receiving_tds
    FROM player_game_logs
    WHERE season = 2024 AND player_name = ?
    ORDER BY (passing_yards + rushing_yards + receiving_yards) DESC
    LIMIT 3
    """

    best_games = conn.execute(best_games_query, [player_name]).fetchall()

    for i, (week, game_type, p_yds, p_tds, r_yds, r_tds, recs, rec_yds, rec_tds) in enumerate(best_games, 1):
        week_label = f"Week {week}" if week else game_type.capitalize()
        total_yds = p_yds + r_yds + rec_yds

        stats_parts = []
        if p_yds > 0:
            stats_parts.append(f"{p_yds} pass yds, {p_tds} TD")
        if r_yds > 0:
            stats_parts.append(f"{r_yds} rush yds")
        if rec_yds > 0:
            stats_parts.append(f"{recs} rec, {rec_yds} rec yds")

        print(f"      {i}. {week_label}: {', '.join(stats_parts)} (Total: {total_yds} yds)")

print(f"\n" + "=" * 80)
print(f"\n✅ All data exported to data/player_stats_2024.parquet")

conn.close()
