"""
Test scraper with just 2024 season
"""

from scrapers.playoff_history import scrape_playoff_history

# Scrape just 2024
scrape_playoff_history(seasons=[2024])
