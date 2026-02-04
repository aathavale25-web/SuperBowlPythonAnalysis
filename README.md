# Super Bowl Betting Research App

A comprehensive Super Bowl betting research application that scrapes historical data, analyzes trends, and generates static HTML reports.

## Project Structure

```
/superbowl-research
├── data/                    # Parquet files and DuckDB database
├── scrapers/               # Web scraping modules
│   ├── superbowl_history.py
│   ├── player_stats.py
│   └── playoff_history.py
├── analysis/               # Analysis modules
│   ├── squares.py
│   ├── props.py
│   └── player_trends.py
├── static_site/           # Generated HTML reports
├── generate_site.py       # Main site generation script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Technologies

- **DuckDB** - Fast analytical database
- **Polars** - High-performance DataFrame library
- **Playwright** - Web scraping and automation
- **Jinja2** - HTML templating
- **Plotly** - Interactive visualizations

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

3. Database is initialized at `data/superbowl.db` with tables:
   - `superbowl_games` - Historical Super Bowl game data
   - `player_game_logs` - Player performance data
   - `playoff_games` - Playoff game history

## Usage

(Coming soon in future phases)

## Phase 1: Project Setup

- ✅ Project structure created
- ✅ DuckDB database initialized
- ✅ Dependencies specified
- 🔄 Scrapers to be implemented
- 🔄 Analysis modules to be implemented
- 🔄 Site generator to be implemented
