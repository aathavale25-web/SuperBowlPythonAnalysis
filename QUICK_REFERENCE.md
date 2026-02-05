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

# Run specific scraper
python -c "from scrapers.superbowl_history import scrape_superbowl_history; scrape_superbowl_history()"
```

## 📂 Key Files

| File | Purpose |
|------|---------|
| `generate_site.py` | Generate static HTML from data |
| `serve_site.py` | Local development server |
| `.github/workflows/update-analysis.yml` | Weekly data updates |
| `.github/workflows/deploy.yml` | GitHub Pages deployment |
| `GITHUB_PAGES_SETUP.md` | Deployment instructions |
| `FUTURE_ENHANCEMENTS.md` | 34 improvement ideas |

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

- `README.md` - Project overview
- `GITHUB_PAGES_SETUP.md` - Deployment guide
- `FUTURE_ENHANCEMENTS.md` - Improvement ideas
- `PHASE*_SUMMARY.md` - Phase details

## ⚡ Quick Tips

1. Always activate venv: `source venv/bin/activate`
2. Test before pushing: `pytest tests/ -v`
3. Regenerate after data changes: `python generate_site.py`
4. Check workflow logs if deployment fails
5. Update README USERNAME before first push
