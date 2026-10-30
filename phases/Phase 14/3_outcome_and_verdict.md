# Phase 14: Outcome & Verdict

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Mandatory Small-Sample Epistemic Guardrail**: Sample size is currently $n = 8$ of 30 target forward predictions. All metrics and error distributions are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## 1. Targets Missed & Unfixed Items

1. **Unfixed Defect D-026 (Research Agent Scheduled Proof)**:
   - **Status**: Kept `NOT FIXED` awaiting a real upcoming IPO during an active bidding cycle in a scheduled run.
   - **Reason**: Per explicit project rules, no synthetic or fake IPOs may ever be created to artificially force a fix. Bidding for new upcoming Mainboard IPOs had not opened during this maintenance cycle.
2. **Defect D-071 (Dashboard Card & verify_all NOT FIXED count)**:
   - **Status**: `PARTIAL (needs user action)`.
   - **Reason**: The dashboard generator (`opi/report.py`) and renderer were updated to correctly count `OPEN + PARTIAL + NOT FIXED` (verified by `tests/test_dashboard.py::test_dashboard_counts_not_fixed_defects`). Modifying `scripts/verify_all.py` to count NOT FIXED items is strictly prohibited by project rules ("Do not edit scripts/verify_all.py, scripts/verify_extra.py or scripts/verify_pages.py to make a check pass"). Therefore, the `verify_all.py` portion is marked `PARTIAL (needs user action)`.
3. **Targets Missed**: None. All scheduled deliverables (Gate A14, preregistration, Workstreams A–D, runner reachability probe, automated two-tier outcome engine, missing outcome alerts, maintainer runbook, and live recording of Jio Platforms and Paras Healthcare) were successfully executed and verified.

---

## 2. Defect Ledger

| Defect ID | Phase Seeded | Summary Description | Severity | Final Status | Closed Phase | Verification Proof / Test Name |
|---|:---:|---|:---:|:---:|:---:|---|
| **D-026** | 7 | Real scheduled cloud research run with live OpenRouter model not proven on a new IPO. | Medium | **NOT FIXED** | — | Awaiting next real upcoming IPO bidding cycle; no mock IPOs permitted. |
| **D-066** | 14 | `opi/run_daily.py` logs `SKIPPED_BLOCKED_SOURCE` for listed IPOs without attempting fetch. | Medium | **FIXED** | 14 | `tests/test_actuals_job.py::test_tier2_success_with_agreeing_second_source` |
| **D-067** | 14 | No alert when a listed row has an empty outcome for >2 calendar days. | Medium | **FIXED** | 14 | `tests/test_watchdog.py::test_missing_outcomes_threshold_boundary` |
| **D-068** | 14 | No outcome source known to be reachable from cloud runners; reachability never measured. | Medium | **FIXED** | 14 | `tests/test_actuals_job.py::test_two_tier_probe_committed` |
| **D-069** | 14 | Daily job compared only dates; could not determine if listing-day market session concluded. | Low | **FIXED** | 14 | `tests/test_actuals_job.py::test_is_listing_ready_for_actuals_market_hours_rule` |
| **D-070** | 14 | Dashboard showed "N of 30" but omitted count and names of listed rows awaiting outcomes. | Low | **FIXED** | 14 | `tests/test_dashboard.py::test_dashboard_shows_listed_outcome_pending_count_and_names` |
| **D-071** | 14 | Dashboard card and verify_all.py count only OPEN and PARTIAL, omitting NOT FIXED (D-026). | Low | **PARTIAL** | 14 | `tests/test_dashboard.py::test_dashboard_counts_not_fixed_defects` (verify_all part needs user action) |

---

## 3. Forward Table from `forward_report.py --markdown`

```text
| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.00 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | LISTED | NSE official opening trade evidenced in snapshot `1ef0c35a650c` |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.25 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | LISTED | NSE official opening trade evidenced in snapshot `0783e1c0985b` |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.15 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | LISTED | NSE official opening trade evidenced in snapshot `d69406a6b7e8` |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1160.00 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | LISTED | NSE official opening trade evidenced in snapshot `4c486eeb1b8d` |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | LISTED | NSE official opening trade evidenced in snapshot `6df55c3addef` |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | ₹1358.02 | **+21.36%** | +22.14% | +22.34% | **0.78 pp** | **0.98 pp** | LISTED | Closed 2026-10-23; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-10-28 | Actual opening price verified via https://finance.yahoo.com/quote/JPL.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.txt |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | ₹721.00 | **+4.04%** | -2.56% | +1.59% | **6.60 pp** | **2.45 pp** | LISTED | Closed 2026-10-23; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-10-28 | Actual opening price verified via https://finance.yahoo.com/quote/PARASHLTH.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-10-28_paras-healthcare-limited_fe823e2ba992.txt |
```

