# Phase 14: Preregistration of Automated Listing-Outcome Recording & Alerting Protocol

> Committed prior to any automated outcome recording execution per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 14/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research decision aid only, not financial, investment, or trading advice.

---

## 1. Objectives & Scope

Phase 14 operationalizes the automated recording of listing day actual outcomes for tracked Mainboard IPOs within GitHub Actions cloud runners, resolving the previous operational gap (D-066) where daily scheduled jobs logged `SKIPPED_BLOCKED_SOURCE` without attempting an actual fetch.

---

## 2. Source Hierarchy & Fallback Chain

When an IPO listing date has arrived and market hours have concluded (IST time > 16:00 on listing date, or any subsequent date per D-069), the automated outcome pipeline executes the following deterministic multi-tier source chain:

### Tier 1: Primary Official Exchange Scraping (`record_actual_from_exchange`)
- **Target**: Official exchange equity quote / corporate announcement page on NSE (`www.nseindia.com`) or BSE (`www.bseindia.com`).
- **Exchange Selection Rule**: 
  - For dual-listed Mainboard IPOs (e.g., Fusion CX, Zetwerk, SMT, Tonbo, Bonfiglioli, Jio Platforms, Paras Healthcare), **NSE** is the authoritative primary exchange for the opening trade price, matching 5 of 6 existing forward rows in repo provenance.
  - For IPOs listed exclusively on BSE (e.g., HD Fire Protect Limited, BSE code 544994), **BSE** is the authoritative exchange.
- **Verification Rule**: Must fetch successfully over HTTPS, prevent non-official redirects, verify company name in the page title/body, parse the exact opening print ("Open" / "EQ ..."), and persist the complete raw HTML/JSON response under `data/evidence/actuals/<date>_<company-slug>_<sha256>.html` along with a structured manifest `.json`.

### Tier 2: Cloud-Reachable Secondary Ingestion (`yfinance` + Independent Cross-Check)
- **Target**: First-session opening print from `<symbol>.NS` (or `<symbol>.BO` for BSE-only listings) via `yfinance`.
- **Raw Evidence Standard (D-055 lesson)**: The raw response data structure must be serialized and saved to disk alongside the parsed `.json` with an accompanying SHA256 checksum.
- **Strict 1.0% Independent Cross-Check Gate**:
  - A Tier 2 price is **strictly rejected** unless a second, completely independent source (such as Chittorgarh listing results or an exchange announcement parsed independently by code) provides an opening listing price within **1.0%** relative tolerance:
    $$\frac{|\text{Price}_{\text{Tier2}} - \text{Price}_{\text{SecondSource}}|}{\text{Price}_{\text{Tier2}}} \le 0.01$$
  - Both raw values, URLs, access timestamps, and snapshot files must be committed to `data/evidence/actuals/`.
- **Dispute & Fallback Policy**:
  - If no independent second source can be retrieved, or if the relative difference exceeds 1.0%, the pipeline **records nothing** in `predictions/prediction_log.csv`, assigns internal status `PENDING_REVIEW`, and triggers an alert issue.

---

## 3. Immutability & Log Mutation Constraints

1. **Zero Overwrite Rule**: Under no circumstances may an existing outcome (`actual_price`, `actual_gain_pct`) be modified or overwritten once recorded.
2. **Log Column Integrity**: No historical input feature columns in `predictions/prediction_log.csv` may be altered during outcome recording.
3. **Audit Provenance in Notes**: When an outcome is recorded, the `notes` field must append:
   - `outcome_source=tier1` or `outcome_source=tier2`
   - Relative path to the evidence manifest in `data/evidence/actuals/`
4. **Treatment in Final Evaluation**: Rows recorded via Tier 2 are treated identically to Tier 1 in the prospective $n=30$ evaluation dataset, but must be explicitly disaggregated in reporting tables with a dedicated `Source Tier` indicator.

---

## 4. Operational Timing & Alerting Rules

1. **Market Hours Rule (D-069)**: Outcome fetching is attempted only if:
   - `listing_date < today (IST)`, OR
   - `listing_date == today (IST)` AND `IST_time >= 16:00`.
2. **Missing-Outcome Alert (D-067)**:
   - If any `FORWARD` row has `listing_date` older than 2 calendar days from current date and still lacks an `actual_gain_pct`, the daily job and the watchdog workflow (`scripts/watchdog.py`) must open or comment on an active GitHub Issue detailing the affected IPO(s) and last error/status.
3. **Dashboard Visibility (D-070)**:
   - The dashboard must explicitly display the count and company names of listed IPOs awaiting outcomes (`listed, outcome pending: K`).

---

## 5. Statistical Governance & Reporting Constraints

1. **Small-Sample Governance**: Sample size is currently $n = 6$ of 30 target forward predictions (with Jio and Paras pending). All forward metrics are provisional and descriptive.
2. **Wording Prohibitions**: In strict compliance with `PHASE_PROTOCOL.md`, no claims of "superiority", "outperforming", "beating GMP", or "falsification" are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.
