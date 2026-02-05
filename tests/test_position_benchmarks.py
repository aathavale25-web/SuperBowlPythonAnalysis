"""
Tests for position benchmarking functions
"""

import pytest
import polars as pl
from analysis.player_trends import (
    calculate_position_benchmarks,
    calculate_combined_hit_rate
)


class TestCalculatePositionBenchmarks:
    """Test position benchmark calculation"""

    def test_calculates_qb_benchmarks_from_sb_history(self):
        """Calculate QB benchmarks from Super Bowl history"""
        # Create sample Super Bowl history data
        sb_history = pl.DataFrame({
            "super_bowl": ["LVIII", "LVIII", "LVII", "LVII"],
            "year": [2024, 2024, 2023, 2023],
            "player_name": ["Patrick Mahomes", "Brock Purdy", "Patrick Mahomes", "Jalen Hurts"],
            "position": ["QB", "QB", "QB", "QB"],
            "team": ["Kansas City Chiefs", "San Francisco 49ers", "Kansas City Chiefs", "Philadelphia Eagles"],
            "passing_yards": [333, 255, 182, 304],
            "passing_tds": [2, 1, 3, 1],
            "interceptions": [1, 0, 0, 1],
            "rushing_yards": [66, 3, 77, 70],
            "rushing_tds": [0, 0, 0, 0],
            "receptions": [0, 0, 0, 0],
            "receiving_yards": [0, 0, 0, 0],
            "receiving_tds": [0, 0, 0, 0]
        })

        benchmarks = calculate_position_benchmarks(sb_history, "QB")

        # Check structure
        assert "avg_passing_yards" in benchmarks
        assert "avg_passing_tds" in benchmarks
        assert "avg_interceptions" in benchmarks
        assert "avg_rushing_yards" in benchmarks

        # Check values (averages should be calculated)
        assert benchmarks["avg_passing_yards"] > 0
        assert benchmarks["avg_passing_tds"] > 0
        assert benchmarks["avg_rushing_yards"] > 0

        # Verify average calculation
        expected_avg_pass_yards = (333 + 255 + 182 + 304) / 4
        assert abs(benchmarks["avg_passing_yards"] - expected_avg_pass_yards) < 0.1


    def test_calculates_rb_benchmarks_from_sb_history(self):
        """Calculate RB benchmarks from Super Bowl history"""
        sb_history = pl.DataFrame({
            "super_bowl": ["LVIII", "LVIII"],
            "year": [2024, 2024],
            "player_name": ["Isiah Pacheco", "Christian McCaffrey"],
            "position": ["RB", "RB"],
            "team": ["Kansas City Chiefs", "San Francisco 49ers"],
            "passing_yards": [0, 0],
            "passing_tds": [0, 0],
            "interceptions": [0, 0],
            "rushing_yards": [59, 80],
            "rushing_tds": [1, 0],
            "receptions": [2, 8],
            "receiving_yards": [33, 80],
            "receiving_tds": [0, 1]
        })

        benchmarks = calculate_position_benchmarks(sb_history, "RB")

        # Check RB-specific stats
        assert "avg_rushing_yards" in benchmarks
        assert "avg_rushing_tds" in benchmarks
        assert "avg_receptions" in benchmarks
        assert "avg_receiving_yards" in benchmarks

        # Verify values
        assert benchmarks["avg_rushing_yards"] == (59 + 80) / 2
        assert benchmarks["avg_receptions"] == (2 + 8) / 2


    def test_calculates_wr_benchmarks_from_sb_history(self):
        """Calculate WR benchmarks from Super Bowl history"""
        sb_history = pl.DataFrame({
            "super_bowl": ["LVIII", "LVIII", "LVIII"],
            "year": [2024, 2024, 2024],
            "player_name": ["Brandon Aiyuk", "Jauan Jennings", "Deebo Samuel"],
            "position": ["WR", "WR", "WR"],
            "team": ["San Francisco 49ers", "San Francisco 49ers", "San Francisco 49ers"],
            "passing_yards": [0, 0, 0],
            "passing_tds": [0, 0, 0],
            "interceptions": [0, 0, 0],
            "rushing_yards": [0, 0, 2],
            "rushing_tds": [0, 0, 0],
            "receptions": [3, 4, 3],
            "receiving_yards": [49, 42, 33],
            "receiving_tds": [0, 1, 0]
        })

        benchmarks = calculate_position_benchmarks(sb_history, "WR")

        # Check WR-specific stats
        assert "avg_receptions" in benchmarks
        assert "avg_receiving_yards" in benchmarks
        assert "avg_receiving_tds" in benchmarks

        # Verify values
        assert benchmarks["avg_receptions"] == (3 + 4 + 3) / 3
        assert benchmarks["avg_receiving_yards"] == (49 + 42 + 33) / 3


    def test_returns_none_when_no_position_data(self):
        """Return None when no data for position"""
        sb_history = pl.DataFrame({
            "super_bowl": ["LVIII"],
            "year": [2024],
            "player_name": ["Patrick Mahomes"],
            "position": ["QB"],
            "team": ["Kansas City Chiefs"],
            "passing_yards": [333],
            "passing_tds": [2],
            "interceptions": [1],
            "rushing_yards": [66],
            "rushing_tds": [0],
            "receptions": [0],
            "receiving_yards": [0],
            "receiving_tds": [0]
        })

        benchmarks = calculate_position_benchmarks(sb_history, "TE")

        assert benchmarks is None


class TestCalculateCombinedHitRate:
    """Test combined hit rate calculation"""

    def test_calculates_weighted_hit_rate_70_30(self):
        """Calculate combined hit rate with 70/30 weighting"""
        season_hit_rate = 0.8  # 80% hit rate from season
        sb_position_hit_rate = 0.6  # 60% hit rate from SB position average

        combined = calculate_combined_hit_rate(season_hit_rate, sb_position_hit_rate, season_weight=0.7)

        # Expected: 0.8 * 0.7 + 0.6 * 0.3 = 0.56 + 0.18 = 0.74
        expected = 0.74
        assert abs(combined - expected) < 0.01


    def test_calculates_with_custom_weighting(self):
        """Calculate combined hit rate with custom weighting"""
        season_hit_rate = 0.75
        sb_position_hit_rate = 0.5

        combined = calculate_combined_hit_rate(season_hit_rate, sb_position_hit_rate, season_weight=0.6)

        # Expected: 0.75 * 0.6 + 0.5 * 0.4 = 0.45 + 0.2 = 0.65
        expected = 0.65
        assert abs(combined - expected) < 0.01


    def test_handles_extreme_values(self):
        """Handle extreme hit rate values (0.0 and 1.0)"""
        # All season hits, no SB hits
        combined1 = calculate_combined_hit_rate(1.0, 0.0, season_weight=0.7)
        assert abs(combined1 - 0.7) < 0.01

        # No season hits, all SB hits
        combined2 = calculate_combined_hit_rate(0.0, 1.0, season_weight=0.7)
        assert abs(combined2 - 0.3) < 0.01


    def test_validates_weights_sum_to_one(self):
        """Ensure weights properly combine to 1.0"""
        season_hit_rate = 0.8
        sb_position_hit_rate = 0.6
        season_weight = 0.7

        combined = calculate_combined_hit_rate(season_hit_rate, sb_position_hit_rate, season_weight)

        # Manual calculation
        sb_weight = 1.0 - season_weight
        expected = (season_hit_rate * season_weight) + (sb_position_hit_rate * sb_weight)

        assert abs(combined - expected) < 0.01
