"""
Tests for Super Bowl history scraper
"""

import pytest
from pathlib import Path
from scrapers.superbowl_history import parse_game_linescore, extract_game_links


class TestParseGameLinescore:
    """Test parsing quarter-by-quarter scores from game detail page"""

    def test_parses_super_bowl_lviii_scores(self):
        """Parse Super Bowl LVIII (2024) - Kansas City vs San Francisco"""
        # Load fixture
        html_content = Path("tests/fixtures/superbowl_lviii_detail.html").read_text()

        # Parse the linescore
        result = parse_game_linescore(html_content)

        # Verify structure
        assert result is not None
        assert "winner" in result
        assert "loser" in result

        # Verify winner (Kansas City Chiefs - 25 points)
        assert result["winner"]["team"] == "Kansas City Chiefs"
        assert result["winner"]["q1"] == 0
        assert result["winner"]["q2"] == 3
        assert result["winner"]["q3"] == 10
        assert result["winner"]["q4"] == 6
        assert result["winner"]["final"] == 25

        # Verify loser (San Francisco 49ers - 22 points)
        assert result["loser"]["team"] == "San Francisco 49ers"
        assert result["loser"]["q1"] == 0
        assert result["loser"]["q2"] == 10
        assert result["loser"]["q3"] == 0
        assert result["loser"]["q4"] == 9
        assert result["loser"]["final"] == 22


class TestExtractGameLinks:
    """Test extracting game boxscore links from index page"""

    def test_extracts_game_links_from_index(self):
        """Extract boxscore links from Super Bowl index page"""
        # Load fixture
        html_content = Path("tests/fixtures/superbowl_index.html").read_text()

        # Extract links
        links = extract_game_links(html_content)

        # Verify we got links
        assert len(links) > 0, "Should extract at least one game link"

        # Verify link structure (should be dict with year and url)
        first_link = links[0]
        assert "year" in first_link
        assert "url" in first_link
        assert "winner" in first_link
        assert "loser" in first_link

        # Verify URL format
        assert first_link["url"].startswith("/boxscores/")
        assert first_link["url"].endswith(".htm")

        # Verify year is an integer
        assert isinstance(first_link["year"], int)
        assert first_link["year"] >= 1967  # First Super Bowl year
