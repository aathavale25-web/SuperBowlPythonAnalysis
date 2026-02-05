"""
Update database schema to add game_result, opponent, and opponent_abbr columns
"""

import duckdb
from pathlib import Path

db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

print("📊 Updating database schema...")

# Add new columns for win/loss and opponent tracking
try:
    conn.execute("ALTER TABLE player_game_logs ADD COLUMN game_result VARCHAR")
    print("✅ Added game_result column")
except Exception as e:
    print(f"⚠️  game_result column may already exist: {e}")

try:
    conn.execute("ALTER TABLE player_game_logs ADD COLUMN opponent VARCHAR")
    print("✅ Added opponent column")
except Exception as e:
    print(f"⚠️  opponent column may already exist: {e}")

try:
    conn.execute("ALTER TABLE player_game_logs ADD COLUMN opponent_abbr VARCHAR")
    print("✅ Added opponent_abbr column")
except Exception as e:
    print(f"⚠️  opponent_abbr column may already exist: {e}")

# Verify the new schema
print("\n📋 Updated schema:")
result = conn.execute("PRAGMA table_info(player_game_logs)").fetchall()
for row in result:
    print(f"  {row[1]}: {row[2]}")

conn.close()
print("\n✅ Schema update complete!")
