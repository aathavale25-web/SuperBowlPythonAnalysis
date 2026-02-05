"""
Load sample Super Bowl data (bypassing Polars due to CPU issues)
"""

import duckdb
from pathlib import Path
from scrapers.superbowl_history import parse_game_linescore

print("🏈 Loading Super Bowl data...\n")

# Connect to database
db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

# Load fixture
fixture_html = Path("tests/fixtures/superbowl_lviii_detail.html").read_text()
linescore = parse_game_linescore(fixture_html)

if linescore:
    # Clear existing data
    conn.execute("DELETE FROM superbowl_games")

    # Insert Super Bowl LVIII
    d = {
        "year": 2024,
        "winner": linescore["winner"]["team"],
        "loser": linescore["loser"]["team"],
        "winner_q1": linescore["winner"]["q1"],
        "winner_q2": linescore["winner"]["q2"],
        "winner_q3": linescore["winner"]["q3"],
        "winner_q4": linescore["winner"]["q4"],
        "winner_final": linescore["winner"]["final"],
        "loser_q1": linescore["loser"]["q1"],
        "loser_q2": linescore["loser"]["q2"],
        "loser_q3": linescore["loser"]["q3"],
        "loser_q4": linescore["loser"]["q4"],
        "loser_final": linescore["loser"]["final"],
    }

    conn.execute("""
        INSERT INTO superbowl_games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [d["year"], d["winner"], d["loser"],
          d["winner_q1"], d["winner_q2"], d["winner_q3"], d["winner_q4"], d["winner_final"],
          d["loser_q1"], d["loser_q2"], d["loser_q3"], d["loser_q4"], d["loser_final"]])

    # Export to parquet using DuckDB
    parquet_path = Path("data/superbowl_games.parquet")
    conn.execute(f"COPY superbowl_games TO '{parquet_path}' (FORMAT PARQUET)")

    print(f"✅ Loaded Super Bowl LVIII (2024)")
    print(f"   {linescore['winner']['team']} {linescore['winner']['final']}, {linescore['loser']['team']} {linescore['loser']['final']}")
    print(f"\n✅ Exported to {parquet_path}")
    print(f"✅ Stored in database")

    # Show the data
    print("\n📊 Data in database:")
    result = conn.execute("""
        SELECT year, winner, winner_q1, winner_q2, winner_q3, winner_q4, winner_final,
               loser, loser_q1, loser_q2, loser_q3, loser_q4, loser_final
        FROM superbowl_games
    """).fetchone()

    year, winner, wq1, wq2, wq3, wq4, wfinal, loser, lq1, lq2, lq3, lq4, lfinal = result
    print(f"\n🏈 Super Bowl {year}")
    print(f"   Winner: {winner}")
    print(f"           Q1: {wq1:2d}  Q2: {wq2:2d}  Q3: {wq3:2d}  Q4: {wq4:2d}  Final: {wfinal:2d}")
    print(f"   Loser:  {loser}")
    print(f"           Q1: {lq1:2d}  Q2: {lq2:2d}  Q3: {lq3:2d}  Q4: {lq4:2d}  Final: {lfinal:2d}")

conn.close()
print("\n🎉 Demo data loaded successfully!")