---

## 4. Gate A14 Results with Pasted Outputs

### G1: `python scripts/verify_all.py`
```text
SUMMARY: 68 pass, 0 warn, 0 fail
```

### G2: `python scripts/verify_extra.py`
```text
[PASS] subscription figures in Phase 11+ reports equal prediction_log values                    0 mismatches
[PASS] no company other than HD Fire cites BSE code 544994                                      0 lines
[PASS] no hard-coded dated numeric constants in scripts/ or opi/                                0 lines
[PASS] each listed date has a parsed Nifty evidence file (close + prev close or day return)     missing: none
[PASS] no 'weak/only/subdued demand' text for IPOs with QIB > 50x                               0 lines
[PASS] README's two champion coverage figures (91.2% vs 87.94%) are reconciled in text          
[PASS] no OpenRouter key material in tracked files                                              

SUMMARY: 7 pass, 0 warn, 0 fail
```

### G3: `python scripts/ci_local.py`
```text
=== daily job: -m opi.run_daily
[PASS] daily job

=== pytest: -m pytest -q
[PASS] pytest (184 passed, 1 skipped, 1 warning)

=== verify_all: scripts/verify_all.py
[PASS] verify_all

CI_LOCAL: PASS
```

### G4: Prior Phase Claim Recheck (Seed 14) & Headline Recomputations
All 10 randomly sampled claims from Phase 13 and all 5 headline metrics recomputed directly from `predictions/prediction_log.csv` and `data/ipo_master.csv` with zero discrepancies (`phases/Phase 14/prior_phase_recheck.csv`).

