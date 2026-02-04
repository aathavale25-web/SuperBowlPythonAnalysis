"""
Tests for playoff props analysis module
"""

import pytest
import polars as pl
from analysis.props import (
    calculate_game_prop_hit_rates,
    calculate_player_prop_hit_rates,
    breakdown_by_round,
    identify_best_playoff_props
)


class TestCalculateGamePropHitRates:
    """Test game prop hit rate calculation"""

    def test_calculates_total_points_hit_rates(self):
        """Calculate hit rates for total points lines"""
        # Sample playoff games
        games = pl.DataFrame({
            "season": [2023, 2023, 2022, 2022, 2021],
            "round": ["Super Bowl", "Divisional", "Super Bowl", "Wild Card", "Super Bowl"],
            "total_points": [57, 41, 43, 38, 60]
        })

        hit_rates = calculate_game_prop_hit_rates(
            games,
            prop_type="total_points",
            lines=[43.5, 47.5, 51.5]
        )

        # Should return dict with hit rates for each line
        assert isinstance(hit_rates, dict)

        # 43.5 line: games with 57, 60 go over (2/5), 41, 43, 38 under
        assert hit_rates[43.5]["over"] == 2
        assert hit_rates[43.5]["under"] == 3
        assert hit_rates[43.5]["hit_rate_over"] == 0.4

        # 47.5 line: games with 57, 60 go over (2/5)
        assert hit_rates[47.5]["over"] == 2
        assert hit_rates[47.5]["hit_rate_over"] == 0.4

        # 51.5 line: games with 57, 60 go over (2/5)
        assert hit_rates[51.5]["over"] == 2
        assert hit_rates[51.5]["hit_rate_over"] == 0.4


    def test_calculates_winning_margin_buckets(self):
        """Calculate hit rates for winning margin buckets"""
        # Sample playoff games with margins
        games = pl.DataFrame({
            "season": [2023, 2023, 2022, 2022, 2021, 2021],
            "winner_score": [31, 28, 23, 27, 31, 34],
            "loser_score": [28, 24, 20, 20, 9, 28]
        })

        hit_rates = calculate_game_prop_hit_rates(
            games,
            prop_type="winning_margin",
            buckets=["1-6", "7-12", "13-18", "19+"]
        )

        # Margins: 3, 4, 3, 7, 22, 6
        # 1-6: 3, 4, 3, 6 = 4 games
        # 7-12: 7 = 1 game
        # 13-18: 0 games
        # 19+: 22 = 1 game

        assert hit_rates["1-6"]["count"] == 4
        assert hit_rates["1-6"]["percentage"] == pytest.approx(0.667, rel=0.01)

        assert hit_rates["7-12"]["count"] == 1
        assert hit_rates["7-12"]["percentage"] == pytest.approx(0.167, rel=0.01)

        assert hit_rates["19+"]["count"] == 1


    def test_detects_defensive_special_teams_tds(self):
        """Detect if defensive/special teams TD occurred"""
        # Sample games with defensive TD flag
        games = pl.DataFrame({
            "season": [2023, 2023, 2022, 2022, 2021],
            "defensive_td": [True, False, True, False, False]
        })

        hit_rates = calculate_game_prop_hit_rates(
            games,
            prop_type="defensive_td",
            lines=None
        )

        # 2 out of 5 games had defensive TD
        assert hit_rates["occurred"]["count"] == 2
        assert hit_rates["occurred"]["percentage"] == 0.4
        assert hit_rates["no_occurrence"]["count"] == 3
        assert hit_rates["no_occurrence"]["percentage"] == 0.6


class TestCalculatePlayerPropHitRates:
    """Test player prop hit rate calculation"""

    def test_calculates_qb_passing_yards_hit_rate(self):
        """Calculate hit rate for QB passing yards in playoff games"""
        # Sample QB playoff performances
        player_stats = pl.DataFrame({
            "season": [2023, 2023, 2022, 2022, 2021],
            "round": ["Super Bowl", "Conference", "Divisional", "Wild Card", "Super Bowl"],
            "player_name": ["Patrick Mahomes"] * 5,
            "position": ["QB"] * 5,
            "passing_yards": [275, 240, 195, 310, 260]
        })

        hit_rates = calculate_player_prop_hit_rates(
            player_stats,
            prop_type="qb_passing_yards",
            line=249.5
        )

        # Games over 249.5: 275, 310, 260 = 3/5
        assert hit_rates["over"] == 3
        assert hit_rates["under"] == 2
        assert hit_rates["hit_rate_over"] == 0.6


    def test_calculates_lead_rb_rushing_yards(self):
        """Calculate hit rate for lead RB rushing yards"""
        # Sample lead RB performances
        player_stats = pl.DataFrame({
            "season": [2023, 2023, 2022, 2022, 2021],
            "player_name": ["RB1", "RB2", "RB3", "RB4", "RB5"],
            "position": ["RB"] * 5,
            "rushing_yards": [85, 60, 120, 55, 90],
            "is_lead_rusher": [True] * 5  # These are the lead rushers per game
        })

        hit_rates = calculate_player_prop_hit_rates(
            player_stats,
            prop_type="rb_rushing_yards",
            line=74.5
        )

        # Games over 74.5: 85, 120, 90 = 3/5
        assert hit_rates["over"] == 3
        assert hit_rates["hit_rate_over"] == 0.6


class TestBreakdownByRound:
    """Test breakdown of props by playoff round"""

    def test_breaks_down_props_by_round(self):
        """Break down prop hit rates by playoff round"""
        # Sample games across different rounds
        games = pl.DataFrame({
            "season": [2023, 2023, 2022, 2022, 2021, 2021],
            "round": ["Super Bowl", "Super Bowl", "Divisional", "Divisional", "Wild Card", "Wild Card"],
            "total_points": [57, 60, 41, 38, 45, 35]
        })

        breakdown = breakdown_by_round(
            games,
            prop_type="total_points",
            line=43.5
        )

        # Should return dict with round breakdown
        assert isinstance(breakdown, dict)
        assert "Super Bowl" in breakdown
        assert "Divisional" in breakdown
        assert "Wild Card" in breakdown

        # Super Bowl: 57, 60 both over 43.5 (2/2 = 100%)
        assert breakdown["Super Bowl"]["over"] == 2
        assert breakdown["Super Bowl"]["hit_rate_over"] == 1.0

        # Divisional: 41, 38 both under 43.5 (0/2 = 0%)
        assert breakdown["Divisional"]["over"] == 0
        assert breakdown["Divisional"]["hit_rate_over"] == 0.0

        # Wild Card: 45 over, 35 under (1/2 = 50%)
        assert breakdown["Wild Card"]["over"] == 1
        assert breakdown["Wild Card"]["hit_rate_over"] == 0.5


class TestIdentifyBestPlayoffProps:
    """Test identification of best playoff props"""

    def test_identifies_props_above_60_percent(self):
        """Identify props with >60% hit rate"""
        all_props = {
            "Total Points O43.5": {"hit_rate_over": 0.75, "over": 15, "under": 5},
            "Total Points O47.5": {"hit_rate_over": 0.55, "over": 11, "under": 9},
            "QB Pass Yds O249.5": {"hit_rate_over": 0.62, "over": 31, "under": 19},
            "Margin 1-6": {"percentage": 0.45, "count": 9}
        }

        best_props = identify_best_playoff_props(all_props, threshold=0.60)

        # Should return props above 60%
        assert len(best_props) == 2
        assert "Total Points O43.5" in best_props
        assert "QB Pass Yds O249.5" in best_props
        assert "Total Points O47.5" not in best_props
