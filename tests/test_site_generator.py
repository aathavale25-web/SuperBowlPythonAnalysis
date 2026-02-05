"""
Tests for static site generator
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from generate_site import (
    extract_plotly_chart,
    collect_squares_data,
    collect_players_data,
    collect_playoffs_data,
    generate_pages
)


class TestExtractPlotlyChart:
    """Test Plotly chart extraction from HTML"""

    def test_extracts_div_and_script_from_plotly_html(self):
        """Extract plotly div and script from standalone HTML"""
        # Create sample Plotly HTML
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><script src="https://cdn.plot.ly/plotly-2.18.0.min.js"></script></head>
        <body>
            <div id="abc123" class="plotly-graph-div" style="height:100%; width:100%;"></div>
            <script type="text/javascript">
                window.PLOTLYENV=window.PLOTLYENV || {};
                Plotly.newPlot('abc123', [{"x": [1,2,3], "y": [4,5,6]}]);
            </script>
        </body>
        </html>
        """

        result = extract_plotly_chart(html_content)

        # Should extract div
        assert 'div' in result
        assert 'plotly-graph-div' in result['div']

        # Should extract script
        assert 'script' in result
        assert 'Plotly.newPlot' in result['script']


class TestCollectSquaresData:
    """Test squares analysis data collection"""

    def test_collects_matrices_and_rankings(self):
        """Collect probability matrices and rankings from squares analysis"""
        data = collect_squares_data()

        # Should have matrices for each quarter
        assert 'matrices' in data
        assert 'q1' in data['matrices']
        assert 'q4' in data['matrices']
        assert 'final' in data['matrices']

        # Each matrix should be 10x10
        assert len(data['matrices']['final']) == 10
        assert len(data['matrices']['final'][0]) == 10

        # Should have ranked squares
        assert 'ranked' in data
        assert 'final' in data['ranked']
        assert len(data['ranked']['final']) == 100  # All 100 combinations

        # Each ranked square should have winner, loser, probability
        top_square = data['ranked']['final'][0]
        assert 'winner' in top_square
        assert 'loser' in top_square
        assert 'probability' in top_square


class TestCollectPlayersData:
    """Test player props data collection"""

    def test_collects_player_summaries(self):
        """Collect player analysis summaries"""
        data = collect_players_data()

        # Should have list of player summaries
        assert 'summaries' in data
        assert isinstance(data['summaries'], list)

        # If players exist, check structure
        if len(data['summaries']) > 0:
            player = data['summaries'][0]
            assert 'player_name' in player
            assert 'position' in player
            assert 'stats' in player
            assert 'hit_rates' in player
            assert 'best_bets' in player
            assert 'trends' in player


class TestCollectPlayoffsData:
    """Test playoff props data collection"""

    def test_collects_game_props_and_round_breakdown(self):
        """Collect playoff game props and round breakdown"""
        data = collect_playoffs_data()

        # Should have game props
        assert 'game_props' in data
        assert 'total_points' in data['game_props']
        assert 'winning_margin' in data['game_props']

        # Should have round breakdown
        assert 'round_breakdown' in data

        # Should have best props
        assert 'best_props' in data


class TestGeneratePages:
    """Test HTML page generation"""

    def test_generates_all_pages_from_templates(self):
        """Generate all HTML pages from templates"""
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Collect all data
            data = {
                'squares': collect_squares_data(),
                'players': collect_players_data(),
                'playoffs': collect_playoffs_data(),
                'timestamp': '2024-01-15T10:30:00'
            }

            # Generate pages
            generate_pages(data, output_dir)

            # Should create all HTML files
            assert (output_dir / 'index.html').exists()
            assert (output_dir / 'squares.html').exists()
            assert (output_dir / 'players.html').exists()
            assert (output_dir / 'playoffs.html').exists()
            assert (output_dir / 'about.html').exists()

            # Should copy CSS
            assert (output_dir / 'assets' / 'styles.css').exists()


    def test_includes_timestamp_in_pages(self):
        """Include timestamp in generated pages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            data = {
                'squares': collect_squares_data(),
                'players': collect_players_data(),
                'playoffs': collect_playoffs_data(),
                'timestamp': '2024-01-15T10:30:00'
            }

            generate_pages(data, output_dir)

            # Check timestamp appears in index
            index_content = (output_dir / 'index.html').read_text()
            assert '2024-01-15' in index_content


    def test_handles_missing_data_gracefully(self):
        """Handle missing data without crashing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Empty data
            data = {
                'squares': {'matrices': {}, 'ranked': {}},
                'players': {'summaries': []},
                'playoffs': {'game_props': {}, 'round_breakdown': {}, 'best_props': {}},
                'timestamp': '2024-01-15T10:30:00'
            }

            # Should not crash
            generate_pages(data, output_dir)

            # Should still create files
            assert (output_dir / 'index.html').exists()
