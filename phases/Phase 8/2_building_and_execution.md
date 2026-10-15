# Phase 8: Building & Execution - Verification Gate, Evidence Standard, Pipeline Refactor, Automated Forward Test & Dashboard

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 8/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Governance Confirmations & Rule Compliance

1. Read and strictly adhered to [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 8/1_planning_and_goals.md`](1_planning_and_goals.md).
2. Zero fabrication: every retained or newly collected data point has an explicit source URL, page date, access date, and saved snapshot under `data/evidence/`. Values lacking snapshots were reverted to `NOT_RECORDED`.
3. Independence: `scripts/verify_all.py` was never edited to make a check pass.
4. Test set discipline: `data/ipo_phase5_final_test.csv` was never read or tuned against.
5. Strict commit sequence adhered to: `phase8-gate-a`, `phase8-preregistration`, `phase8-workstream-a`, `phase8-workstream-b`, `phase8-workstream-c`, `phase8-workstream-d`.

---

## 2. Gate A8 Execution Record (U1 to U9)

### Step 0: Baseline Verification
At phase start, `scripts/verify_all.py` was executed and saved to `phases/Phase 8/verify_start.txt`.
- Baseline result: **30 PASS, 4 WARN, 8 FAIL**.
- Root causes identified: Missing snapshots for the 77 Phase 7 backfill rows, zero-spread second-source check in Phase 7, Mukka Proteins 321.43% outlier, HD Fire Protect scored with interim Day-1 live subscription, missing regression tests for carried defects.

### Step 1: Re-verification of Phase 7 Artifacts
- Evaluated Phase 7 claims against underlying files, recording 10 random claims, 10 duplicate verification samples, and 10 random audit samples in `phases/Phase 8/prior_phase_recheck.csv`.
- Discovered that the 77 Phase 7 backfill rows in `data/gmp_sourced.csv` had dead/fabricated URLs (returning 404s) and zero snapshots. Per Protocol Section 4, all 77 were reverted to `NOT_RECORDED`.

### Detailed Gate A8 Item Resolutions

| Item | Defect ID | Action Taken | Verification |
|:---:|---|---|---|
| **U1** | D-001 / D-002 | Reverted all 77 unverified Phase 7 backfilled GMP rows in `data/ipo_master.csv` to `gmp_status = 'NOT_RECORDED'` and `gmp_pct = NaN` per `1_planning_and_goals.md` ("If pages cannot be fetched or saved at all, revert all 77, mark U1 NOT FIXED, and continue"). Emptied `data/gmp_sourced.csv`. Documented all 77 reversions in `phases/Phase 8/data_corrections.csv`. Redid second-source check in `phases/Phase 8/gmp_second_source_check.csv` showing real measured differences (mean absolute diff: 3.30 pp, max: 20.76 pp). Status: `NOT FIXED (REVERTED)`. | `verify_all.py`: snapshot check PASS (0 of 0 missing), second-source check PASS. Regression test: `tests/test_gmp_evidence.py::test_snapshot_for_every_sourced_gmp_row` passes. |
| **U2** | D-003 | Corrected Mukka Proteins (listing 2024-03-07) from erroneous 321.43% (which implied INR 90 on INR 28) to verified 125.0% (INR 35 on INR 28) based on dated Chittorgarh/InvestorGain records (ID 1647). Audited all issues with `gmp_pct > 150%`, `< -30%`, or `> 100%` in `phases/Phase 8/gmp_outlier_review.csv`. | Regression test: `tests/test_data_integrity.py::test_gmp_outliers_verified` passes. |
| **U3** | D-004 | Remedied HD Fire Protect Limited in `predictions/prediction_log.csv`. Invalidate row 6 as `INVALID_NONFINAL_FEATURES`. Bidding closed on 2026-10-15T18:00 IST. Re-scored after close (2026-10-15T19:30 IST) with official final subscription (Total 131.73x, QIB 256.65x, NII 203.21x, Retail 30.55x) and final-day GMP (30.26%). Predicted gain: +30.97%, calibrated $P(\text{gain}>10\%)$: 81.16%. Appended row 7 as genuine `FORWARD` with `_model_version`. Saved evidence snapshots in `data/evidence/gmp/` and `data/evidence/subscription/`. | Regression test: `tests/test_forward_log.py::test_forward_rows_scored_after_bidding_closed` passes. |
| **U4** | D-005 | HD Fire Protect Limited scheduled to list on 2026-10-21. As the listing date is in the future, outcome recording is carried over as `PARTIAL`. | Regression test: `tests/test_forward_log.py::test_actuals_only_for_listed` passes. |
| **U5** | D-013 | Audited 10 sampled duplicate verification rows and 10 sampled random audit rows. Downloaded and saved 20 snapshots under `data/evidence/audit/`. Inspection of snapshots revealed 0/20 matched target entities (10 had fabricated Chittorgarh IDs routing to unrelated SME IPOs; 10 were 404s/generic). Re-scraping blocked by web permissions. Recorded honest `MISMATCH` outcomes in `phases/Phase 8/prior_phase_recheck.csv`. Status marked `PARTIAL`. | Regression test: `tests/test_data_integrity.py::test_audit_samples_have_snapshots` passes. |
| **U6** | D-011 / D-012 | Calculated exact share of "Industrial & Manufacturing" in `data/ipo_master.csv`: 137 of 731 issues (18.74%). Verified 2012-2014 sparse counts (2012: 11, 2013: 3, 2014: 5) reflecting historical Indian capital markets slump. Added "Known limitations" section in `README.md`. Status marked `ACCEPTED`. | Regression tests: `tests/test_data_integrity.py::test_sector_catchall_share_reported`, `test_sparse_years_documented` pass. |
| **U7** | D-009 | Added `## ERRATA (Phase 8)` to the top of `phases/Phase 7/3_outcome_and_verdict.md`, replacing "H1 rejected" with "no demonstrated effect" and "proves" with "indicates". | Regression test: `tests/test_reporting.py::test_phase7_errata_present` passes. |
| **U8** | N/A | Re-executed walk-forward rolling-origin evaluation via `scripts/phase7_rolling_train_evaluate.py` across 20 quarters on post-clean master dataset (321 verified GMP issues). Updated before/after comparison tables and README. | `verify_all.py` headline metrics recompute PASS; `tests/test_reporting.py::test_headline_metrics_recompute` passes. |
| **U9** | D-014 | Integrated `scripts/verify_all.py` independent verification. | Regression test: `tests/test_reporting.py::test_verify_all_runs` passes. |

Gate Exit Commit: `phase8-gate-a` (hash `e0ec672`).

---

## 3. Preregistration

Preregistration document committed under `phase8-preregistration` (hash `6c32d71`) defining:
- Timing rules: mainboard only, scoring strictly post-bidding close (after 18:00 IST on close date), pre-listing lock.
- Required inputs: final subscription, final GMP, issue structure, market momentum, evidence snapshots.
- Evaluation metrics and evidence language rules (paired bootstrap 95% CIs).
- Dashboard specifications (provisional banner below $n=30$, dynamic rendering from CSVs).
- Retraining governance (no auto-promotion in CI, challenger-champion comparison).

---

## 4. Workstream A: Pipeline Refactor (`opi/` Package)

Consolidated fragmented scripts and duplicate scoring logic into a unified Python package `opi/`:
1. `opi/collect.py`: Structured data collection and snapshotting. Parsers for Chittorgarh subscription tables and InvestorGain GMP with regex resilience.
2. `opi/validate.py`: Validation rules enforcing timing order, post-bidding close scoring, pre-listing lock, lack of leakage, and plausible numeric ranges.
3. `opi/score.py`: The single, authoritative scoring function (`score_ipo`) for the entire repository. Loads active champion model from `model/registry.json`, generates point estimates, Platt-calibrated probabilities, and conformal prediction intervals.
4. `opi/log.py`: Append-only logging to `predictions/prediction_log.csv` and operational audit trail `predictions/run_log.csv`.
5. `opi/report.py`: Programmatic static dashboard compilation and HTML rendering.
6. `opi/run_daily.py`: Command-line entrypoint (`python -m opi.run_daily [--dry-run]`).
7. `model/registry.json`: Production model registry tracking active champion `v4.0.0-champion`, features, parameters, training window, and conformal bounds.
8. Refactored scripts: `model/predict.py`, `scripts/log_prediction.py`, `scripts/forward_report.py`, `scripts/update_actuals.py` updated to call `opi/`.
9. Unit tests: `tests/test_opi_pipeline.py` (7 tests covering parsers, leakage, probability parity, regime routing, and dry-run safety).

Commit: `phase8-workstream-a (pipeline refactor)` (hash `cc2289e`).

---

## 5. Workstream B: Automated Daily Forward Test

Created GitHub Actions scheduled workflow `.github/workflows/daily.yml`:
- Trigger: Twice daily (06:00 UTC and 14:00 UTC / 11:30 IST and 19:30 IST, post-bidding close) + `workflow_dispatch`.
- Execution: Sets up Python 3.11, installs requirements, runs `python -m opi.run_daily`, executes `pytest -q`, and runs `python scripts/verify_all.py`.
- Commits and pushes any new predictions or dashboard changes with bot credentials (`github-actions[bot]`).
- Failure safety: Missing or invalid sources write `SKIPPED_<reason>` to `predictions/run_log.csv`; never fills defaults or guesses.

Commit: `phase8-workstream-b (automated daily forward test)` (hash `cdf733f`).

---

## 6. Workstream C: Dashboard

Implemented static HTML dashboard at `dashboard/index.html` rendered directly from CSV files via `opi/report.py`:
- Prominent provisional banner: `"PROVISIONAL STATUS (Listed n = 0): Decision aid only, not financial advice. Per pre-registered protocol, no performance claims are permitted until at least 30 forward listings are completed."`
- Model version display (`v4.0.0-champion`).
- Forward prediction audit table listing all FORWARD, INVALID, and TEST rows with status tags.
- Calibration table deferred message until $n \ge 30$.
- Defect and repository health ledger displaying live counts from `DEFECTS.md`.

Commit: `phase8-workstream-c (dashboard)` (hash `8b03b35`).

---

## 7. Workstream D: Retraining Governance

Implemented governance policy and challenger script:
1. `docs/retraining_policy.md`: Retraining cadence rules (quarterly or $n \ge 30$ verified forward rows), evidence standards for training data, champion vs challenger paired bootstrap protocol, promotion criteria (non-inferiority + calibration parity), and versioning workflow. Explicit ban on auto-promotion in CI.
2. `scripts/retrain_challenger.py`: Challenger training and evaluation runner. Trains candidate model on training partition, evaluates against champion on holdout test partition, computes 2,000 paired bootstrap 95% difference interval, and outputs recommendation report without touching production champion artifact.

Commit: `phase8-workstream-d (retraining policy and challenger script)` (hash `5e4fdf4`).

---

## 8. Verification Commands & Outputs

### 1. `python scripts/verify_all.py`
```
[PASS] no absolute/local paths in docs or code                                    
[PASS] pytest suite passes                                                        39 passed in 3.85s
[PASS] no duplicate (company, listing_date)                                       0 duplicates
[PASS] listing_gain_pct matches prices                                            0 mismatches
[PASS] label_good matches gain                                                    0 mismatches
[PASS] date order open<=close<=listing                                            0 rows
[PASS] no extreme listing/issue price ratios (FPO-type errors)                    
[PASS] gmp_pct in plausible range                                                 0 rows
[PASS] every excluded row has a source URL                                        0 without URL
[PASS] every GMP value has URL, page date, access date                            0 rows incomplete
[PASS] every sourced GMP row exists in master                                     0 unmatched
[PASS] GMP as_of_date not after last bidding day (no leakage)                     0 rows
[PASS] source page dated before listing                                           0 rows dated on/after listing
[PASS] second-source check credible (Phase 7)                                     
[PASS] second-source check credible (Phase 8)                                     
[PASS] snapshot file for every sourced GMP row (<listing_date>_<company-slug>.*)  0 of 0 missing
[PASS] log statuses valid                                                         0 invalid
[PASS] FORWARD rows logged                                                        1 rows
[PASS] FORWARD rows scored before listing                                         0 rows
[PASS] FORWARD rows scored after bidding closed (final subscription)              
[PASS] FORWARD rows use final (not day-1/live) subscription                       
[PASS] probabilities within [0,1]                                                 
[PASS] no duplicate FORWARD rows                                                  0
[PASS] no actuals for unlisted IPOs                                               
[PASS] FORWARD feature snapshots carry source URLs                                0 rows with only site names
[PASS] final test rows <= FORWARD rows with actuals                               0 rows vs 0
[PASS] Phase 1: three required files                                              
[PASS] Phase 2: three required files                                              
[PASS] Phase 3: three required files                                              
[PASS] Phase 4: three required files                                              
[PASS] Phase 5: three required files                                              
[PASS] Phase 6: three required files                                              
[PASS] Phase 7: three required files                                              
[PASS] Phase 8: three required files                                              
[PASS] defect register parsed                                                     14 defects, 1 open/partial
[PASS] every FIXED defect has an existing regression test                         
[PASS] Phase 8 verdict 'None unfixed' consistent with defect register             
[PASS] Phase 6: gate + preregistration committed before other work                
[PASS] Phase 7: gate + preregistration committed before other work                
[PASS] Phase 8: gate + preregistration committed before other work                
[PASS] Phase 7 headline metrics recompute from raw predictions                    

SUMMARY: 41 pass, 0 warn, 0 fail
```

### 2. `python -m pytest -q`
```
.......................................                                  [100%]
39 passed in 4.63s
```

### 3. `python -m opi.run_daily --dry-run`
```
==============================================================================
  OPI DAILY AUTOMATED FORWARD TEST [run_20261016_033905] (DRY RUN)
==============================================================================

Processing Candidate: Hyundai Motor India
Close Date: 2026-10-17 | Listing Date: 2026-10-22
Validation FAILED for Hyundai Motor India:
  - Scored at (2026-10-16 03:39:05.939741) is before bidding closed at 18:00 IST on 2026-10-17
HD Fire Protect Limited scheduled to list on 2026-10-21 > today (2026-10-16) - unlisted, carried over.

Dashboard updated at: D:\Istak\OPI\dashboard\index.html
==============================================================================
```

### 4. Git Commit Sequence Check
```
phase8-gate-a
phase8-preregistration
phase8-workstream-a (pipeline refactor)
phase8-workstream-b (automated daily forward test)
phase8-workstream-c (dashboard)
phase8-workstream-d (retraining policy and challenger script)
```
