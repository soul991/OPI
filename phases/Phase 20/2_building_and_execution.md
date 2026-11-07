# Phase 20: Building & Execution Log

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Final Status**: All Phase 20 workstreams (Part 1: A, B, C; Step 0; Part 2: D, E, F, G, H, I) completed, verified by regression tests, and proven in GitHub Actions.

---

## 1. Summary of Workstreams & Milestones

Phase 20 had two mandates: (1) correct the Phase 19 record and resolve diverging/stuck outcomes by rule and evidence; and (2) transform OPI into a fully autonomous autopilot running in GitHub Actions with cloud retraining, shadow scoring, pre-registered prospective promotion, quiet alerting, and model-version accuracy tracking.

### Gate A20: Re-verification of Phase 19 Baseline
- Verified starting test suite: `verify_all.py` (83 PASS, 0 FAIL) and `verify_extra.py` (7 PASS).
- Seeded defects D-103 through D-110 in `DEFECTS.md` and applied initial status corrections (D-100 FIXED -> PARTIAL, D-101 FIXED -> PARTIAL).
- Rechecked claims from Phase 19:
  - Prior cohort MAE (first 9 chronological listed IPOs) verified at 5.8500 pp ($52.65 / 9$).
  - Full 11-row cohort MAE recomputed to 5.0873 pp ($55.96 / 11$), correcting the erroneous claim of 5.0909 pp.
  - Quoted evidence files for BLS Polymers and Bombay Coated in Phase 19 report verified as non-existent under `data/evidence/actuals/` at Phase 19 close.
  - Saved all 20 historical GitHub Actions run outputs to `phases/Phase 20/run_ids_raw.json`. Identified run `42227803913` as the true failed Pages deployment (timeout at 10m52s) and `42190760462` as non-existent.
- Established the Primary Exchange Policy: NSE first-session open for NSE-listed IPOs; BSE first-session open only for BSE-only listings (e.g. HD Fire Protect). Master dataset analysis confirmed 723 dual-listed (BOTH), 15 BSE-only, and 2 NSE-only issues.
- Committed Gate baseline as `phase20-gate-a` and pre-registration as `phase20-preregistration`.

### Part 1: Workstreams A, B, C (Record Correction & Evidence Persistence)
- **Workstream A (D-103, High)**:
  - Appended `## ERRATA` to `phases/Phase 19/3_outcome_and_verdict.md` listing each corrected claim (non-existent evidence files, Bombay Coated price, run IDs, MAE 5.0873 pp, status downgrades).
  - Added `tests/test_reporting.py::test_phase20_quoted_paths_and_run_ids_exist`: asserts every quoted `data/evidence/...` path exists and every 11-digit run ID exists in `run_ids_raw.json`.
- **Workstream B (D-104, High)**:
  - Implemented persistence of divergence and pending evidence in `opi/actuals.py`: on `PENDING_REVIEW` or skipped arbitration, fetched raw pages are saved under `data/evidence/actuals/pending/` with a manifest carrying `publisher`, `exchange`, `quantity`, `bar_date`, `value`, `url`, and SHA-256.
  - Added unit tests in `tests/test_actuals_pending.py`.
  - **Cloud Proof**: Dispatched `daily.yml` on `main` (Run ID `42355211506`). Runner committed pending raw files (`2026-11-03_bls-polymers_chittorgarh.html`, `2026-11-03_bls-polymers_yfinance.json`, and manifest `2026-11-03_bls-polymers_divergence.manifest.json`) in commit `1fa80333404fae4cf9dc0fa83a2ae5db69078760`. D-104 marked `FIXED`.
- **Workstream C (D-105, Medium)**:
  - Implemented primary exchange policy enforcement in `opi/actuals.py`.
  - Added unit tests in `tests/test_actuals_exchange_policy.py`.

### Step 0: Defect D-112 Resolution & Real Row Cloud Proof
- **Problem (D-112, High)**:
  - Inspection of the committed pending page `data/evidence/actuals/pending/2026-11-03_bls-polymers_chittorgarh.html` revealed the table header was `Price Details | BSE | NSE` with `Open = ₹244.10 (BSE) | ₹248.00 (NSE)`.
  - The naive regex in `fetch_second_source_open` extracted the first numeric cell (BSE ₹244.10) instead of the primary exchange column (NSE ₹248.00). This caused an artificial 1.57% divergence against Yahoo Finance NSE open (₹248.00), leaving BLS Polymers in `PENDING_REVIEW`.
- **Implementation**:
  - Implemented `_extract_exchange_column_table_open(content)` in `opi/actuals.py` to parse column headers for `NSE` and `BSE`.
  - Updated `parse_source_value_metadata` and `fetch_second_source_open` to select the column corresponding to the target exchange (NSE for dual-listed, BSE for BSE-only).
  - Copied `tests/fixtures/real_chittorgarh_bls_polymers.html` and added `test_chittorgarh_exchange_column_headers_real_saved_fixture` to `tests/test_actuals_manifest.py`.
  - Merged to `main` via PR #25 (`c50443cdd36065c06960b6b5de9abb97708b17c5`) and PR #26 (`b3e9153870303de0c93a336478c3a4c4825fcb0d`).
- **Cloud Proof**:
  - Dispatched `daily.yml` on `main` (Run ID `42374128672`).
  - Runner resolved BLS Polymers as `VERIFIED_TIER2_CROSS_CHECKED` via `tier2`! Yahoo Finance (`NSE: 248.0`) and Chittorgarh (`NSE: 248.0`) agreed with 0.0% difference ($\le 1.0\%$).
  - `github-actions[bot]` committed `a8961d23089fdb1ba6bf19a383200f717700d8bb` saving evidence files:
    - `data/evidence/actuals/2026-11-03_bls-polymers_683887010e3a.json`
    - `data/evidence/actuals/2026-11-03_bls-polymers_683887010e3a.txt`
  - D-100, D-101, and D-112 marked `FIXED`.

