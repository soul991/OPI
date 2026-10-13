---
name: ipo-data-collector
description: Collect a large, clean dataset of past Indian mainboard IPOs (NSE/BSE) with subscription, valuation, GMP, market context and actual listing gain, written to a master CSV for model training. Use whenever the user wants to gather, extend, clean or validate IPO history data for India, build an IPO training dataset, or add newly listed IPOs to the master CSV.
---

# IPO Data Collector (India)

Build `data/ipo_master.csv` with one row per Indian mainboard IPO, using the columns in `references/schema.md`. Scope is India only. Keep SME IPOs in a separate file `data/ipo_sme.csv`.

## Requirements
Web search/fetch access and the ability to run Python. If either is missing, tell the user which one and stop; never invent numbers.

## Workflow

1. **Build the IPO list first.** For the year range requested (default: newest to oldest, back to 2010), list every mainboard IPO with name, open/close/listing dates. Sources, in order: NSE and BSE IPO/past-issue pages, Chittorgarh IPO lists, SEBI/RHP filings. Save the list to `data/ipo_list.csv` so work can resume.
2. **Fill rows in batches of 20-40 IPOs**, one year at a time. For each IPO fill every schema column. Leave a cell **empty** when a value cannot be found. Never guess.
3. **Record the source** in the `source_urls` column (semicolon-separated).
4. **Compute derived fields** per `references/schema.md` (`listing_gain_pct`, `label_good`, `recent_ipo_avg_gain`, `nifty_30d_return`).
5. **Append to the master CSV** after every batch (checkpointing) and run:
   `python scripts/validate_dataset.py data/ipo_master.csv`
   Fix every error it reports before starting the next batch.
6. **Spot-check:** after each batch re-verify 3 random rows against a second source. Report the mismatch rate to the user.
7. **Dedupe** on (company, listing_date). Keep the row with fewer empty cells.
8. At the end, report: total rows, rows per year, % missing per column, and any columns too empty to be useful (over 40% missing).

## Rules
- Time-leakage rule: every feature must be knowable before listing. GMP means the grey market premium on the last bidding day, not on listing day.
- Subscription figures are the final overall multiples (times subscribed).
- If sources disagree, prefer exchange data, then Chittorgarh, then others, and note the conflict in `notes`.
- Fetch pages normally and slowly; respect each site's terms.
