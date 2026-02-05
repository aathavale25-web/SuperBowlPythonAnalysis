"""
Fetch sample playoff HTML for test fixtures
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def fetch_playoff_samples():
    """Fetch sample playoff HTML for testing"""
    fixtures_dir = Path("tests/fixtures")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Fetch 2024 playoff schedule/results
        print("Fetching 2024 playoff schedule...")
        page.goto("https://www.pro-football-reference.com/years/2024/playoffs.htm", timeout=60000)
        page.wait_for_timeout(3000)

        playoff_index = page.content()
        (fixtures_dir / "playoffs_2024_index.html").write_text(playoff_index)
        print(f"✅ Saved playoff index ({len(playoff_index)} bytes)")

        time.sleep(2)

        # Fetch one playoff game detail (2024 Divisional - Chiefs vs Bills)
        # This will have player stats
        print("\nFetching playoff game detail (2024 Divisional)...")
        page.goto("https://www.pro-football-reference.com/boxscores/202501260kan.htm", timeout=60000)
        page.wait_for_timeout(3000)

        game_detail = page.content()
        (fixtures_dir / "playoff_2024_divisional_detail.html").write_text(game_detail)
        print(f"✅ Saved playoff game detail ({len(game_detail)} bytes)")

        browser.close()

    print("\n✅ Playoff fixture files saved to tests/fixtures/")

if __name__ == "__main__":
    fetch_playoff_samples()