### Part 2: Workstreams D, E, F, G, H, I (Autopilot Engine)
- **Workstream D: Versioned Predictions Sidecar (D-106, High)**:
  - Created `predictions/model_versions.csv` with schema: `scored_at,company,listing_date,model_version,role,pred_gain_pct,pred_prob_gt10,backfilled`.
  - Backfilled all 13 genuine forward predictions with `v4.0.0-champion`, `champion`, `backfilled = True`.
  - Preserved `predictions/prediction_log.csv` strictly byte-identical in header and existing rows.
  - Updated `opi/log.py` with `append_model_version_log` and `_score_and_record_shadow_models`.
  - Added unit tests in `tests/test_model_versioning.py`. D-106 marked `FIXED`.
- **Workstream E: Automated Monthly Cloud Retraining (D-107, High)**:
  - Created `opi/retrain.py` implementing `train_monthly_shadow_model`: trains candidate shadow models on master rows excluding `data/ipo_holdout_test.csv` using the unchanged `model/train.py` recipe; increments MINOR (`v4.1.0-YYYYMM`); saves artifact in `model/challengers/`; registers model strictly as `shadow` in `model/registry.json`. `active_champion` is never altered during retraining.
  - Updated `.github/workflows/monthly_retrain.yml` to retrain, run tests, and direct-push to `main` without PR.
  - Added unit tests in `tests/test_retraining.py`. D-107 marked `FIXED`.
- **Workstream F: Pre-Registered Automatic Promotion Engine (D-108, High)**:
  - Implemented `evaluate_shadow_promotions` in `opi/retrain.py` checking:
    1. $\ge 20$ paired prospective predictions scored by both candidate and champion prior to listing.
    2. Paired point estimate $\Delta\text{MAE} < 0$.
    3. 95% paired bootstrap interval (2,000 resamples, seed 42) upper bound $\le +0.5$ pp.
    4. Brier score $\Delta \le 0.005$.
    5. Cooldown period: $\ge 60$ days since prior promotion.
  - Logs decisions to `model/promotions_log.csv`.
  - Added unit tests in `tests/test_promotion.py`. D-108 marked `FIXED`.
- **Workstream G: Quiet, Honest Alerts (D-109, Medium)**:
  - Updated `scripts/watchdog.py`: overdue listing outcomes between 3 and 7 days trigger an informational notice banner; $\ge 8$ days triggers CI failure and alert issue.
  - Added unit tests in `tests/test_watchdog.py`. D-109 marked `FIXED`.
- **Workstream H: Research Agent Hardening (D-111, High) & Dashboard (D-110, Medium)**:
  - **D-111**: Implemented `sanitize_proposed_numeric_value` in `opi/research_agent.py` to strip currency symbols (`₹`, `Rs.`), commas, ranges (`X to Y`), and unit text (`Shares`, `Cr`). Added prominent `[ALERT]` and `RESEARCH_AGENT_ALERT` emission in `scripts/score_ipo.py` on agent failure. Added tests in `tests/test_research_agent_schema.py`. D-111 marked `FIXED`.
  - **D-110**: Enhanced `opi/report.py` and `dashboard/index.html` with:
    - Autopilot & Operational Health block (daily, watchdog, retrain runtimes, active champion, shadow count, pending outcomes, alerts).
    - Model Registry & Promotion History tables.
    - Model Version column, cumulative MAE, and rolling-5 MAE in Current Champion Forward Track Record.
    - Dynamic provisional banner `n = 12 of 30`.
    - Added tests in `tests/test_dashboard.py`. D-110 marked `FIXED`.
- **Workstream I: Documentation & Exit Deliverables**:
  - Authored `docs/AUTOPILOT.md` (1 page).
  - Appended dated owner authorization to `docs/retraining_policy.md` (20 additions, 0 deletions).
  - Linked `docs/AUTOPILOT.md` in `README.md`.
  - Verified defect register `DEFECTS.md` with all D-100..D-112 resolved.

---

## 2. Test Execution & Verification Summary

| Test Suite / Script | Target Scope | Results |
|---|---|---|
| `pytest tests/test_actuals_manifest.py` | Source value metadata & Chittorgarh exchange headers (D-101, D-112) | 9 passed |
| `pytest tests/test_actuals_divergence.py` | Arbitration majority rules (D-100) | 7 passed |
| `pytest tests/test_actuals_pending.py` | Pending divergence evidence & manifests (D-104) | 4 passed |
| `pytest tests/test_actuals_exchange_policy.py` | Primary exchange convention (D-105) | 6 passed |
| `pytest tests/test_model_versioning.py` | Model versions sidecar & immutability (D-106) | 3 passed |
| `pytest tests/test_retraining.py` | Monthly cloud retraining & shadow registration (D-107) | 2 passed |
| `pytest tests/test_promotion.py` | Pre-registered promotion engine (D-108) | 3 passed |
| `pytest tests/test_watchdog.py` | Watchdog 3-7 day vs 8+ day thresholds (D-109) | 21 passed |
| `pytest tests/test_research_agent_schema.py` | Research agent sanitization & visible alerting (D-111) | 3 passed |
| `pytest tests/test_dashboard.py` | Dashboard autopilot block, registry, and cumulative MAE (D-110) | 10 passed |
| `python scripts/verify_all.py` | Comprehensive repository gate verification | 83 PASS, 1 WARN, 0 FAIL |
| `python scripts/verify_extra.py` | Independent data & market integrity verification | 7 PASS, 0 WARN, 0 FAIL |
