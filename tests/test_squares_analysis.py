"""
Tests for squares analysis module
"""

import pytest
from analysis.squares import (
    calculate_digit_frequency,
    apply_recency_weighting,
    calculate_probability_matrix,
    rank_squares
)


class TestCalculateDigitFrequency:
    """Test digit frequency calculation"""

    def test_calculates_last_digit_frequency(self):
        """Calculate frequency of last digits in scores"""
        # Sample game data
        games = [
            {"winner_final": 27, "loser_final": 20},  # 7-0
            {"winner_final": 31, "loser_final": 17},  # 1-7
            {"winner_final": 24, "loser_final": 21},  # 4-1
        ]

        freq = calculate_digit_frequency(games, "final")

        # Should return a dict with digit frequencies
        assert isinstance(freq, dict)
        assert "winner" in freq
        assert "loser" in freq

        # Check specific frequencies
        # Winner digits: 7, 1, 4
        assert freq["winner"][7] == 1
        assert freq["winner"][1] == 1
        assert freq["winner"][4] == 1

        # Loser digits: 0, 7, 1
        assert freq["loser"][0] == 1
        assert freq["loser"][7] == 1
        assert freq["loser"][1] == 1


class TestApplyRecencyWeighting:
    """Test recency weighting application"""

    def test_applies_recency_weights(self):
        """Apply higher weights to recent games"""
        # Sample games with years
        games = [
            {"year": 2024, "winner_final": 27},  # 0 years ago: 3x
            {"year": 2015, "winner_final": 31},  # 9 years ago: 2x
            {"year": 2005, "winner_final": 24},  # 19 years ago: 1x
        ]

        weighted_games = apply_recency_weighting(games, current_year=2024)

        # Should have more entries for recent games
        assert len(weighted_games) > len(games)

        # Count occurrences by year
        year_2024_count = sum(1 for g in weighted_games if g["year"] == 2024)
        year_2015_count = sum(1 for g in weighted_games if g["year"] == 2015)
        year_2005_count = sum(1 for g in weighted_games if g["year"] == 2005)

        # Verify weighting: 2024 (3x), 2015 (2x), 2005 (1x)
        assert year_2024_count == 3
        assert year_2015_count == 2
        assert year_2005_count == 1


class TestCalculateProbabilityMatrix:
    """Test probability matrix calculation"""

    def test_creates_10x10_probability_matrix(self):
        """Create 10x10 probability matrix from frequencies"""
        # Sample frequency data
        frequencies = {
            "winner": {0: 5, 1: 3, 7: 10},  # etc.
            "loser": {0: 8, 3: 6, 7: 4}
        }

        matrix = calculate_probability_matrix(frequencies)

        # Should be 10x10 matrix
        assert len(matrix) == 10
        assert all(len(row) == 10 for row in matrix)

        # All probabilities should sum to ~1.0 (allowing for rounding)
        total_prob = sum(sum(row) for row in matrix)
        assert 0.99 <= total_prob <= 1.01

        # All individual probabilities should be between 0 and 1
        for row in matrix:
            for prob in row:
                assert 0 <= prob <= 1


class TestRankSquares:
    """Test square ranking"""

    def test_ranks_squares_by_probability(self):
        """Rank all 100 squares by probability"""
        # Sample probability matrix
        matrix = [[0.01 for _ in range(10)] for _ in range(10)]
        # Make some squares better
        matrix[0][0] = 0.05  # 0-0 is best
        matrix[7][0] = 0.04  # 7-0 is second best
        matrix[9][9] = 0.001  # 9-9 is worst

        ranked = rank_squares(matrix)

        # Should return list of 100 tuples: (winner_digit, loser_digit, probability)
        assert len(ranked) == 100

        # Check it's sorted by probability (descending)
        assert ranked[0][2] >= ranked[1][2]
        assert ranked[1][2] >= ranked[2][2]

        # Check best and worst
        assert ranked[0] == (0, 0, 0.05)
        assert ranked[1] == (7, 0, 0.04)
        assert ranked[-1] == (9, 9, 0.001)
