# Quick Start Guide

Get your Foreplay to Slack automation running in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- Slack workspace admin access (to create webhooks)
- Foreplay API key (already configured)

## Step 1: Run Setup

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bash
pip install -r requirements.txt
python foreplay_slack_automation.py
```

## Step 2: Create Slack Webhook

The setup script will guide you, or follow these steps:

1. Visit https://api.slack.com/apps
2. Click **Create New App** → **From scratch**
3. App Name: `Foreplay Ad Bot`
4. Select your workspace
5. Click **Incoming Webhooks** in sidebar
6. Toggle **Activate Incoming Webhooks** to ON
7. Click **Add New Webhook to Workspace**
8. Select **#creative** channel
9. Click **Allow**
10. Copy the webhook URL (starts with `https://hooks.slack.com/services/`)

## Step 3: Configure Webhook

Edit `.env` file and paste your webhook URL:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Or if you used setup.sh, it already prompted you for this.

## Step 4: Test Run

```bash
python3 foreplay_slack_automation.py
```

You should see:
- ✓ Brands being searched
- ✓ Ads being found
- ✓ Messages posting to #creative

## Step 5: Schedule Weekly

**Mac/Linux - Using Cron:**

```bash
crontab -e
```

Add this line (runs every Monday at 9 AM):
```
0 9 * * 1 cd /path/to/your/script && python3 foreplay_slack_automation.py >> automation.log 2>&1
```

Replace `/path/to/your/script` with the actual directory path.

**Windows - Using Task Scheduler:**

1. Open Task Scheduler
2. Create Basic Task → Name: "Foreplay Weekly Ads"
3. Trigger: Weekly → Monday, 9:00 AM
4. Action: Start a program
   - Program: `python.exe`
   - Arguments: `foreplay_slack_automation.py`
   - Start in: `C:\path\to\script\folder`

## Troubleshooting

**No ads found?**
- Normal if brands haven't launched new ads in the past 7 days
- Try running the test script: `python3 test_foreplay_api.py`

**Slack posting fails?**
- Verify webhook URL in .env is correct
- Check webhook points to #creative channel
- Test webhook manually: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' YOUR_WEBHOOK_URL`

**API errors?**
- Check your Foreplay API key is valid
- View credits remaining at: https://public.api.foreplay.co/
- Each run uses ~10-20 credits

## What It Does

Every week, the script will:

1. Search for your 9 tracked brands on Foreplay
2. Find ads that started running in the last 7 days
3. Post each ad to #creative with:
   - Visual preview (image/video thumbnail)
   - Headline and description
   - CTA button text
   - Platform information
   - Video duration (if applicable)
   - Start date
   - Link to landing page
4. Post a summary with total count

## Customization

Edit `foreplay_slack_automation.py` to:

- **Add/remove brands**: Modify the `TRACKED_BRANDS` list
- **Change lookback period**: Edit `DAYS_LOOKBACK` (default: 7)
- **Adjust message format**: Edit the `format_ad_message()` function
- **Change channel**: Update `SLACK_CHANNEL_ID`

## Support

- Foreplay API docs: https://docs.foreplay.co/
- Slack API docs: https://api.slack.com/docs
- Issues? Check the logs: `tail -f automation.log`
