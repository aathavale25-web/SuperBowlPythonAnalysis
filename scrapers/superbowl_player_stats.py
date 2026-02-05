"""
Scraper for historical Super Bowl player statistics
"""

import duckdb
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from pathlib import Path
import time


def safe_int(value):
    """Safely convert a value to int, returning 0 if conversion fails"""
    if value is None or value == '':
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def parse_superbowl_boxscore(html_content, super_bowl, year, team):
    """
    Parse Super Bowl boxscore HTML to extract player stats

    Args:
        html_content: HTML content of Super Bowl boxscore page
        super_bowl: Super Bowl number (e.g., "LVIII", "LVII")
        year: Year of Super Bowl
        team: Team name

    Returns:
        list of player stat dicts
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    players = []

    # Find offense table
    offense_table = soup.find('table', {'id': 'player_offense'})
    if not offense_table:
        return players

    tbody = offense_table.find('tbody')
    if not tbody:
        return players

    rows = tbody.find_all('tr')

    for row in rows:
        # Skip header rows
        if row.get('class') and 'thead' in row.get('class'):
            continue

        cells = row.find_all(['th', 'td'])
        if len(cells) < 2:
            continue

        # Extract cell data
        cell_data = {}
        for cell in cells:
            stat_name = cell.get('data-stat')
            if stat_name:
                cell_data[stat_name] = cell.get_text(strip=True)

        if 'player' not in cell_data:
            continue

        player_name = cell_data['player']
        if not player_name or player_name == 'Player':  # Skip if empty or header
            continue

        # Extract stats safely
        pass_yds = safe_int(cell_data.get('pass_yds'))
        pass_td = safe_int(cell_data.get('pass_td'))
        pass_int = safe_int(cell_data.get('pass_int'))
        rush_yds = safe_int(cell_data.get('rush_yds'))
        rush_td = safe_int(cell_data.get('rush_td'))
        rec = safe_int(cell_data.get('rec'))
        rec_yds = safe_int(cell_data.get('rec_yds'))
        rec_td = safe_int(cell_data.get('rec_td'))

        # Skip if all stats are zero (likely a header or empty row)
        if all(x == 0 for x in [pass_yds, pass_td, rush_yds, rec, rec_yds]):
            continue

        # Determine position based on stats present
        position = "FLEX"
        if pass_yds > 0:
            position = "QB"
        elif rush_yds > 50:
            position = "RB"
        elif rec > 0:
            # Heuristic: if primarily receiving, likely WR or TE
            if rec_yds > 40:
                position = "WR"
            else:
                position = "TE"

        player = {
            "super_bowl": super_bowl,
            "year": year,
            "player_name": player_name,
            "position": position,
            "team": team,
            "passing_yards": pass_yds,
            "passing_tds": pass_td,
            "interceptions": pass_int,
            "rushing_yards": rush_yds,
            "rushing_tds": rush_td,
            "receptions": rec,
            "receiving_yards": rec_yds,
            "receiving_tds": rec_td
        }

        players.append(player)

    return players


def get_superbowl_info(year):
    """
    Get Super Bowl number and team info for a given year

    Args:
        year: Year of Super Bowl

    Returns:
        dict with sb_number (Roman numeral), url, winner, loser
    """
    # Super Bowl mapping for 2000-2024
    superbowl_map = {
        2000: {"sb": "XXXIV", "url": "/boxscores/200001300ram.htm", "winner": "St. Louis Rams", "loser": "Tennessee Titans"},
        2001: {"sb": "XXXV", "url": "/boxscores/200101280rav.htm", "winner": "Baltimore Ravens", "loser": "New York Giants"},
        2002: {"sb": "XXXVI", "url": "/boxscores/200202030nwe.htm", "winner": "New England Patriots", "loser": "St. Louis Rams"},
        2003: {"sb": "XXXVII", "url": "/boxscores/200301260tam.htm", "winner": "Tampa Bay Buccaneers", "loser": "Oakland Raiders"},
        2004: {"sb": "XXXVIII", "url": "/boxscores/200402010nwe.htm", "winner": "New England Patriots", "loser": "Carolina Panthers"},
        2005: {"sb": "XXXIX", "url": "/boxscores/200502060nwe.htm", "winner": "New England Patriots", "loser": "Philadelphia Eagles"},
        2006: {"sb": "XL", "url": "/boxscores/200602050pit.htm", "winner": "Pittsburgh Steelers", "loser": "Seattle Seahawks"},
        2007: {"sb": "XLI", "url": "/boxscores/200702040clt.htm", "winner": "Indianapolis Colts", "loser": "Chicago Bears"},
        2008: {"sb": "XLII", "url": "/boxscores/200802030nyg.htm", "winner": "New York Giants", "loser": "New England Patriots"},
        2009: {"sb": "XLIII", "url": "/boxscores/200902010pit.htm", "winner": "Pittsburgh Steelers", "loser": "Arizona Cardinals"},
        2010: {"sb": "XLIV", "url": "/boxscores/201002070nor.htm", "winner": "New Orleans Saints", "loser": "Indianapolis Colts"},
        2011: {"sb": "XLV", "url": "/boxscores/201102060gnb.htm", "winner": "Green Bay Packers", "loser": "Pittsburgh Steelers"},
        2012: {"sb": "XLVI", "url": "/boxscores/201202050nyg.htm", "winner": "New York Giants", "loser": "New England Patriots"},
        2013: {"sb": "XLVII", "url": "/boxscores/201302030rav.htm", "winner": "Baltimore Ravens", "loser": "San Francisco 49ers"},
        2014: {"sb": "XLVIII", "url": "/boxscores/201402020sea.htm", "winner": "Seattle Seahawks", "loser": "Denver Broncos"},
        2015: {"sb": "XLIX", "url": "/boxscores/201502010nwe.htm", "winner": "New England Patriots", "loser": "Seattle Seahawks"},
        2016: {"sb": "L", "url": "/boxscores/201602070den.htm", "winner": "Denver Broncos", "loser": "Carolina Panthers"},
        2017: {"sb": "LI", "url": "/boxscores/201702050nwe.htm", "winner": "New England Patriots", "loser": "Atlanta Falcons"},
        2018: {"sb": "LII", "url": "/boxscores/201802040phi.htm", "winner": "Philadelphia Eagles", "loser": "New England Patriots"},
        2019: {"sb": "LIII", "url": "/boxscores/201902030nwe.htm", "winner": "New England Patriots", "loser": "Los Angeles Rams"},
        2020: {"sb": "LIV", "url": "/boxscores/202002020kan.htm", "winner": "Kansas City Chiefs", "loser": "San Francisco 49ers"},
        2021: {"sb": "LV", "url": "/boxscores/202102070tam.htm", "winner": "Tampa Bay Buccaneers", "loser": "Kansas City Chiefs"},
        2022: {"sb": "LVI", "url": "/boxscores/202202130ram.htm", "winner": "Los Angeles Rams", "loser": "Cincinnati Bengals"},
        2023: {"sb": "LVII", "url": "/boxscores/202302120kan.htm", "winner": "Kansas City Chiefs", "loser": "Philadelphia Eagles"},
        2024: {"sb": "LVIII", "url": "/boxscores/202402110kan.htm", "winner": "Kansas City Chiefs", "loser": "San Francisco 49ers"}
    }

    return superbowl_map.get(year)


def scrape_superbowl_player_stats(start_year=2000, end_year=2024):
    """
    Scrape historical Super Bowl player stats

    Args:
        start_year: Starting year to scrape (default 2000)
        end_year: Ending year to scrape (default 2024)
    """
    print(f"📊 Starting Super Bowl player stats scraper ({start_year}-{end_year})...\n")

    all_players = []

    base_url = "https://www.pro-football-reference.com"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for year in range(start_year, end_year + 1):
            sb_info = get_superbowl_info(year)

            if not sb_info:
                print(f"⚠️  No Super Bowl data for {year}")
                continue

            sb_number = sb_info["sb"]
            sb_url = sb_info["url"]
            winner = sb_info["winner"]
            loser = sb_info["loser"]

            print(f"📥 Scraping Super Bowl {sb_number} ({year}) - {winner} vs {loser}...")

            try:
                # Navigate to boxscore
                full_url = f"{base_url}{sb_url}"
                page.goto(full_url, timeout=30000)
                page.wait_for_timeout(2000)

                html = page.content()

                # Parse the boxscore
                # NOTE: The HTML contains both teams' stats in the same table.
                # We cannot distinguish between teams from the HTML structure alone.
                # All players are parsed with a generic "TBD" team label.
                # Team names would need to be corrected manually or with additional parsing logic.
                players = parse_superbowl_boxscore(html, sb_number, year, "TBD")
                print(f"   ✓ Parsed {len(players)} players (teams: {winner} vs {loser})")

                all_players.extend(players)

                # Rate limiting
                time.sleep(3)

            except Exception as e:
                print(f"   ✗ Error scraping SB {sb_number}: {str(e)[:100]}")
                continue

        browser.close()

    # Export to parquet using DuckDB
    parquet_path = Path("data/superbowl_player_history.parquet")
    if all_players:
        conn = duckdb.connect()
        # Create a table from the list of dicts
        conn.execute("CREATE TABLE sb_history AS SELECT * FROM (VALUES " +
                     ", ".join([f"('{p['super_bowl']}', {p['year']}, '{p['player_name']}', '{p['position']}', '{p['team']}', "
                               f"{p['passing_yards']}, {p['passing_tds']}, {p['interceptions']}, "
                               f"{p['rushing_yards']}, {p['rushing_tds']}, {p['receptions']}, "
                               f"{p['receiving_yards']}, {p['receiving_tds']})" for p in all_players]) +
                     ") AS t(super_bowl, year, player_name, position, team, passing_yards, passing_tds, interceptions, " +
                     "rushing_yards, rushing_tds, receptions, receiving_yards, receiving_tds)")
        conn.execute(f"COPY sb_history TO '{parquet_path}' (FORMAT PARQUET)")
        conn.close()
        print(f"\n✅ Exported {len(all_players)} player records to {parquet_path}")
    else:
        print("\n⚠️  No data scraped")

    print("\n🎉 Super Bowl player stats scraping complete!")


if __name__ == "__main__":
    scrape_superbowl_player_stats()
