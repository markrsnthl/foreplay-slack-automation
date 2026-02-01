#!/usr/bin/env python3
"""
MVR Digital - CSV Dashboard Generator

Export P&L from QuickBooks with "Display columns by: Month" for best results.
Alternatively, a single-month export will work too.

USAGE:
    python3 dashboard.py                    # Process most recent CSV
    python3 dashboard.py myfile.csv         # Process specific file
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
OUTPUT_DIR = SCRIPT_DIR / "reports"

TARGETS = {
    'revenue': 150000,
    'margin': 0.35,
    'am_trigger': 110000,
    'pm_trigger': 120000,
    'contract_labor_max_pct': 0.25
}


def find_latest_csv():
    DATA_DIR.mkdir(exist_ok=True)
    csvs = list(DATA_DIR.glob("*.csv")) + list(SCRIPT_DIR.glob("*.csv"))
    if not csvs:
        return None
    return max(csvs, key=lambda f: f.stat().st_mtime)


def parse_value(val_str):
    if not val_str:
        return 0
    val_str = str(val_str).replace(',', '').replace('$', '').replace('"', '').strip()
    if not val_str or val_str == '-':
        return 0
    try:
        return float(val_str)
    except ValueError:
        return 0


def parse_qbo_pnl(filepath):
    """Parse QuickBooks P&L CSV export - handles both monthly and single-period formats"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Extract report period from header rows
    report_period = "Current Period"
    for row in rows[:5]:
        for cell in row:
            if '2024' in str(cell) or '2025' in str(cell) or '2026' in str(cell):
                if '-' in str(cell) or 'January' in str(cell) or 'February' in str(cell):
                    report_period = str(cell).strip()
                    break

    # Find the header row - look for "Account" or "Distribution account"
    header_idx = None
    for i, row in enumerate(rows):
        if row:
            first_cell = str(row[0]).strip().lower()
            if first_cell in ['account', 'distribution account', '']:
                # Check if next cells look like headers
                if len(row) > 1 and ('total' in str(row[-1]).lower() or any('2025' in str(c) or '2026' in str(c) for c in row)):
                    header_idx = i
                    break

    if header_idx is None:
        # Try another approach - find row with "Total" header
        for i, row in enumerate(rows):
            if row and len(row) >= 2:
                if 'Total' in str(row[-1]) or 'Total' in str(row[1]):
                    header_idx = i
                    break

    if header_idx is None:
        print(f"Could not find header row. First few rows:")
        for i, row in enumerate(rows[:10]):
            print(f"  {i}: {row[:3]}...")
        return None

    headers = rows[header_idx]

    # Determine if this is monthly breakdown or single period
    months = []
    month_indices = []
    total_col_idx = None

    for i, h in enumerate(headers):
        h_str = str(h).strip()
        if h_str.lower() == 'total':
            total_col_idx = i
        elif h_str and ('2024' in h_str or '2025' in h_str or '2026' in h_str):
            months.append(h_str)
            month_indices.append(i)

    # If no month columns found, this is a single-period report - use Total column
    is_single_period = len(months) == 0
    if is_single_period:
        if total_col_idx is None:
            # Find first numeric column
            for i, h in enumerate(headers):
                if i > 0 and str(h).strip():
                    total_col_idx = i
                    break
        if total_col_idx is None:
            total_col_idx = 1  # Default to second column

        months = [report_period]
        month_indices = [total_col_idx]

    results = {
        'months': months,
        'report_period': report_period,
        'is_single_period': is_single_period,
        'revenue_by_month': {m: 0 for m in months},
        'expenses_by_month': {m: 0 for m in months},
        'expense_detail': defaultdict(lambda: {m: 0 for m in months}),
        'net_income_by_month': {m: 0 for m in months},
    }

    # Parse data rows
    in_expenses = False
    for row in rows[header_idx + 1:]:
        if not row or len(row) < 2:
            continue

        label = str(row[0]).strip()

        # Track when we're in expenses section
        if label.lower() == 'expenses':
            in_expenses = True
            continue
        if 'net operating income' in label.lower() or 'net income' in label.lower():
            in_expenses = False

        # Total Income
        if label.lower() == 'total for income' or label.lower() == 'total income':
            for mi, month in zip(month_indices, months):
                if mi < len(row):
                    results['revenue_by_month'][month] = parse_value(row[mi])

        # Gross Profit (backup for revenue if no "Total for Income")
        elif label.lower() == 'gross profit' and all(v == 0 for v in results['revenue_by_month'].values()):
            for mi, month in zip(month_indices, months):
                if mi < len(row):
                    results['revenue_by_month'][month] = parse_value(row[mi])

        # Total Expenses
        elif label.lower() == 'total for expenses' or label.lower() == 'total expenses':
            for mi, month in zip(month_indices, months):
                if mi < len(row):
                    results['expenses_by_month'][month] = parse_value(row[mi])

        # Net Income
        elif 'net income' in label.lower() or 'net operating income' in label.lower():
            for mi, month in zip(month_indices, months):
                if mi < len(row):
                    results['net_income_by_month'][month] = parse_value(row[mi])

        # Track expense categories (when in expenses section or matches key terms)
        expense_keywords = ['contract labor', 'salaries', 'software', 'insurance',
                          'accounting', 'benefits', 'travel', 'consulting']
        if in_expenses or any(kw in label.lower() for kw in expense_keywords):
            if not label.lower().startswith('total'):
                for mi, month in zip(month_indices, months):
                    if mi < len(row):
                        val = parse_value(row[mi])
                        if val > 0:
                            results['expense_detail'][label][month] = val

    # Calculate totals
    results['total_revenue'] = sum(results['revenue_by_month'].values())
    results['total_expenses'] = sum(results['expenses_by_month'].values())
    results['total_net_income'] = results['total_revenue'] - results['total_expenses']

    return results


