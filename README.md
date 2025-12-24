# Challenger Tracker

A website that tracks all League of Legends players who have reached Challenger rank during the current season.

## Features

- 📊 Tracks all players who reach Challenger (not just current)
- 📅 Automatically updates daily after 23:45 UTC
- 🔍 Search functionality for player names
- 📈 Sortable columns (Days in Challenger, Average Rank, Current Rank, LP)
- 🎯 Tracks players by PUUID (handles name changes)
- 🌐 Hosted on GitHub Pages

## Setup Instructions

### 1. Create GitHub Repository

```bash
git clone https://github.com/YOUR_USERNAME/challenger-tracker.git
cd challenger-tracker
```

### 2. Create Directory Structure

```bash
mkdir -p .github/workflows
mkdir -p data
```

### 3. Create All Files

Create these files with the content from the artifacts above:

- `index.html`
- `styles.css`
- `script.js`
- `update.py`
- `.github/workflows/update-data.yml`
- `data/players.json`

### 4. Configure Region

Edit `update.py` and change these lines to match your region:

```python
REGION = 'na1'  # Options: na1, euw1, eune1, kr, br1, jp1, la1, la2, oc1, tr1, ru
ROUTING = 'americas'  # Options: americas, europe, asia, sea
```

**Region Routing Map:**
- **americas**: na1, br1, la1, la2, oc1
- **europe**: euw1, eune1, tr1, ru
- **asia**: kr, jp1
- **sea**: (Southeast Asia servers)

### 5. Add Files to Git

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 6. Set Up API Key Secret

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `RIOT_API_KEY`
5. Value: Your Riot API key
6. Click **Add secret**

### 7. Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under "Source", select **Deploy from a branch**
3. Select branch: **main**
4. Select folder: **/ (root)**
5. Click **Save**

### 8. Run Initial Data Collection

1. Go to **Actions** tab in your repository
2. Click on "Update Challenger Data" workflow
3. Click "Run workflow" dropdown
4. Click "Run workflow" button

Wait for the workflow to complete (5-10 minutes). This will populate your `data/players.json` file.

### 9. Access Your Website

Your site will be available at:
```
https://YOUR_USERNAME.github.io/challenger-tracker/
```

## How It Works

### Data Collection

The `update.py` script:
1. Fetches current Challenger ladder from Riot API
2. Gets PUUID for each player (permanent ID)
3. Fetches Riot ID (gameName#tagLine)
4. Calculates days in Challenger since first seen
5. Tracks rank history and calculates average rank
6. Marks players as active/inactive

### Automatic Updates

GitHub Actions workflow runs daily at 23:50 UTC:
1. Runs the Python script
2. Commits updated `players.json`
3. GitHub Pages automatically redeploys

### Tracking Logic

- **First Time**: Player added with current date as `firstSeenDate`
- **Still Challenger**: Updates stats, increments days
- **Dropped Out**: Marked as inactive, stops counting days
- **Returned**: Reactivated, continues counting from original `firstSeenDate`

## API Rate Limits

Riot API Development Key limits:
- 20 requests per second
- 100 requests per 2 minutes

The script includes delays to respect these limits. For production use, consider applying for a Production API key.

## Troubleshooting

### Workflow Fails

Check Actions tab for error messages. Common issues:
- **API Key Invalid**: Verify secret is set correctly
- **Rate Limited**: Wait and manually re-run workflow
- **Region Wrong**: Check REGION and ROUTING in update.py

### Website Shows Old Data

- Check if workflow ran successfully in Actions tab
- Manually trigger workflow to force update
- Clear browser cache

### Players Not Appearing

- Ensure workflow has run at least once
- Check `data/players.json` has data
- Verify GitHub Pages is enabled and deployed

## Customization

### Change Update Time

Edit `.github/workflows/update-data.yml`:
```yaml
- cron: '50 23 * * *'  # Change to desired time (UTC)
```

### Change Styling

Edit `styles.css` to customize colors, fonts, layout.

### Add More Stats

Edit `update.py` to track additional metrics, then update `index.html` and `script.js` to display them.

## License

MIT License - Feel free to use and modify!
