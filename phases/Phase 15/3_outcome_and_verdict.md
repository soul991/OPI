# Phase 15: Outcome & Verdict (Gate A15 State)

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 15/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Epistemic Guardrail**: Sample size is currently $n = 8$ of 30 target forward predictions. All metrics and error distributions are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets remain open, partial, or pending at Gate A15:

1. **D-026: Live Web Research Agent Proof (OpenRouter)**
   - Status: **NOT FIXED (awaiting real new IPO in scheduled run)**
   - Reason: In accordance with project rules ("Never create fake IPOs to prove the research agent; leave D-026 NOT FIXED until a scheduled run handles a real new IPO"), D-026 remains NOT FIXED until an upcoming Mainboard IPO bidding cycle appears in scheduled runs.
2. **D-071: Dashboard Card & verify_all NOT FIXED count**
   - Status: **PARTIAL (needs user action)**
   - Reason: Dashboard generation was fixed in Phase 14 (`opi/report.py`), but `scripts/verify_all.py` line 202 continues to count only `OPEN` and `PARTIAL`. Updating `verify_all.py` status tuple is pending user action; agents are strictly forbidden from modifying control verification scripts.
3. **D-072: Tier 2 Wrong-Day Price Fallback**
   - Status: **OPEN (seeded in Gate A15)**
   - Reason: `fetch_yfinance_first_session_open` silently fell back to the first available bar when the listing date bar was absent, recording Paras Healthcare from the 2026-10-29 bar (721, +4.04%) instead of the 2026-10-28 listing price (720, +3.90%). Scheduled for Workstream A.
4. **D-073: Audited Outcome Correction Mechanism**
   - Status: **OPEN (seeded in Gate A15)**
   - Reason: No mechanism existed to correct recorded outcomes while preserving byte-identical immutability of `prediction_log.csv`. Scheduled for Workstream B (`outcome_corrections.csv` and `effective_outcome`).
5. **D-074: Cloud Runner Reachability Probe**
   - Status: **OPEN (seeded in Gate A15)**
   - Reason: D-068 was verified against a local win32 probe rather than cloud runners. D-068 remains PARTIAL until runner-generated evidence (`phases/Phase 15/source_probe_runner.md`) is committed in Workstream C.
