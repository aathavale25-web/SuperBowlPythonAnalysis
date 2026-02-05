# Super Bowl Player Props Analysis Design

**Date:** February 4, 2026
**Goal:** Enable Super Bowl LIX predictions for New England Patriots vs Seattle Seahawks using position-based historical trends combined with 2025 season player data

## Overview

Enhance the existing Super Bowl analysis tool to provide player prop predictions for the upcoming Super Bowl by:
1. Scraping 2025 season data for key NE and SEA players
2. Scraping historical Super Bowl player performance data by position
3. Combining season performance with Super Bowl position benchmarks to predict prop hit rates
4. Displaying predictions with confidence indicators

## 1. Data Requirements

### New Player Tracking Configuration
- Update `players_to_track.json` with key NE and SEA players
- Include: QB, top RB, top 2 WRs, top TE from each team
- Requires user input for specific player names

### Two Types of Historical Data

**Player Season Data (2025):**
- Individual game logs for NE/SEA players
- Calculate season averages, trends, hit rates
- Stored in: `data/player_stats_2025.parquet`

**Super Bowl Player Data (Historical):**
- Past Super Bowl game logs by position (all QBs, WRs, RBs, TEs)
- Position-specific trends and benchmarks
- Stored in: `data/superbowl_player_history.parquet`

### New Scraper Requirements
- Modify `scrapers/player_stats.py` to scrape 2025 season for multiple players
- Create `scrapers/superbowl_player_stats.py` for historical Super Bowl player performance
- Both output to parquet files with consistent schema

## 2. Analysis Module Changes

### Modifications to `analysis/player_trends.py`

**Add Position Benchmarking Function:**
```python
calculate_position_benchmarks(superbowl_history, position)
```
- Returns historical Super Bowl averages for position
- Example output: QBs average 285 yards, 2.1 TDs, hit O275.5 yards in 68% of Super Bowls

**Enhanced Player Summary:**
- Current: Player's season stats + hit rates + trends
- Add: Comparison to Super Bowl position benchmarks
- Example: "Player X averages 320 yards (season) vs 285 yards (SB position average)"

**Combined Hit Rate Prediction:**
- Weight: Player season performance (70%) + Position SB history (30%)
- Formula: `predicted_rate = (season_rate * 0.7) + (position_sb_rate * 0.3)`
- Accounts for "Super Bowl is different" factor

**Best Bets Identification:**
- Keep existing 65% threshold
- Add "SB-validated" flag when position historically performs well
- Example: "Player O275.5 yards - 78% season, 68% SB position ✓ STRONG BET"

## 3. Scraper Implementation

### New Scraper: `scrapers/superbowl_player_stats.py`

**What It Scrapes:**
- Historical Super Bowl game logs (Super Bowl I through LVIII)
- Player stats by position: passing_yards, passing_tds, rushing_yards, receiving_yards, receptions, etc.
- Top performers from each Super Bowl (starting QB, leading RBs, top WRs/TEs)

**Data Structure:**
```
superbowl_player_history.parquet:
- super_bowl (text): "LVIII", "LVII", etc.
- year (int): 2024, 2023, etc.
- player_name (text)
- position (text): "QB", "RB", "WR", "TE"
- team (text)
- passing_yards (int)
- passing_tds (int)
- interceptions (int)
- rushing_yards (int)
- rushing_tds (int)
- receptions (int)
- receiving_yards (int)
- receiving_tds (int)
```

### Modified `scrapers/player_stats.py`

**Changes:**
- Change hardcoded season from 2024 to 2025
- Add ability to scrape multiple players in one run
- Read from `players_to_track.json` instead of hardcoding player names
- Output to `player_stats_2025.parquet`

**Error Handling:**
- If player data not available (injury, DNP, etc.), log warning and continue
- If Super Bowl historical data incomplete, still provide season-based analysis
- Graceful degradation: missing SB data doesn't break player analysis

## 4. Site Generation & Display

### Updates to `generate_site.py`

**New Data Loading:**
- Load `player_stats_2025.parquet` (update from 2024)
- Load `superbowl_player_history.parquet` (new file)
- Pass both datasets to analysis modules

**Enhanced Player Props Page:**
- Current: Player stats + hit rates + trends
- Add: "Super Bowl Context" section per player
- Show position benchmarks: "QBs in Super Bowls average X, hit this line Y%"
- Highlight alignment/differences between season performance and SB history

**New "Super Bowl Predictions" Section:**
- Dashboard card: "Top 5 Best Bets for Super Bowl LIX"
- Only show props with >65% combined hit rate (season + SB history)
- Include confidence indicators based on data agreement

### Template Updates

**`templates/players.html`:**
- Add SB benchmark comparison tables
- Visual indicators for each prop

**`templates/index.html`:**
- Add "Super Bowl Predictions" card to dashboard
- Summary of best bets

**Visual Indicators:**
- ✓ SB-validated bets (season and SB data agree)
- ⚠️ Season-only bets (limited SB position data)

## 5. Implementation Steps & Testing

### Implementation Order

**Phase 1: Update Player Configuration**
- Update `players_to_track.json` with NE and SEA players
- Obtain roster from user or look up 2025 rosters

**Phase 2: Build Super Bowl History Scraper**
- Create `scrapers/superbowl_player_stats.py`
- Test scraper, verify data quality
- Generate `superbowl_player_history.parquet`

**Phase 3: Update Season Stats Scraper**
- Modify `scrapers/player_stats.py` to use 2025 season
- Loop through all players in config
- Generate `player_stats_2025.parquet`

**Phase 4: Enhance Analysis Module**
- Add position benchmark functions to `analysis/player_trends.py`
- Add combined prediction logic
- Update output formatting

**Phase 5: Update Site Generator & Templates**
- Modify `generate_site.py` to load both datasets
- Update HTML templates with new sections
- Test locally with `python serve_site.py`

### Testing Strategy

**Unit Tests:**
- Test new scraper functions
- Test position benchmark calculations
- Test combined prediction formulas

**Data Verification:**
- Verify parquet files have expected columns
- Check data types and ranges
- Validate historical SB data completeness

**Manual Testing:**
- Generate site locally
- Check predictions make sense
- Compare known player's season stats vs SB position benchmarks
- Verify visual indicators display correctly

### Data Update Workflow

**Manual Updates:**
- Run scrapers when fresh 2025 data needed
- Super Bowl history scraper: run once (static historical data)
- Player stats scraper: can run weekly during season

**GitHub Actions:**
- Update weekly for player stats
- Super Bowl history: one-time scrape, stored in repo

## Success Criteria

1. Site displays player prop predictions for NE vs SEA Super Bowl
2. Each player shows season stats + Super Bowl position benchmarks
3. Combined hit rate predictions weight season (70%) and position history (30%)
4. Best bets identified with >65% threshold and SB-validation flags
5. All tests pass
6. Site generates without errors

## YAGNI Principles Applied

- No advanced ML models (simple weighted averages)
- No real-time odds integration (manual line entry acceptable)
- No historical matchup analysis (position-based only)
- No injury data integration (manual adjustments by user)
- No user customization of weighting formula (fixed 70/30)

## Dependencies

- Existing: polars, beautifulsoup4, playwright, jinja2
- No new dependencies required

## Rollback Plan

If implementation has issues:
- Keep existing 2024 data and analysis working
- New features are additive, won't break existing functionality
- Can fall back to season-only analysis if SB scraper fails
