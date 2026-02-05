# Web Scraping Guide

Complete documentation for all scrapers in the Super Bowl Analysis project.

## Overview

This project uses **Playwright** for web scraping NFL data from official sources. All scrapers save data in **Parquet** format for efficient storage and fast loading with Polars.

## Scrapers

### 1. Super Bowl Game History (`superbowl_history.py`)

**Purpose:** Scrape complete Super Bowl game results for squares analysis.

**Data Collected:**
- Winner and loser team names
- Final scores
- Quarter-by-quarter scores (Q1, Q2, Q3, Q4)

**Output:** `data/superbowl_games.parquet`

**Usage:**
```python
from scrapers.superbowl_history import scrape_superbowl_history

# Scrape all Super Bowl games
scrape_superbowl_history()
```

**Sample Output:**
```
┌──────────────┬──────────────┬──────────────┬──────────────┬─────┬─────┬─────┬─────┬────────────┬────────────┐
│ winner       ┆ loser        ┆ winner_score ┆ loser_score  ┆ q1w ┆ q2w ┆ q3w ┆ q4w ┆ q1l        ┆ q4l        │
├──────────────┼──────────────┼──────────────┼──────────────┼─────┼─────┼─────┼─────┼────────────┼────────────┤
│ Kansas City  ┆ Philadelphia ┆ 38           ┆ 35           ┆ 7   ┆ 24  ┆ 31  ┆ 38  ┆ 14         ┆ 35         │
└──────────────┴──────────────┴──────────────┴──────────────┴─────┴─────┴─────┴─────┴────────────┴────────────┘
```

**Notes:**
- Scrapes from NFL's official Super Bowl history page
- Handles all Super Bowl games (I through current)
- Extracts quarter scores from game detail pages
- Uses Playwright for dynamic content loading

---

### 2. Super Bowl Player History (`superbowl_player_history.py`)

**Purpose:** Scrape individual player performances in Super Bowl games for prediction benchmarking.

**Data Collected:**

**QB Stats:**
- Passing yards, passing TDs, interceptions
- Rushing yards, rushing TDs

**RB Stats:**
- Rushing yards, rushing TDs
- Receiving yards, receptions, receiving TDs

**WR/TE Stats:**
- Receiving yards, receptions, receiving TDs

**Output:** `data/superbowl_player_history.parquet`

**Usage:**
```python
from scrapers.superbowl_player_history import scrape_superbowl_player_history

# Scrape all Super Bowl player performances
scrape_superbowl_player_history()
```

**Sample Output:**
```
┌──────────────────┬──────────┬──────────────┬──────────┬────────────┬──────────────┐
│ player_name      ┆ position ┆ passing_yards┆ pass_tds ┆ rush_yards ┆ rush_tds     │
├──────────────────┼──────────┼──────────────┼──────────┼────────────┼──────────────┤
│ Patrick Mahomes  ┆ QB       ┆ 333          ┆ 3        ┆ 44         ┆ 1            │
│ Jalen Hurts      ┆ QB       ┆ 304          ┆ 1        ┆ 70         ┆ 3            │
└──────────────────┴──────────┴──────────────┴──────────┴────────────┴──────────────┘
```

**Implementation Details:**
- Scrapes from Pro Football Reference boxscores
- Iterates through all Super Bowl games (I-LVIII)
- Extracts passing, rushing, and receiving stats tables
- Maps player names to positions (QB, RB, WR, TE)
- Handles missing data gracefully

**Key Functions:**
```python
def scrape_superbowl_player_history():
    """Main function to scrape all Super Bowl player stats"""

def extract_player_stats_from_boxscore(page, game_id):
    """Extract player stats from single boxscore page"""

def parse_stats_table(table_html, stat_type, position):
    """Parse HTML table into structured data"""
```

---

### 3. Playoff History (`playoff_history.py`)

**Purpose:** Scrape playoff game results for game prop analysis.

