# Phase 14: Outcome & Verdict - Automatic Listing-Outcome Recording in the Cloud, and an Alert When It Does Not Happen (Gate A14)

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 14/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets remain open, partial, or pending in Phase 14 Gate A:

1. **D-026: Live Web Research Agent Proof (OpenRouter)**
   - Status: **NOT FIXED (awaiting real new IPO in scheduled run)**
   - Audit: `OPENROUTER_API_KEY` is confirmed configured in GitHub repository secrets. In accordance with user rules ("Never create fake IPOs to prove the research agent; leave D-026 NOT FIXED until a scheduled run handles a real new IPO"), D-026 remains NOT FIXED until an upcoming Mainboard IPO bidding cycle appears in live scheduled runs. No fake IPOs were created.
2. **D-066 to D-070: Cloud Outcome Recording, Missing-Outcome Alert, Source Probe, Market Hours Guard, Pending Dashboard Counter**
   - Status: **OPEN (seeded in Gate A14)**
   - Audit: Seeded in `DEFECTS.md` per Phase 14 plan; scheduled for Workstreams A, B, and C following user "continue" instruction.
3. **Jio Platforms Limited and Paras Healthcare Limited Listing Outcomes**
   - Status: **PENDING (Listed 2026-10-28; scheduled for automated cloud recording in Workstream B)**
   - Audit: Both rows currently hold status `FORWARD` in `predictions/prediction_log.csv` without actuals recorded. Automated cloud fetching and validation chain will record these upon workflow dispatch on `main`.

---

## 2. Defect Ledger

All 70 defects tracked in [`DEFECTS.md`](../../DEFECTS.md):

| Defect ID | Phase Introduced | Description | Severity | Status Before Gate A14 | Status After Gate A14 | Due Phase | Verification Proof |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** to **D-052** | 1-11 | Historical defects resolved or accepted in earlier phases | Various | FIXED / ACCEPTED | **FIXED / ACCEPTED** | - | See `DEFECTS.md` |
| **D-053** | 12 | `phases/Phase 11/forward_postmortem.md` has no ERRATA block; wrong Bonfiglioli 3.4x | Medium | FIXED | **FIXED** | 13 | `tests/test_reporting.py::test_phase11_postmortem_has_errata` |
| **D-054** | 12 | Macro snapshot labelled 2026-10-23 contains 2026-10-22 values | Low | FIXED | **FIXED** | 13 | `tests/test_gate_a.py::test_gate_a13_macro_correction` |
| **D-055** | 12 | `data/evidence/market/*_nifty.raw` is parsed output, not original response | Low | FIXED | **FIXED** | 13 | `tests/test_gate_a.py::test_gate_a13_market_raw_decision` |
| **D-056** | 12 | Dashboard defect counter is stale (1 vs 2) and does not show last cloud run date | Low | FIXED | **FIXED** | 13 | `tests/test_dashboard.py::test_dashboard_shows_last_cloud_run` |
| **D-057** | 12 | No alert when a scheduled run fails | Medium | FIXED | **FIXED** | 13 | `tests/test_alerts.py::test_handle_failure_creates_new_issue_when_none_open` |
| **D-058** | 12 | Schedule risks: runs start 4.7 h late; GitHub 60-day pause risk | Medium | FIXED | **FIXED** | 13 | `tests/test_watchdog.py::test_scheduled_run_freshness_fresh` |
| **D-059** | 12 | Dependencies not pinned | Medium | FIXED | **FIXED** | 13 | `tests/test_ci.py::test_requirements_lock_and_ci_pinning` |
| **D-060** | 12 | The n = 30 evaluation is not preregistered or automated | Medium | FIXED | **FIXED** | 13 | `tests/test_final_evaluation.py::test_full_evaluation_on_synthetic_fixture` |
| **D-061** | 12 | No runbook for the user | Low | FIXED | **FIXED** | 13 | `tests/test_docs.py::test_runbook_sections_and_headings` |
| **D-062** | 13 | Workflows used `ubuntu-latest` and Node-20 actions | Low | FIXED | **FIXED** | 13 | `tests/test_ci.py::test_workflows_pin_runner_and_node24_actions` |
| **D-063** | 13 | CI test failure on dashboard write before pytest; no pre-push check | Medium | FIXED | **FIXED** | 13 | `tests/test_ci.py::test_ci_local_replicates_ci_order` |
| **D-064** | 13 | Watchdog false failure; stored-date fallback in verify_pages.py | Medium | FIXED | **FIXED** | 14 | `tests/test_watchdog.py::test_check_a_never_falls_back_to_a_stored_date` |
| **D-065** | 13 | Alert issues lacked detailed failure reason | Low | FIXED | **FIXED** | 14 | `tests/test_watchdog.py::test_alert_reason_file_is_used` |
| **D-066** | 14 | `opi/run_daily.py` logs `SKIPPED_BLOCKED_SOURCE` without attempting fetch | Medium | - | **OPEN** | 14 | Scheduled for Workstream B |
| **D-067** | 14 | No alert when listed row has empty outcome > 2 days | Medium | - | **OPEN** | 14 | Scheduled for Workstream C |
| **D-068** | 14 | Cloud runner source reachability unmeasured | Medium | - | **OPEN** | 14 | Scheduled for Workstream A (`source_probe.md`) |
| **D-069** | 14 | Same-day listing cannot distinguish pre/post market open | Low | - | **OPEN** | 14 | Scheduled for Workstream B |
| **D-070** | 14 | Dashboard does not show pending listed outcome count | Low | - | **OPEN** | 14 | Scheduled for Workstream C |

