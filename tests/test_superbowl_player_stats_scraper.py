"""
Tests for Super Bowl player stats scraper
"""

import pytest
import polars as pl
from scrapers.superbowl_player_stats import (
    parse_superbowl_boxscore,
    scrape_superbowl_player_stats
)


class TestParseSuperbowlBoxscore:
    """Test parsing Super Bowl boxscore HTML"""

    def test_parses_qb_stats_from_boxscore(self):
        """Parse QB passing stats from Super Bowl boxscore"""
        # Sample HTML structure (simplified)
        html = """
        <table id="player_offense">
            <tbody>
                <tr>
                    <td data-stat="player">Tom Brady</td>
                    <td data-stat="pass_cmp">21</td>
                    <td data-stat="pass_att">29</td>
                    <td data-stat="pass_yds">201</td>
                    <td data-stat="pass_td">2</td>
                    <td data-stat="pass_int">0</td>
                </tr>
            </tbody>
        </table>
        """

        players = parse_superbowl_boxscore(html, "XLIX", 2015, "New England Patriots")

        assert len(players) > 0
        qb = players[0]
        assert qb["player_name"] == "Tom Brady"
        assert qb["super_bowl"] == "XLIX"
        assert qb["year"] == 2015
        assert qb["passing_yards"] == 201
        assert qb["passing_tds"] == 2
        assert qb["interceptions"] == 0
        assert qb["position"] == "QB"


    def test_parses_rb_stats_from_boxscore(self):
        """Parse RB rushing stats from Super Bowl boxscore"""
        html = """
        <table id="player_offense">
            <tbody>
                <tr>
                    <td data-stat="player">James White</td>
                    <td data-stat="rush_att">6</td>
                    <td data-stat="rush_yds">29</td>
                    <td data-stat="rush_td">2</td>
                    <td data-stat="targets">12</td>
                    <td data-stat="rec">14</td>
                    <td data-stat="rec_yds">110</td>
                    <td data-stat="rec_td">1</td>
                </tr>
            </tbody>
        </table>
        """

        players = parse_superbowl_boxscore(html, "LI", 2017, "New England Patriots")

        assert len(players) > 0
        rb = players[0]
        assert rb["rushing_yards"] == 29
        assert rb["rushing_tds"] == 2
        assert rb["receptions"] == 14
        assert rb["receiving_yards"] == 110
        assert rb["receiving_tds"] == 1


    def test_parses_wr_stats_from_boxscore(self):
        """Parse WR receiving stats from Super Bowl boxscore"""
        html = """
        <table id="player_offense">
            <tbody>
                <tr>
                    <td data-stat="player">Julian Edelman</td>
                    <td data-stat="targets">10</td>
                    <td data-stat="rec">10</td>
                    <td data-stat="rec_yds">141</td>
                    <td data-stat="rec_td">0</td>
                </tr>
            </tbody>
        </table>
        """

        players = parse_superbowl_boxscore(html, "XLIX", 2015, "New England Patriots")

        wr = players[0]
        assert wr["receptions"] == 10
        assert wr["receiving_yards"] == 141
        assert wr["position"] == "WR"
