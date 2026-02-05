"""
Fetch sample player game log HTML for testing
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def fetch_player_sample():
    """Fetch Patrick Mahomes 2024 game log"""
    fixtures_dir = Path("tests/fixtures")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Fetch Patrick Mahomes game log page
        print("Fetching Patrick Mahomes 2024 game log...")
        page.goto("https://www.pro-football-reference.com/players/M/MahoPa00/gamelog/2024/", timeout=60000)
        page.wait_for_timeout(3000)

        html = page.content()
        (fixtures_dir / "mahomes_2024_gamelog.html").write_text(html)
        print(f"✅ Saved ({len(html)} bytes)")

        browser.close()

    print("\n✅ Player fixture saved to tests/fixtures/")

if __name__ == "__main__":
    fetch_player_sample()
