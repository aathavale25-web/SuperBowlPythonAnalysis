"""
Add 2025-2026 season championship games to database
"""

import json
import duckdb
from pathlib import Path

print("🏈 Adding 2025-2026 Season Championship Games...\n")

# Load the new games
with open('championship_games_2025_estimated.json', 'r') as f:
    new_games = json.load(f)

print(f"📂 Loaded {len(new_games)} new games\n")

# Connect to database
db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

# Check current game count
current_count = conn.execute("SELECT COUNT(*) FROM superbowl_games").fetchone()[0]
print(f"Current games in database: {current_count}")

# Insert new games
for game in new_games:
    # Check if game already exists
    existing = conn.execute("""
        SELECT COUNT(*) FROM superbowl_games
        WHERE year = ? AND game_type = ?
    """, [game['year'], game['game_type']]).fetchone()[0]

    if existing > 0:
        print(f"  ⚠️  {game['year']} {game['game_type']} already exists, skipping")
        continue

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

    print(f"  ✅ Added: {game['year']} {game['game_type']}")
    print(f"     {game['winner']} {game['winner_final']} - {game['loser']} {game['loser_final']}")

# Show updated count
new_count = conn.execute("SELECT COUNT(*) FROM superbowl_games").fetchone()[0]
print(f"\n📊 Total games in database: {new_count}")

# Show breakdown by type
summary = conn.execute("""
    SELECT game_type, COUNT(*) as count
    FROM superbowl_games
    GROUP BY game_type
    ORDER BY game_type
""").fetchall()

print("\nBreakdown by game type:")
for game_type, count in summary:
    print(f"   - {game_type}: {count} games")

# Show most recent games
print("\n🎯 Most Recent Championship Games:")
recent = conn.execute("""
    SELECT year, game_type, winner, loser, winner_final, loser_final
    FROM superbowl_games
    WHERE year >= 2024
    ORDER BY year DESC,
        CASE game_type
            WHEN 'afc_championship' THEN 1
            WHEN 'nfc_championship' THEN 2
            WHEN 'superbowl' THEN 3
        END
""").fetchall()

for year, gtype, winner, loser, w_score, l_score in recent:
    print(f"   {year} {gtype:20s}: {winner} {w_score} - {loser} {l_score}")

conn.close()
print("\n✅ Done!")
