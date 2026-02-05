# GitHub Pages Setup Guide

Follow these steps to deploy your Super Bowl Analysis to GitHub Pages.

## Prerequisites

- GitHub account
- Git installed locally
- Repository ready to push

## Step-by-Step Setup

### 1. Update README with Your Username

Before pushing, replace `USERNAME` in README.md with your actual GitHub username:

```bash
# Find and replace USERNAME in README.md
sed -i '' 's/USERNAME/your-actual-username/g' README.md

# Or manually edit README.md and replace:
# - https://github.com/USERNAME/SuperBowlPythonAnalysis
# - https://USERNAME.github.io/SuperBowlPythonAnalysis
```

### 2. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `SuperBowlPythonAnalysis`
3. Description: "Data-driven Super Bowl betting analysis with automated updates"
4. Visibility: Public (required for free GitHub Pages)
5. Do NOT initialize with README, .gitignore, or license
6. Click "Create repository"

### 3. Push Your Code to GitHub

```bash
# Add remote (replace YOUR-USERNAME)
git remote add origin https://github.com/YOUR-USERNAME/SuperBowlPythonAnalysis.git

# Verify remote
git remote -v

# Push main branch
git push -u origin main

# Verify push was successful
# - Go to https://github.com/YOUR-USERNAME/SuperBowlPythonAnalysis
# - Confirm files are visible
```

### 4. Enable GitHub Pages

1. **Navigate to Repository Settings**
   - Go to your repository on GitHub
   - Click "Settings" tab (top right)

2. **Configure Pages**
   - In left sidebar, click "Pages" (under "Code and automation")
   - Under "Source", select: **GitHub Actions**
   - Click "Save"

3. **Verify Configuration**
   - You should see: "Your site is ready to be published at https://YOUR-USERNAME.github.io/SuperBowlPythonAnalysis/"
   - The page will update with the URL once deployed

### 5. Trigger Initial Deployment

**Option A: Push a Change**
```bash
# Make a small change to trigger deployment
git commit --allow-empty -m "Trigger initial deployment"
git push
```

**Option B: Manual Workflow Trigger**
1. Go to repository on GitHub
2. Click "Actions" tab
3. Select "Deploy to GitHub Pages" workflow
4. Click "Run workflow" button
5. Click green "Run workflow"

### 6. Verify Deployment

1. **Check Actions Tab**
   - Click "Actions" tab
   - You should see workflows running:
     - "Deploy to GitHub Pages" (should complete in ~1-2 minutes)
   - Wait for green checkmark

2. **Visit Your Site**
   - Go to: `https://YOUR-USERNAME.github.io/SuperBowlPythonAnalysis/`
   - You should see your dashboard!

3. **Common Issues:**
   - **404 Error**: Wait 2-3 minutes, GitHub Pages needs time to initialize
   - **Blank Page**: Check browser console for errors
   - **No deployment**: Verify GitHub Pages is enabled in Settings

### 7. Test Automatic Updates

1. **Trigger Data Update Workflow**
   - Go to repository → Actions tab
   - Select "Update Analysis Data"
   - Click "Run workflow"
   - Wait ~5-10 minutes for completion

2. **Verify Automatic Deployment**
   - After data update completes, "Deploy to GitHub Pages" should auto-trigger
   - Check Actions tab for deployment workflow
   - Visit site to see updated timestamp

### 8. Verify Weekly Schedule

The data update will run automatically every Sunday at 2am UTC. To verify:

1. Check next run time:
   - Go to Actions → "Update Analysis Data"
   - Click on the workflow
   - "Next scheduled run" should show upcoming Sunday

2. No action needed - it runs automatically!

## Troubleshooting

### Deployment Fails

**Check workflow logs:**
```
1. Actions tab → Failed workflow
2. Click on the failed run
3. Expand failed step
4. Read error message
```

**Common fixes:**
- Ensure static_site/ folder has content
- Check .nojekyll file exists
- Verify permissions in Settings → Actions → General → Workflow permissions (should be "Read and write")

### Site Shows 404

**Solutions:**
1. Wait 2-3 minutes after first deployment
2. Verify GitHub Pages is enabled
3. Check URL is correct: `https://YOUR-USERNAME.github.io/SuperBowlPythonAnalysis/`
4. Clear browser cache

### Data Update Fails

**Check scrapers:**
```bash
# Test locally first
source venv/bin/activate
python -c "from scrapers.superbowl_history import scrape_superbowl_history; scrape_superbowl_history()"
```

**Common issues:**
- Website HTML structure changed (update scrapers)
- Network timeout (retry)
- Playwright browser not installed (check workflow logs)

### Workflow Permissions Error

1. Settings → Actions → General
2. Scroll to "Workflow permissions"
3. Select "Read and write permissions"
4. Check "Allow GitHub Actions to create and approve pull requests"
5. Click "Save"

## Optional Enhancements

### Custom Domain

1. Buy a domain (e.g., from Namecheap, Google Domains)
2. Add DNS records:
   ```
   Type: CNAME
   Name: www
   Value: YOUR-USERNAME.github.io
   ```
3. In GitHub:
   - Settings → Pages → Custom domain
   - Enter: www.yourdomain.com
   - Wait for DNS check (can take up to 24 hours)
   - Enable "Enforce HTTPS"

### Add Status Badge to README

Already included! The badges will show green once workflows run:

```markdown
[![Update Analysis](https://github.com/YOUR-USERNAME/SuperBowlPythonAnalysis/actions/workflows/update-analysis.yml/badge.svg)](...)
```

### Email Notifications

1. Settings → Notifications
2. Enable "Actions" notifications
3. You'll get emails on workflow failures

## Verification Checklist

Before considering setup complete:

- [ ] Repository created on GitHub
- [ ] Code pushed to main branch
- [ ] GitHub Pages enabled (Source: GitHub Actions)
- [ ] README.md updated with correct username
- [ ] Initial deployment succeeded
- [ ] Site accessible at GitHub Pages URL
- [ ] Data update workflow runs successfully
- [ ] Automatic deployment triggers after data update
- [ ] Next scheduled run shows upcoming Sunday
- [ ] All Actions badges show passing (green)

## Success!

Your site is now live at:
**https://YOUR-USERNAME.github.io/SuperBowlPythonAnalysis/**

Updates happen automatically every Sunday at 2am UTC, or manually via Actions tab.

## Support

Having issues?
1. Check workflow logs in Actions tab
2. Review troubleshooting section above
3. Search GitHub Pages documentation
4. Open an issue in your repository
