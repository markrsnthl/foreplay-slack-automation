# Foreplay to Slack Weekly Ad Automation

Automated pipeline that fetches new ads from trusted brands on Foreplay and posts them to Slack #creative every week.

## What's Fixed (Production-Ready)

✅ **No hard-coded secrets** - Fails fast if env vars missing
✅ **Deduplication** - Tracks posted ads, prevents spam
✅ **Grouped by brand** - Clean UX, max 10 ads per brand
✅ **Idempotent** - Safe to re-run, won't duplicate posts
✅ **GitHub Actions ready** - Zero infra, runs weekly

## Tracked Brands

IM8, Eadem, Armra, Fatty15, Seed, True Classic, Magic Spoon Cereal, Hims, AG1

## Quick Start

### 1. Create Slack Webhook

1. Go to https://api.slack.com/apps
2. Create New App → From scratch → Name: "Foreplay Ad Bot"
3. Incoming Webhooks → Toggle ON
4. Add New Webhook → Select **#creative**
5. Copy webhook URL

### 2. Set Up GitHub Repository

**Option A: Use this repo**

```bash
# Clone and push to your GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/foreplay-slack-automation.git
git push -u origin main
```

**Option B: Fork or import**

Just fork this repo or import it to your GitHub account.

### 3. Add Secrets to GitHub

1. Go to repo Settings → Secrets and variables → Actions
2. Add repository secrets:
   - `FOREPLAY_API_KEY`: Your Foreplay API key
   - `SLACK_WEBHOOK_URL`: Your Slack webhook URL

### 4. Enable GitHub Actions

1. Go to Actions tab
2. Enable workflows if prompted
3. Click "Weekly Ad Update" → Run workflow (test it)

Done! It will now run every Monday at 9 AM UTC.

## How It Works

1. **Fetch**: Searches Foreplay for your 9 brands
2. **Filter**: Gets ads started in last 7 days
3. **Deduplicate**: Skips ads already posted (tracked in `posted_ads.json`)
4. **Group**: Combines multiple ads per brand into one message
5. **Post**: Sends to Slack with thumbnails, CTA, platform, duration
6. **Track**: Commits updated `posted_ads.json` back to repo

## Configuration

Edit `foreplay_slack_automation.py`:

```python
TRACKED_BRANDS = ['IM8', 'Eadem', ...]  # Add/remove brands
DAYS_LOOKBACK = 7                        # Change time window
MAX_ADS_PER_BRAND = 10                   # Prevent channel spam
```

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FOREPLAY_API_KEY="your-key"
export SLACK_WEBHOOK_URL="your-webhook"

# Run
python foreplay_slack_automation.py
```

## Architecture Decisions

**Why GitHub Actions?**
- Zero infrastructure
- Free for public repos
- Built-in secrets management
- Reliable scheduling
- Automatic retries

**Why JSON deduplication file?**
- Simple and transparent
- Version controlled
- No external dependencies
- Easy to audit or reset

**Why group ads by brand?**
- Prevents Slack noise at scale
- Better scanning/pattern recognition
- Respects channel members' attention

## Monitoring

**Check if it ran:**
- Actions tab → Latest workflow run

**Check what posted:**
- View `posted_ads.json` commits
- Workflow logs show ad counts

**Force re-run:**
- Actions → Run workflow → Manual trigger

## Troubleshooting

**No ads found:** Normal if brands haven't launched new ads recently.

**Duplicate posts:** Check `posted_ads.json` is being committed correctly.

**API errors:** Verify FOREPLAY_API_KEY secret is set correctly.

**Slack posting fails:** Verify SLACK_WEBHOOK_URL points to #creative.

## Roadmap (Future Enhancements)

- [ ] YAML config instead of editing Python
- [ ] Slack interactive buttons (save, tag, dismiss)
- [ ] Daily lightweight run + weekly digest
- [ ] Ad performance metrics from Foreplay
- [ ] Custom filters (platform, format, duration)

## Credit Usage

Approximately 10-20 Foreplay API credits per run depending on number of brands and ads.

## Support

- Foreplay API: https://docs.foreplay.co/
- Slack API: https://api.slack.com/docs
- Issues: Open a GitHub issue
