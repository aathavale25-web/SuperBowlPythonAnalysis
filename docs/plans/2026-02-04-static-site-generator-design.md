# Static Site Generator Design

**Date:** 2026-02-04
**Status:** Approved
**Implementation:** Phase 8

## Overview

Create a static site generator that transforms Super Bowl analysis results (squares, player props, playoff props) into a modern, interactive web dashboard with regeneration capabilities.

## Design Decisions

### Architecture
- **Style:** Minimalist analytics dashboard (dark mode, data-focused)
- **Structure:** Separate HTML pages for each section
- **Charts:** Extract and embed Plotly divs with shared CDN
- **Data Display:** Single page with collapsible cards for multiple items
- **Server:** Python HTTP server with regenerate endpoint
- **Regeneration UX:** Loading overlay with auto-refresh

## File Structure

```
SuperBowlPythonAnalysis/
├── generate_site.py          # Main site generator
├── serve_site.py              # HTTP server with regenerate endpoint
├── templates/                 # Jinja2 templates
│   ├── base.html             # Base template with nav, header, footer
│   ├── index.html            # Dashboard home
│   ├── squares.html          # Squares analysis
│   ├── players.html          # Player props
│   ├── playoffs.html         # Playoff props
│   └── about.html            # Methodology
├── static/                    # Template assets (CSS, icons)
│   └── styles.css            # Main stylesheet
└── static_site/              # Generated output (gitignored)
    ├── index.html
    ├── squares.html
    ├── players.html
    ├── playoffs.html
    ├── about.html
    └── assets/
        └── styles.css        # Copied from static/
```

## Component Details

### 1. Base Template (`base.html`)

**Visual Design:**
- Background: `#1a1a1a`
- Cards: `#2d2d2d`
- Text: `#e0e0e0`
- Fixed sidebar navigation (~250px wide)
- Main content area (max-width 1400px)
- Footer with timestamp and regenerate button
- Plotly.js loaded from CDN

**Navigation Sidebar:**
```
🏈 Super Bowl Analysis
   ├── Dashboard
   ├── Squares Analysis
   ├── Player Props
   ├── Playoff Props
   └── About

   [🔄 Regenerate] button
```

**Typography:**
- Font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`
- Headers: 24-32px, semi-bold
- Body: 16px, regular
- Stats: `Monaco, monospace`

**Color Accents:**
- Success/good bets: `#4ade80` (green)
- Warning/moderate: `#fbbf24` (amber)
- Error/avoid: `#f87171` (red)
- Links: `#60a5fa` (blue)

**Responsive:**
- Mobile: Sidebar → hamburger menu
- Tables: Horizontal scroll or stack
- Charts: Scale to container width

### 2. Dashboard Page (`index.html`)

**Content:**
- Hero section with key stats:
  - Best square combination (final score)
  - Top player prop bet (if >65%)
  - Best playoff prop (if >60%)
- Three-column grid:
  - Squares Analysis card → squares.html
  - Player Props card → players.html
  - Playoff Props card → playoffs.html
- Each card shows teaser stat

### 3. Squares Page (`squares.html`)

**Content:**
- Introduction to quarter-by-quarter analysis
- Sections for each quarter (Q1, Q2, Q3, Q4, Final)
- Per quarter:
  - Embedded Plotly heatmap (10x10 grid)
  - Top 10 best squares table
  - Bottom 10 worst squares table
- Methodology explanation (recency weighting)

### 4. Players Page (`players.html`)

**Content:**
- Search/filter box (optional text filter)
- Collapsible card per player:
  - Header: Name, position, expand icon
  - Expanded view:
    - Season stats (avg, median, high, low)
    - Hit rates per betting line
    - Best bets highlighted (>65%)
    - Trends (📈 improving, 📉 declining, ➡️ stable)

### 5. Playoffs Page (`playoffs.html`)

**Content:**
- Game props section:
  - Total points hit rates
  - Winning margin distribution
  - Defensive TD occurrence
- Round breakdown table
- Best props (>60%) highlighted
- Super Bowl trends callout

### 6. About Page (`about.html`)

**Content:**
- Methodology explanation
- Data sources
- Hit rate interpretation
- Limitations/disclaimers

## Technical Implementation

### Data Collection Flow

```python
def collect_analysis_data():
    """Run all analyses and collect results"""
    return {
        'squares': {
            'matrices': run_squares_analysis(),
            'ranked': get_ranked_squares(),
            'heatmaps': extract_plotly_charts('squares_heatmap_*.html')
        },
        'players': {
            'summaries': run_player_analysis(),
        },
        'playoffs': {
            'game_props': run_playoff_props(),
            'round_breakdown': get_round_breakdown(),
            'best_props': get_best_playoff_props()
        },
        'timestamp': datetime.now().isoformat()
    }
```

### Plotly Chart Extraction

```python
def extract_plotly_chart(html_file):
    """Extract div and script from standalone Plotly HTML"""
    soup = BeautifulSoup(html_file, 'html.parser')
    plotly_div = soup.find('div', {'class': 'plotly-graph-div'})
    scripts = soup.find_all('script')
    chart_script = [s for s in scripts if 'Plotly.newPlot' in s.string][0]

    return {
        'div': str(plotly_div),
        'script': str(chart_script)
    }
```

### Template Rendering

```python
def generate_pages(data):
    """Render all templates with data"""
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))

    for template_name in ['index', 'squares', 'players', 'playoffs', 'about']:
        template = env.get_template(f'{template_name}.html')
        output = template.render(data=data)

        with open(f'static_site/{template_name}.html', 'w') as f:
            f.write(output)
```

### HTTP Server with Regeneration

**Server (`serve_site.py`):**
- Serves static files from `static_site/`
- POST to `/regenerate` triggers `generate_site.py`
- Returns JSON status

**Frontend Button:**
- Shows loading overlay during regeneration
- Disables navigation/interactions
- Auto-refreshes on completion

**Loading Overlay:**
- Full-page dark overlay
- Spinner animation
- "Regenerating analysis..." message
- Progress text

## Error Handling

**Graceful Degradation:**
- If analysis fails, show error message in UI
- Don't crash entire site generation
- Log errors to console with traceback

**Template Safety:**
```jinja
{% if data.players.summaries %}
  {# Render players #}
{% else %}
  <div class="error-card">
    ⚠️ No player data available
  </div>
{% endif %}
```

## Dependencies

```
jinja2==3.1.2
beautifulsoup4==4.12.2
```

## Usage

```bash
# Generate site initially
python generate_site.py

# Start server
python serve_site.py

# Visit http://localhost:8000
# Click regenerate button to refresh data
```

## Testing

- Manual: Run generator, verify all pages render
- Check all links work
- Test regenerate end-to-end
- Mobile responsive (Chrome DevTools)
- Verify Plotly interactivity
- Test with missing/incomplete data

## Future Enhancements (Out of Scope)

- Progress WebSocket for live updates
- Chart export as PNG
- Data export as CSV
- Historical comparison tracking