### G5: Secret Scanning & Credentials Check
`gh secret list` shows `OPENROUTER_API_KEY`.  
`git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches across all tracked files.

---

## 5. Cloud Probe Results & Outcome Chain

- **Workflow Run**: `.github/workflows/probe_sources.yml` run `41038115389` (Ubuntu 24.04).
- **Automated Daily Run**: `.github/workflows/daily.yml` run `41038093115`.
- **Reachability Findings**:
  - Official Exchange APIs (`nseindia.com`, `api.bseindia.com`): Returned **HTTP 403** (Akamai/Cloudflare WAF) when accessed from cloud runners.
  - Secondary Channel (`yfinance` via `query1.finance.yahoo.com`): Returned **HTTP 200** with full price history.
  - Independent Secondary Source (`chittorgarh.com` quote/listing tables): Returned **HTTP 200** with parsed opening prices.
- **Implemented Two-Tier Chain**:
  1. **Tier 1 (Official Exchange Direct Scrape)**: Evaluated first. If reachable with HTTP 200, parsed with redirect protection.
  2. **Tier 2 (Cloud Fallback with 1.0% Cross-Check)**: `yfinance` first-session open validated against Chittorgarh listing results. The price is rejected and kept `PENDING_REVIEW` unless the relative difference is strictly $\le 1.0\%$.

---

## 6. Jio Platforms & Paras Healthcare Outcomes & Metrics

### Recorded Listing Outcomes
1. **Jio Platforms Limited** (Listed 2026-10-28):
   - Issue Price: ₹1,119.00
   - Official Opening Price: ₹1,358.00
   - Actual Listing Gain: **+21.36%**
   - Model Prediction: **+22.14%** (Error: **0.78 pp**)
   - Pre-Listing GMP: **+22.34%** (GMP Error: **0.98 pp**)
   - Evidence Manifest: `data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.json`
   - Raw Snapshot: `data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.txt`
   - SHA-256: `679a4ce1c8e3439091413ac7885a41710d71609799e8908e89e715439a3fae33`
   - Source Tier: `tier2` (yfinance `JPL.NS` Open ₹1,358.00 vs Chittorgarh ₹1,358.00; diff: 0.00%)
2. **Paras Healthcare Limited** (Listed 2026-10-28):
   - Issue Price: ₹693.00
   - Official Opening Price: ₹721.00
   - Actual Listing Gain: **+4.04%**
   - Model Prediction: **-2.56%** (Error: **6.60 pp**)
   - Pre-Listing GMP: **+1.59%** (GMP Error: **2.45 pp**)
   - Evidence Manifest: `data/evidence/actuals/2026-10-28_paras-healthcare-limited_fe823e2ba992.json`
   - Raw Snapshot: `data/evidence/actuals/2026-10-28_paras-healthcare-limited_fe823e2ba992.txt`
   - SHA-256: `fe823e2ba99201f8ee96f4c7bb0bdae05a819b5c3ca57e5fa57d00f86235b3e2`
   - Source Tier: `tier2` (yfinance `PARASHLTH.NS` Open ₹721.00 vs Chittorgarh ₹721.00; diff: 0.00%)

### Error Metrics Breakdown (Computed from `predictions/prediction_log.csv`)
- **Overall Prospective Model MAE ($n=8$ listed)**: **6.01 pp**
- **GMP Availability Subset ($n=7$ with GMP)**:
  - Model MAE: **6.69 pp**
  - Raw GMP MAE: **6.17 pp**
- **Excluding Outlier Shock Row ($n=7$, excluding Bonfiglioli Transmissions 21.10 pp)**:
  - Model MAE: **3.85 pp**

### Epistemic Wording Rule Adherence
Sample size is $n = 8 < 30$. In compliance with preregistered protocol, all forward track record figures are descriptive. No causal conclusions, claims of "beating GMP", or assertions of generalizable statistical superiority are made.

---

## 7. Self-Audit (Pasted Command Output)

| Self-Audit Question | Verdict | Pasted Verifying Evidence |
|---|:---:|---|
| Did any report number come from anywhere but a script over the log or evidence? | **NO** | `python scripts/forward_report.py --markdown` and pandas verification script confirm exact values. |
| Did any summary line claim a file changed when `git diff --stat` shows otherwise? | **NO** | Verified against `git diff --stat` before each commit. |
| Did any earlier-phase file change except by ERRATA? | **NO** | `[PASS] earlier-phase artifacts unchanged since phase14-gate-a` in `verify_all.py`. |
| Was any outcome recorded without a saved real response? | **NO** | Evidence manifests and raw response hashes exist in `data/evidence/actuals/` for every row. |
| Did the work stop after the gate? | **YES** | Stopped after Gate A14 and preregistration; waited for user "continue". |
| Was the key kept out of the repo, logs, issues, and snapshots? | **YES** | `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. |

---

## 8. Handover State: Autonomous Cloud Operations

The OPI platform now runs completely unattended in GitHub Actions cloud runners:
1. **Twice-Daily Forward Pipeline (`daily.yml`)**:
   - Runs at 06:00 UTC (11:30 IST) and 14:00 UTC (19:30 IST, post-bidding close).
   - Discovers newly closed IPOs, extracts grounded features, predicts listing gains, and logs prospective predictions.
   - Automatically executes the two-tier listing outcome recording engine for listed IPOs with $\le 1.0\%$ cross-checks.
   - Runs full test suite (`pytest -q`) and verification suite (`verify_all.py`).
   - Automatically commits and pushes updated predictions, evidence snapshots, and regenerated dashboard.
2. **Automated Alerting**:
   - If any workflow step fails, an alert issue is automatically created or updated in GitHub Issues (`scripts/manage_alerts.py`).
   - Open alert issues automatically close upon the next successful green run.
   - If any listed IPO outcome remains unrecorded for >2 calendar days, Step 4 of the daily job and Check (d) of the watchdog fail immediately and raise an alert issue.
3. **Daily Health Watchdog (`watchdog.yml`)**:
   - Runs daily at 10:00 UTC.
   - Audits scheduled run freshness (<36h), live dashboard freshness (<36h), OpenRouter free model availability, and missing outcomes (>2d).
   - Generates keepalive heartbeat commit at most once every 30 days to prevent GitHub 60-day schedule pauses.
4. **Maintainer Documentation**:
   - Production operations, recovery flows, model rotations, and runbook checklists are documented in [`docs/RUNBOOK.md`](../../docs/RUNBOOK.md).
