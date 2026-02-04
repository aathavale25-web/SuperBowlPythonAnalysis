"""
Scraper for playoff game history
"""

import duckdb
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from pathlib import Path
import time


def parse_playoff_game_detail(html_content):
    """
    Parse playoff game teams and scores from detail page HTML

    Args:
        html_content: HTML content of a playoff game boxscore page

    Returns:
        dict with winner, loser, winner_score, loser_score
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the linescore table
    linescore_table = soup.find('table', {'class': 'linescore'})
    if not linescore_table:
        return None

    rows = linescore_table.find('tbody').find_all('tr')
    if len(rows) < 2:
        return None

    # Parse both teams
    teams_data = []
    for row in rows:
        cells = row.find_all(['th', 'td'])
        if len(cells) < 3:
            continue

        # Cell 0 is logo, Cell 1 is team name, last cell is final score
        team_name = cells[1].get_text(strip=True)
        final_score = int(cells[-1].get_text(strip=True))

        teams_data.append({
            "team": team_name,
            "score": final_score
        })

    if len(teams_data) < 2:
        return None

    # Determine winner and loser
    if teams_data[0]["score"] > teams_data[1]["score"]:
        winner, loser = teams_data[0], teams_data[1]
    else:
        winner, loser = teams_data[1], teams_data[0]

    return {
        "winner": winner["team"],
        "loser": loser["team"],
        "winner_score": winner["score"],
        "loser_score": loser["score"]
    }


def extract_player_passing_stats(html_content):
    """
    Extract QB passing stats from game detail page

    Args:
        html_content: HTML content of a playoff game boxscore page

    Returns:
        list of dicts with player_name, team, passing_yards, passing_tds, interceptions, rushing_yards
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find passing stats tables (one per team)
    passing_tables = soup.find_all('table', {'id': lambda x: x and 'passing' in x.lower()})

    qb_stats = []

    for table in passing_tables:
        tbody = table.find('tbody')
        if not tbody:
            continue

        rows = tbody.find_all('tr', class_=lambda x: x != 'thead')

        for row in rows:
            # Skip header rows
            th = row.find('th')
            if not th or th.get('data-stat') != 'player':
                continue

            cells = row.find_all(['th', 'td'])
            if len(cells) < 10:
                continue

            # Extract player name and team
            player_name = cells[0].get_text(strip=True)
            team = cells[1].get_text(strip=True) if len(cells) > 1 else ""

            # Find passing stats columns
            pass_yds = 0
            pass_tds = 0
            interceptions = 0

            for cell in cells:
                stat = cell.get('data-stat', '')
                if stat == 'pass_yds':
                    pass_yds = int(cell.get_text(strip=True) or 0)
                elif stat == 'pass_td':
                    pass_tds = int(cell.get_text(strip=True) or 0)
                elif stat == 'pass_int':
                    interceptions = int(cell.get_text(strip=True) or 0)

            # Get rushing yards for QB from rushing table
            rush_yds = 0
            # For now, set to 0, we'll fetch from rushing table if needed

            qb_stats.append({
                "player_name": player_name,
                "team": team,
                "passing_yards": pass_yds,
                "passing_tds": pass_tds,
                "interceptions": interceptions,
                "rushing_yards": rush_yds
            })

    return qb_stats