def generate_dashboard(data, month=None):
    if month is None:
        month = data['months'][-1]

    revenue = data['revenue_by_month'].get(month, 0)
    expenses = data['expenses_by_month'].get(month, 0)
    net_income = revenue - expenses
    margin = (net_income / revenue * 100) if revenue > 0 else 0

    expense_breakdown = {}
    for category, month_vals in data['expense_detail'].items():
        val = month_vals.get(month, 0)
        if val > 0:
            expense_breakdown[category] = val

    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  MVR DIGITAL FINANCIAL DASHBOARD")
    if data['is_single_period']:
        lines.append(f"  {data['report_period']}")
    else:
        lines.append(f"  {month}")
    lines.append("=" * 60)

    lines.append("")
    lines.append("📊 FINANCIAL SUMMARY")
    lines.append("-" * 45)
    lines.append(f"  Revenue:              ${revenue:>12,.0f}")
    lines.append(f"  Expenses:             ${expenses:>12,.0f}")
    lines.append(f"  Net Operating Income: ${net_income:>12,.0f}")
    lines.append(f"  Operating Margin:     {margin:>12.1f}%")

    lines.append("")
    lines.append("🎯 VS TARGETS")
    lines.append("-" * 45)

    rev_gap = TARGETS['revenue'] - revenue
    if rev_gap <= 0:
        lines.append(f"  Revenue ($150K):      ✓ ACHIEVED (+${-rev_gap:,.0f})")
    else:
        lines.append(f"  Revenue ($150K):      Gap: ${rev_gap:,.0f}")

    if margin >= TARGETS['margin'] * 100:
        lines.append(f"  Margin (35%):         ✓ ABOVE TARGET")
    else:
        lines.append(f"  Margin (35%):         Current: {margin:.1f}%")

    lines.append("")
    lines.append("👥 HIRING TRIGGERS")
    lines.append("-" * 45)
    lines.append(f"  Account Manager ($110K):  {'✓ READY TO HIRE' if revenue >= TARGETS['am_trigger'] else 'Not yet'}")
    lines.append(f"  Project Manager ($120K):  {'✓ READY TO HIRE' if revenue >= TARGETS['pm_trigger'] else 'Not yet'}")

    lines.append("")
    lines.append("💰 TOP EXPENSES")
    lines.append("-" * 45)
    sorted_exp = sorted(expense_breakdown.items(), key=lambda x: x[1], reverse=True)[:8]
    for name, amt in sorted_exp:
        lines.append(f"  {name[:28]:<28} ${amt:>10,.0f}")

    contract_labor = expense_breakdown.get('Contract labor', 0)
    if contract_labor > 0 and revenue > 0:
        cl_pct = contract_labor / revenue
        lines.append("")
        lines.append("📋 CONTRACT LABOR CHECK")
        lines.append("-" * 45)
        lines.append(f"  Contract Labor:       ${contract_labor:>12,.0f}")
        lines.append(f"  % of Revenue:         {cl_pct*100:>12.1f}%")
        status = "⚠️  HIGH (target <25%)" if cl_pct > TARGETS['contract_labor_max_pct'] else "✓ OK"
        lines.append(f"  Status:               {status}")

    # YTD only if multi-month
    if not data['is_single_period'] and len(data['months']) > 1:
        lines.append("")
        lines.append("📈 YEAR-TO-DATE")
        lines.append("-" * 45)
        lines.append(f"  YTD Revenue:          ${data['total_revenue']:>12,.0f}")
        lines.append(f"  YTD Expenses:         ${data['total_expenses']:>12,.0f}")
        lines.append(f"  YTD Net Income:       ${data['total_net_income']:>12,.0f}")
        ytd_margin = (data['total_net_income'] / data['total_revenue'] * 100) if data['total_revenue'] > 0 else 0
        lines.append(f"  YTD Margin:           {ytd_margin:>12.1f}%")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)
    lines.append("")

    return "\n".join(lines), {
        'month': month,
        'revenue': revenue,
        'expenses': expenses,
        'net_income': net_income,
        'margin': margin,
        'expense_breakdown': expense_breakdown
    }


def main():
    print("\n🔄 MVR Digital Dashboard Generator\n")

    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        csv_path = Path(sys.argv[1])
        if not csv_path.exists():
            csv_path = DATA_DIR / sys.argv[1]
    else:
        csv_path = find_latest_csv()

    if not csv_path or not csv_path.exists():
        print("❌ No CSV file found!")
        print(f"\nPlace your QuickBooks P&L export in: {DATA_DIR}/")
        sys.exit(1)

    print(f"📂 Processing: {csv_path.name}")

    data = parse_qbo_pnl(csv_path)
    if not data:
        print("❌ Could not parse CSV")
        sys.exit(1)

    dashboard_text, month_data = generate_dashboard(data)
    print(dashboard_text)

    OUTPUT_DIR.mkdir(exist_ok=True)
    month_str = month_data['month'].replace(' ', '_').replace(',', '').replace('-', '_')

    report_file = OUTPUT_DIR / f"dashboard_{month_str}.txt"
    with open(report_file, 'w') as f:
        f.write(dashboard_text)

    json_file = OUTPUT_DIR / f"data_{month_str}.json"
    with open(json_file, 'w') as f:
        json.dump({
            'generated': datetime.now().isoformat(),
            **month_data,
            'ytd_revenue': data['total_revenue'],
            'ytd_expenses': data['total_expenses'],
            'ytd_net_income': data['total_net_income']
        }, f, indent=2)

    print(f"📄 Report saved: {report_file}")
    print(f"📊 Data saved: {json_file}")


if __name__ == '__main__':
    main()
