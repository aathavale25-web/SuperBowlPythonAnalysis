"""
Load all championship games (Super Bowls + AFC/NFC Championships) into database
"""

import json
import duckdb
from pathlib import Path

# Load both JSON files
print("📂 Loading championship game data...\n")

with open('championship_games_data.json', 'r') as f:
    superbowls = json.load(f)

with open('championship_games_additional.json', 'r') as f:
    championships = json.load(f)

all_games = superbowls + championships

print(f"Loaded {len(superbowls)} Super Bowls")
print(f"Loaded {len(championships)} Championship games")
print(f"Total: {len(all_games)} games\n")

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
print("💾 Inserting games into database...")
for game in all_games:
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

# Show summary by type
print("\n📊 Summary by game type:")
summary = conn.execute("""
    SELECT game_type, COUNT(*) as count
    FROM superbowl_games
    GROUP BY game_type
    ORDER BY game_type
""").fetchall()

for game_type, count in summary:
    print(f"   - {game_type}: {count} games")

# Verify 2007-2008 games
print("\n🏆 2007-2008 Season Games:")
games_2007 = conn.execute("""
    SELECT game_type, winner, loser, winner_final, loser_final
    FROM superbowl_games
    WHERE year = 2007
    ORDER BY
        CASE game_type
            WHEN 'afc_championship' THEN 1
            WHEN 'nfc_championship' THEN 2
            WHEN 'superbowl' THEN 3
        END
""").fetchall()

for game_type, winner, loser, w_score, l_score in games_2007:
    print(f"   {game_type:20s}: {winner} {w_score} - {loser} {l_score}")

# Show total and date range
total = conn.execute("SELECT COUNT(*) FROM superbowl_games").fetchone()[0]
years = conn.execute("SELECT MIN(year), MAX(year) FROM superbowl_games").fetchone()

print(f"\n✅ Successfully loaded {total} games!")
print(f"   Coverage: {years[0]}-{years[1]}")

conn.close()
print("\n🎉 Done!")
