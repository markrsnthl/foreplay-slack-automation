# MVR Digital Dashboard

Simple financial dashboard that reads your QuickBooks P&L export.

## Monthly Workflow (2 minutes)

1. **Export P&L from QuickBooks:**
   - Go to Reports > Profit and Loss
   - Set date range (e.g., Jan 1 - Jan 31, 2026)
   - Click Export > CSV
   - Save to the `data/` folder

2. **Run the dashboard:**
   ```bash
   cd mvr_dashboard
   python3 dashboard.py
   ```

3. **Review the output** - it shows:
   - Revenue vs $150K target
   - Margin vs 35% target
   - Hiring triggers (AM at $110K, PM at $120K)
   - Contract labor % check
   - YTD summary

## What Gets Tracked

| Metric | Target | Why |
|--------|--------|-----|
| Monthly Revenue | $150,000 | Growth goal |
| Operating Margin | 35%+ | Profitability floor |
| Contract Labor | <25% of revenue | Cost control |
| AM Hire Trigger | $110K revenue | Safe to hire |
| PM Hire Trigger | $120K revenue | Safe to hire |

## Adjusting Targets

Edit the `TARGETS` dict at the top of `dashboard.py`:

```python
TARGETS = {
    'revenue': 150000,
    'margin': 0.35,
    'am_trigger': 110000,
    'pm_trigger': 120000,
    'contract_labor_max_pct': 0.25
}
```

## Output Files

Reports are saved to `reports/` folder:
- `dashboard_Month_Year.txt` - Text version of dashboard
- `data_Month_Year.json` - Raw data for historical tracking
