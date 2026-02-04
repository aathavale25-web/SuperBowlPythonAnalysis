"""
Tests for playoff history scraper
"""

import pytest
from pathlib import Path
from scrapers.playoff_history import (
    parse_playoff_game_detail,
    extract_player_passing_stats,
    extract_player_rushing_stats,
    extract_player_receiving_stats
)


class TestParsePlayoffGameDetail:
    """Test parsing playoff game basic info from detail page"""

    def test_parses_game_teams_and_scores(self):
        """Parse teams and final scores from playoff game"""
        html_content = Path("tests/fixtures/playoff_2024_divisional_detail.html").read_text()

        result = parse_playoff_game_detail(html_content)

        assert result is not None
        assert "winner" in result
        assert "loser" in result
        assert "winner_score" in result
        assert "loser_score" in result

        # Kansas City Chiefs won 32-29 vs Buffalo Bills
        # (One team scored more - we determine winner/loser)
        teams = {result["winner"], result["loser"]}
        assert "Kansas City Chiefs" in teams
        assert "Buffalo Bills" in teams

        # Check scores are reasonable
        assert result["winner_score"] >= result["loser_score"]
        assert result["winner_score"] > 0
        assert result["loser_score"] > 0


class TestExtractPlayerPassingStats:
    """Test extracting QB passing statistics"""

    def test_extracts_qb_passing_stats(self):
        """Extract QB passing yards, TDs, INTs, rushing yards"""
        html_content = Path("tests/fixtures/playoff_2024_divisional_detail.html").read_text()

        stats = extract_player_passing_stats(html_content)

        # Should have stats for QBs from both teams
        assert len(stats) >= 2

        # Check first QB has required fields
        qb = stats[0]
        assert "player_name" in qb
        assert "team" in qb
        assert "passing_yards" in qb
        assert "passing_tds" in qb
        assert "interceptions" in qb
        assert "rushing_yards" in qb

        # Values should be integers
        assert isinstance(qb["passing_yards"], int)
        assert isinstance(qb["passing_tds"], int)
        assert isinstance(qb["interceptions"], int)
        assert isinstance(qb["rushing_yards"], int)

        # Should have Josh Allen (BUF)
        qb_names = [q["player_name"] for q in stats]
        assert "Josh Allen" in qb_names


class TestExtractPlayerRushingStats:
    """Test extracting RB rushing statistics"""

    def test_extracts_top_rushers(self):
        """Extract top 2 RBs per team with rushing yards, TDs, receptions"""
        html_content = Path("tests/fixtures/playoff_2024_divisional_detail.html").read_text()

        stats = extract_player_rushing_stats(html_content, top_n=2)

        # Should have top 2 rushers from each team (4 total)
        assert len(stats) >= 2
        assert len(stats) <= 4

        # Check first rusher has required fields
        rb = stats[0]
        assert "player_name" in rb
        assert "team" in rb
        assert "rushing_yards" in rb
        assert "rushing_tds" in rb
        assert "receptions" in rb

        # Values should be integers
        assert isinstance(rb["rushing_yards"], int)
        assert isinstance(rb["rushing_tds"], int)
        assert isinstance(rb["receptions"], int)


class TestExtractPlayerReceivingStats:
    """Test extracting WR/TE receiving statistics"""

    def test_extracts_top_receivers(self):
        """Extract top 3 WR/TE per team with receptions, yards, TDs"""
        html_content = Path("tests/fixtures/playoff_2024_divisional_detail.html").read_text()

        stats = extract_player_receiving_stats(html_content, top_n=3)

        # Should have top 3 receivers from each team (up to 6 total)
        assert len(stats) >= 3
        assert len(stats) <= 6

        # Check first receiver has required fields
        wr = stats[0]
        assert "player_name" in wr
        assert "team" in wr
        assert "receptions" in wr
        assert "receiving_yards" in wr
        assert "receiving_tds" in wr

        # Values should be integers
        assert isinstance(wr["receptions"], int)
        assert isinstance(wr["receiving_yards"], int)
        assert isinstance(wr["receiving_tds"], int)

        # Receiving yards should be > 0 for top receivers
        assert wr["receiving_yards"] > 0
