"""
Tests for player prop analysis module
"""

import pytest
import polars as pl
from analysis.player_trends import (
    calculate_player_stats,
    calculate_hit_rates,
    identify_best_bets,
    analyze_last_n_games_trend
)


class TestCalculatePlayerStats:
    """Test player statistics calculation"""

    def test_calculates_averages_and_medians_for_qb(self):
        """Calculate average and median stats for QB"""
        # Sample QB game logs
        games = pl.DataFrame({
            "player_name": ["Patrick Mahomes"] * 5,
            "passing_yards": [250, 300, 275, 225, 350],
            "passing_tds": [2, 3, 2, 1, 4],
            "interceptions": [0, 1, 0, 0, 1],
            "rushing_yards": [20, 15, 30, 10, 25],
            "rushing_tds": [0, 0, 1, 0, 0]
        })

        stats = calculate_player_stats(games, "Patrick Mahomes")

        # Should return dict with averages and medians
        assert isinstance(stats, dict)
        assert "avg_passing_yards" in stats
        assert "median_passing_yards" in stats

        # Check calculated values
        assert stats["avg_passing_yards"] == 280.0  # (250+300+275+225+350)/5
        assert stats["median_passing_yards"] == 275.0
        assert stats["avg_passing_tds"] == 2.4  # (2+3+2+1+4)/5
        assert stats["median_passing_tds"] == 2.0

        # Season high/low
        assert stats["high_passing_yards"] == 350
        assert stats["low_passing_yards"] == 225


class TestCalculateHitRates:
    """Test hit rate calculation for betting lines"""

    def test_calculates_qb_passing_yards_hit_rates(self):
        """Calculate hit rates for QB passing yard lines"""
        # Sample QB game logs
        games = pl.DataFrame({
            "player_name": ["Patrick Mahomes"] * 5,
            "passing_yards": [250, 300, 275, 200, 350]
        })

        hit_rates = calculate_hit_rates(
            games,
            "Patrick Mahomes",
            stat_column="passing_yards",
            lines=[224.5, 249.5, 274.5]
        )

        # Should return dict with hit rates for each line
        assert isinstance(hit_rates, dict)

        # 224.5 line: 5/5 games over (250, 300, 275, 200 is under, 350)
        assert hit_rates[224.5]["over"] == 4  # 4 games over 224.5
        assert hit_rates[224.5]["under"] == 1  # 1 game under
        assert hit_rates[224.5]["hit_rate_over"] == 0.8  # 80%

        # 249.5 line: 4/5 games over (250, 300, 275, 350)
        assert hit_rates[249.5]["over"] == 4
        assert hit_rates[249.5]["hit_rate_over"] == 0.8

        # 274.5 line: 3/5 games over (275, 300, 350)
        assert hit_rates[274.5]["over"] == 3
        assert hit_rates[274.5]["hit_rate_over"] == 0.6


class TestIdentifyBestBets:
    """Test best bet identification"""

    def test_identifies_bets_above_65_percent(self):
        """Identify lines with >65% hit rate"""
        hit_rates = {
            224.5: {"hit_rate_over": 0.8, "over": 8, "under": 2},
            249.5: {"hit_rate_over": 0.7, "over": 7, "under": 3},
            274.5: {"hit_rate_over": 0.5, "over": 5, "under": 5},
            299.5: {"hit_rate_over": 0.3, "over": 3, "under": 7}
        }

        best_bets = identify_best_bets(hit_rates, threshold=0.65)

        # Should return only lines above 65%
        assert len(best_bets) == 2
        assert 224.5 in best_bets
        assert 249.5 in best_bets
        assert 274.5 not in best_bets


class TestAnalyzeLastNGamesTrend:
    """Test trend analysis for recent games"""

    def test_detects_improving_trend(self):
        """Detect improving performance in last 5 games"""
        games = pl.DataFrame({
            "player_name": ["Patrick Mahomes"] * 10,
            "passing_yards": [200, 220, 210, 230, 250, 270, 280, 300, 320, 340],
            "week": list(range(1, 11))
        })

        trend = analyze_last_n_games_trend(
            games,
            "Patrick Mahomes",
            stat_column="passing_yards",
            n=5
        )

        # Last 5 games: 270, 280, 300, 320, 340
        # Average of last 5: 302 vs previous 5: 222
        assert trend["direction"] == "improving"
        assert trend["last_n_avg"] > trend["previous_n_avg"]


    def test_detects_declining_trend(self):
        """Detect declining performance in last 5 games"""
        games = pl.DataFrame({
            "player_name": ["Patrick Mahomes"] * 10,
            "passing_yards": [340, 320, 300, 280, 270, 250, 230, 210, 220, 200],
            "week": list(range(1, 11))
        })

        trend = analyze_last_n_games_trend(
            games,
            "Patrick Mahomes",
            stat_column="passing_yards",
            n=5
        )

        # Last 5 games: 250, 230, 210, 220, 200
        # Average of last 5: 222 vs previous 5: 302
        assert trend["direction"] == "declining"
        assert trend["last_n_avg"] < trend["previous_n_avg"]


class TestGeneratePlayerSummaryWithSBHistory:
    """Test player summary generation with Super Bowl history"""

    def test_generate_player_summary_with_sb_history(self):
        """Verify SB benchmarks are calculated when sb_history provided"""
        from analysis.player_trends import generate_player_summary

        # Sample regular season games
        games = pl.DataFrame({
            "player_name": ["Patrick Mahomes"] * 10,
            "passing_yards": [280, 300, 250, 320, 290, 310, 275, 295, 305, 285],
            "passing_tds": [2, 3, 2, 3, 2, 3, 2, 2, 3, 2],
            "interceptions": [0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
            "rushing_yards": [20, 15, 25, 10, 30, 20, 15, 25, 20, 15],
            "rushing_tds": [0, 0, 1, 0, 0, 1, 0, 0, 0, 1]
        })

        # Sample Super Bowl history
        sb_history = pl.DataFrame({
            "player_name": ["Patrick Mahomes", "Patrick Mahomes", "Other QB"],
            "position": ["QB", "QB", "QB"],
            "passing_yards": [270, 290, 250],
            "passing_tds": [2, 3, 2],
            "interceptions": [1, 0, 1],
            "rushing_yards": [15, 20, 10],
            "rushing_tds": [0, 1, 0]
        })

        # Generate summary with SB history
        summary = generate_player_summary(
            games,
            "Patrick Mahomes",
            "QB",
            sb_player_history=sb_history
        )

        # Verify sb_benchmarks exist
        assert "sb_benchmarks" in summary
        assert summary["sb_benchmarks"] is not None

        # Verify SB benchmarks have expected stats
        sb_benchmarks = summary["sb_benchmarks"]
        assert "avg_passing_yards" in sb_benchmarks
        assert "avg_passing_tds" in sb_benchmarks
        assert sb_benchmarks["avg_passing_yards"] == 280.0  # (270 + 290) / 2

        # Verify hit rates include combined metrics
        assert "hit_rates" in summary
        for stat_column, hit_rates in summary["hit_rates"].items():
            for line, metrics in hit_rates.items():
                assert "hit_rate_over" in metrics
                assert "over" in metrics
                assert "under" in metrics

        # Verify best bets include sb_validated flag
        if summary.get("best_bets"):
            for bet in summary["best_bets"]:
                assert "sb_validated" in bet
                assert isinstance(bet["sb_validated"], bool)
