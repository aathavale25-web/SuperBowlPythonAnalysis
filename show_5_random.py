"""
Show 5 random Super Bowl games (no Polars, pure DuckDB)
"""

import duckdb
from pathlib import Path

db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

# Get total count
result = conn.execute("SELECT COUNT(*) as count FROM superbowl_games").fetchone()
total = result[0]
print(f"📊 Total Super Bowl games in database: {total}\n")

if total > 0:
    # Show 5 random games with quarter scores
    print("🎲 5 Random Super Bowl Games with Quarter Scores:\n")
    print("=" * 100)

    query = """
    SELECT
        year,
        winner,
        winner_q1, winner_q2, winner_q3, winner_q4, winner_final,
        loser,
        loser_q1, loser_q2, loser_q3, loser_q4, loser_final
    FROM superbowl_games
    ORDER BY RANDOM()
    LIMIT 5
    """

    games = conn.execute(query).fetchall()

    for game in games:
        year, winner, wq1, wq2, wq3, wq4, wfinal, loser, lq1, lq2, lq3, lq4, lfinal = game
        print(f"\n🏈 Super Bowl {year}")
        print(f"   Winner: {winner}")
        print(f"           Q1: {wq1:2d}  Q2: {wq2:2d}  Q3: {wq3:2d}  Q4: {wq4:2d}  Final: {wfinal:2d}")
        print(f"   Loser:  {loser}")
        print(f"           Q1: {lq1:2d}  Q2: {lq2:2d}  Q3: {lq3:2d}  Q4: {lq4:2d}  Final: {lfinal:2d}")
        print("   " + "-" * 60)

    print("\n" + "=" * 100)

    # Check parquet file
    parquet_path = Path("data/superbowl_games.parquet")
    if parquet_path.exists():
        print(f"\n✅ Parquet file exists at {parquet_path}")
    else:
        print(f"\n⚠️  Parquet file not found (likely not saved due to early termination)")
else:
    print("⚠️  Database is empty - the scraper was likely interrupted before saving")

conn.close()
