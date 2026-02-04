"""
Scraper for historical Super Bowl game data
"""

import duckdb
import polars as pl
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from pathlib import Path


def parse_game_linescore(html_content):
    """
    Parse quarter-by-quarter scores from game detail HTML

    Args:
        html_content: HTML content of a game boxscore page

    Returns:
        dict with winner and loser team data including quarter scores
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the linescore table
    linescore_table = soup.find('table', {'class': 'linescore'})
    if not linescore_table:
        return None

    rows = linescore_table.find('tbody').find_all('tr')
    if len(rows) < 2:
        return None

    # Parse both team rows
    teams_data = []
    for row in rows:
        cells = row.find_all(['th', 'td'])
        if len(cells) < 7:  # Need logo, team, Q1-4, final minimum
            continue

        # Cell 0 is logo, Cell 1 is team name
        team_name = cells[1].get_text(strip=True)

        # Extract scores starting from cell 2 (Q1, Q2, Q3, Q4, potentially OT, Final)
        scores = [c.get_text(strip=True) for c in cells[2:]]

        # Determine if there's overtime
        if len(scores) == 6:  # Q1, Q2, Q3, Q4, OT, Final
            q1, q2, q3, q4, ot, final = scores
        elif len(scores) == 5:  # Q1, Q2, Q3, Q4, Final
            q1, q2, q3, q4, final = scores
        else:
            continue

        teams_data.append({
            "team": team_name,
            "q1": int(q1),
            "q2": int(q2),
            "q3": int(q3),
            "q4": int(q4),
            "final": int(final)
        })

    if len(teams_data) < 2:
        return None

    # Determine winner and loser by final score
    if teams_data[0]["final"] > teams_data[1]["final"]:
        winner, loser = teams_data[0], teams_data[1]
    else:
        winner, loser = teams_data[1], teams_data[0]

    return {
        "winner": winner,
        "loser": loser
    }


def extract_game_links(html_content):
    """
    Extract boxscore links from Super Bowl index page

    Args:
        html_content: HTML content of the Super Bowl index page

    Returns:
        list of dicts with year, url, winner, loser for each game
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all tables (the index page has multiple tables without IDs)
    tables = soup.find_all('table')

    games = []
    for table in tables:
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')

        for row in rows:
            cells = row.find_all(['th', 'td'])
            if len(cells) < 10:  # Need all columns
                continue

            # Check if this looks like a game row (has date, SB link, teams)
            date_cell = cells[0].get_text(strip=True)
            sb_cell = cells[1]
            winner_cell = cells[2]
            loser_cell = cells[4]

            # Skip header rows
            if date_cell == "Date" or sb_cell.get_text(strip=True) == "SB":
                continue

            # Get the boxscore link from SB column
            sb_link = sb_cell.find('a')
            if not sb_link:
                continue

            url = sb_link.get('href')
            if not url or not url.startswith('/boxscores/'):
                continue

            # Extract year from date (format: "Feb 8, 2026")
            try:
                year = int(date_cell.split(',')[-1].strip())
            except (ValueError, IndexError):
                continue

            # Get team names
            winner = winner_cell.get_text(strip=True)
            loser = loser_cell.get_text(strip=True)

            if not winner or not loser:
                continue

            games.append({
                "year": year,
                "url": url,
                "winner": winner,
                "loser": loser
            })

    return games


def scrape_superbowl_history():
    """
    Scrape historical Super Bowl game data and store in DuckDB
    Includes rate limiting (2 second delay between requests)
    """
    print("🏈 Starting Super Bowl history scraper...\n")

    # Connect to database
    db_path = Path("data/superbowl.db")
    conn = duckdb.connect(str(db_path))

    base_url = "https://www.pro-football-reference.com"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Fetch index page
        print("📄 Fetching Super Bowl index page...")
        page.goto(f"{base_url}/super-bowl/", timeout=60000)
        page.wait_for_timeout(2000)

        index_html = page.content()
        games = extract_game_links(index_html)
        print(f"✅ Found {len(games)} Super Bowl games\n")

        # Fetch each game's detail page
        all_game_data = []
        for i, game in enumerate(games, 1):
            # Skip future games (not yet played)
            if game['year'] > 2025:
                print(f"[{i}/{len(games)}] Skipping {game['year']} (future game)")
                continue

            print(f"[{i}/{len(games)}] Fetching {game['year']} - {game['winner']} vs {game['loser']}...")

            try:
                # Navigate to game page
                game_url = f"{base_url}{game['url']}"
                page.goto(game_url, timeout=30000)
                page.wait_for_timeout(2000)

                # Parse linescore
                game_html = page.content()
                linescore = parse_game_linescore(game_html)

                if linescore:
                    game_data = {
                        "year": game["year"],
                        "winner": linescore["winner"]["team"],
                        "loser": linescore["loser"]["team"],
                        "winner_q1": linescore["winner"]["q1"],
                        "winner_q2": linescore["winner"]["q2"],
                        "winner_q3": linescore["winner"]["q3"],
                        "winner_q4": linescore["winner"]["q4"],
                        "winner_final": linescore["winner"]["final"],
                        "loser_q1": linescore["loser"]["q1"],
                        "loser_q2": linescore["loser"]["q2"],
                        "loser_q3": linescore["loser"]["q3"],
                        "loser_q4": linescore["loser"]["q4"],
                        "loser_final": linescore["loser"]["final"],
                    }
                    all_game_data.append(game_data)
                    print(f"   ✓ {linescore['winner']['team']} {linescore['winner']['final']}, {linescore['loser']['team']} {linescore['loser']['final']}")
                else:
                    print(f"   ⚠ Could not parse linescore for {game['year']}")

            except Exception as e:
                print(f"   ✗ Error fetching {game['year']}: {str(e)[:100]}")
                continue

            # Rate limiting - 2 second delay
            time.sleep(2)

        browser.close()

    # Store in DuckDB
    print(f"\n💾 Storing {len(all_game_data)} games in DuckDB...")

    # Clear existing data
    conn.execute("DELETE FROM superbowl_games")

    # Insert data using Polars
    df = pl.DataFrame(all_game_data)
    conn.execute("INSERT INTO superbowl_games SELECT * FROM df")

    # Export to parquet
    parquet_path = Path("data/superbowl_games.parquet")
    df.write_parquet(parquet_path)
    print(f"✅ Exported to {parquet_path}")

    # Show summary
    result = conn.execute("SELECT COUNT(*) as count FROM superbowl_games").fetchone()
    print(f"✅ Database contains {result[0]} Super Bowl games")

    conn.close()
    print("\n🎉 Scraping complete!")


if __name__ == "__main__":
    scrape_superbowl_history()
