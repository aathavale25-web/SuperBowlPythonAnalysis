"""
Examine playoff HTML structure
"""

from pathlib import Path
from bs4 import BeautifulSoup

# Examine playoff index
print("=== PLAYOFF INDEX (2024) ===\n")
index_html = Path("tests/fixtures/playoffs_2024_index.html").read_text()
soup = BeautifulSoup(index_html, 'html.parser')

# Find playoff games table
tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

# Look for playoff game structure
divs = soup.find_all('div', {'class': 'game'})
print(f"Found {len(divs)} game divs\n")

# Try to find game summaries
summaries = soup.find_all('div', {'class': 'game_summary'})
print(f"Found {len(summaries)} game summaries")

if summaries:
    first_game = summaries[0]
    print("\nFirst game structure:")
    print(first_game.get_text()[:300])

# Examine game detail page for player stats
print("\n\n=== PLAYOFF GAME DETAIL ===\n")
detail_html = Path("tests/fixtures/playoff_2024_divisional_detail.html").read_text()
soup = BeautifulSoup(detail_html, 'html.parser')

# Find passing stats table
passing_table = soup.find('table', {'id': lambda x: x and 'passing' in x.lower()})
if passing_table:
    print("✓ Found passing stats table")
    rows = passing_table.find('tbody').find_all('tr')[:2]
    print(f"  First 2 rows:")
    for row in rows:
        cells = [c.get_text(strip=True) for c in row.find_all(['th', 'td'])]
        print(f"    {cells[:5]}")

# Find rushing stats
rushing_table = soup.find('table', {'id': lambda x: x and 'rushing' in x.lower()})
if rushing_table:
    print("\n✓ Found rushing stats table")

# Find receiving stats
receiving_table = soup.find('table', {'id': lambda x: x and 'receiving' in x.lower()})
if receiving_table:
    print("✓ Found receiving stats table")

# Find team names and score
linescore = soup.find('table', {'class': 'linescore'})
if linescore:
    print("\n✓ Found linescore")
    rows = linescore.find('tbody').find_all('tr')
    for row in rows[:2]:
        cells = [c.get_text(strip=True) for c in row.find_all(['th', 'td'])]
        print(f"  {cells[:3]}")
