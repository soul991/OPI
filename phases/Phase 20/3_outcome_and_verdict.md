# Phase 20: Outcome & Verdict

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Mandatory Small-Sample Epistemic Guardrail**: Sample size is currently $n = 12$ listed of 30 target forward predictions (1 pending listing outcome verification: Bombay Coated). All metrics and error distributions are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## ERRATA

### 1. Phase 19 Evidence Citations & Run ID Corrections (D-103)
- **Non-Existent Evidence Files**: The Phase 19 chat report quoted evidence files for BLS Polymers and Bombay Coated under `data/evidence/actuals/` (e.g. `2026-11-03_bls-polymers-limited_yfinance_raw.json`) with digest `5e6cbf790be4` and a price of 89.00 for Bombay Coated. No such files existed at Phase 19 close, and the execution logs record only prices 91.0 and 92.02.
- **Pages Deployment Run ID**: The failed GitHub Pages deployment was workflow run `42227803913` (run #79, timeout after 10m52s). Quoted run ID `42190760462` was non-existent (HTTP 404).
- **Event Trigger Inconsistency**: Workflow run `42286425753` was triggered by `schedule`, not `workflow_dispatch`.
- **Cohort MAE Recalculation**: The 11-row forward MAE in Phase 19 was reported as 5.0909 percentage points; recomputation gives **5.0873 percentage points** ($55.96 / 11$).

### 2. Defect Register Status Corrections (D-100 & D-101)
- At Gate A20, D-100 and D-101 were downgraded from FIXED to PARTIAL because arbitration rules and metadata labelling had only been verified on synthetic fixtures without real-world cloud proof.
- Both defects are now definitively resolved and proven in cloud Actions run `42374128672` (commit `a8961d23089fdb1ba6bf19a383200f717700d8bb`), which recorded BLS Polymers as `VERIFIED_TIER2_CROSS_CHECKED` with complete exchange metadata manifests (`data/evidence/actuals/2026-11-03_bls-polymers_683887010e3a.json`).

---

## 1. Prospective Forward Cohort Evaluation (n = 12 of 30)

During Phase 20, BLS Polymers was successfully verified and recorded by GitHub Actions (old $n = 11$, new $n = 12$).

```
======================================================================================
  OPI FORWARD PREDICTION AUDIT & PROSPECTIVE PERFORMANCE REPORT
======================================================================================
Log File Location          : predictions/prediction_log.csv
Total Logged Rows          : 19
Excluded TEST Rows         : 2 (status starting with TEST_*)
Excluded INVALID Rows      : 4 (status starting with INVALID*)
Genuine FORWARD Rows       : 13 (status == 'FORWARD')
Missed FORWARD Rows        : 0 (recorded in predictions/missed_forward.csv)
Tracked Defects Health     : 112 total (102 fixed, 7 accepted, 0 deferred, 2 open/partial, 1 not fixed)
--------------------------------------------------------------------------------------
Evaluated (Listed) Rows    : 12 of 30 target
Pending (Unlisted) Rows    : 1
--------------------------------------------------------------------------------------
[!] PROVISIONAL STATUS BANNER: n listed = 12 of 30
    Per pre-registered rules: no empirical superiority claims or interval comparisons
    are permitted below n = 30 ('n too small'). All metrics are strictly descriptive.
--------------------------------------------------------------------------------------
Provisional Model MAE      : 5.67 percentage points (n=12)
Prior Cohort Model MAE     : 5.85 percentage points (n=9)
Provisional Raw GMP MAE    : 6.15 percentage points (n=7)
--------------------------------------------------------------------------------------
Company                    Listing     Model %   GMP %    Actual %   Err Model  Err GMP
--------------------------------------------------------------------------------------
HD Fire Protect Limited    2026-10-21  +26.12%   +30.3%   +23.39%     2.73 pp     6.87 pp
Fusion CX Limited          2026-10-22   +4.33%     N/A     +5.54%     1.21 pp      N/A
Zetwerk Manufacturing Bus  2026-10-23   -0.77%    +2.3%    +5.46%     6.23 pp     3.14 pp
Sahajanand Medical Techno  2026-10-23   +8.32%    +7.0%    +7.89%     0.43 pp     0.91 pp
Tonbo Imaging India Limit  2026-10-23  +74.70%   +72.9%   +65.71%     8.99 pp     7.15 pp
Bonfiglioli Transmissions  2026-10-23  +21.10%   +21.7%    +0.00%    21.10 pp    21.67 pp
Jio Platforms Limited      2026-10-28  +22.14%   +22.3%   +21.36%     0.78 pp     0.98 pp
Paras Healthcare Limited   2026-10-28   -2.56%    +1.6%    +3.90%     6.46 pp     2.31 pp
M.K.Sons Fine Jewels       2026-11-04   +4.37%     N/A     +5.56%     1.19 pp      N/A
BLS Polymers               2026-11-03  +53.28%     N/A    +65.33%    12.05 pp      N/A
SFC Environmental Technol  2026-11-03   +5.49%     N/A     +7.61%     2.12 pp      N/A
EAAA India Alternatives    2026-11-02   +5.35%     N/A     +0.63%     4.72 pp      N/A

Pending Upcoming IPOs:
  - Bombay Coated & Special Steels: Model +10.14%, GMP +11.3%, P(>10%) 54.4%, Listing: 2026-11-05
======================================================================================
```

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Tier | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.39 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | tier1 | LISTED | Actual opening price verified via BSE |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.01 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | tier1 | LISTED | Actual opening price verified via NSE |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.24 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | tier1 | LISTED | Actual opening price verified via NSE |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.14 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | tier1 | LISTED | Actual opening price verified via NSE |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1159.97 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | tier1 | LISTED | Actual opening price verified via NSE |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | tier1 | LISTED | Actual opening price verified via NSE |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | ₹1358.02 | **+21.36%** | +22.14% | +22.34% | **0.78 pp** | **0.98 pp** | tier2 | LISTED | Actual opening price verified via Yahoo Finance NSE |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | ₹721.00 | **+4.04%** | -2.56% | +1.59% | **6.46 pp** | **2.31 pp** | tier2 | LISTED | Actual opening price verified via Yahoo Finance NSE |
| **M.K.Sons Fine Jewels** | 2026-11-04 | ₹162.00 | ₹171.01 | **+5.56%** | +4.37% | None (NOT_RECORDED) | **1.19 pp** | N/A | tier2 | LISTED | Actual opening price verified via Yahoo Finance NSE |
| **BLS Polymers** | 2026-11-03 | ₹150.00 | ₹248.00 | **+65.33%** | +53.28% | None (NOT_RECORDED) | **12.05 pp** | N/A | tier2 | LISTED | Actual opening price verified via Yahoo Finance NSE and Chittorgarh NSE |
| **SFC Environmental Technologies** | 2026-11-03 | ₹330.00 | ₹355.11 | **+7.61%** | +5.49% | None (NOT_RECORDED) | **2.12 pp** | N/A | tier2 | LISTED | Actual opening price verified via Yahoo Finance NSE |
| **EAAA India Alternatives** | 2026-11-02 | ₹1665.00 | ₹1675.49 | **+0.63%** | +5.35% | None (NOT_RECORDED) | **4.72 pp** | N/A | tier2 | LISTED | Actual opening price verified via Yahoo Finance NSE |
| **Bombay Coated & Special Steels** | 2026-11-05 | ₹82.00 | Pending | Pending | +10.14% | +11.28% | Pending | N/A | tier2 | FORWARD | Status: SKIPPED_NO_MATCH (first bar is 2026-11-06) |

### Read-Only Exchange Policy Audit of All 12 Forward Outcomes
All 12 completed forward listings in `predictions/prediction_log.csv` were audited against their committed snapshots and manifests under `data/evidence/actuals/`:
- **11 Dual-Listed IPOs**: Fusion CX, Zetwerk, Sahajanand, Tonbo, Bonfiglioli, Jio Platforms, Paras Healthcare, M.K.Sons, BLS Polymers, SFC Environmental, EAAA India Alternatives. All 11 recorded opening prices match the **NSE first-session open** (`.NS` or `nseindia.com`).
- **1 Sole BSE Listing**: HD Fire Protect Limited (listed only on BSE). Its recorded opening price matches the **BSE first-session open** (`bseindia.com`).
- **Result**: Exactly 0 discrepancies across all 12 recorded outcomes; 100% compliance with the pre-registered Primary Exchange Policy.

---

## 2. Cloud Autopilot Verification

Phase 20 established autonomous cloud execution verified across multiple GitHub Actions runs:

1. **Pending Evidence Persistence (D-104)**:
   - Run ID: `42355211506` (`daily.yml`, commit `84fa7bfee3552727bcd31735c27a0f77ff131c14`).
   - Bot committed pending evidence in commit `1fa80333404fae4cf9dc0fa83a2ae5db69078760`:
     - `data/evidence/actuals/pending/2026-11-03_bls-polymers_chittorgarh.html`
     - `data/evidence/actuals/pending/2026-11-03_bls-polymers_yahoo-finance.json`
     - `data/evidence/actuals/pending/2026-11-03_bls-polymers.manifest.json`
2. **Outcome Verification & Defect Resolution (D-100, D-101, D-112)**:
   - Run ID: `42374128672` (`daily.yml`, commit `b3e9153870303de0c93a336478c3a4c4825fcb0d`).
   - Bot committed verified outcome in commit `a8961d23089fdb1ba6bf19a383200f717700d8bb`:
     - `data/evidence/actuals/2026-11-03_bls-polymers_683887010e3a.json`
     - `data/evidence/actuals/2026-11-03_bls-polymers_683887010e3a.txt`
     - Resolved BLS Polymers with opening price ₹248.00 (65.33% gain) with 0.0% difference between Yahoo Finance NSE and Chittorgarh NSE.
3. **Dashboard Deployment**:
   - Run ID: `42374524596` (`pages build and deployment` on commit `a8961d23089fdb1ba6bf19a383200f717700d8bb`, success).
   - Live URL: `https://soul991.github.io/OPI/dashboard/`.

---

## 3. Targets Missed & Unfixed Items

Per `PHASE_PROTOCOL.md`, all non-FIXED defects are explicitly accounted for:

1. **D-013 (Historical Phase 7 Audit Samples Lack Snapshots)**:
   - **Status**: `PARTIAL`.
   - **Reason**: 20 historical audit samples from Phase 7 route to 404s or wrong SME entities on Chittorgarh; re-scraping remains blocked by site permissions. Project rules forbid inventing synthetic data.
2. **D-026 (Live Web Research Agent Cloud Proof)**:
   - **Status**: `NOT FIXED`.
   - **Reason**: The research agent is integrated into `opi/run_daily.py` with numeric input sanitization (D-111) and visible alerting. Awaiting a newly discovered unrecorded IPO in scheduled cloud execution.
3. **D-096 (Automate Tier 2b Dual-Source Outcome Verification)**:
   - **Status**: `PARTIAL`.
   - **Reason**: Automated Tier 2b dual-source fallback logic is implemented; awaits a live production case where Yahoo is delayed but two independent non-Yahoo sources are present.

All defects registered or touched in Phase 20 (D-100, D-101, D-103, D-104, D-105, D-106, D-107, D-108, D-109, D-110, D-111, D-112) are **FIXED**.

---

## 4. Phase 20 Final Verdict

**Verdict**: **ACCEPT - PHASE 20 COMPLETE**.
- The record of Phase 19 is corrected in `phases/Phase 19/3_outcome_and_verdict.md`.
- Diverging and stuck outcomes now persist raw pages and manifests under `data/evidence/actuals/pending/` and resolve via strict exchange-consistent parsing.
- BLS Polymers was recorded in production by GitHub Actions without manual intervention.
- The system is now an autonomous cloud autopilot:
  - Versioned prospective predictions are recorded in `predictions/model_versions.csv`.
  - Monthly retraining runs in GitHub Actions, registers new candidate models as `shadow` in `model/registry.json`, and direct-pushes verified artifacts.
  - Pre-registered prospective promotion rules are automated and logged to `model/promotions_log.csv`.
  - Honest alerts notify on overdue outcomes without false job failures.
  - The public dashboard tracks autopilot health, model registry, promotion history, cumulative MAE, and rolling-5 MAE.
