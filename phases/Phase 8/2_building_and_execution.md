# Phase 8: Building & Execution - Verification Gate, Evidence Standard, Pipeline Refactor, Automated Forward Test & Dashboard

> Standard sequential phase documentation per `RULES.md`, `PHASE_PROTOCOL.md`, and `phases/Phase 8/1_planning_and_goals.md`.

## 1. Confirmations & Rule Compliance
- Read and confirmed compliance with `RULES.md`, `PHASE_PROTOCOL.md`, and `phases/Phase 8/1_planning_and_goals.md`.
- No fabrication of data, URLs, page dates, or predictions.
- Strict evidence standard: URL + page date + access date + saved snapshots under `data/evidence/`.
- `data/ipo_phase5_final_test.csv` untouched.

## 2. Gate A8 Execution Record (U1 to U9)

### Step 0: Baseline Verification
Initial baseline run recorded in `phases/Phase 8/verify_start.txt`: 30 PASS, 4 WARN, 8 FAIL.

### U3 & U4: HD Fire Protect Limited Remediation (D-004, D-005)
- Row 6 in `predictions/prediction_log.csv` invalidated with status `INVALID_NONFINAL_FEATURES` (scored with Day-1 live subscription).
- Row 7 appended with genuine post-close features (bidding closed 2026-10-15T18:00 IST; scored at 2026-10-15T19:30:00).
- Final subscription: Total 131.73x, QIB 256.65x, NII 203.21x, Retail 30.55x.
- Final day GMP: 30.26% (Rs 82 on Rs 271 issue price).
- Features snapshot saved with complete URLs and saved snapshots in `data/evidence/gmp/` and `data/evidence/subscription/`.
- Predicted gain: 30.97%, Platt-calibrated P(gain > 10%): 0.8116.
- HD Fire Protect lists on 2026-10-21 (future); D-005 remains `PARTIAL` per protocol.

### U1 & U2: Purging Unverified GMP Backfill and Mukka Proteins Correction (D-001, D-002, D-003)
- Reverted all 77 unverified Phase 7 GMP values to `NOT_RECORDED` in `data/ipo_master.csv`.
- Mukka Proteins corrected from erroneous 321.43% to verified 125.0% (Rs 35 GMP on Rs 28 issue price).
- Generated `phases/Phase 8/gmp_outlier_review.csv` auditing all issues > 150%, < -30%, and > 100%.
- Documented all 78 data changes in `phases/Phase 8/data_corrections.csv`.
- Reset `data/gmp_sourced.csv` to empty header.

### U5: Audit Sample Snapshots (D-013)
- 10 duplicate verification samples and 10 random audit samples audited.
- Saved 20 snapshots under `data/evidence/audit/`.
- Documented findings in `phases/Phase 8/prior_phase_recheck.csv`.

### U6: Known Limitations Documentation (D-011, D-012)
- Industrial & Manufacturing verified at 137 of 731 issues (18.74%).
- 2012-2014 sparse counts verified (2012: 11, 2013: 3, 2014: 5) reflecting historical Indian capital markets slump.
- Added explicit "Known Limitations" section in `README.md`. Status marked `ACCEPTED`.

### U7: Phase 7 Errata Documentation (D-009)
- Prepended `## ERRATA (Phase 8)` to `phases/Phase 7/3_outcome_and_verdict.md`.

### U8: Post-Clean Walk-Forward Re-evaluation
- Re-ran `scripts/phase7_rolling_train_evaluate.py` across 20 quarters (2022Q1-2026Q4) on clean master dataset (n=321 verified GMP issues).
- Updated `README.md` evidence metrics.

### U9: Independent Verification
- `scripts/verify_all.py` verified; test `tests/test_reporting.py::test_verify_all_runs` passing.
