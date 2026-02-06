"""
Scrape Super Bowl and Championship games from Pro Football Reference
"""

import requests
from bs4 import BeautifulSoup
import duckdb
from pathlib import Path
import time
import re

def scrape_superbowl_page(year):
    """
    Scrape a Super Bowl game from Pro Football Reference

    Args:
        year: Year of the Super Bowl

    Returns:
        dict with game data or None
    """
    # Pro Football Reference uses the year the season started
    # Super Bowl is played in February of the following year
    season_year = year - 1

    url = f"https://www.pro-football-reference.com/years/{season_year}/playoffs.htm"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the Super Bowl table
        tables = soup.find_all('table', {'id': 'playoff_results'})
        if not tables:
            return None

        table = tables[0]
        rows = table.find_all('tr')

        superbowl_game = None
        afc_champ = None
        nfc_champ = None

        for row in rows:
            # Check if this is a Super Bowl row
            th = row.find('th')
            if th and 'Super Bowl' in th.get_text():
                superbowl_game = parse_game_row(row, year, 'superbowl')

            # Check for Championship games
            elif th:
                text = th.get_text()
                if 'AFC Championship' in text:
                    afc_champ = parse_game_row(row, year, 'afc_championship')
                elif 'NFC Championship' in text:
                    nfc_champ = parse_game_row(row, year, 'nfc_championship')

        return {
            'superbowl': superbowl_game,
            'afc': afc_champ,
            'nfc': nfc_champ
        }

    except Exception as e:
        print(f"  Error scraping {year}: {e}")
        return None


def parse_game_row(row, year, game_type):
    """
    Parse a game row from Pro Football Reference

    Args:
        row: BeautifulSoup row element
        year: Year of the game
        game_type: 'superbowl', 'afc_championship', or 'nfc_championship'

    Returns:
        dict with game data or None
    """
    try:
        cells = row.find_all('td')
        if len(cells) < 4:
            return None

        # Winner is in first cell
        winner_cell = cells[0]
        winner_name = winner_cell.get_text().strip()

        # Loser is in second cell
        loser_cell = cells[1]
        loser_name = loser_cell.get_text().strip()

        # Score is in cells[2] - format like "31-25"
        score_text = cells[2].get_text().strip()
        score_parts = score_text.split('-')
        if len(score_parts) != 2:
            return None

        winner_final = int(score_parts[0])
        loser_final = int(score_parts[1])

        # Try to find box score link to get quarter scores
        box_score_link = None
        for cell in cells:
            link = cell.find('a', href=re.compile(r'/boxscores/'))
            if link:
                box_score_link = 'https://www.pro-football-reference.com' + link['href']
                break

        # Get quarter scores from box score page
        quarters = get_quarter_scores(box_score_link, winner_name, loser_name)

        if quarters:
            return {
                'year': year,
                'game_type': game_type,
                'winner': winner_name,
                'loser': loser_name,
                **quarters,
                'winner_final': winner_final,
                'loser_final': loser_final
            }

        # If we can't get quarter scores, return with zeros
        return {
            'year': year,
            'game_type': game_type,
            'winner': winner_name,
            'loser': loser_name,
            'winner_q1': 0,
            'winner_q2': 0,
            'winner_q3': 0,
            'winner_q4': 0,
            'winner_final': winner_final,
            'loser_q1': 0,
            'loser_q2': 0,
            'loser_q3': 0,
            'loser_q4': 0,
            'loser_final': loser_final
        }

    except Exception as e:
        print(f"    Error parsing row: {e}")
        return None


