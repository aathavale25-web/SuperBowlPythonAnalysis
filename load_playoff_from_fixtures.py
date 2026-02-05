"""
Load playoff data from cached fixtures (demonstration)
"""

import duckdb
from pathlib import Path
from scrapers.playoff_history import (
    parse_playoff_game_detail,
    extract_player_passing_stats,
    extract_player_rushing_stats,
    extract_player_receiving_stats
)

print("🏈 Loading playoff data from fixtures...\n")

# Connect to database
db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

# Load fixture
fixture_html = Path("tests/fixtures/playoff_2024_divisional_detail.html").read_text()

# Parse game info
game_info = parse_playoff_game_detail(fixture_html)
passing_stats = extract_player_passing_stats(fixture_html)
rushing_stats = extract_player_rushing_stats(fixture_html, top_n=2)
receiving_stats = extract_player_receiving_stats(fixture_html, top_n=3)

print(f"✅ Parsed game: {game_info['winner']} {game_info['winner_score']}, {game_info['loser']} {game_info['loser_score']}")
print(f"✅ Extracted {len(passing_stats)} QB stats")
print(f"✅ Extracted {len(rushing_stats)} RB stats")
print(f"✅ Extracted {len(receiving_stats)} WR/TE stats")

# Clear and insert
conn.execute("DELETE FROM playoff_games")
conn.execute("DELETE FROM player_game_logs")

# Insert game
conn.execute("""
    INSERT INTO playoff_games (id, season, round, date, winner, loser, winner_score, loser_score, total_points)
    VALUES (1, 2024, 'Divisional', '2025-01-26', ?, ?, ?, ?, ?)
""", [game_info["winner"], game_info["loser"], game_info["winner_score"],
      game_info["loser_score"], game_info["winner_score"] + game_info["loser_score"]])

# Insert player stats
player_id = 1
for stat in passing_stats + rushing_stats + receiving_stats:
    conn.execute("""
        INSERT INTO player_game_logs (
            id, player_name, team, season, week, game_type,
            passing_yards, passing_tds, interceptions,
            rushing_yards, rushing_tds,
            receptions, receiving_yards, receiving_tds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [player_id, stat["player_name"], stat["team"], 2024, None, "playoff",
          stat.get("passing_yards", 0), stat.get("passing_tds", 0), stat.get("interceptions", 0),
          stat.get("rushing_yards", 0), stat.get("rushing_tds", 0),
          stat.get("receptions", 0), stat.get("receiving_yards", 0), stat.get("receiving_tds", 0)])
    player_id += 1

# Export
parquet_path = Path("data/playoff_games.parquet")
conn.execute(f"COPY playoff_games TO '{parquet_path}' (FORMAT PARQUET)")

print(f"\n✅ Exported to {parquet_path}")
print(f"✅ Database contains 1 playoff game with {player_id-1} player stats")

conn.close()
print("\n🎉 Demo playoff data loaded!")
