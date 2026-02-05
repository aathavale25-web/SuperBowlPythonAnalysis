"""
Scraper for player game statistics
"""

import duckdb
import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from pathlib import Path
import time


def parse_player_game_log(html_content, player_name, team_abbr, season=2025):
    """
    Parse player game log from HTML

    Args:
        html_content: HTML content of player's game log page
        player_name: Player's full name
        team_abbr: Team abbreviation (e.g., "KAN", "PHI")
        season: Season year (default 2025)

    Returns:
        list of game dicts with stats
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find stats table
    stats_table = soup.find('table', {'id': 'stats'})
    if not stats_table:
        return []

    tbody = stats_table.find('tbody')
    if not tbody:
        return []

    games = []
    rows = tbody.find_all('tr', class_=lambda x: x != 'thead')

    for row in rows:
        # Skip if it's a divider row
        th = row.find('th')
        if not th or not th.get('data-stat'):
            continue

        cells = row.find_all(['th', 'td'])
        if len(cells) < 10:
            continue

        # Extract basic game info
        week = None
        date = None
        game_type = "regular"  # default to regular season

        # Parse cells by data-stat attribute
        cell_data = {}
        for cell in cells:
            stat_name = cell.get('data-stat')
            if stat_name:
                cell_data[stat_name] = cell.get_text(strip=True)

        # Extract week number
        if 'week_num' in cell_data:
            week_text = cell_data['week_num']
            # Playoff games might be labeled differently
            if week_text.isdigit():
                week = int(week_text)
            elif 'Wild' in week_text or 'Division' in week_text or 'Conference' in week_text or 'Super' in week_text:
                game_type = "playoff"
                week = None
            else:
                week = None

        # Extract date
        if 'date' in cell_data:
            date = cell_data['date']

        # Extract stats
        passing_yards = int(cell_data.get('pass_yds', 0) or 0)
        passing_tds = int(cell_data.get('pass_td', 0) or 0)
        interceptions = int(cell_data.get('pass_int', 0) or 0)
        rushing_yards = int(cell_data.get('rush_yds', 0) or 0)
        rushing_tds = int(cell_data.get('rush_td', 0) or 0)
        receptions = int(cell_data.get('rec', 0) or 0)
        receiving_yards = int(cell_data.get('rec_yds', 0) or 0)
        receiving_tds = int(cell_data.get('rec_td', 0) or 0)

        game = {
            "player_name": player_name,
            "team": team_abbr,
            "season": season,
            "week": week,
            "game_type": game_type,
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


def scrape_player_stats(config_path="players_to_track.json", season=2025):
    """
    Scrape player game logs and store in DuckDB

    Args:
        config_path: Path to players config JSON
        season: Season to scrape (default 2025)
    """
    print(f"📊 Starting player stats scraper for {season} season...\n")

    # Load player config
    players = load_players_config(config_path)
    print(f"✅ Loaded {len(players)} players from config\n")

    # Connect to database
    db_path = Path("data/superbowl.db")
    conn = duckdb.connect(str(db_path))

    base_url = "https://www.pro-football-reference.com"

    all_game_logs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for player in players:
            player_name = player["name"]
            player_url = player["url"]
            team = player.get("team", "")

            print(f"📥 Scraping {player_name} ({team})...")

            try:
                # Build game log URL
                gamelog_url = f"{base_url}{player_url}gamelog/{season}/"

                page.goto(gamelog_url, timeout=30000)
                page.wait_for_timeout(2000)

                html = page.content()

                # Parse game log
                # Extract team abbreviation from player data or parse from page
                team_abbr = team.split()[-1][:3].upper() if team else "UNK"

                games = parse_player_game_log(html, player_name, team_abbr, season)

                print(f"   ✓ Found {len(games)} games")

                # Add to collection
                all_game_logs.extend(games)

                # Rate limiting
                time.sleep(2)

            except Exception as e:
                print(f"   ✗ Error: {str(e)[:100]}")
                continue

        browser.close()

    # Store in DuckDB
    print(f"\n💾 Storing {len(all_game_logs)} game logs in DuckDB...")

    # Clear existing 2024 player logs
    conn.execute(f"DELETE FROM player_game_logs WHERE season = {season}")

    # Insert game logs
    for i, log in enumerate(all_game_logs, start=1):
        conn.execute("""
            INSERT INTO player_game_logs (
                id, player_name, team, season, week, game_type,
                passing_yards, passing_tds, interceptions,
                rushing_yards, rushing_tds,
                receptions, receiving_yards, receiving_tds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [i, log["player_name"], log["team"], log["season"], log["week"], log["game_type"],
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

    conn.close()
    print("\n🎉 Player stats scraping complete!")


if __name__ == "__main__":
    scrape_player_stats()
