"""
ESPN API scraper for player game statistics
"""

import duckdb
import json
import requests
from pathlib import Path
import time


# ESPN athlete ID mapping (found via ESPN website)
ESPN_ATHLETE_IDS = {
    # New England Patriots
    "Drake Maye": "4431452",
    "Rhamondre Stevenson": "4569173",
    "TreVeyon Henderson": "4432710",
    "Stefon Diggs": "2976212",
    "DeMario Douglas": "4427095",
    "Hunter Henry": "3046439",
    # Seattle Seahawks
    "Sam Darnold": "3912547",
    "Kenneth Walker III": "4567048",
    "Jaxon Smith-Njigba": "4430878",
    "Cooper Kupp": "2977187",
    "Rashid Shaheed": "4032473",
    "AJ Barner": "4576297"
}


def fetch_espn_gamelog(athlete_id, season=2025):
    """
    Fetch player game log from ESPN API

    Args:
        athlete_id: ESPN athlete ID
        season: Season year

    Returns:
        dict with game log data
    """
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{athlete_id}/gamelog"
    params = {"season": str(season)}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ✗ API Error: {str(e)}")
        return None


def parse_espn_gamelog(data, player_name, team_abbr, season=2025):
    """
    Parse ESPN game log data into our format

    Args:
        data: ESPN API response JSON
        player_name: Player's full name
        team_abbr: Team abbreviation
        season: Season year

    Returns:
        list of game dicts with stats
    """
    if not data or "seasonTypes" not in data:
        return []

    games = []
    names = data.get("names", [])
    events_metadata = data.get("events", {})

    # Create mapping from stat names to indices
    stat_indices = {}
    for i, name in enumerate(names):
        stat_indices[name] = i

    # Stats are in seasonTypes -> categories -> events
    for season_type in data.get("seasonTypes", []):
        # Determine game type from season type
        season_type_name = season_type.get("displayName", "")
        game_type = "playoff" if "Postseason" in season_type_name else "regular"

        for category in season_type.get("categories", []):
            for event in category.get("events", []):
                event_id = event.get("eventId")
                stats = event.get("stats", [])

                if not stats or not event_id:
                    continue

                # Get week and game info from events metadata
                event_meta = events_metadata.get(event_id, {})
                week = event_meta.get("week")
                game_result = event_meta.get("gameResult", "")  # "W" or "L"
                opponent_info = event_meta.get("opponent", {})
                opponent_name = opponent_info.get("displayName", "")
                opponent_abbr = opponent_info.get("abbreviation", "")

                # Extract stats using indices
                def get_stat(name):
                    if name in stat_indices:
                        idx = stat_indices[name]
                        if idx < len(stats):
                            value = stats[idx]
                            # Handle empty strings and convert to int
                            try:
                                return int(float(value)) if value and value != '' else 0
                            except (ValueError, TypeError):
                                return 0
                    return 0

                passing_yards = get_stat("passingYards")
                passing_tds = get_stat("passingTouchdowns")
                interceptions = get_stat("interceptions")
                rushing_yards = get_stat("rushingYards")
                rushing_tds = get_stat("rushingTouchdowns")
                receptions = get_stat("receptions")
                receiving_yards = get_stat("receivingYards")
                receiving_tds = get_stat("receivingTouchdowns")

                game = {
                    "player_name": player_name,
                    "team": team_abbr,
                    "season": season,
                    "week": week,
                    "game_type": game_type,
                    "game_result": game_result,
                    "opponent": opponent_name,
                    "opponent_abbr": opponent_abbr,
                    "passing_yards": passing_yards,
                    "passing_tds": passing_tds,
                    "interceptions": interceptions,
                    "rushing_yards": rushing_yards,
                    "rushing_tds": rushing_tds,
                    "receptions": receptions,
                    "receiving_yards": receiving_yards,
                    "receiving_tds": receiving_tds
                }

                games.append(game)

    return games


def load_players_config(config_path="players_to_track.json"):
    """
    Load player configuration from JSON file

    Args:
        config_path: Path to JSON config file

    Returns:
        list of player dicts
    """
    config_file = Path(config_path)
    if not config_file.exists():
        return []

    with open(config_file, 'r') as f:
        config = json.load(f)

    return config.get("players", [])


