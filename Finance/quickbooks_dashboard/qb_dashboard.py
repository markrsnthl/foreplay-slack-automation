"""
MVR Digital - QuickBooks Online Dashboard Integration

This script connects to QuickBooks Online API to automatically pull
financial data and generate a monthly dashboard.

SETUP REQUIRED:
1. Create an Intuit Developer account: https://developer.intuit.com
2. Create a new app (select QuickBooks Online Accounting)
3. Get your Client ID and Client Secret from the app's Keys & OAuth section
4. Add redirect URI: http://localhost:8000/callback
5. Update config.json with your credentials

FIRST RUN:
    python qb_dashboard.py --auth

MONTHLY DASHBOARD:
    python qb_dashboard.py --dashboard

SPECIFIC MONTH:
    python qb_dashboard.py --dashboard --month 2026-01
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

# Configuration
CONFIG_FILE = Path(__file__).parent / "config.json"
TOKEN_FILE = Path(__file__).parent / "tokens.json"

# QuickBooks API endpoints
QBO_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QBO_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QBO_API_BASE = "https://quickbooks.api.intuit.com/v3/company"

DEFAULT_CONFIG = {
    "client_id": "YOUR_CLIENT_ID_HERE",
    "client_secret": "YOUR_CLIENT_SECRET_HERE",
    "redirect_uri": "http://localhost:8000/callback",
    "company_id": "",  # Will be set during auth
    "environment": "production"  # or "sandbox" for testing
}


def load_config():
    """Load configuration from config.json"""
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"Created {CONFIG_FILE} - please update with your Intuit app credentials")
        sys.exit(1)

    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_tokens(tokens):
    """Save OAuth tokens to file"""
    tokens['saved_at'] = datetime.now().isoformat()
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)


def load_tokens():
    """Load OAuth tokens from file"""
    if not TOKEN_FILE.exists():
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def refresh_access_token(config, tokens):
    """Refresh the access token using refresh token"""
    response = requests.post(
        QBO_TOKEN_URL,
        auth=(config['client_id'], config['client_secret']),
        headers={'Accept': 'application/json'},
        data={
            'grant_type': 'refresh_token',
            'refresh_token': tokens['refresh_token']
        }
    )

    if response.status_code == 200:
        new_tokens = response.json()
        new_tokens['company_id'] = tokens.get('company_id', config.get('company_id'))
        save_tokens(new_tokens)
        return new_tokens
    else:
        print(f"Error refreshing token: {response.text}")
        return None


def get_valid_token(config):
    """Get a valid access token, refreshing if necessary"""
    tokens = load_tokens()
    if not tokens:
        print("No tokens found. Run with --auth first.")
        sys.exit(1)

    # Check if token might be expired (tokens last 1 hour)
    saved_at = datetime.fromisoformat(tokens.get('saved_at', '2000-01-01'))
    if datetime.now() - saved_at > timedelta(minutes=55):
        print("Token may be expired, refreshing...")
        tokens = refresh_access_token(config, tokens)
        if not tokens:
            print("Failed to refresh token. Run with --auth again.")
            sys.exit(1)

    return tokens


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    auth_code = None
    realm_id = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if 'code' in params:
            OAuthCallbackHandler.auth_code = params['code'][0]
            OAuthCallbackHandler.realm_id = params.get('realmId', [None])[0]

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html><body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body></html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization Failed</h1></body></html>")

    def log_message(self, format, *args):
        pass  # Suppress logging


def authenticate(config):
    """Run OAuth2 authentication flow"""
    print("\n=== QuickBooks OAuth2 Authentication ===\n")

    if config['client_id'] == 'YOUR_CLIENT_ID_HERE':
        print("ERROR: Please update config.json with your Intuit app credentials")
        print("\nSteps:")
        print("1. Go to https://developer.intuit.com")
        print("2. Create an app (QuickBooks Online Accounting)")
        print("3. Copy Client ID and Client Secret to config.json")
        print("4. Add redirect URI: http://localhost:8000/callback")
        sys.exit(1)

    # Build authorization URL
    scope = "com.intuit.quickbooks.accounting"
    auth_url = (
        f"{QBO_AUTH_URL}?"
        f"client_id={config['client_id']}&"
        f"redirect_uri={config['redirect_uri']}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"state=mvr_dashboard"
    )

    print("Opening browser for QuickBooks authorization...")
    print(f"\nIf browser doesn't open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    # Start local server to receive callback
    server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
    print("Waiting for authorization callback...")
    server.handle_request()

    if not OAuthCallbackHandler.auth_code:
        print("Authorization failed - no code received")
        sys.exit(1)

    # Exchange code for tokens
    print("Exchanging authorization code for tokens...")
    response = requests.post(
        QBO_TOKEN_URL,
        auth=(config['client_id'], config['client_secret']),
        headers={'Accept': 'application/json'},
        data={
            'grant_type': 'authorization_code',
            'code': OAuthCallbackHandler.auth_code,
            'redirect_uri': config['redirect_uri']
        }
    )

    if response.status_code == 200:
        tokens = response.json()
        tokens['company_id'] = OAuthCallbackHandler.realm_id
        save_tokens(tokens)

        # Update config with company_id
        config['company_id'] = OAuthCallbackHandler.realm_id
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        print("\n✓ Authentication successful!")
        print(f"✓ Company ID: {OAuthCallbackHandler.realm_id}")
        print(f"✓ Tokens saved to {TOKEN_FILE}")
    else:
        print(f"Error getting tokens: {response.text}")
        sys.exit(1)


def qbo_request(config, tokens, endpoint, params=None):
    """Make authenticated request to QuickBooks API"""
    url = f"{QBO_API_BASE}/{tokens['company_id']}/{endpoint}"

    headers = {
        'Authorization': f"Bearer {tokens['access_token']}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 401:
        # Token expired, try refresh
        tokens = refresh_access_token(config, tokens)
        if tokens:
            headers['Authorization'] = f"Bearer {tokens['access_token']}"
            response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"API Error ({response.status_code}): {response.text}")
        return None


def get_profit_and_loss(config, tokens, start_date, end_date):
    """Get Profit & Loss report for date range"""
    params = {
        'start_date': start_date,
        'end_date': end_date,
        'minorversion': 65
    }
    return qbo_request(config, tokens, 'reports/ProfitAndLoss', params)


def get_invoices_by_customer(config, tokens, start_date, end_date):
    """Get invoices grouped by customer for date range"""
    query = (
        f"SELECT * FROM Invoice WHERE TxnDate >= '{start_date}' "
        f"AND TxnDate <= '{end_date}'"
    )
    params = {'query': query, 'minorversion': 65}
    return qbo_request(config, tokens, 'query', params)


def get_vendors_paid(config, tokens, start_date, end_date):
    """Get vendor payments (contractor costs) for date range"""
    query = (
        f"SELECT * FROM Bill WHERE TxnDate >= '{start_date}' "
        f"AND TxnDate <= '{end_date}'"
    )
    params = {'query': query, 'minorversion': 65}
    return qbo_request(config, tokens, 'query', params)


def parse_pnl_report(report):
    """Parse P&L report into structured data"""
    if not report:
        return None

    result = {
        'revenue': 0,
        'expenses': {},
        'net_income': 0
    }

    try:
        rows = report.get('Rows', {}).get('Row', [])
        for row in rows:
            header = row.get('Header', {})
            col_data = header.get('ColData', [])

            if len(col_data) >= 2:
                name = col_data[0].get('value', '')
                value_str = col_data[1].get('value', '0')

                try:
                    value = float(value_str.replace(',', ''))
                except:
                    value = 0

                if 'Income' in name:
                    result['revenue'] += value
                elif 'Net Income' in name:
                    result['net_income'] = value

            # Parse expense details
            if row.get('type') == 'Section':
                section_rows = row.get('Rows', {}).get('Row', [])
                for sec_row in section_rows:
                    sec_col = sec_row.get('ColData', [])
                    if len(sec_col) >= 2:
                        exp_name = sec_col[0].get('value', '')
                        exp_val_str = sec_col[1].get('value', '0')
                        try:
                            exp_val = float(exp_val_str.replace(',', ''))
                            result['expenses'][exp_name] = exp_val
                        except:
                            pass
    except Exception as e:
        print(f"Error parsing P&L: {e}")

    return result


def generate_dashboard(config, tokens, month=None):
    """Generate monthly dashboard"""
    if month:
        year, mon = map(int, month.split('-'))
    else:
        today = datetime.now()
        # Default to previous month
        first_of_month = today.replace(day=1)
        last_month = first_of_month - timedelta(days=1)
        year, mon = last_month.year, last_month.month

    # Calculate date range
    start_date = f"{year}-{mon:02d}-01"
    if mon == 12:
        end_date = f"{year+1}-01-01"
    else:
        end_date = f"{year}-{mon+1:02d}-01"
    end_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

    month_name = datetime(year, mon, 1).strftime('%B %Y')

    print(f"\n{'='*50}")
    print(f"MVR DIGITAL - {month_name} DASHBOARD")
    print(f"{'='*50}\n")

    # Get P&L
    print("Fetching Profit & Loss...")
    pnl_report = get_profit_and_loss(config, tokens, start_date, end_date)
    pnl = parse_pnl_report(pnl_report)

    if pnl:
        revenue = pnl['revenue']
        total_expenses = sum(pnl['expenses'].values())
        net_income = revenue - total_expenses
        margin = (net_income / revenue * 100) if revenue > 0 else 0

        print(f"\n📊 FINANCIAL SUMMARY")
        print(f"{'─'*40}")
        print(f"Revenue:          ${revenue:>12,.0f}")
        print(f"Total Expenses:   ${total_expenses:>12,.0f}")
        print(f"Net Income:       ${net_income:>12,.0f}")
        print(f"Operating Margin: {margin:>12.1f}%")

        # Key expense categories
        print(f"\n📋 TOP EXPENSES")
        print(f"{'─'*40}")
        sorted_expenses = sorted(pnl['expenses'].items(), key=lambda x: x[1], reverse=True)
        for name, amount in sorted_expenses[:8]:
            if amount > 0:
                print(f"{name[:25]:<25} ${amount:>10,.0f}")

        # Targets check
        print(f"\n🎯 TARGETS CHECK")
        print(f"{'─'*40}")

        target_revenue = 150000
        target_margin = 35
        am_trigger = 110000
        pm_trigger = 120000

        print(f"Revenue vs $150K target:  {'✓ ON TRACK' if revenue >= target_revenue else f'Gap: ${target_revenue - revenue:,.0f}'}")
        print(f"Margin vs 35% target:     {'✓ ABOVE' if margin >= target_margin else f'Current: {margin:.1f}%'}")
        print(f"AM Hire Trigger ($110K):  {'✓ READY' if revenue >= am_trigger else 'Not yet'}")
        print(f"PM Hire Trigger ($120K):  {'✓ READY' if revenue >= pm_trigger else 'Not yet'}")

        # Contract labor detail
        contract_labor = pnl['expenses'].get('Contract labor', 0)
        if contract_labor > 0:
            print(f"\n💼 CONTRACT LABOR")
            print(f"{'─'*40}")
            print(f"Total:            ${contract_labor:>12,.0f}")
            print(f"% of Revenue:     {contract_labor/revenue*100:>12.1f}%")
            print(f"Target (<25%):    {'✓ OK' if contract_labor/revenue < 0.25 else '⚠ HIGH'}")

        # Save to JSON for later use
        dashboard_data = {
            'month': month_name,
            'generated_at': datetime.now().isoformat(),
            'revenue': revenue,
            'expenses': total_expenses,
            'net_income': net_income,
            'margin': margin,
            'expense_detail': pnl['expenses']
        }

        output_file = Path(__file__).parent / f"dashboard_{year}_{mon:02d}.json"
        with open(output_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        print(f"\n✓ Dashboard data saved to {output_file}")

    else:
        print("Could not retrieve P&L data")

    print(f"\n{'='*50}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='MVR Digital QuickBooks Dashboard')
    parser.add_argument('--auth', action='store_true', help='Run OAuth authentication')
    parser.add_argument('--dashboard', action='store_true', help='Generate monthly dashboard')
    parser.add_argument('--month', type=str, help='Month to report (YYYY-MM format)')

    args = parser.parse_args()

    config = load_config()

    if args.auth:
        authenticate(config)
    elif args.dashboard:
        tokens = get_valid_token(config)
        generate_dashboard(config, tokens, args.month)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