---

## 3. Forward Results Table (Generated by `scripts/forward_report.py --markdown`)

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.00 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | LISTED | NSE official opening trade evidenced in snapshot `1ef0c35a650c` |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.25 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | LISTED | NSE official opening trade evidenced in snapshot `0783e1c0985b` |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.15 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | LISTED | NSE official opening trade evidenced in snapshot `d69406a6b7e8` |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1160.00 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | LISTED | NSE official opening trade evidenced in snapshot `4c486eeb1b8d` |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | LISTED | NSE official opening trade evidenced in snapshot `6df55c3addef` |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | Pending | Pending | +22.14% | +22.34% | Pending | Pending | FORWARD | listing scheduled 2026-10-28 |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | Pending | Pending | -2.56% | +1.59% | Pending | Pending | FORWARD | listing scheduled 2026-10-28 |

> **Provisional Evaluation Notice**: Sample size $n = 6$ of 30 target forward predictions. Results are strictly descriptive. No performance claims or statistical superiority statements are permitted prior to $n \ge 30$.

---

## 4. Gate A14 Results & Independent Verification

### G1. Prior-Phase Recheck (Seed 14 Sample) & Headline Recomputations
- Sampled 10 claims from Phase 13 outcome and verdict (seed 14) recorded in `phases/Phase 14/prior_phase_recheck.csv`:
  - 7 claims on specific IPO figures (HD Fire Protect, Zetwerk Mfg, Sahajanand Medical Technologies, Paras Healthcare, Jio Platforms, Bonfiglioli Transmissions, Tonbo Imaging).
  - 3 claims of the form "file X contains Y" (`requirements.lock`, `phases/Phase 11/forward_postmortem.md`, `docs/RUNBOOK.md`).
  - 10 of 10 claims verified.
- Recomputed 5 headline numbers directly from raw data via `scripts/recompute_gate_a14.py`:
  1. Forward Model MAE ($n=6$ listed): **6.7817 pp** (reported 6.78 pp).
  2. Forward Raw GMP MAE ($n=5$ with GMP): **7.9480 pp** (reported 7.95 pp).
  3. Master dataset row count: **731 data rows** in `data/ipo_master.csv`.
  4. Prediction log breakdown: **14 total rows** (6 non-forward/invalid, 8 genuine FORWARD: 6 listed, 2 pending).
  5. Defect counts: **70 total defects** seeded in `DEFECTS.md` (57 FIXED, 6 ACCEPTED, 1 PARTIAL, 1 NOT FIXED, 5 OPEN).

