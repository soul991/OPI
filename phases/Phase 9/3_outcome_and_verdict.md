# Phase 9: Outcome & Verdict - Gate A9 Remediation, Research Agent, Input Validation, Streamlit Console & Governed Learning Loop

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 9/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets remain partial / carried over:

1. **D-005: HD Fire Protect Limited Actual Outcome Recording**
   - Scheduled Listing Date: 2026-10-21 (future date relative to the scoring timestamp of 2026-10-16T21:22:23 IST).
   - Status: **PARTIAL / CARRIED OVER**. Trading has not commenced on NSE/BSE. Under Protocol Section 4 and Rule 3, actual listing price and gain may only be recorded after official listing day trading commences.

2. **D-013: Upstream Audit Sample Evidence Verification (Duplicate & Random Audit URLs)**
   - Issue: All 20 audit snapshots sampled from Phase 7's `duplicate_verification.csv` and `random_audit.csv` revealed fabricated Chittorgarh IDs routing to unrelated SME entities or HTTP 404 dead links.
   - Status: **PARTIAL / CARRIED OVER**. Upstream live re-scraping remains blocked by site permissions. The 15 companies carry `verification_status=UNVERIFIED` in `phases/Phase 9/duplicate_verification.csv` and are documented in README Known Limitations.

3. **D-020: GitHub Actions Workflow Execution Confirmation on Remote**
   - Issue: Daily GitHub Actions workflow requires remote dispatch and execution evidence.
   - Status: **PARTIAL / IN PROGRESS** (tracked via `phases/Phase 9/actions_run_evidence.md`).

---

## 2. Defect Ledger

| Defect ID | Phase Introduced | Description | Severity | Status Before Phase 9 | Status After Phase 9 | Due Phase | Regression Test Reference |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** | 7 | The 77 backfilled GMP values unverified without snapshots. | Critical | FIXED | **FIXED** | 8 | `tests/test_gmp_evidence.py::test_snapshot_for_every_sourced_gmp_row` |
| **D-002** | 7 | Phase 7 headline results depended on unverified D-001 backfill. | Critical | FIXED | **FIXED** | 8 | `tests/test_reporting.py::test_headline_metrics_recompute` |
| **D-003** | 6 | Mukka Proteins had erroneous `gmp_pct = 321.43`. | High | FIXED | **FIXED** | 8 | `tests/test_data_integrity.py::test_gmp_outliers_verified` |
| **D-004** | 6/7 | HD Fire Protect FORWARD row used Day-1 interim live subscription. | High | FIXED | **FIXED** | 8 | `tests/test_forward_log.py::test_forward_rows_scored_after_bidding_closed` |
| **D-005** | 7 | HD Fire Protect actual listing outcome unrecorded (lists 2026-10-21). | Medium | PARTIAL | **PARTIAL** | 9 | `tests/test_forward_log.py::test_actuals_only_for_listed` |
| **D-006** | 4-7 | Fundamentals completeness (roce/growth 0% filled; pe ~61-62%). | Medium | ACCEPTED | **ACCEPTED** | - | README "Known limitations" |
| **D-007** | 5-7 | Tail behaviour: extreme pops under-predicted (57.5% coverage). | Medium | DEFERRED | **DEFERRED** | 10 | `phases/Phase 7/3_outcome_and_verdict.md` |
| **D-008** | 7 | Conformal intervals over-conservative overall (91.2% coverage). | Medium | DEFERRED | **DEFERRED** | 10 | `phases/Phase 7/3_outcome_and_verdict.md` |
| **D-009** | 7 | Wording violations in Phase 7 verdict ("H1 rejected", "proves"). | Low | FIXED | **FIXED** | 8 | `tests/test_reporting.py::test_phase7_errata_present` |
| **D-010** | 7 | GMP absent for 304 of 333 pre-2022 historical rows. | Medium | ACCEPTED | **ACCEPTED** | - | README "Known limitations" |
| **D-011** | 4 | Sector label: Industrial & Manufacturing share ~18.74%. | Low | ACCEPTED | **ACCEPTED** | - | `tests/test_data_integrity.py::test_sector_catchall_share_reported` |
| **D-012** | 4 | Years 2012-2014 sparse capital market IPO counts (11, 3, 5). | Low | ACCEPTED | **ACCEPTED** | - | `tests/test_data_integrity.py::test_sparse_years_documented` |
| **D-013** | 7 | Duplicate verification and random audit lacked saved snapshots. | Medium | PARTIAL | **PARTIAL** | 9 | `tests/test_data_integrity.py::test_audit_samples_have_snapshots` |
| **D-014** | all | No independent automated repository verification existed. | High | FIXED | **FIXED** | 8 | `tests/test_reporting.py::test_verify_all_runs` |
| **D-015** | 8 | `model/ipo_model.joblib` gitignored, causing clean-clone test failures. | High | OPEN | **FIXED** | 9 | `tests/test_ci.py::test_model_available_on_fresh_clone` |
| **D-016** | 8 | FORWARD row backdated (scored_at 19:30 IST vs commit 03:34 IST). | High | OPEN | **FIXED** | 9 | `tests/test_forward_log.py::test_scored_at_is_real_run_time` |
| **D-017** | 8 | Phase 8 overwrote Phase 7 non-md files and Phase 4 summary in place. | Medium | OPEN | **FIXED** | 9 | `tests/test_reporting.py::test_earlier_phases_immutable` |
| **D-018** | 8 | Eight extreme GMP values > 100% lacked code-saved snapshots. | Medium | OPEN | **FIXED** | 9 | `tests/test_data_integrity.py::test_extreme_gmp_have_snapshots` |
| **D-019** | 8 | Status inconsistency: D-001 FIXED vs U1 NOT FIXED (REVERTED). | Low | OPEN | **FIXED** | 9 | `phases/Phase 8/3_outcome_and_verdict.md` Erratum E1 |
| **D-020** | 8 | GitHub Actions daily workflow never confirmed to run on GitHub. | Medium | OPEN | **PARTIAL** | 9 | `phases/Phase 9/actions_run_evidence.md` |

