"""
Quick script to examine HTML structure
"""

from pathlib import Path
from bs4 import BeautifulSoup

# Examine index page
index_html = Path("tests/fixtures/superbowl_index.html").read_text()
soup = BeautifulSoup(index_html, 'html.parser')

print("=== SUPER BOWL INDEX PAGE ===\n")

# Find all tables and their IDs
tables = soup.find_all('table')
print(f"Found {len(tables)} tables\n")
for table in tables[:5]:  # Show first 5
    table_id = table.get('id', 'no-id')
    print(f"Table ID: {table_id}")

# Try to find Super Bowl data
table = soup.find('table', {'id': 'super_bowls'})
if not table:
    # Try other possible IDs
    for possible_id in ['superbowls', 'results', 'games']:
        table = soup.find('table', {'id': possible_id})
        if table:
            print(f"\nFound table with ID: {possible_id}")
            break

if table:
    rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')
    print(f"Found {len(rows)} rows\n")

    # Show first two rows structure
    for row_idx, row in enumerate(rows[:2]):
        print(f"\nRow {row_idx}:")
        for i, cell in enumerate(row.find_all(['th', 'td'])):
            text = cell.get_text(strip=True)[:60]
            print(f"  {i}: {text}")
            if cell.find('a'):
                print(f"      Link: {cell.find('a').get('href')}")
else:
    print("\nCould not find Super Bowl results table")

print("\n=== GAME DETAIL PAGE ===\n")

# Examine game detail page
detail_html = Path("tests/fixtures/superbowl_lviii_detail.html").read_text()
soup = BeautifulSoup(detail_html, 'html.parser')

# Find scoring table
scoring_table = soup.find('table', {'class': 'linescore'})
if scoring_table:
    print("Found linescore table\n")
    rows = scoring_table.find('tbody').find_all('tr')
    for row in rows:
        cells = row.find_all(['th', 'td'])
        team_name = cells[0].get_text(strip=True) if cells else ''
        scores = [c.get_text(strip=True) for c in cells[1:]]
        print(f"{team_name}: {scores}")
else:
    print("Could not find linescore table")