### G2. Regression Tests for Carried Defects (D-053 through D-065)
- All 13 defects D-053 through D-065 verified with named passing tests in `tests/`:
  - `tests/test_reporting.py::test_phase11_postmortem_has_errata` (D-053): PASS
  - `tests/test_gate_a.py::test_gate_a13_macro_correction` (D-054): PASS
  - `tests/test_gate_a.py::test_gate_a13_market_raw_decision` (D-055): PASS
  - `tests/test_dashboard.py::test_dashboard_shows_last_cloud_run` (D-056): PASS
  - `tests/test_alerts.py::test_handle_failure_creates_new_issue_when_none_open` (D-057): PASS
  - `tests/test_watchdog.py::test_scheduled_run_freshness_fresh` (D-058): PASS
  - `tests/test_ci.py::test_requirements_lock_and_ci_pinning` (D-059): PASS
  - `tests/test_final_evaluation.py::test_full_evaluation_on_synthetic_fixture` (D-060): PASS
  - `tests/test_docs.py::test_runbook_sections_and_headings` (D-061): PASS
  - `tests/test_ci.py::test_workflows_pin_runner_and_node24_actions` (D-062): PASS
  - `tests/test_ci.py::test_ci_local_replicates_ci_order` (D-063): PASS
  - `tests/test_watchdog.py::test_check_a_never_falls_back_to_a_stored_date` (D-064): PASS
  - `tests/test_watchdog.py::test_alert_reason_file_is_used` (D-065): PASS

### G3. GitHub Actions Scheduled Runs & Issues Health
- Live check via `gh run list --event schedule -L 12` and `gh api repos/soul991/OPI/issues`:
  - Last 8 consecutive scheduled `daily.yml` runs are 100% green.
  - Zero open alert issues in the repository.
  - Documented in `phases/Phase 14/actions_status.md`.

### G4. Dashboard & Prediction Log Agreement
- Dashboard displays "6 of 30" forward predictions completed.
- Prediction log contains 8 genuine FORWARD rows (6 listed with verified actuals, 2 pending: Jio Platforms Limited and Paras Healthcare Limited, listed 2026-10-28).

### G5. Secrets Presence & Sanitization
- `gh secret list` confirms `OPENROUTER_API_KEY` present.
- `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. Zero API key material committed.

---

## 5. Workstream Results & Verification Evidence
*(Workstreams A through C paused at Step 5 per protocol. To be executed upon user "continue" instruction.)*

---

## 6. Wording Check
In strict adherence to the preregistration rules:
- No claims of "superiority", "outperformance", or "beating" GMP are made.
- The forward evaluation status remains explicitly **PROVISIONAL ($n = 6$ of 30)**.
- Model MAE (6.78 pp) and Raw GMP MAE (7.95 pp) are presented purely as descriptive statistics.

---

## 7. Self-Audit (Yes/No, with Pasted Evidence)

| Audit Question | Verdict | Pasted Terminal Evidence |
|---|:---:|---|
| Did any report number come from anywhere but a script over the log/evidence? | **NO** | All headline figures generated via `scripts/recompute_gate_a14.py` and `scripts/forward_report.py --markdown`. |
| Did any claim in the summary say a file was changed when it was not? | **NO** | Verified each change with `git diff --stat` prior to staging and commit. |
| Did any earlier-phase file change except by ERRATA? | **NO** | Zero modifications to historical phase directories. |
| Did any value enter a feature without a snapshot? | **NO** | Zero modifications to logged feature values in `predictions/prediction_log.csv`. |
| Did the work stop after Gate A14? | **YES** | Execution strictly halted at Step 5 awaiting explicit user "continue" confirmation. |
| Was the key kept out of the repo, logs, issues, and snapshots? | **YES** | `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. |

---

## 8. Handover State
- Gate A14 complete and fully verified.
- Repository ready for Workstreams A through C upon user continuation signal.
