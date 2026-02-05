"""Debug linescore parsing"""
from pathlib import Path
from bs4 import BeautifulSoup

html = Path("tests/fixtures/superbowl_lviii_detail.html").read_text()
soup = BeautifulSoup(html, 'html.parser')

# Find linescore table
linescore = soup.find('table', {'class': 'linescore'})
print(f"Found linescore table: {linescore is not None}")

if linescore:
    rows = linescore.find('tbody').find_all('tr') if linescore.find('tbody') else linescore.find_all('tr')
    print(f"Number of rows: {len(rows)}")

    for i, row in enumerate(rows):
        cells = row.find_all(['th', 'td'])
        print(f"\nRow {i}: {len(cells)} cells")
        for j, cell in enumerate(cells):
            print(f"  Cell {j}: '{cell.get_text(strip=True)[:100]}'")