def extract_player_rushing_stats(html_content, top_n=2):
    """
    Extract top RB rushing stats from game detail page

    Args:
        html_content: HTML content of a playoff game boxscore page
        top_n: Number of top rushers to extract per team

    Returns:
        list of dicts with player_name, team, rushing_yards, rushing_tds, receptions
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find rushing stats tables
    rushing_tables = soup.find_all('table', {'id': lambda x: x and 'rushing' in x.lower()})

    all_rushers = []

    for table in rushing_tables:
        tbody = table.find('tbody')
        if not tbody:
            continue

        rows = tbody.find_all('tr', class_=lambda x: x != 'thead')
        team_rushers = []

        for row in rows:
            th = row.find('th')
            if not th or th.get('data-stat') != 'player':
                continue

            cells = row.find_all(['th', 'td'])
            if len(cells) < 5:
                continue

            player_name = cells[0].get_text(strip=True)
            team = cells[1].get_text(strip=True) if len(cells) > 1 else ""

            rush_yds = 0
            rush_tds = 0
            receptions = 0

            for cell in cells:
                stat = cell.get('data-stat', '')
                if stat == 'rush_yds':
                    rush_yds = int(cell.get_text(strip=True) or 0)
                elif stat == 'rush_td':
                    rush_tds = int(cell.get_text(strip=True) or 0)

            team_rushers.append({
                "player_name": player_name,
                "team": team,
                "rushing_yards": rush_yds,
                "rushing_tds": rush_tds,
                "receptions": receptions,
                "yards": rush_yds  # For sorting
            })

        # Get top N rushers by yards
        team_rushers.sort(key=lambda x: x["yards"], reverse=True)
        for rusher in team_rushers[:top_n]:
            rusher.pop("yards")  # Remove sorting key
            all_rushers.append(rusher)

    return all_rushers


def extract_player_receiving_stats(html_content, top_n=3):
    """
    Extract top WR/TE receiving stats from game detail page

    Args:
        html_content: HTML content of a playoff game boxscore page
        top_n: Number of top receivers to extract per team

    Returns:
        list of dicts with player_name, team, receptions, receiving_yards, receiving_tds
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find receiving stats tables
    receiving_tables = soup.find_all('table', {'id': lambda x: x and 'receiving' in x.lower()})

    all_receivers = []

    for table in receiving_tables:
        tbody = table.find('tbody')
        if not tbody:
            continue

        rows = tbody.find_all('tr', class_=lambda x: x != 'thead')
        team_receivers = []

        for row in rows:
            th = row.find('th')
            if not th or th.get('data-stat') != 'player':
                continue

            cells = row.find_all(['th', 'td'])
            if len(cells) < 5:
                continue

            player_name = cells[0].get_text(strip=True)
            team = cells[1].get_text(strip=True) if len(cells) > 1 else ""

            receptions = 0
            rec_yds = 0
            rec_tds = 0

            for cell in cells:
                stat = cell.get('data-stat', '')
                if stat == 'rec':
                    receptions = int(cell.get_text(strip=True) or 0)
                elif stat == 'rec_yds':
                    rec_yds = int(cell.get_text(strip=True) or 0)
                elif stat == 'rec_td':
                    rec_tds = int(cell.get_text(strip=True) or 0)

            team_receivers.append({
                "player_name": player_name,
                "team": team,
                "receptions": receptions,
                "receiving_yards": rec_yds,
                "receiving_tds": rec_tds,
                "sort_yards": rec_yds  # For sorting
            })

        # Get top N receivers by yards
        team_receivers.sort(key=lambda x: x["sort_yards"], reverse=True)
        for receiver in team_receivers[:top_n]:
            receiver.pop("sort_yards")  # Remove sorting key
            all_receivers.append(receiver)

    return all_receivers