6. **D-075: Workflow Entry-Point Standalone Execution Regression**
   - Status: **OPEN (seeded in Gate A15)**
   - Reason: Watchdog failed in scheduled run 41090951686 (issue #6) due to missing `sys.path` insertion for `scripts.manage_alerts`. Fixed on `main` in commit `9dd1b7d` without a register entry. Scheduled for full verification via entry-point smoke test in Workstream C.
7. **D-076: Commits to Main Without Branch, PR, or Defect ID**
   - Status: **OPEN (seeded in Gate A15)**
   - Reason: Fixes `06ff884` and `9dd1b7d` were pushed directly to `main`. Scheduled for protocol update in `PHASE_PROTOCOL.md` and pre-push enforcement in Workstream C.

---

## 2. Defect Ledger

All 76 defects tracked in [`DEFECTS.md`](../../DEFECTS.md):

| Defect ID | Phase Introduced | Description | Severity | Status Before Gate A15 | Status After Gate A15 | Due Phase | Verification Proof |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** to **D-052** | 1-11 | Historical defects resolved or accepted in earlier phases | Various | FIXED / ACCEPTED | **FIXED / ACCEPTED** | - | See `DEFECTS.md` |
| **D-053** | 12 | `phases/Phase 11/forward_postmortem.md` has no ERRATA block | Medium | FIXED | **FIXED** | 13 | `tests/test_reporting.py::test_phase11_postmortem_has_errata` |
| **D-054** | 12 | Macro snapshot labelled 2026-10-23 contains 2026-10-22 values | Low | FIXED | **FIXED** | 13 | `tests/test_gate_a.py::test_gate_a13_macro_correction` |
| **D-055** | 12 | `data/evidence/market/*_nifty.raw` is parsed output, not original response | Low | FIXED | **FIXED** | 13 | `tests/test_gate_a.py::test_gate_a13_market_raw_decision` |
| **D-056** | 12 | Dashboard defect counter stale and lacks cloud run date | Low | FIXED | **FIXED** | 13 | `tests/test_dashboard.py::test_dashboard_shows_last_cloud_run` |
| **D-057** | 12 | No alert when scheduled run fails | Medium | FIXED | **FIXED** | 13 | `tests/test_alerts.py::test_handle_failure_creates_new_issue_when_none_open` |
| **D-058** | 12 | Schedule lag and 60-day pause risks | Medium | FIXED | **FIXED** | 13 | `tests/test_watchdog.py::test_scheduled_run_freshness_fresh` |
| **D-059** | 12 | Dependencies not pinned | Medium | FIXED | **FIXED** | 13 | `tests/test_ci.py::test_requirements_lock_and_ci_pinning` |
| **D-060** | 12 | Evaluation n=30 not automated | Medium | FIXED | **FIXED** | 13 | `tests/test_final_evaluation.py::test_full_evaluation_on_synthetic_fixture` |
| **D-061** | 12 | Maintainer runbook missing | Low | FIXED | **FIXED** | 13 | `tests/test_docs.py::test_runbook_sections_and_headings` |
| **D-062** | 13 | Workflows pinned to ubuntu-latest / Node-20 | Low | FIXED | **FIXED** | 13 | `tests/test_ci.py::test_workflows_pin_runner_and_node24_actions` |
| **D-063** | 13 | CI test failure on dashboard rewrite before pytest | Medium | FIXED | **FIXED** | 13 | `tests/test_ci.py::test_ci_local_replicates_ci_order` |
| **D-064** | 13 | Watchdog false failure and stored-date fallback | Medium | FIXED | **FIXED** | 14 | `tests/test_watchdog.py::test_check_a_never_falls_back_to_a_stored_date` |
| **D-065** | 13 | Alert issues lacked structured reason | Low | FIXED | **FIXED** | 14 | `tests/test_watchdog.py::test_alert_reason_file_is_used` |
| **D-066** | 14 | Daily job skipped listed IPOs without attempting fetch | Medium | FIXED | **FIXED** | 14 | `tests/test_actuals_job.py::test_tier2_success_with_agreeing_second_source` |
| **D-067** | 14 | No alert for unrecorded outcomes >2 days | Medium | FIXED | **FIXED** | 14 | `tests/test_watchdog.py::test_missing_outcomes_threshold_boundary` |
| **D-068** | 14 | Cloud runner reachability unmeasured | Medium | FIXED | **PARTIAL (D-074)** | 14 | `tests/test_actuals_job.py::test_two_tier_probe_committed`; needs runner probe |
| **D-069** | 14 | Date-only comparison ignored market trading hours | Low | FIXED | **FIXED** | 14 | `tests/test_actuals_job.py::test_is_listing_ready_for_actuals_market_hours_rule` |
| **D-070** | 14 | Dashboard omitted count/names of pending listed rows | Low | FIXED | **FIXED** | 14 | `tests/test_dashboard.py::test_dashboard_shows_listed_outcome_pending_count_and_names` |
| **D-071** | 14 | Dashboard and verify_all count only OPEN/PARTIAL | Low | PARTIAL | **PARTIAL** | 14 | `tests/test_dashboard.py::test_dashboard_defect_counter_matches_register` (verify_all pending user action) |
| **D-072** | 14 | Tier 2 falls back to wrong-day bar when listing bar missing | Medium | - | **OPEN** | 15 | Scheduled for Workstream A |
| **D-073** | 14 | No audited way to correct wrong outcomes without editing log | Medium | - | **OPEN** | 15 | Scheduled for Workstream B |
| **D-074** | 14 | D-068 probe was executed on win32 instead of cloud runner | Medium | - | **OPEN** | 15 | Scheduled for Workstream C |
| **D-075** | 14 | Watchdog standalone execution failed on runner (issue #6) | Medium | - | **OPEN** | 15 | Scheduled for Workstream C |
| **D-076** | 15 | Fixes pushed to main without PR, branch, or defect ID | Low | - | **OPEN** | 15 | Scheduled for Workstream C |

---

## 3. Forward Table from `forward_report.py --markdown`

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

---

## 4. Gate A15 Results & Verification Proofs

### G1: Prior-Phase Recheck (Seed 15 Sample) & Recomputations
- 10 claims sampled with `seed=15` from `phases/Phase 14/3_outcome_and_verdict.md` (6 IPO claims including Jio and Paras, 4 "file X contains Y" claims).
- Recorded in `phases/Phase 15/prior_phase_recheck.csv`: all 10 claims audited against underlying files.
- Recomputed 5 headline numbers directly from raw data via `scripts/recompute_gate_a15.py`:
  1. Forward Model MAE ($n=8$ listed): **6.01 pp** (6.0088 pp).
  2. Forward Raw GMP MAE ($n=7$ with GMP): **6.17 pp** (6.1671 pp).
  3. Master dataset row count: **731 rows** in `data/ipo_master.csv`.
  4. Prediction log breakdown: **14 total rows** (6 non-forward/invalid, 8 genuine FORWARD, 8 listed).
  5. Defect counts: **76 total defects** in `DEFECTS.md` (62 FIXED, 6 ACCEPTED, 2 PARTIAL, 1 NOT FIXED, 5 OPEN).

### G2: Carried Defects Regression Verification (D-053 through D-070)
- All 18 regression tests passed (18 passed in 21.51s).
- Defect whose "FIXED" depends on a file produced off the runner:
  - **D-068**: Verified by `test_two_tier_probe_committed` checking `phases/Phase 14/source_probe.md`, which was generated on `win32` instead of a GitHub Actions Linux runner (D-074). D-068 is marked `PARTIAL` pending runner execution in Workstream C.

### G3: GitHub Actions Scheduled Health & Issue #6 Post-Mortem
- Last 10 scheduled runs recorded in `phases/Phase 15/actions_status.md` (9 SUCCESS, 1 FAILURE: watchdog run 41090951686).
- Issue #6 created at `2026-10-30T16:33:47Z`, automatically closed at `2026-10-30T17:12:32Z` upon successful dispatched run `41096687304`.
- 0 open issues currently in the repository.
- Commits since `phase14-gate-a` audited and mapped to defects: commits `06ff884` and `9dd1b7d` identified as unmanaged direct pushes to `main` (D-075, D-076).

### G4: Paras Healthcare Price & Trading Session Dissection
Side-by-side comparison of saved evidence:
- **Yahoo Finance Raw Bars** (`data/evidence/actuals/2026-10-28_paras-healthcare-limited_fe823e2ba992.txt`):
  - Bar 1: `2026-10-28T18:30:00.000Z` -> **2026-10-29 00:00:00 IST** (Day AFTER listing). Open = **₹721.00**.
  - Bar 2: `2026-10-29T18:30:00.000Z` -> **2026-10-30 00:00:00 IST**. Open = ₹774.25.
  - **Listing Date Bar (2026-10-28 IST) was completely MISSING** in Yahoo history.
- **Chittorgarh Listing Results** (`second_source_url` in manifest):
  - Listing Date: **2026-10-28**.
  - Official Opening Price: **₹720.00**.
  - Listing Gain on Issue Price ₹693: **+3.90%** (vs +4.04% logged from 2026-10-29 bar).
- **Provenance**: The recorded listing price in `predictions/prediction_log.csv` (₹721.00, +4.04%) came from the 2026-10-29 trading bar due to the first-row fallback in `opi/actuals.py`.

### G5: Secret Scanning & Credentials Check
- `gh secret list` shows `OPENROUTER_API_KEY`.
- `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. Zero API key material committed.

---

## 5. Workstream Results & Execution Plans
*(Paused at Step 5 awaiting explicit user "continue" instruction.)*

---

## 6. Self-Audit (Pasted Command Output)

| Audit Question | Verdict | Verifying Evidence |
|---|:---:|---|
| Did any report number come from anywhere but a script over the log/evidence? | **NO** | Recomputed via `scripts/recompute_gate_a15.py` and `scripts/forward_report.py --markdown`. |
| Did any claim say a file changed when `git diff --stat` shows otherwise? | **NO** | Verified with `git diff --stat` before staging. |
| Did the log get edited at all? | **NO** | `git diff predictions/prediction_log.csv` shows 0 changes. |
| Did any earlier-phase file change except by ERRATA? | **NO** | Zero modifications to historical phase files. |
| Was any outcome recorded without a saved real response? | **NO** | All outcomes backed by saved manifests in `data/evidence/actuals/`. |
| Does any FIXED row rely on a file produced off the runner? | **YES (D-068)** | D-068 identified; D-074 opened to run probe on cloud runner. |
| Did the work stop after Gate A15? | **YES** | Execution strictly halted at Step 5 awaiting user "continue". |
| Was the key kept out of the repo, logs, issues, and snapshots? | **YES** | `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. |

---

## 7. Handover State
Gate A15 complete and verified. Repository halted at Step 5.
