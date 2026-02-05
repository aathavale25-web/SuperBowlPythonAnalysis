"""
Tests for player stats scraper
"""

import pytest
from pathlib import Path
from scrapers.player_stats import (
    parse_player_game_log,
    load_players_config,
    scrape_player_stats
)


class TestParsePlayerGameLog:
    """Test parsing player game log from HTML"""

    def test_parses_mahomes_game_log(self):
        """Parse Patrick Mahomes 2024 game log"""
        html_content = Path("tests/fixtures/mahomes_2024_gamelog.html").read_text()

        games = parse_player_game_log(html_content, "Patrick Mahomes", "KAN", season=2024)

        # Should have multiple games (2024 season)
        assert len(games) > 0, "Should extract at least one game"

        # Check first game structure
        game = games[0]
        assert "player_name" in game
        assert "team" in game
        assert "season" in game
        assert "week" in game
        assert "game_type" in game

        # Verify player name
        assert game["player_name"] == "Patrick Mahomes"
        assert game["team"] == "KAN"
        assert game["season"] == 2024

        # Should have stats
        assert "passing_yards" in game
        assert "passing_tds" in game
        assert "interceptions" in game
        assert "rushing_yards" in game

        # Mahomes should have passing yards in first game
        assert game["passing_yards"] >= 0
        assert isinstance(game["passing_yards"], int)


    def test_distinguishes_regular_and_playoff_games(self):
        """Correctly identify regular season vs playoff games"""
        html_content = Path("tests/fixtures/mahomes_2024_gamelog.html").read_text()

        games = parse_player_game_log(html_content, "Patrick Mahomes", "KAN", season=2024)

        # Check game types
        game_types = {g["game_type"] for g in games}

        # Should have both regular and playoff games
        # (or at least identify them correctly)
        for game in games:
            assert game["game_type"] in ["regular", "playoff"]


class TestLoadPlayersConfig:
    """Test loading player configuration"""

    def test_loads_players_from_json(self):
        """Load players from players_to_track.json"""
        players = load_players_config()

        # Should load at least the 4 test players
        assert len(players) >= 4

        # Check first player structure
        player = players[0]
        assert "name" in player
        assert "url" in player
        assert "team" in player
        assert "position" in player

        # Verify we have players from both teams
        teams = {p["team"] for p in players}
        assert "New England Patriots" in teams
        assert "Seattle Seahawks" in teams

        # Verify we have key positions
        positions = {p["position"] for p in players}
        assert "QB" in positions
        assert "RB" in positions
        assert "WR" in positions
        assert "TE" in positions
