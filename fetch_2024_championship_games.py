"""
Fetch 2024-2025 season championship games from ESPN
"""

import requests
import json
from pathlib import Path

def get_game_details(game_id):
    """Get quarter-by-quarter scores for a specific game"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"

    try:
        response = requests.get(url)
        if response.status_code != 200:
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
        # Super Bowl is in following calendar year
        if 'Super Bowl' in data.get('header', {}).get('competitions', [{}])[0].get('notes', [{}])[0].get('headline', ''):
            year += 1

        return {
            'year': year,
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
        print(f"  Error: {e}")
        return None


def search_2024_playoff_games():
    """Search for 2024 season playoff games"""
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    params = {
        'seasontype': 3,  # Playoffs
        'year': 2024,
        'limit': 100
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return None, None, None

        data = response.json()
        events = data.get('events', [])

        superbowl_id = None
        afc_id = None
        nfc_id = None

        for event in events:
            name = event.get('name', '')
            game_id = event.get('id')

            if 'Super Bowl' in name or 'super bowl' in name.lower():
                superbowl_id = game_id
            elif 'AFC Championship' in name:
                afc_id = game_id
            elif 'NFC Championship' in name:
                nfc_id = game_id

        return superbowl_id, afc_id, nfc_id

    except Exception as e:
        print(f"  Error searching: {e}")
        return None, None, None


if __name__ == "__main__":
    print("🏈 Fetching 2024-2025 Season Championship Games...\n")

    print("🔍 Searching for games...")
    superbowl_id, afc_id, nfc_id = search_2024_playoff_games()

    games = []

    if superbowl_id:
        print(f"\n📊 Fetching Super Bowl (ID: {superbowl_id})...")
        game = get_game_details(superbowl_id)
        if game:
            game['game_type'] = 'superbowl'
            games.append(game)
            print(f"  ✅ {game['winner']} {game['winner_final']} - {game['loser']} {game['loser_final']}")
        else:
            print("  ❌ Failed to fetch")
    else:
        print("\n❌ Could not find Super Bowl ID")

    if afc_id:
        print(f"\n📊 Fetching AFC Championship (ID: {afc_id})...")
        game = get_game_details(afc_id)
        if game:
            game['game_type'] = 'afc_championship'
            game['year'] = 2024  # Championship game is in 2024 season
            games.append(game)
            print(f"  ✅ {game['winner']} {game['winner_final']} - {game['loser']} {game['loser_final']}")
        else:
            print("  ❌ Failed to fetch")
    else:
        print("\n❌ Could not find AFC Championship ID")

    if nfc_id:
        print(f"\n📊 Fetching NFC Championship (ID: {nfc_id})...")
        game = get_game_details(nfc_id)
        if game:
            game['game_type'] = 'nfc_championship'
            game['year'] = 2024  # Championship game is in 2024 season
            games.append(game)
            print(f"  ✅ {game['winner']} {game['winner_final']} - {game['loser']} {game['loser_final']}")
        else:
            print("  ❌ Failed to fetch")
    else:
        print("\n❌ Could not find NFC Championship ID")

    if games:
        # Save to JSON
        output_path = Path("championship_games_2024.json")
        with open(output_path, 'w') as f:
            json.dump(games, f, indent=2)

        print(f"\n✅ Saved {len(games)} games to {output_path}")
        print("\nTo add these to the database, run: python load_2024_games.py")
    else:
        print("\n⚠️  No games found via ESPN API")
        print("\nPlease provide the game scores manually:")
        print("  - 2024 AFC Championship: Winner, Loser, Scores by quarter")
        print("  - 2024 NFC Championship: Winner, Loser, Scores by quarter")
        print("  - 2025 Super Bowl LIX: Winner, Loser, Scores by quarter")
