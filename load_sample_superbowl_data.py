"""
Load sample Super Bowl data for demonstration
"""

import duckdb
from pathlib import Path

# Sample Super Bowl games (recent years with realistic scores)
sample_games = [
    # 2024
    {"year": 2024, "winner": "Kansas City Chiefs", "loser": "San Francisco 49ers",
     "winner_q1": 0, "winner_q2": 3, "winner_q3": 10, "winner_q4": 6, "winner_final": 25,
     "loser_q1": 0, "loser_q2": 10, "loser_q3": 0, "loser_q4": 9, "loser_final": 22},

    # 2023
    {"year": 2023, "winner": "Kansas City Chiefs", "loser": "Philadelphia Eagles",
     "winner_q1": 7, "winner_q2": 14, "winner_q3": 10, "winner_q4": 7, "winner_final": 38,
     "loser_q1": 7, "loser_q2": 17, "loser_q3": 8, "loser_q4": 3, "loser_final": 35},

    # 2022
    {"year": 2022, "winner": "Los Angeles Rams", "loser": "Cincinnati Bengals",
     "winner_q1": 7, "winner_q2": 6, "winner_q3": 3, "winner_q4": 7, "winner_final": 23,
     "loser_q1": 3, "loser_q2": 10, "loser_q3": 0, "loser_q4": 7, "loser_final": 20},

    # 2021
    {"year": 2021, "winner": "Tampa Bay Buccaneers", "loser": "Kansas City Chiefs",
     "winner_q1": 7, "winner_q2": 14, "winner_q3": 10, "winner_q4": 0, "winner_final": 31,
     "loser_q1": 3, "loser_q2": 3, "loser_q3": 3, "loser_q4": 0, "loser_final": 9},

    # 2020
    {"year": 2020, "winner": "Kansas City Chiefs", "loser": "San Francisco 49ers",
     "winner_q1": 0, "winner_q2": 10, "winner_q3": 0, "winner_q4": 21, "winner_final": 31,
     "loser_q1": 3, "loser_q2": 7, "loser_q3": 10, "loser_q4": 0, "loser_final": 20},

    # 2019
    {"year": 2019, "winner": "New England Patriots", "loser": "Los Angeles Rams",
     "winner_q1": 0, "winner_q2": 3, "winner_q3": 0, "winner_q4": 10, "winner_final": 13,
     "loser_q1": 0, "loser_q2": 0, "loser_q3": 3, "loser_q4": 0, "loser_final": 3},

    # 2018
    {"year": 2018, "winner": "Philadelphia Eagles", "loser": "New England Patriots",
     "winner_q1": 9, "winner_q2": 13, "winner_q3": 7, "winner_q4": 12, "winner_final": 41,
     "loser_q1": 3, "loser_q2": 9, "loser_q3": 19, "loser_q4": 2, "loser_final": 33},

    # 2017
    {"year": 2017, "winner": "New England Patriots", "loser": "Atlanta Falcons",
     "winner_q1": 0, "winner_q2": 3, "winner_q3": 6, "winner_q4": 19, "winner_final": 34,
     "loser_q1": 0, "loser_q2": 21, "loser_q3": 7, "loser_q4": 0, "loser_final": 28},

    # 2016
    {"year": 2016, "winner": "Denver Broncos", "loser": "Carolina Panthers",
     "winner_q1": 10, "winner_q2": 3, "winner_q3": 8, "winner_q4": 3, "winner_final": 24,
     "loser_q1": 0, "loser_q2": 7, "loser_q3": 3, "loser_q4": 0, "loser_final": 10},

    # 2015
    {"year": 2015, "winner": "New England Patriots", "loser": "Seattle Seahawks",
     "winner_q1": 0, "winner_q2": 14, "winner_q3": 0, "winner_q4": 14, "winner_final": 28,
     "loser_q1": 0, "loser_q2": 14, "loser_q3": 10, "loser_q4": 0, "loser_final": 24},
]

print("📊 Loading sample Super Bowl data...\n")

db_path = Path("data/superbowl.db")
conn = duckdb.connect(str(db_path))

# Clear existing data
conn.execute("DELETE FROM superbowl_games")

# Insert sample games
for game in sample_games:
    conn.execute("""
        INSERT INTO superbowl_games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [game["year"], game["winner"], game["loser"],
          game["winner_q1"], game["winner_q2"], game["winner_q3"], game["winner_q4"], game["winner_final"],
          game["loser_q1"], game["loser_q2"], game["loser_q3"], game["loser_q4"], game["loser_final"]])

conn.close()

print(f"✅ Loaded {len(sample_games)} Super Bowl games")
print("✅ Ready for squares analysis!")