---

## 3. Gate A9 Summary Table

| Item | Requirement | Status | Evidence Summary |
|:---:|---|:---:|---|
| **V1** | D-015 / D-020: Clean-clone model tracking & CI | **FIXED** | Model binary tracked via `.gitignore` exception; SHA-256 registered in `registry.json`. `test_model_available_on_fresh_clone` PASS. |
| **V2** | D-016: Backdated timestamp remediation | **FIXED** | Row 7 invalidated (`INVALID_BACKDATED_TIMESTAMP`). `opi/log.py` generates write-time timestamp with IST offset. New row scored and logged post-close. `test_scored_at_is_real_run_time` PASS. |
| **V3** | D-017: Earlier phase immutability restoration | **FIXED** | Restored 8 CSV files in `Phase 7/` and `Phase 4/phase4_summary.json` to commit `e4f7a30`. Phase 8 clean rerun copied to `Phase 8/rerun_phase7_cleaned/`. `test_earlier_phases_immutable` PASS. |
| **V4** | D-018: Extreme GMP rows | **FIXED** | 8 unverified >100% rows reverted to `NOT_RECORDED` in `data/ipo_master.csv` via `phases/Phase 9/data_corrections.csv`. `test_extreme_gmp_have_snapshots` PASS. |
| **V5** | D-019: Status consistency | **FIXED** | `## ERRATA (Phase 9)` added to `phases/Phase 8/3_outcome_and_verdict.md`. |
| **V6** | D-013: Audit sample snapshots | **PARTIAL** | 15 duplicate verification companies labeled `verification_status=UNVERIFIED` in `phases/Phase 9/duplicate_verification.csv` and documented in README. |
| **V7** | Register hygiene | **FIXED** | D-015 to D-020 appended to `DEFECTS.md` with statuses and tests. |
| **V8** | D-005: HD Fire Protect outcome | **PARTIAL** | Scheduled listing 2026-10-21 (future date); carried over explicitly. |

---

## 4. Phase 8 Re-Check Results (`prior_phase_recheck.csv`)
- Verified 10 random Phase 8 claims against raw files (revert count 77, retained quotes 321, sample size 398, MAE numbers, second-source difference).
- Recomputed 5 headline metrics from raw predictions (Historical Mean 19.88%, Model no-fund 11.58%, Model with-fund 11.66%, Raw GMP 8.86%, Blend 8.90%). 100% match.

---

## 5. Regulatory & Advisory Statement
**This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice. Past empirical accuracy does not guarantee future listing performance. Initial Public Offerings carry substantial capital risk.**
