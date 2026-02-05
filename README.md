# 🏈 Super Bowl Analysis

[![Update Analysis](https://github.com/USERNAME/SuperBowlPythonAnalysis/actions/workflows/update-analysis.yml/badge.svg)](https://github.com/USERNAME/SuperBowlPythonAnalysis/actions/workflows/update-analysis.yml)
[![Deploy to Pages](https://github.com/USERNAME/SuperBowlPythonAnalysis/actions/workflows/deploy.yml/badge.svg)](https://github.com/USERNAME/SuperBowlPythonAnalysis/actions/workflows/deploy.yml)

Data-driven Super Bowl betting analysis with historical trends, player props, and playoff statistics.

## 🌐 Live Site

**[View Live Analysis](https://USERNAME.github.io/SuperBowlPythonAnalysis/)**

Updated weekly with the latest data.

## 📊 Features

### Squares Analysis
- Quarter-by-quarter probability analysis
- Recency-weighted historical data
- Interactive heatmaps
- Top 10 best and worst squares

### Player Props
- Season statistics and trends
- Betting line hit rates
- Best bets identification (>65% hit rate)
- Last 5 games trend analysis

### Playoff Props
- Historical playoff game analysis (2020-2024)
- Total points and winning margin trends
- Round-specific breakdowns
- Super Bowl vs Conference vs Divisional analysis

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/USERNAME/SuperBowlPythonAnalysis.git
   cd SuperBowlPythonAnalysis
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install polars beautifulsoup4 jinja2 duckdb playwright lxml
   playwright install chromium
   ```

4. **Generate the site**
   ```bash
   python generate_site.py
   ```

5. **Start local server**
   ```bash
   python serve_site.py
   ```

6. **View locally**

   Open http://localhost:8000 in your browser

## 🔄 Updating Analysis Data

### Automatic Updates

The analysis data updates automatically:
- **Weekly**: Every Sunday at 2am UTC via GitHub Actions
- **Manual**: Trigger the "Update Analysis Data" workflow in GitHub Actions

### Manual Local Update

Run the scrapers to fetch latest data:

```bash
# Scrape Super Bowl history
python -c "from scrapers.superbowl_history import scrape_superbowl_history; scrape_superbowl_history()"

# Scrape playoff data (2020-2024)
python -c "from scrapers.playoff_history import scrape_playoff_history; scrape_playoff_history(seasons=list(range(2020, 2025)))"

# Scrape player stats (2024 season)
python -c "from scrapers.player_stats import scrape_player_stats; scrape_player_stats(season=2024)"

# Regenerate site
python generate_site.py
```

## 📁 Project Structure

```
SuperBowlPythonAnalysis/
├── .github/workflows/       # GitHub Actions
│   ├── update-analysis.yml  # Weekly data updates
│   └── deploy.yml           # GitHub Pages deployment
├── analysis/                # Analysis modules
│   ├── squares.py           # Squares betting analysis
│   ├── player_trends.py     # Player prop analysis
│   └── props.py             # Playoff props analysis
├── scrapers/                # Web scraping modules
│   ├── superbowl_history.py # Super Bowl game scraper
│   ├── playoff_history.py   # Playoff game scraper
│   └── player_stats.py      # Player stats scraper
├── templates/               # Jinja2 templates
│   ├── base.html            # Base layout
│   ├── index.html           # Dashboard
│   ├── squares.html         # Squares analysis
│   ├── players.html         # Player props
│   ├── playoffs.html        # Playoff props
│   └── about.html           # Methodology
├── static/                  # Static assets
│   └── styles.css           # Site stylesheet
├── data/                    # Data files (Parquet)
│   ├── playoff_games.parquet
│   └── player_stats_2024.parquet
├── static_site/             # Generated site (deployed to Pages)
├── tests/                   # Test suite
├── generate_site.py         # Static site generator
├── serve_site.py            # Local development server
└── README.md                # This file
```

## 🧪 Running Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

All 34 tests should pass.

## 🛠️ Technology Stack

- **Python 3.14** - Native ARM for performance
- **Polars 1.38.0** - Fast DataFrame operations
- **DuckDB** - Analytical database
- **Playwright** - Web scraping
- **Jinja2** - HTML templating
- **Plotly** - Interactive visualizations
- **GitHub Actions** - Automated updates and deployment
- **GitHub Pages** - Static site hosting

## 📈 Data Sources

All data is scraped from official NFL sources:
- Historical Super Bowl games (complete game data)
- Playoff game results (2020-2024 seasons)
- Player game logs (2024 season)

## ⚠️ Disclaimer

This analysis is for educational and informational purposes only. Past performance does not guarantee future results. Sample sizes vary - always check game counts. Does not account for matchups, injuries, or game conditions.

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 Support

For issues or questions, please open a GitHub issue.

---

Built with ❤️ using Test-Driven Development
