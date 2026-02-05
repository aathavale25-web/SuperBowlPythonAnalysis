"""
Examine player game log HTML structure
"""

from pathlib import Path
from bs4 import BeautifulSoup

html = Path("tests/fixtures/mahomes_2024_gamelog.html").read_text()
soup = BeautifulSoup(html, 'html.parser')

print("=== PLAYER GAME LOG ===\n")

# Find game log table
table = soup.find('table', {'id': 'stats'})
if table:
    print("✓ Found stats table")

    # Check header
    thead = table.find('thead')
    if thead:
        headers = [th.get_text(strip=True) for th in thead.find_all('th')]
        print(f"\nHeaders ({len(headers)}):")
        print(f"  {headers[:15]}")

    # Check first few game rows
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr', class_=lambda x: x != 'thead')[:3]
        print(f"\nFirst 3 game rows:\n")

        for i, row in enumerate(rows, 1):
            cells = row.find_all(['th', 'td'])
            print(f"Row {i} ({len(cells)} cells):")

            # Show first 10 cells
            for j, cell in enumerate(cells[:10]):
                stat = cell.get('data-stat', 'unknown')
                text = cell.get_text(strip=True)
                print(f"  {j}: {stat:20s} = {text}")
            print()
else:
    print("✗ Stats table not found")
