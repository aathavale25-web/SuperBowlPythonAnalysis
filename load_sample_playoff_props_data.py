"""
Load sample playoff data for props analysis demonstration
"""

import polars as pl
from pathlib import Path

# Sample playoff games from last 5 years (realistic scores and rounds)
sample_playoff_games = [
    # 2024 Season Playoffs
    {"season": 2024, "round": "Super Bowl", "winner": "Kansas City Chiefs", "loser": "Philadelphia Eagles",
     "winner_score": 38, "loser_score": 35, "total_points": 73},
    {"season": 2024, "round": "Conference", "winner": "Kansas City Chiefs", "loser": "Buffalo Bills",
     "winner_score": 32, "loser_score": 29, "total_points": 61},
    {"season": 2024, "round": "Divisional", "winner": "Kansas City Chiefs", "loser": "Houston Texans",
     "winner_score": 23, "loser_score": 14, "total_points": 37},

    # 2023 Season Playoffs
    {"season": 2023, "round": "Super Bowl", "winner": "Kansas City Chiefs", "loser": "San Francisco 49ers",
     "winner_score": 25, "loser_score": 22, "total_points": 47},
    {"season": 2023, "round": "Conference", "winner": "Kansas City Chiefs", "loser": "Baltimore Ravens",
     "winner_score": 17, "loser_score": 10, "total_points": 27},
    {"season": 2023, "round": "Divisional", "winner": "Kansas City Chiefs", "loser": "Buffalo Bills",
     "winner_score": 27, "loser_score": 24, "total_points": 51},

    # 2022 Season Playoffs
    {"season": 2022, "round": "Super Bowl", "winner": "Kansas City Chiefs", "loser": "Philadelphia Eagles",
     "winner_score": 38, "loser_score": 35, "total_points": 73},
    {"season": 2022, "round": "Conference", "winner": "Kansas City Chiefs", "loser": "Cincinnati Bengals",
     "winner_score": 23, "loser_score": 20, "total_points": 43},
    {"season": 2022, "round": "Divisional", "winner": "Kansas City Chiefs", "loser": "Jacksonville Jaguars",
     "winner_score": 27, "loser_score": 20, "total_points": 47},

    # 2021 Season Playoffs
    {"season": 2021, "round": "Super Bowl", "winner": "Los Angeles Rams", "loser": "Cincinnati Bengals",
     "winner_score": 23, "loser_score": 20, "total_points": 43},
    {"season": 2021, "round": "Conference", "winner": "Los Angeles Rams", "loser": "San Francisco 49ers",
     "winner_score": 20, "loser_score": 17, "total_points": 37},
    {"season": 2021, "round": "Divisional", "winner": "Los Angeles Rams", "loser": "Tampa Bay Buccaneers",
     "winner_score": 30, "loser_score": 27, "total_points": 57},

    # 2020 Season Playoffs
    {"season": 2020, "round": "Super Bowl", "winner": "Tampa Bay Buccaneers", "loser": "Kansas City Chiefs",
     "winner_score": 31, "loser_score": 9, "total_points": 40},
    {"season": 2020, "round": "Conference", "winner": "Tampa Bay Buccaneers", "loser": "Green Bay Packers",
     "winner_score": 31, "loser_score": 26, "total_points": 57},
    {"season": 2020, "round": "Divisional", "winner": "Tampa Bay Buccaneers", "loser": "New Orleans Saints",
     "winner_score": 30, "loser_score": 20, "total_points": 50},
]

print("📊 Loading sample playoff data for props analysis...\\n")

# Create DataFrame
df = pl.DataFrame(sample_playoff_games)

# Add defensive TD flag (simulate: ~20% of games have defensive TD)
import random
random.seed(42)
defensive_td_values = [random.random() < 0.2 for _ in range(len(df))]
df = df.with_columns(
    pl.Series("defensive_td", defensive_td_values, dtype=pl.Boolean)
)

# Save to parquet
output_path = Path("data/playoff_games.parquet")
df.write_parquet(output_path)

print(f"✅ Loaded {len(df)} playoff games")
print(f"   Seasons: 2020-2024")
print(f"   Rounds: {df['round'].unique().sort().to_list()}")
print(f"   Total Points range: {df['total_points'].min()}-{df['total_points'].max()}")
print(f"\\n✅ Saved to {output_path}")
print("✅ Ready for playoff props analysis!")
