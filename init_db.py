"""
Initialize DuckDB database with required tables
"""

import duckdb
from pathlib import Path


def init_database():
    """
    Create DuckDB database with tables for Super Bowl data
    """
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Connect to DuckDB
    db_path = data_dir / "superbowl.db"
    conn = duckdb.connect(str(db_path))

    # Create superbowl_games table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS superbowl_games (
            year INTEGER PRIMARY KEY,
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

    # Create player_game_logs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS player_game_logs (
            id INTEGER PRIMARY KEY,
            player_name VARCHAR,
            team VARCHAR,
            season INTEGER,
            week INTEGER,
            game_type VARCHAR,
            passing_yards INTEGER,
            passing_tds INTEGER,
            interceptions INTEGER,
            rushing_yards INTEGER,
            rushing_tds INTEGER,
            receptions INTEGER,
            receiving_yards INTEGER,
            receiving_tds INTEGER
        )
    """)

    # Create playoff_games table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playoff_games (
            id INTEGER PRIMARY KEY,
            season INTEGER,
            round VARCHAR,
            date DATE,
            winner VARCHAR,
            loser VARCHAR,
            winner_score INTEGER,
            loser_score INTEGER,
            total_points INTEGER
        )
    """)

    # Create sequence for auto-incrementing IDs
    conn.execute("CREATE SEQUENCE IF NOT EXISTS player_game_logs_seq START 1")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS playoff_games_seq START 1")

    conn.close()

    print(f"✅ Database initialized at {db_path}")
    print("✅ Tables created:")
    print("   - superbowl_games")
    print("   - player_game_logs")
    print("   - playoff_games")


if __name__ == "__main__":
    init_database()