def get_quarter_scores(box_score_url, winner_name, loser_name):
    """
    Get quarter-by-quarter scores from box score page

    Args:
        box_score_url: URL to box score page
        winner_name: Name of winning team
        loser_name: Name of losing team

    Returns:
        dict with quarter scores or None
    """
    if not box_score_url:
        return None

    try:
        response = requests.get(box_score_url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the linescore table
        linescore = soup.find('table', {'class': 'linescore'})
        if not linescore:
            return None

        rows = linescore.find_all('tr')
        if len(rows) < 3:
            return None

        # Rows are: header, team1, team2
        team1_row = rows[1]
        team2_row = rows[2]

        # Get team names
        team1_name = team1_row.find('th').get_text().strip()
        team2_name = team2_row.find('th').get_text().strip()

        # Determine which row is winner/loser
        winner_row = team1_row if winner_name in team1_name else team2_row
        loser_row = team2_row if winner_name in team1_name else team1_row

        # Extract quarter scores (cumulative)
        def extract_quarters(row):
            cells = row.find_all('td')
            quarters = []
            cumulative = 0
            for i in range(4):  # Q1-Q4
                if i < len(cells):
                    try:
                        quarter_score = int(cells[i].get_text().strip())
                        cumulative += quarter_score
                        quarters.append(cumulative)
                    except:
                        quarters.append(0)
                else:
                    quarters.append(0)
            return quarters

        winner_quarters = extract_quarters(winner_row)
        loser_quarters = extract_quarters(loser_row)

        return {
            'winner_q1': winner_quarters[0],
            'winner_q2': winner_quarters[1],
            'winner_q3': winner_quarters[2],
            'winner_q4': winner_quarters[3],
            'loser_q1': loser_quarters[0],
            'loser_q2': loser_quarters[1],
            'loser_q3': loser_quarters[2],
            'loser_q4': loser_quarters[3]
        }

    except Exception as e:
        print(f"      Error getting quarter scores: {e}")
        return None


if __name__ == "__main__":
    print("🏈 Scraping Championship Games from Pro Football Reference (2000-2024)...\n")

    all_games = []

    # Scrape each year
    for year in range(2000, 2025):
        print(f"Scraping {year}...", end=' ')

        result = scrape_superbowl_page(year)

        if result:
            games_found = []
            if result['superbowl']:
                all_games.append(result['superbowl'])
                games_found.append('SB')
            if result['afc']:
                all_games.append(result['afc'])
                games_found.append('AFC')
            if result['nfc']:
                all_games.append(result['nfc'])
                games_found.append('NFC')

            if games_found:
                print(f"✅ {', '.join(games_found)}")
            else:
                print("❌ No games found")
        else:
            print("❌ Failed")

        time.sleep(1)  # Be respectful to PFR

    print(f"\n💾 Saving {len(all_games)} games to database...")

    if all_games:
        db_path = Path("data/superbowl.db")
        conn = duckdb.connect(str(db_path))

        # Drop and recreate table
        conn.execute("DROP TABLE IF EXISTS superbowl_games")
        conn.execute("""
            CREATE TABLE superbowl_games (
                year INTEGER,
                game_type VARCHAR,
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

        # Insert games
        for game in all_games:
            conn.execute("""
                INSERT INTO superbowl_games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                game['year'],
                game['game_type'],
                game['winner'],
                game['loser'],
                game['winner_q1'],
                game['winner_q2'],
                game['winner_q3'],
                game['winner_q4'],
                game['winner_final'],
                game['loser_q1'],
                game['loser_q2'],
                game['loser_q3'],
                game['loser_q4'],
                game['loser_final']
            ])

        conn.close()

        # Print summary
        superbowls = len([g for g in all_games if g['game_type'] == 'superbowl'])
        afc_champs = len([g for g in all_games if g['game_type'] == 'afc_championship'])
        nfc_champs = len([g for g in all_games if g['game_type'] == 'nfc_championship'])

        print(f"\n✅ Successfully saved {len(all_games)} games!")
        print(f"   - {superbowls} Super Bowls")
        print(f"   - {afc_champs} AFC Championships")
        print(f"   - {nfc_champs} NFC Championships")

        # Show example: 2007-2008 Super Bowl
        sb_2008 = [g for g in all_games if g['year'] == 2008 and g['game_type'] == 'superbowl']
        if sb_2008:
            game = sb_2008[0]
            print(f"\n🏆 2007-2008 Super Bowl XLII:")
            print(f"   {game['winner']} {game['winner_final']} - {game['loser']} {game['loser_final']}")
            print(f"   Quarter scores - Winner: {game['winner_q1']}, {game['winner_q2']}, {game['winner_q3']}, {game['winner_q4']}")
            print(f"   Quarter scores - Loser:  {game['loser_q1']}, {game['loser_q2']}, {game['loser_q3']}, {game['loser_q4']}")

        print(f"\n🎉 Done!")
    else:
        print("❌ No games found to save")
