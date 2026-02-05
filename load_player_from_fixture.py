"""
Load player stats from cached fixture
"""

import duckdb
from pathlib import Path
from scrapers.player_stats import parse_player_game_log

print("📊 Loading player stats from fixture...\n")

# Connect to database
db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

# Load Mahomes fixture
fixture_html = Path("tests/fixtures/mahomes_2024_gamelog.html").read_text()
games = parse_player_game_log(fixture_html, "Patrick Mahomes", "KAN")

print(f"✅ Parsed {len(games)} games for Patrick Mahomes\n")

# Clear and insert
conn.execute("DELETE FROM player_game_logs WHERE season = 2024")

# Insert games
for i, game in enumerate(games, start=1):
    conn.execute("""
        INSERT INTO player_game_logs (
            id, player_name, team, season, week, game_type,
            passing_yards, passing_tds, interceptions,
            rushing_yards, rushing_tds,
            receptions, receiving_yards, receiving_tds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [i, game["player_name"], game["team"], game["season"], game["week"], game["game_type"],
          game["passing_yards"], game["passing_tds"], game["interceptions"],
          game["rushing_yards"], game["rushing_tds"],
          game["receptions"], game["receiving_yards"], game["receiving_tds"]])

# Export to parquet
parquet_path = Path("data/player_stats_2024.parquet")
conn.execute(f"COPY (SELECT * FROM player_game_logs WHERE season = 2024) TO '{parquet_path}' (FORMAT PARQUET)")

print(f"✅ Exported to {parquet_path}")
print(f"✅ Database contains {len(games)} game logs")

conn.close()
print("\n🎉 Player data loaded!")