def scrape_espn_player_stats(config_path="players_to_track.json", season=2025):
    """
    Scrape player game logs from ESPN API and store in DuckDB

    Args:
        config_path: Path to players config JSON
        season: Season to scrape (default 2025)
    """
    print(f"📊 Starting ESPN API scraper for {season} season...\n")

    # Load player config
    players = load_players_config(config_path)
    print(f"✅ Loaded {len(players)} players from config\n")

    # Connect to database
    db_path = Path("data/superbowl.db")
    conn = duckdb.connect(str(db_path))

    all_game_logs = []

    for player in players:
        player_name = player["name"]
        team = player.get("team", "")

        # Skip placeholder players
        if player_name.startswith("Player Name"):
            print(f"⏭️  Skipping placeholder: {player_name}")
            continue

        # Get ESPN athlete ID
        athlete_id = ESPN_ATHLETE_IDS.get(player_name)
        if not athlete_id:
            print(f"⚠️  No ESPN ID for {player_name}, skipping...")
            continue

        print(f"📥 Fetching {player_name} ({team})...")

        try:
            # Fetch from ESPN API
            data = fetch_espn_gamelog(athlete_id, season)

            if not data:
                print(f"   ✗ No data returned")
                continue

            # Parse game log
            team_abbr = team.split()[-1][:3].upper() if team else "UNK"
            games = parse_espn_gamelog(data, player_name, team_abbr, season)

            print(f"   ✓ Found {len(games)} games")

            # Add to collection
            all_game_logs.extend(games)

            # Rate limiting (be nice to ESPN's API)
            time.sleep(1)

        except Exception as e:
            print(f"   ✗ Error: {str(e)[:100]}")
            continue

    # Store in DuckDB
    print(f"\n💾 Storing {len(all_game_logs)} game logs in DuckDB...")

    # Clear existing 2025 player logs
    conn.execute(f"DELETE FROM player_game_logs WHERE season = {season}")

    # Get max existing ID to avoid conflicts
    max_id_result = conn.execute("SELECT COALESCE(MAX(id), 0) FROM player_game_logs").fetchone()
    max_id = max_id_result[0] if max_id_result else 0

    # Insert game logs
    for i, log in enumerate(all_game_logs, start=max_id + 1):
        conn.execute("""
            INSERT INTO player_game_logs (
                id, player_name, team, season, week, game_type,
                game_result, opponent, opponent_abbr,
                passing_yards, passing_tds, interceptions,
                rushing_yards, rushing_tds,
                receptions, receiving_yards, receiving_tds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [i, log["player_name"], log["team"], log["season"], log["week"], log["game_type"],
              log["game_result"], log["opponent"], log["opponent_abbr"],
              log["passing_yards"], log["passing_tds"], log["interceptions"],
              log["rushing_yards"], log["rushing_tds"],
              log["receptions"], log["receiving_yards"], log["receiving_tds"]])

    # Export to parquet
    parquet_path = Path(f"data/player_stats_{season}.parquet")
    conn.execute(f"""
        COPY (SELECT * FROM player_game_logs WHERE season = {season})
        TO '{parquet_path}' (FORMAT PARQUET)
    """)

    print(f"✅ Exported to {parquet_path}")

    # Show summary
    result = conn.execute(f"SELECT COUNT(*) FROM player_game_logs WHERE season = {season}").fetchone()
    print(f"✅ Database contains {result[0]} game logs for {season} season")

    # Show breakdown by player
    print(f"\n📈 Games per player:")
    results = conn.execute(f"""
        SELECT player_name, COUNT(*) as game_count
        FROM player_game_logs
        WHERE season = {season}
        GROUP BY player_name
        ORDER BY game_count DESC
    """).fetchall()

    for player_name, count in results:
        print(f"   {player_name}: {count} games")

    conn.close()
    print("\n🎉 ESPN API scraping complete!")


if __name__ == "__main__":
    scrape_espn_player_stats()