**Data Collected:**
- Game date and teams
- Final scores
- Winning margin
- Round (Wild Card, Divisional, Conference, Super Bowl)
- Whether game had a defensive TD

**Output:** `data/playoff_games.parquet`

**Usage:**
```python
from scrapers.playoff_history import scrape_playoff_history

# Scrape specific seasons
scrape_playoff_history(seasons=[2023, 2024])

# Scrape season range
scrape_playoff_history(seasons=list(range(2020, 2025)))
```

**Sample Output:**
```
┌────────────┬────────────┬──────────────┬──────────────┬────────────┬────────────────┐
│ date       ┆ winner     ┆ winner_score ┆ loser_score  ┆ round      ┆ defensive_td   │
├────────────┼────────────┼──────────────┼──────────────┼────────────┼────────────────┤
│ 2024-02-11 ┆ KC         ┆ 25           ┆ 22           ┆ Super Bowl ┆ False          │
└────────────┴────────────┴──────────────┴──────────────┴────────────┴────────────────┘
```

**Notes:**
- Configurable season range
- Identifies playoff rounds automatically
- Calculates derived metrics (total points, margin)
- Defensive TD detection (placeholder - requires game-by-game analysis)

---

### 4. Player Stats (`player_stats.py`)

**Purpose:** Scrape season-long game logs for tracked players.

**Data Collected:**

Player statistics by position (same as SB scraper):
- QB: Passing/rushing stats
- RB: Rushing/receiving stats
- WR/TE: Receiving stats

**Output:** `data/player_stats_2025.parquet` (or specified year)

**Usage:**
```python
from scrapers.player_stats import scrape_player_stats

# Scrape 2025 season (default)
scrape_player_stats(season=2025)

# Scrape different season
scrape_player_stats(season=2024)
```

**Configuration:**
Reads from `players_to_track.json`:
```json
{
  "players": [
    {
      "name": "Patrick Mahomes",
      "position": "QB",
      "team": "KC"
    },
    {
      "name": "Christian McCaffrey",
      "position": "RB",
      "team": "SF"
    }
  ]
}
```

**Sample Output:**
```
┌──────────────────┬──────────┬──────┬──────────────┬──────────┬────────────┐
│ player_name      ┆ position ┆ week ┆ passing_yards┆ pass_tds ┆ rush_yards │
├──────────────────┼──────────┼──────┼──────────────┼──────────┼────────────┤
│ Patrick Mahomes  ┆ QB       ┆ 1    ┆ 291          ┆ 2        ┆ 16         │
│ Patrick Mahomes  ┆ QB       ┆ 2    ┆ 320          ┆ 3        ┆ 8          │
└──────────────────┴──────────┴──────┴──────────────┴──────────┴────────────┘
```

**Notes:**
- Requires player configuration file
- Scrapes complete season game logs
- Handles bye weeks and missed games
- Year-specific output files

---

## Common Patterns

### Error Handling

All scrapers implement robust error handling:

```python
try:
    # Scraping logic
    data = scrape_data()
    save_to_parquet(data)
except Exception as e:
    print(f"Error: {e}")
    # Graceful fallback
```

### Playwright Browser Management

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Scraping logic
    page.goto(url)
    content = page.content()

    browser.close()
```

### Parquet Output

All scrapers use Polars for efficient data handling:

```python
import polars as pl

# Create DataFrame
df = pl.DataFrame(data)

# Save to Parquet
df.write_parquet("data/output.parquet")
```

---

## Troubleshooting

### Browser Not Found

**Error:** `Executable doesn't exist`

**Solution:**
```bash
playwright install chromium
```

### Rate Limiting

If you encounter rate limiting:
- Add delays between requests: `time.sleep(2)`
- Respect robots.txt
- Don't scrape too frequently

### Missing Data

If scraper returns incomplete data:
1. Check if website structure changed
2. Verify selectors in scraper code
3. Add debug prints to see HTML structure
4. Update CSS/XPath selectors as needed

### Parquet File Issues

**Error:** File locked or corrupt

