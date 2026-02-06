"""
Load championship games data from JSON into database
"""

import json
import duckdb
from pathlib import Path

# Load the JSON data
with open('championship_games_data.json', 'r') as f:
    games = json.load(f)

print(f"🏈 Loading {len(games)} championship games into database...\n")

# Connect to database
db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

# Drop and recreate table
conn.execute("DROP TABLE IF EXISTS superbowl_games")
conn.execute("""
    CREATE TABLE superbowl_games (
        year INTEGER,
        game_type VARCHAR,
        winner VARCHAR,
        loser VARCHAR,
        winner_q1 INTEGER,
        winner_q2 INTEGER,
        winner_q3 INTEGER,
        winner_q4 INTEGER,
        winner_final INTEGER,
        loser_q1 INTEGER,
        loser_q2 INTEGER,
        loser_q3 INTEGER,
        loser_q4 INTEGER,
        loser_final INTEGER
    )
""")

# Insert all games
for game in games:
    conn.execute("""
        INSERT INTO superbowl_games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        game['year'],
        game['game_type'],
        game['winner'],
        game['loser'],
        game['winner_q1'],
        game['winner_q2'],
        game['winner_q3'],
        game['winner_q4'],
        game['winner_final'],
        game['loser_q1'],
        game['loser_q2'],
        game['loser_q3'],
        game['loser_q4'],
        game['loser_final']
    ])
    print(f"✅ {game['year']}: {game['winner']} {game['winner_final']} - {game['loser']} {game['loser_final']}")

# Verify the 2007 game
sb_2007 = conn.execute("""
    SELECT year, winner, loser, winner_final, loser_final,
           winner_q1, winner_q2, winner_q3, winner_q4,
           loser_q1, loser_q2, loser_q3, loser_q4
    FROM superbowl_games
    WHERE year = 2007
""").fetchone()

if sb_2007:
    print(f"\n🏆 Verified 2007-2008 Super Bowl XLII:")
    print(f"   {sb_2007[1]} {sb_2007[3]} - {sb_2007[2]} {sb_2007[4]}")
    print(f"   Quarter scores - Winner: {sb_2007[5]}, {sb_2007[6]}, {sb_2007[7]}, {sb_2007[8]}")
    print(f"   Quarter scores - Loser:  {sb_2007[9]}, {sb_2007[10]}, {sb_2007[11]}, {sb_2007[12]}")

# Show summary
total = conn.execute("SELECT COUNT(*) FROM superbowl_games").fetchone()[0]
print(f"\n✅ Successfully loaded {total} games into database!")

# Show years covered
years = conn.execute("SELECT MIN(year), MAX(year) FROM superbowl_games").fetchone()
print(f"   Coverage: {years[0]}-{years[1]}")

conn.close()
print("\n🎉 Done!")
