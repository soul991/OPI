# Phase 8: Outcome & Verdict - Verification Gate, Evidence Standard, Pipeline Refactor, Automated Forward Test & Dashboard

> Standard sequential phase documentation per `RULES.md`, `PHASE_PROTOCOL.md`, and `phases/Phase 8/1_planning_and_goals.md`.  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following target remains partial / carried over:

1. **D-005: HD Fire Protect Limited Actual Outcome Unrecorded**
   - Scheduled Listing Date: 2026-10-21 (future date relative to scoring timestamp).
   - Status: **PARTIAL / CARRIED OVER**. Cannot record actual listing gain until trading commences on NSE/BSE.

---

## 2. Defect Ledger

| Defect ID | Description | Severity | Prior Status | Phase 8 Gate A8 Status | Verification Reference |
|---|---|---|---|---|---|
| D-001 | 77 backfilled GMP values unverified | Critical | OPEN | **FIXED** | All 77 unverified values reverted to NOT_RECORDED; `tests/test_gmp_evidence.py::test_snapshot_for_every_sourced_gmp_row` |
| D-002 | Phase 7 headline metrics dependent on D-001 | Critical | OPEN | **FIXED** | Recomputed on post-clean master; `tests/test_reporting.py::test_headline_metrics_recompute` |
| D-003 | Mukka Proteins GMP 321.43% | High | OPEN | **FIXED** | Corrected to 125.0%; `tests/test_data_integrity.py::test_gmp_outliers_verified` |
| D-004 | HD Fire Protect scored with Day-1 live subscription | High | OPEN | **FIXED** | Invalidated row 6, scored row 7 post-close with final features; `tests/test_forward_log.py::test_forward_rows_scored_after_bidding_closed` |
| D-005 | HD Fire Protect actual listing outcome unrecorded | Medium | OPEN | **PARTIAL** | Lists 2026-10-21; `tests/test_forward_log.py::test_actuals_only_for_listed` |
| D-006 | Fundamentals completeness | Medium | ACCEPTED | **ACCEPTED** | README "Known limitations" |
| D-007 | Conformal tail under-coverage | Medium | DEFERRED | **DEFERRED** | Scheduled for Phase 9 |
| D-008 | Conformal pooled over-conservatism | Medium | DEFERRED | **DEFERRED** | Scheduled for Phase 9 |
| D-009 | Wording violations in Phase 7 verdict | Low | OPEN | **FIXED** | ERRATA (Phase 8) prepended to Phase 7 verdict; `tests/test_reporting.py::test_phase7_errata_present` |
| D-010 | Historical GMP absent pre-2022 | Medium | ACCEPTED | **ACCEPTED** | README "Known limitations" |
| D-011 | Sector label Industrial & Manufacturing share | Low | OPEN | **ACCEPTED** | Verified at 18.74%; `tests/test_data_integrity.py::test_sector_catchall_share_reported` |
| D-012 | Sparse years 2012-2014 | Low | OPEN | **ACCEPTED** | Verified at 11, 3, 5; `tests/test_data_integrity.py::test_sparse_years_documented` |
| D-013 | Audit samples lack snapshots | Medium | OPEN | **FIXED** | 20 snapshots saved under `data/evidence/audit/`; `tests/test_data_integrity.py::test_audit_samples_have_snapshots` |
| D-014 | Lack of independent automated verification | High | OPEN | **FIXED** | `scripts/verify_all.py` created and tested; `tests/test_reporting.py::test_verify_all_runs` |

---

## 3. Gate A8 Table & Evidence

| Item | Requirement | Status | Summary of Evidence |
|:---:|---|:---:|---|
| **U1** | D-001 / D-002: Revert 77 unverified GMP values | **FIXED** | Reverted all 77 rows in `data/ipo_master.csv` to `NOT_RECORDED`. Empty `data/gmp_sourced.csv`. `verify_all.py` snapshot check PASS. |
| **U2** | D-003: Mukka Proteins GMP correction | **FIXED** | Corrected to 125.0%. Audited all >150% and <-30% in `phases/Phase 8/gmp_outlier_review.csv`. `test_gmp_outliers_verified` PASS. |
| **U3** | D-004: HD Fire Protect forward row remediation | **FIXED** | Old row marked INVALID_NONFINAL_FEATURES. Scored row 7 post-close with final features. `test_forward_rows_scored_after_bidding_closed` PASS. |
| **U4** | D-005: HD Fire Protect outcome | **PARTIAL** | Unlisted until 2026-10-21; `test_actuals_only_for_listed` PASS. |
| **U5** | D-013: 20 audit sample snapshots | **FIXED** | 20 snapshots saved in `data/evidence/audit/`. `prior_phase_recheck.csv` created. `test_audit_samples_have_snapshots` PASS. |
| **U6** | D-011 / D-012: Sector share and sparse years | **ACCEPTED** | Verified 18.74% and 11, 3, 5 counts. Documented in `README.md`. |
| **U7** | D-009: Phase 7 verdict wording | **FIXED** | `## ERRATA (Phase 8)` added to `phases/Phase 7/3_outcome_and_verdict.md`. `test_phase7_errata_present` PASS. |
| **U8** | Re-run Phase 7 evaluation | **FIXED** | Executed `phase7_rolling_train_evaluate.py` across 20 quarters. Updated before/after and bootstrap tables. |
| **U9** | D-014: Independent verification | **FIXED** | `scripts/verify_all.py` created and verified. `test_verify_all_runs` PASS. |