**Solution:**
```bash
# Delete and re-scrape
rm data/*.parquet
python -c "from scrapers.X import scrape_X; scrape_X()"
```

---

## Best Practices

1. **Always test scrapers locally** before running in production
2. **Check output data** after scraping:
   ```python
   import polars as pl
   df = pl.read_parquet("data/output.parquet")
   print(df)
   ```
3. **Version control data files** (if small) or document schema
4. **Set appropriate headless mode**:
   - Development: `headless=False` (see browser)
   - Production: `headless=True` (faster)
5. **Handle missing data** gracefully with defaults
6. **Log scraping results** for debugging
7. **Use GitHub Actions** for automated weekly updates

---

## Data Schema Reference

### superbowl_games.parquet
```
winner: str          # Winning team name
loser: str           # Losing team name
winner_score: int    # Final winner score
loser_score: int     # Final loser score
q1w, q2w, q3w, q4w: int  # Winner quarter scores
q1l, q2l, q3l, q4l: int  # Loser quarter scores
```

### superbowl_player_history.parquet
```
player_name: str       # Player full name
position: str          # QB, RB, WR, or TE
passing_yards: int     # QB passing yards
passing_tds: int       # QB passing touchdowns
interceptions: int     # QB interceptions
rushing_yards: int     # Rushing yards (QB, RB)
rushing_tds: int       # Rushing touchdowns
receiving_yards: int   # Receiving yards (RB, WR, TE)
receptions: int        # Receptions (RB, WR, TE)
receiving_tds: int     # Receiving touchdowns
```

### playoff_games.parquet
```
date: date             # Game date
winner: str            # Winning team abbreviation
loser: str             # Losing team abbreviation
winner_score: int      # Final winner score
loser_score: int       # Final loser score
round: str             # Wild Card, Divisional, Conference, Super Bowl
total_points: int      # Sum of scores
winning_margin: int    # Score difference
defensive_td: bool     # Whether game had defensive TD
```

### player_stats_YYYY.parquet
```
player_name: str       # Player full name
position: str          # QB, RB, WR, or TE
week: int              # NFL week number
[Same stat columns as superbowl_player_history]
```

---

## Maintenance

### Updating for New Season

1. Update `players_to_track.json` with current roster
2. Run player stats scraper with new season:
   ```bash
   python -c "from scrapers.player_stats import scrape_player_stats; scrape_player_stats(season=2026)"
   ```
3. Update `generate_site.py` if filename changed
4. Regenerate site

### Adding New Players

Edit `players_to_track.json`:
```json
{
  "players": [
    {
      "name": "New Player",
      "position": "QB",
      "team": "KC"
    }
  ]
}
```

Then re-run scraper.

### Extending Scrapers

To add new stats:
1. Identify HTML selector for new stat
2. Add column to DataFrame schema
3. Update extraction logic
4. Test with sample data
5. Update analysis modules to use new stat

---

## GitHub Actions Integration

Scrapers run automatically via `.github/workflows/update-analysis.yml`:

```yaml
- name: Scrape Data
  run: |
    python -c "from scrapers.superbowl_history import scrape_superbowl_history; scrape_superbowl_history()"
    python -c "from scrapers.superbowl_player_history import scrape_superbowl_player_history; scrape_superbowl_player_history()"
    python -c "from scrapers.playoff_history import scrape_playoff_history; scrape_playoff_history(seasons=list(range(2020, 2026)))"
    python -c "from scrapers.player_stats import scrape_player_stats; scrape_player_stats(season=2025)"
```

Updates run:
- **Weekly:** Every Sunday at 2am UTC
- **Manual:** Trigger via Actions tab

---

## Resources

- **Playwright Docs:** https://playwright.dev/python/
- **Polars Docs:** https://pola-rs.github.io/polars/
- **Pro Football Reference:** https://www.pro-football-reference.com/
- **NFL.com:** https://www.nfl.com/

---

**Last Updated:** February 2025
