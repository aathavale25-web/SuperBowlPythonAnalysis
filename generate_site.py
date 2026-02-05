"""
Generate static HTML site from analysis results
"""

import duckdb
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
import shutil

# Helper to convert pandas to polars-like API
class PandasPolarsAdapter:
    """Adapter to make pandas DataFrames work with Polars-like API"""
    def __init__(self, df):
        self.df = df

    def filter(self, condition):
        # Handle boolean mask
        return PandasPolarsAdapter(self.df[condition])

    def __len__(self):
        return len(self.df)

    def __getitem__(self, key):
        return self.df[key]

    @property
    def columns(self):
        return self.df.columns.tolist()

def col(column_name):
    """Polars-like col() function for pandas"""
    def compare(df_or_adapter):
        if isinstance(df_or_adapter, PandasPolarsAdapter):
            return df_or_adapter.df[column_name]
        return df_or_adapter[column_name]
    return compare

# Import analysis modules
from analysis.squares import (
    load_superbowl_games,
    apply_recency_weighting,
    calculate_digit_frequency,
    calculate_probability_matrix,
    rank_squares
)
from analysis.player_trends import (
    load_player_data,
    generate_player_summary,
    get_betting_lines_for_position
)
from analysis.props import (
    load_playoff_data,
    calculate_game_prop_hit_rates,
    breakdown_by_round,
    identify_best_playoff_props
)


def extract_plotly_chart(html_content):
    """
    Extract plotly div and script from standalone HTML

    Args:
        html_content: HTML string from Plotly standalone file

    Returns:
        dict with 'div' and 'script' keys
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the plotly div
    plotly_div = soup.find('div', {'class': 'plotly-graph-div'})

    # Find the script with Plotly.newPlot
    scripts = soup.find_all('script')
    chart_script = None
    for script in scripts:
        if script.string and 'Plotly.newPlot' in script.string:
            chart_script = script
            break

    return {
        'div': str(plotly_div) if plotly_div else '',
        'script': str(chart_script) if chart_script else ''
    }


def collect_squares_data():
    """
    Collect squares analysis data

    Returns:
        dict with matrices, ranked squares, and heatmaps
    """
    # Load games
    games = load_superbowl_games()
    if not games:
        return {'matrices': {}, 'ranked': {}}

    # Apply recency weighting
    weighted_games = apply_recency_weighting(games)

    # Analyze each quarter
    quarters = ["q1", "q2", "q3", "q4", "final"]
    matrices = {}
    ranked = {}

    for quarter in quarters:
        # Calculate frequencies and matrix
        freq = calculate_digit_frequency(weighted_games, quarter)
        matrix = calculate_probability_matrix(freq)
        matrices[quarter] = matrix

        # Rank squares
        ranked_squares = rank_squares(matrix)
        # Convert to dict format
        ranked[quarter] = [
            {
                'winner': w,
                'loser': l,
                'probability': prob
            }
            for w, l, prob in ranked_squares
        ]

    return {
        'matrices': matrices,
        'ranked': ranked
    }


def collect_players_data():
    """
    Collect player props analysis data

    Returns:
        dict with player summaries
    """
    import json

    # Load player data (2025 season)
    games = load_player_data()
    if games is None:
        return {'summaries': []}

    # Load Super Bowl player history if available
    sb_history_path = Path("data/superbowl_player_history.parquet")
    sb_player_history = None
    if sb_history_path.exists():
        try:
            sb_player_history = pl.read_parquet(sb_history_path)
        except Exception as e:
            print(f"Warning: Could not load SB player history: {e}")

    # Load player config
    config_path = Path("players_to_track.json")
    if not config_path.exists():
        return {'summaries': []}

    with open(config_path) as f:
        config = json.load(f)

    # Generate summary for each player
    summaries = []
    for player_config in config["players"]:
        player_name = player_config["name"]
        position = player_config["position"]

        player_games = games.filter(pl.col("player_name") == player_name)

        if len(player_games) == 0:
            continue

        summary = generate_player_summary(
            player_games,
            player_name,
            position,
            sb_player_history=sb_player_history
        )
        summaries.append(summary)

    return {'summaries': summaries}


def collect_playoffs_data():
    """
    Collect playoff props analysis data

    Returns:
        dict with game props, round breakdown, best props
    """
    # Load playoff data
    games = load_playoff_data()
    if games is None:
        return {
            'game_props': {},
            'round_breakdown': {},
            'best_props': {}
        }

    # Calculate game props
    total_points_hr = calculate_game_prop_hit_rates(
        games,
        prop_type="total_points",
        lines=[43.5, 47.5, 51.5]
    )

    margin_hr = calculate_game_prop_hit_rates(
        games,
        prop_type="winning_margin",
        buckets=["1-6", "7-12", "13-18", "19+"]
    )

    def_td_hr = calculate_game_prop_hit_rates(
        games,
        prop_type="defensive_td"
    )

    game_props = {
        'total_points': total_points_hr,
        'winning_margin': margin_hr,
        'defensive_td': def_td_hr
    }

    # Round breakdown
    round_breakdown = breakdown_by_round(games, "total_points", 47.5)

    # Identify best props
    all_props = {}
    for line in [43.5, 47.5, 51.5]:
        all_props[f"Total Points O{line}"] = total_points_hr[line]
    for bucket in ["1-6", "7-12", "13-18", "19+"]:
        all_props[f"Margin {bucket}"] = margin_hr[bucket]

    best_props = identify_best_playoff_props(all_props, threshold=0.60)

    return {
        'game_props': game_props,
        'round_breakdown': round_breakdown,
        'best_props': best_props
    }


def generate_pages(data, output_dir):
    """
    Generate all HTML pages from templates

    Args:
        data: Dict with all analysis data
        output_dir: Path to output directory
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Create assets directory
    assets_dir = output_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)

    # Copy CSS if it exists
    static_css = Path('static/styles.css')
    if static_css.exists():
        shutil.copy(static_css, assets_dir / 'styles.css')

    # Setup Jinja2
    template_dir = Path('templates')
    if not template_dir.exists():
        # Create minimal templates if they don't exist
        template_dir.mkdir(exist_ok=True)
        return

    env = Environment(loader=FileSystemLoader('templates'))

    # Generate each page
    pages = ['index', 'squares', 'players', 'playoffs', 'about']

    for page_name in pages:
        template_file = f'{page_name}.html'

        # Skip if template doesn't exist
        if not (template_dir / template_file).exists():
            continue

        template = env.get_template(template_file)
        output = template.render(data=data)

        # Write to output
        with open(output_dir / template_file, 'w') as f:
            f.write(output)


def generate_site():
    """
    Generate static HTML reports using Jinja2 templates and Plotly visualizations
    """
    print("🏈 Generating static site...\n")

    # Collect all data
    print("📊 Collecting analysis data...")
    data = {
        'squares': collect_squares_data(),
        'players': collect_players_data(),
        'playoffs': collect_playoffs_data(),
        'timestamp': datetime.now().isoformat()
    }

    # Generate pages
    print("📝 Generating HTML pages...")
    output_dir = Path("static_site")
    generate_pages(data, output_dir)

    print(f"\n✅ Site generated at {output_dir}/")
    print("   Run 'python serve_site.py' to view")


if __name__ == "__main__":
    generate_site()
