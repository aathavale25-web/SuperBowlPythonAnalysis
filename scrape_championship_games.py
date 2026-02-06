"""
Scrape Super Bowl and AFC/NFC Championship games from 2000 onwards
"""

import requests
from bs4 import BeautifulSoup
import duckdb
from pathlib import Path
import time

def get_game_details(game_id):
    """
    Get quarter-by-quarter scores for a specific game

    Args:
        game_id: ESPN game ID

    Returns:
        dict with game details or None
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"  ⚠️  Failed to fetch game {game_id}: {response.status_code}")
            return None

        data = response.json()

        # Extract basic info
        header = data.get('header', {}).get('competitions', [{}])[0]
        competitors = header.get('competitors', [])

        if len(competitors) != 2:
            return None

        # Determine winner/loser
        team1 = competitors[0]
        team2 = competitors[1]

        team1_score = int(team1.get('score', 0))
        team2_score = int(team2.get('score', 0))

        if team1_score > team2_score:
            winner = team1
            loser = team2
        else:
            winner = team2
            loser = team1

        # Extract quarter scores from linescores
        winner_linescores = winner.get('linescores', [])
        loser_linescores = loser.get('linescores', [])

        # Build cumulative scores by quarter
        winner_quarters = []
        loser_quarters = []

        winner_cumulative = 0
        loser_cumulative = 0

        for i in range(4):  # Q1-Q4
            if i < len(winner_linescores):
                winner_cumulative += int(winner_linescores[i].get('value', 0))
            winner_quarters.append(winner_cumulative)

            if i < len(loser_linescores):
                loser_cumulative += int(loser_linescores[i].get('value', 0))
            loser_quarters.append(loser_cumulative)

        # Get year from date
        year = int(data.get('header', {}).get('season', {}).get('year', 0))

        return {
            'year': year,
            'game_id': game_id,
            'winner': winner.get('team', {}).get('displayName', ''),
            'loser': loser.get('team', {}).get('displayName', ''),
            'winner_q1': winner_quarters[0] if len(winner_quarters) > 0 else 0,
            'winner_q2': winner_quarters[1] if len(winner_quarters) > 1 else 0,
            'winner_q3': winner_quarters[2] if len(winner_quarters) > 2 else 0,
            'winner_q4': winner_quarters[3] if len(winner_quarters) > 3 else 0,
            'winner_final': int(winner.get('score', 0)),
            'loser_q1': loser_quarters[0] if len(loser_quarters) > 0 else 0,
            'loser_q2': loser_quarters[1] if len(loser_quarters) > 1 else 0,
            'loser_q3': loser_quarters[2] if len(loser_quarters) > 2 else 0,
            'loser_q4': loser_quarters[3] if len(loser_quarters) > 3 else 0,
            'loser_final': int(loser.get('score', 0))
        }

    except Exception as e:
        print(f"  ⚠️  Error fetching game {game_id}: {e}")
        return None


def get_championship_games():
    """
    Get Super Bowl and Championship game IDs from 2000 onwards

    Returns:
        dict with 'superbowl', 'afc', 'nfc' lists of game IDs
    """
    # Super Bowl game IDs from ESPN (2000-2024)
    # Format: (year, game_id, description)
    superbowl_ids = [
        (2000, '200130028', 'SB XXXV'),
        (2001, '210203028', 'SB XXXVI'),
        (2002, '220126028', 'SB XXXVII'),
        (2003, '240201028', 'SB XXXVIII'),
        (2004, '250206028', 'SB XXXIX'),
        (2005, '260205028', 'SB XL'),
        (2006, '270204028', 'SB XLI'),
        (2007, '280203028', 'SB XLII'),
        (2008, '290201028', 'SB XLIII'),
        (2009, '300207028', 'SB XLIV'),
        (2010, '310206028', 'SB XLV'),
        (2011, '320205028', 'SB XLVI'),
        (2012, '330203028', 'SB XLVII'),
        (2013, '340202028', 'SB XLVIII'),
        (2014, '350201028', 'SB XLIX'),
        (2015, '360207028', 'SB 50'),
        (2016, '370205028', 'SB LI'),
        (2017, '380204028', 'SB LII'),
        (2018, '390203028', 'SB LIII'),
        (2019, '400202028', 'SB LIV'),
        (2020, '410207028', 'SB LV'),
        (2021, '410213028', 'SB LVI'),
        (2022, '430212028', 'SB LVII'),
        (2023, '440211028', 'SB LVIII'),
        (2024, '440209028', 'SB LIX'),
    ]

    # AFC/NFC Championship game IDs (these are harder to get systematically)
    # We'll need to search for them by year
    championship_ids = {
        'superbowl': superbowl_ids,
        'afc': [],
        'nfc': []
    }

    return championship_ids


def search_championship_games_by_year(year):
    """
    Search for AFC and NFC Championship games for a given year

    Args:
        year: Season year (e.g., 2023 for 2023-24 season)

    Returns:
        tuple of (afc_game_id, nfc_game_id) or (None, None)
    """
    # Try to get the playoff schedule for the year
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={year}0101-{year+1}0228&seasontype=3"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None, None

        data = response.json()
        events = data.get('events', [])

        afc_game_id = None
        nfc_game_id = None

        for event in events:
            name = event.get('name', '').lower()
            game_id = event.get('id')

            if 'afc championship' in name:
                afc_game_id = game_id
            elif 'nfc championship' in name:
                nfc_game_id = game_id

        return afc_game_id, nfc_game_id

    except Exception as e:
        print(f"  ⚠️  Error searching games for {year}: {e}")
        return None, None


if __name__ == "__main__":
    print("🏈 Scraping Championship Games (2000-2024)...\n")

    # Get game IDs
    print("📋 Loading game IDs...")
    game_data = get_championship_games()

    all_games = []

    # Fetch Super Bowls
    print(f"\n📊 Fetching {len(game_data['superbowl'])} Super Bowls...")
    for year, game_id, desc in game_data['superbowl']:
        print(f"  {year} {desc}...", end=' ')
        game = get_game_details(game_id)
        if game:
            game['game_type'] = 'superbowl'
            all_games.append(game)
            print(f"✅ {game['winner']} {game['winner_final']} - {game['loser']} {game['loser_final']}")
        else:
            print("❌")
        time.sleep(0.5)  # Be nice to ESPN's servers

    # Fetch AFC/NFC Championship games
    print(f"\n📊 Searching for AFC/NFC Championship games (2000-2024)...")
    for year in range(2000, 2025):
        print(f"  {year} season...", end=' ')
        afc_id, nfc_id = search_championship_games_by_year(year)

        if afc_id:
            game = get_game_details(afc_id)
            if game:
                game['game_type'] = 'afc_championship'
                all_games.append(game)
                print(f"AFC ✅", end=' ')

        if nfc_id:
            game = get_game_details(nfc_id)
            if game:
                game['game_type'] = 'nfc_championship'
                all_games.append(game)
                print(f"NFC ✅", end=' ')

        if not afc_id and not nfc_id:
            print("❌")
        else:
            print()

        time.sleep(0.5)

    # Save to database
    print(f"\n💾 Saving {len(all_games)} games to database...")

    db_path = Path("data/superbowl.db")
    conn = duckdb.connect(str(db_path))

    # Drop existing table and create new one with game_type
    conn.execute("DROP TABLE IF EXISTS superbowl_games")
    conn.execute("""
        CREATE TABLE superbowl_games (
            year INTEGER,
            game_id VARCHAR,
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
            INSERT INTO superbowl_games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            game['year'],
            game['game_id'],
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

    # Summary
    print(f"\n✅ Successfully saved {len(all_games)} games!")

    superbowls = len([g for g in all_games if g['game_type'] == 'superbowl'])
    afc_champs = len([g for g in all_games if g['game_type'] == 'afc_championship'])
    nfc_champs = len([g for g in all_games if g['game_type'] == 'nfc_championship'])

    print(f"   - {superbowls} Super Bowls")
    print(f"   - {afc_champs} AFC Championships")
    print(f"   - {nfc_champs} NFC Championships")
    print(f"\n🎉 Done!")