def scrape_playoff_history(seasons=[2020, 2021, 2022, 2023, 2024]):
    """
    Scrape playoff game history and player stats, store in DuckDB

    Args:
        seasons: List of seasons to scrape (default 2020-2024)
    """
    print(f"🏈 Starting playoff scraper for seasons {seasons[0]}-{seasons[-1]}...\n")

    # Connect to database
    db_path = Path("data/superbowl.db")
    conn = duckdb.connect(str(db_path))

    base_url = "https://www.pro-football-reference.com"

    all_playoff_games = []
    all_player_stats = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for season in seasons:
            print(f"📅 Scraping {season} playoffs...")

            try:
                # Fetch playoff schedule page
                playoff_url = f"{base_url}/years/{season}/playoffs.htm"
                page.goto(playoff_url, timeout=30000)
                page.wait_for_timeout(2000)

                # Extract game links
                playoff_html = page.content()
                soup = BeautifulSoup(playoff_html, 'html.parser')

                # Find game summary divs
                game_summaries = soup.find_all('div', {'class': 'game_summary'})

                print(f"   Found {len(game_summaries)} playoff games")

                for game_div in game_summaries:
                    # Find boxscore link (text is exactly "Final")
                    link = game_div.find('a', text='Final')
                    if not link:
                        # Try alternative: look for any link to /boxscores/
                        boxscore_links = [a for a in game_div.find_all('a') if a.get('href', '').startswith('/boxscores/')]
                        if boxscore_links:
                            link = boxscore_links[0]
                        else:
                            continue

                    game_url = link.get('href')
                    if not game_url or not game_url.startswith('/boxscores/'):
                        continue

                    # Determine round
                    round_text = "Unknown"
                    if 'Wild' in game_div.get_text():
                        round_text = "Wild Card"
                    elif 'Division' in game_div.get_text():
                        round_text = "Divisional"
                    elif 'Conference' in game_div.get_text():
                        round_text = "Conference"
                    elif 'Super' in game_div.get_text():
                        round_text = "Super Bowl"

                    # Fetch game detail
                    full_url = f"{base_url}{game_url}"
                    print(f"      Fetching game: {game_url.split('/')[-1]}")

                    page.goto(full_url, timeout=30000)
                    page.wait_for_timeout(2000)

                    game_html = page.content()

                    # Parse game info
                    game_info = parse_playoff_game_detail(game_html)
                    if not game_info:
                        print(f"         ⚠ Could not parse game info")
                        continue

                    # Extract date from URL (format: /boxscores/202501260kan.htm)
                    date_str = game_url.split('/')[-1][:8]  # YYYYMMDD
                    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

                    # Calculate total points
                    total_points = game_info["winner_score"] + game_info["loser_score"]

                    # Store playoff game
                    playoff_game = {
                        "season": season,
                        "round": round_text,
                        "date": date,
                        "winner": game_info["winner"],
                        "loser": game_info["loser"],
                        "winner_score": game_info["winner_score"],
                        "loser_score": game_info["loser_score"],
                        "total_points": total_points
                    }
                    all_playoff_games.append(playoff_game)

                    print(f"         ✓ {game_info['winner']} {game_info['winner_score']}, {game_info['loser']} {game_info['loser_score']}")

                    # Extract player stats
                    passing_stats = extract_player_passing_stats(game_html)
                    rushing_stats = extract_player_rushing_stats(game_html, top_n=2)
                    receiving_stats = extract_player_receiving_stats(game_html, top_n=3)

                    # Combine all player stats with game context
                    for stat in passing_stats + rushing_stats + receiving_stats:
                        player_log = {
                            "player_name": stat["player_name"],
                            "team": stat["team"],
                            "season": season,
                            "week": None,  # Playoffs don't have weeks
                            "game_type": "playoff",
                            "passing_yards": stat.get("passing_yards", 0),
                            "passing_tds": stat.get("passing_tds", 0),
                            "interceptions": stat.get("interceptions", 0),
                            "rushing_yards": stat.get("rushing_yards", 0),
                            "rushing_tds": stat.get("rushing_tds", 0),
                            "receptions": stat.get("receptions", 0),
                            "receiving_yards": stat.get("receiving_yards", 0),
                            "receiving_tds": stat.get("receiving_tds", 0)
                        }
                        all_player_stats.append(player_log)

                    # Rate limiting
                    time.sleep(2)

            except Exception as e:
                print(f"   ✗ Error scraping {season}: {str(e)[:100]}")
                continue

        browser.close()

    # Store in DuckDB
    print(f"\n💾 Storing {len(all_playoff_games)} playoff games in DuckDB...")

    # Clear existing playoff data
    conn.execute("DELETE FROM playoff_games")
    conn.execute("DELETE FROM player_game_logs WHERE game_type = 'playoff'")

    # Insert playoff games
    for i, game in enumerate(all_playoff_games, start=1):
        conn.execute("""
            INSERT INTO playoff_games (id, season, round, date, winner, loser, winner_score, loser_score, total_points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [i, game["season"], game["round"], game["date"], game["winner"], game["loser"],
              game["winner_score"], game["loser_score"], game["total_points"]])

    # Insert player stats
    print(f"💾 Storing {len(all_player_stats)} player game logs...")

    for i, log in enumerate(all_player_stats, start=1):
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
    parquet_path = Path("data/playoff_games.parquet")
    conn.execute(f"COPY playoff_games TO '{parquet_path}' (FORMAT PARQUET)")
    print(f"✅ Exported playoff games to {parquet_path}")

    # Show summary
    result = conn.execute("SELECT COUNT(*) FROM playoff_games").fetchone()
    print(f"✅ Database contains {result[0]} playoff games")

    result = conn.execute("SELECT COUNT(*) FROM player_game_logs WHERE game_type = 'playoff'").fetchone()
    print(f"✅ Database contains {result[0]} playoff player game logs")

    conn.close()
    print("\n🎉 Playoff scraping complete!")


if __name__ == "__main__":
    scrape_playoff_history()
