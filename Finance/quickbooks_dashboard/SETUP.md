# QuickBooks Dashboard Setup Guide

## Overview

This script connects to your QuickBooks Online account and generates a monthly financial dashboard automatically. Once set up, you can run it at the start of each month to see exactly where you stand.

## One-Time Setup (15 minutes)

### Step 1: Create an Intuit Developer Account

1. Go to [developer.intuit.com](https://developer.intuit.com)
2. Sign in with your Intuit account (same as QuickBooks)
3. Click "Create an app"

### Step 2: Create Your App

1. Select **QuickBooks Online Accounting**
2. Name it something like "MVR Dashboard"
3. Select **Production** environment (not Sandbox)
4. Click Create

### Step 3: Get Your Credentials

1. Go to your app's **Keys & OAuth** section
2. Copy the **Client ID**
3. Copy the **Client Secret**
4. Update `config.json` with these values:

```json
{
  "client_id": "ABcd1234...",
  "client_secret": "xyz789...",
  "redirect_uri": "http://localhost:8000/callback",
  "company_id": "",
  "environment": "production"
}
```

### Step 4: Add Redirect URI

1. In your Intuit app settings, go to **Keys & OAuth**
2. Under **Redirect URIs**, add: `http://localhost:8000/callback`
3. Save changes

### Step 5: Install Dependencies

```bash
pip install requests
```

### Step 6: Authenticate

Run the authentication flow (one time):

```bash
python qb_dashboard.py --auth
```

This will:
- Open your browser to QuickBooks login
- Ask you to authorize the app
- Save your tokens locally

## Monthly Usage

### Generate This Month's Dashboard

```bash
python qb_dashboard.py --dashboard
```

### Generate a Specific Month

```bash
python qb_dashboard.py --dashboard --month 2026-02
```

### Sample Output

```
==================================================
MVR DIGITAL - January 2026 DASHBOARD
==================================================

📊 FINANCIAL SUMMARY
────────────────────────────────────────
Revenue:          $      95,000
Total Expenses:   $      45,000
Net Income:       $      50,000
Operating Margin:         52.6%

📋 TOP EXPENSES
────────────────────────────────────────
Contract labor            $    28,000
Salaries & Wages          $     6,300
Software/Tools            $     4,000
Insurance                 $     3,000

🎯 TARGETS CHECK
────────────────────────────────────────
Revenue vs $150K target:  Gap: $55,000
Margin vs 35% target:     ✓ ABOVE
AM Hire Trigger ($110K):  Not yet
PM Hire Trigger ($120K):  Not yet

✓ Dashboard data saved to dashboard_2026_01.json
```

## Automating It

### Option 1: Calendar Reminder

Set a monthly reminder to run the script on the 5th of each month (after books are closed).

### Option 2: Cron Job (Mac/Linux)

Add to crontab to run automatically on the 5th at 9am:

```bash
crontab -e
```

Add this line:
```
0 9 5 * * cd /path/to/quickbooks_dashboard && python qb_dashboard.py --dashboard
```

### Option 3: Windows Task Scheduler

Create a scheduled task to run monthly.

## Troubleshooting

### "Token expired" error

Tokens refresh automatically, but if you haven't run the script in 100+ days, you may need to re-authenticate:

```bash
python qb_dashboard.py --auth
```

### "No data returned"

- Check that your QuickBooks has data for the requested month
- Verify you're connected to the right company

### API Errors

- Ensure your Intuit app is set to **Production** (not Sandbox)
- Check that you've added the redirect URI correctly

## Security Notes

- `tokens.json` contains your access credentials. Don't share it.
- Add both `tokens.json` and `config.json` to `.gitignore` if using version control
- Tokens auto-refresh and are valid for 100 days of inactivity

## What Data is Accessed

The script reads:
- Profit & Loss report (revenue, expenses)
- Invoice data (customer revenue breakdown)

The script does NOT:
- Modify any data
- Access bank account details
- Access sensitive customer data
