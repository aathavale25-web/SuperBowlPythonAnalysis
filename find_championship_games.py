"""
Find Super Bowl and Championship game IDs from ESPN API
"""

import requests
import time

def find_playoff_games_for_season(season_year):
    """
    Find all playoff games for a given season

    Args:
        season_year: The year the season started (e.g., 2023 for 2023-24 season)

    Returns:
        dict with game info
    """
    # Playoffs are seasontype=3
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    params = {
        'seasontype': 3,  # Playoffs
        'year': season_year,
        'limit': 100
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"  ⚠️  Failed to fetch {season_year}: {response.status_code}")
            return []

        data = response.json()
        events = data.get('events', [])

        games = []
        for event in events:
            name = event.get('name', '')
            game_id = event.get('id')

            # Check if it's a championship game
            game_type = None
            if 'Super Bowl' in name or 'super bowl' in name.lower():
                game_type = 'superbowl'
            elif 'AFC Championship' in name:
                game_type = 'afc_championship'
            elif 'NFC Championship' in name:
                game_type = 'nfc_championship'

            if game_type:
                games.append({
                    'season': season_year,
                    'game_id': game_id,
                    'game_type': game_type,
                    'name': name
                })

        return games

    except Exception as e:
        print(f"  ⚠️  Error fetching {season_year}: {e}")
        return []


if __name__ == "__main__":
    print("🔍 Finding Championship Games from ESPN API...\n")

    all_games = []

    # Search each season from 2000-2024
    for year in range(2000, 2025):
        print(f"Searching {year} season...", end=' ')
        games = find_playoff_games_for_season(year)

        if games:
            all_games.extend(games)
            game_types = ', '.join([g['game_type'] for g in games])
            print(f"✅ Found: {game_types}")
            for game in games:
                print(f"  - {game['name']} (ID: {game['game_id']})")
        else:
            print("❌")

        time.sleep(0.3)  # Be nice to the API

    print(f"\n📊 Summary:")
    print(f"Total games found: {len(all_games)}")

    superbowls = [g for g in all_games if g['game_type'] == 'superbowl']
    afc = [g for g in all_games if g['game_type'] == 'afc_championship']
    nfc = [g for g in all_games if g['game_type'] == 'nfc_championship']

    print(f"  - {len(superbowls)} Super Bowls")
    print(f"  - {len(afc)} AFC Championships")
    print(f"  - {len(nfc)} NFC Championships")

    # Save game IDs to a file for reference
    if all_games:
        print("\n📝 Game IDs for reference:")
        print("="*80)
        for game in sorted(all_games, key=lambda x: (x['season'], x['game_type'])):
            print(f"{game['season']} {game['game_type']:20s} {game['game_id']:15s} {game['name']}")
