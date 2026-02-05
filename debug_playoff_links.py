"""
Debug playoff link extraction
"""

from pathlib import Path
from bs4 import BeautifulSoup

html = Path("tests/fixtures/playoffs_2024_index.html").read_text()
soup = BeautifulSoup(html, 'html.parser')

# Find game summaries
game_summaries = soup.find_all('div', {'class': 'game_summary'})
print(f"Found {len(game_summaries)} game summaries\n")

for i, game_div in enumerate(game_summaries[:3]):
    print(f"\n=== Game {i+1} ===")
    print(f"Text preview: {game_div.get_text()[:200]}")

    # Look for links
    links = game_div.find_all('a')
    print(f"\nLinks found ({len(links)}):")
    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        print(f"  {text[:30]:30s} -> {href}")
