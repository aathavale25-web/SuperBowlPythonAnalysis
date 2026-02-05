"""
One-time script to fetch HTML samples for testing
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

def fetch_samples():
    """Fetch sample HTML for test fixtures"""
    fixtures_dir = Path("tests/fixtures")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Fetch Super Bowl index page
        print("Fetching Super Bowl index page...")
        page.goto("https://www.pro-football-reference.com/super-bowl/", timeout=60000)
        page.wait_for_timeout(3000)  # Wait 3 seconds for content to load

        index_html = page.content()
        (fixtures_dir / "superbowl_index.html").write_text(index_html)
        print(f"✅ Saved index page ({len(index_html)} bytes)")

        # Fetch one game detail page (Super Bowl LVIII - 2024)
        print("\nFetching Super Bowl LVIII detail page...")
        page.goto("https://www.pro-football-reference.com/boxscores/202402110kan.htm", timeout=60000)
        page.wait_for_timeout(3000)  # Wait 3 seconds for content to load

        game_html = page.content()
        (fixtures_dir / "superbowl_lviii_detail.html").write_text(game_html)
        print(f"✅ Saved game detail page ({len(game_html)} bytes)")

        browser.close()

    print("\n✅ Sample HTML files saved to tests/fixtures/")

if __name__ == "__main__":
    fetch_samples()
