# SuperBowlPythonAnalysis - Setup Guide

## Environment Setup

This project uses native ARM Python for optimal performance on Apple Silicon Macs.

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- Homebrew installed

### Installation

1. **Python is already installed** via Homebrew at `/opt/homebrew/bin/python3` (Python 3.14)

2. **Virtual environment is ready** at `./venv/`

3. **Activate the environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Verify native ARM:**
   ```bash
   python -c "import platform; print(f'Architecture: {platform.machine()}')"
   # Should output: Architecture: arm64
   ```

### Installed Packages

All dependencies are installed in the virtual environment:
- **duckdb** 1.4.4 - Analytical database (native ARM)
- **polars** 1.38.0 - Fast DataFrame library (native ARM, no crashes!)
- **playwright** 1.58.0 - Web scraping
- **jinja2** 3.1.6 - Templating
- **plotly** 6.5.2 - Interactive visualizations
- **beautifulsoup4** 4.14.3 - HTML parsing
- **pytest** 9.0.2 - Testing framework

### Running the Project

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

3. **Run analysis:**
   ```bash
   python load_sample_superbowl_data.py
   python analysis/squares.py
   ```

### Why Native ARM?

**Before:** Using x86_64 (Intel) Python under Rosetta emulation
- Polars crashed with segmentation faults
- Slower performance due to emulation

**After:** Using native ARM Python
- Polars works perfectly
- ~2x faster performance
- No crashes

### Troubleshooting

**If you see "command not found: python":**
```bash
source venv/bin/activate
```

**If Polars crashes:**
- Make sure you're using the virtual environment
- Check architecture: `python -c "import platform; print(platform.machine())"`
- Should be `arm64`, not `x86_64`

**To deactivate virtual environment:**
```bash
deactivate
```

### Development Workflow

Always work inside the virtual environment:
```bash
# Start your session
source venv/bin/activate

# Do your work
pytest tests/
python analysis/squares.py

# When done
deactivate
```
