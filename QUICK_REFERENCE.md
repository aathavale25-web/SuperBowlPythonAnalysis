# Quick Reference Card

## 🚀 Deployment Checklist

- [ ] Update `USERNAME` in README.md (3 places)
- [ ] Create GitHub repo: SuperBowlPythonAnalysis
- [ ] Push: `git push -u origin main`
- [ ] Enable GitHub Pages (Settings → Pages → Source: GitHub Actions)
- [ ] Verify deployment at `https://USERNAME.github.io/SuperBowlPythonAnalysis/`

## 💻 Local Commands

```bash
# Generate site
python generate_site.py

# Start server
python serve_site.py

# Run tests
pytest tests/ -v

# Run scrapers
python -c "from scrapers.superbowl_history import scrape_superbowl_history; scrape_superbowl_history()"
python -c "from scrapers.superbowl_player_history import scrape_superbowl_player_history; scrape_superbowl_player_history()"
python -c "from scrapers.playoff_history import scrape_playoff_history; scrape_playoff_history(seasons=list(range(2020, 2026)))"
python -c "from scrapers.player_stats import scrape_player_stats; scrape_player_stats(season=2025)"
```

## 📂 Key Files

| File | Purpose |
|------|---------|
| `generate_site.py` | Generate static HTML from data |
| `serve_site.py` | Local development server |
| `players_to_track.json` | Player configuration for scraping |
| `.github/workflows/update-analysis.yml` | Weekly data updates |
| `.github/workflows/deploy.yml` | GitHub Pages deployment |
| `docs/SCRAPING_GUIDE.md` | Complete scraper documentation |
| `GITHUB_PAGES_SETUP.md` | Deployment instructions |
| `FUTURE_ENHANCEMENTS.md` | 34 improvement ideas |

## 📊 Data Files

| File | Description |
|------|-------------|
| `data/superbowl_games.parquet` | Super Bowl game scores by quarter |
| `data/superbowl_player_history.parquet` | Player stats from all Super Bowls |
| `data/playoff_games.parquet` | Playoff games (2020-2024) |
| `data/player_stats_2025.parquet` | Current season player game logs |

## 🔧 Workflows

**Trigger Manual Update:**
1. GitHub → Actions tab
2. "Update Analysis Data" workflow
3. "Run workflow" button
4. Wait 5-10 minutes

**Check Deployment:**
1. GitHub → Actions tab
2. Look for green checkmarks
3. Click on workflow for details

## 📊 Generated Pages

- `index.html` - Dashboard with key insights
- `squares.html` - Squares analysis with heatmaps
- `players.html` - Player prop analysis
- `playoffs.html` - Playoff props and trends
- `about.html` - Methodology and disclaimers

## 🧪 Test Commands

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_site_generator.py -v

# With coverage
pytest tests/ --cov=analysis --cov=scrapers
```

## 🌐 URLs

- **Local:** http://localhost:8000
- **Live:** https://USERNAME.github.io/SuperBowlPythonAnalysis/
- **Actions:** https://github.com/USERNAME/SuperBowlPythonAnalysis/actions

## 📈 Project Stats

- **Phases:** 9 complete
- **Tests:** 34 passing
- **Modules:** 8 Python files
- **Templates:** 6 HTML templates
- **Workflows:** 2 GitHub Actions

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Site shows 404 | Wait 2-3 minutes, clear cache |
| Workflow fails | Check Actions tab for logs |
| Tests fail | Run `pytest tests/ -v` for details |
| Import errors | `source venv/bin/activate` |

## 📚 Documentation

- `README.md` - Project overview and quick start
- `docs/SCRAPING_GUIDE.md` - Complete scraper documentation
- `GITHUB_PAGES_SETUP.md` - Deployment guide
- `FUTURE_ENHANCEMENTS.md` - Improvement ideas
- `PHASE*_SUMMARY.md` - Phase details

## ⚡ Quick Tips

1. Always activate venv: `source venv/bin/activate`
2. Test before pushing: `pytest tests/ -v`
3. Regenerate after data changes: `python generate_site.py`
4. Check workflow logs if deployment fails
5. Update README USERNAME before first push
