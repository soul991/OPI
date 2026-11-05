# Phase 17: Outcome & Verdict

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Mandatory Small-Sample Epistemic Guardrail**: Sample size is currently $n = 9$ listed of 30 target forward predictions ($n = 7$ with GMP, 4 pending unlisted). All metrics and error distributions are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## ERRATA

No errata identified for Phase 17. (Phase 16 errata are recorded in `phases/Phase 16/2_building_and_execution.md` and `phases/Phase 16/3_outcome_and_verdict.md`.)

---

## 1. Targets Missed & Unfixed Items

The following items in `DEFECTS.md` remain open or partial at the conclusion of Phase 17:

1. **D-013 (Historical Phase 7 Audit Samples Lack Snapshots)**:
   - **Status**: `PARTIAL`.
   - **Reason**: 20 historical audit samples from Phase 7 have URLs routing to 404s or wrong SME entities on Chittorgarh; re-scraping is blocked by web permissions and rules prohibit inventing data. Maintained as a tracked historical defect per `PHASE_PROTOCOL.md`.
2. **D-026 (Live Web Research Agent Cloud Proof)**:
   - **Status**: `NOT FIXED`.
   - **Reason**: The research agent is wired into `opi.run_daily` with strict grounding and bounding checks (D-082), but has not yet executed against a real unlisted IPO during a scheduled cloud run. Per project rules, no synthetic, mock, or fake IPOs may ever be created to artificially force a fix.
3. **D-085 (Market Evidence for Missing Listing Dates)**:
   - **Status**: `PARTIAL`.
   - **Reason**: Automated market evidence collection was wired into `opi.run_daily` and successfully recorded `data/evidence/market/2026-11-02_nifty.raw` and `.json` in daily cloud run `41925558666`. Market evidence for 2026-11-03 remains pending until the listing outcomes for BLS Polymers and SFC Environmental are recorded.
4. **Targets Missed**:
   - Defect D-026 remains `NOT FIXED` (pending live scheduled IPO event).
   - Defect D-085 remains `PARTIAL` (pending 2026-11-03 listing actuals).
   - Defect D-013 remains `PARTIAL` (accepted historical constraint).

---

## 2. Defect Ledger

| Defect ID | Phase Seeded | Summary Description | Severity | Final Status | Closed Phase | Verification Proof / Test Name |
|---|:---:|---|:---:|:---:|:---:|---|
| **D-013** | 8 | Discrepancies between Phase 7 and Phase 8 summary files. | Low | **PARTIAL** | — | Historical tracking preserved |
| **D-026** | 7/9 | Real scheduled cloud research run with live OpenRouter model not proven on a new IPO. | High | **NOT FIXED** | — | Awaiting next real upcoming IPO bidding cycle; no mock IPOs permitted |
| **D-071** | 14 | Dashboard card and verify_all.py count only OPEN and PARTIAL, omitting NOT FIXED items. | Low | **FIXED** | 17 | `tests/test_dashboard.py::test_verify_all_and_dashboard_count_not_fixed` |
| **D-083** | 16 | Monthly retraining opens pull request with challenger comparison. | Medium | **FIXED** | 17 | `tests/test_retraining.py::test_monthly_retrain_workflow_opens_pr` (Cloud proof: PR #17, run `41927342216`) |
| **D-085** | 17 | No Nifty market evidence is saved for new listing dates. | Medium | **PARTIAL** | — | `tests/test_market_evidence_job.py::test_job_records_missing_listing_date_nifty_evidence` (Cloud proof: run `41925558666`, 2026-11-02 evidence recorded) |
| **D-086** | 17 | `verify_extra.py` is not run by any workflow or by `ci_local.py`. | Medium | **FIXED** | 17 | `tests/test_watchdog.py::test_watchdog_runs_verify_extra_and_reports_failure` (Cloud proof: watchdog run `41926847918`) |
| **D-087** | 17 | Monthly retraining PR governance, permissions, and validation. | Medium | **FIXED** | 17 | `tests/test_retraining.py::test_monthly_retrain_workflow_branch_verification_and_alerting` (Cloud proof: PR #17, run `41927342216`) |
| **D-088** | 17 | Phase 16 reports quote verification results that differ from committed output files. | Low | **FIXED** | 17 | `tests/test_reporting.py::test_quoted_verify_results_match_saved_files` |
| **D-089** | 17 | D-071 is stale: `verify_all.py` counts NOT FIXED now, the register still says PARTIAL. | Low | **FIXED** | 17 | `tests/test_dashboard.py::test_verify_all_and_dashboard_count_not_fixed` |
| **D-090** | 17 | Pre-listing table shows the close date twice as the bidding window. | Low | **FIXED** | 17 | `tests/test_pre_listing.py::test_pre_listing_table_shows_distinct_bidding_dates` |
| **D-091** | 17 | Daily failure alerts name the step "Execution" with a generic reason. | Low | **FIXED** | 17 | `tests/test_alerts.py::test_daily_alert_includes_failed_step_name_and_trace` (Run `41908615355` trace verification) |
| **D-092** | 17 | Monthly promotion rewrites master dataset (year 2010 -> 2010.0 and updated_at added). | Medium | **FIXED** | 17 | `tests/test_retraining.py::test_promote_forward_rows_byte_identical_existing` (PR #17: 0 existing rows changed, +9 additions only) |
| **D-093** | 17 | PR breaks tests unnoticed: discovery tests dependent on master membership; lack of CI on bot PRs. | Medium | **FIXED** | 17 | `tests/test_discover.py::test_discovery_independent_of_master_membership` (PR #17 branch run verification embedded in PR body) |
| **D-094** | 17 | `verify_all.py` fails "three required files" during in-progress phases, causing `daily.yml` to skip commits. | High | **FIXED** | 17 | `tests/test_reporting.py::test_verify_all_allows_in_progress_phase` (Cloud proof: daily run `41925558666`) |

---

## 3. Forward Table & Prospective Performance

### Prospective Forward Table (`python scripts/forward_report.py --markdown`)

```text
[!] PROVISIONAL STATUS BANNER: n listed = 9 of 30
    Per pre-registered rules: no empirical superiority claims or interval comparisons
    are permitted below n = 30 ('n too small'). All metrics are strictly descriptive.
```

- **Current Cohort Model MAE ($n = 9$)**: **5.85 percentage points**
- **Prior Cohort Model MAE ($n = 8$)**: **5.99 percentage points**
- **Provisional Raw GMP MAE ($n = 7$)**: **6.15 percentage points**
- *(Contextual diagnostic note: Excluding Bonfiglioli Transmissions (21.10 pp outlier), Model MAE is 3.94 pp across $n=8$ with GMP).*

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Tier | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | unspecified | LISTED | BSE official opening trade (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.00 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | unspecified | LISTED | NSE official opening trade evidenced in snapshot `1ef0c35a650c` |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.25 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `0783e1c0985b` |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.15 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `d69406a6b7e8` |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1160.00 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `4c486eeb1b8d` |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `6df55c3addef` |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | ₹1358.02 | **+21.36%** | +22.14% | +22.34% | **0.78 pp** | **0.98 pp** | Tier 2 | LISTED | Closed 2026-10-23; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-10-28 | Actual opening price verified via https://finance.yahoo.com/quote/JPL.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.txt |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | ₹720.00 | **+3.90%** | -2.56% | +1.59% | **6.46 pp** | **2.31 pp** | Tier 2b | LISTED | Corrected (D-073) via Tier 2b from raw 4.04% |
| **M.K.Sons Fine Jewels** | 2026-11-04 | ₹162.00 | Pending | Pending | +4.37% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-04 |
| **BLS Polymers** | 2026-11-03 | ₹150.00 | Pending | Pending | +53.28% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-03 |
| **SFC Environmental Technologies** | 2026-11-03 | ₹330.00 | Pending | Pending | +5.49% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-03 |
| **EAAA India Alternatives** | 2026-11-02 | ₹1665.00 | ₹1675.49 | **+0.63%** | +5.35% | None (NOT_RECORDED) | **4.72 pp** | N/A | Tier 2 | LISTED | Closed 2026-10-28; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-02 | Actual opening price verified via https://finance.yahoo.com/quote/EDELALTS.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-11-02_eaaa-india-alternatives_a8a32fe858d1.txt |
| **Bombay Coated & Special Steels** | 2026-11-05 | ₹82.00 | Pending | Pending | +10.14% | +11.28% | Pending | Pending | — | FORWARD | listing scheduled 2026-11-05 |

---

## 4. Gate A17 Results

- Gate A17 baseline verification:
  - `phases/Phase 17/verify_start.txt: 74 pass, 1 warn, 3 fail`
  - `phases/Phase 17/verify_extra_start.txt: 6 pass, 0 warn, 1 fail`
- Exit verification:
  - `phases/Phase 17/verify_end.txt: 79 pass, 0 warn, 0 fail`
  - `phases/Phase 17/verify_extra_end.txt: 7 pass, 0 warn, 0 fail`
- Prior phase audit (`prior_phase_recheck.csv`): 10 of 10 sampled Phase 16 claims verified against primary data sources.

---

## 5. The Two Cloud Failures of 2026-11-02 and How Each Is Now Handled

1. **Daily Failure (`41463708776`)**:
   - Cause: Indentation error committed to `scripts/verify_all.py` caused pytest failure in the daily workflow. The alert issue (#11) generically reported "Execution" without naming the step.
   - Resolution: Step IDs and failure reasoning capture were implemented in `daily.yml` (D-091). Alerts now name the specific step (`Run Test Suite` or `Run Independent Repository Verification`) and attach the last 40 lines of output.
2. **Monthly Retraining Dispatch Failure (`41453047131`)**:
   - Cause: The step "Open Pull Request with Challenger Comparison" failed due to missing GitHub Actions PR permissions. A subsequent manual run created defective PR #12 (731 rows altered, discovery test broke).
   - Resolution: `monthly_retrain.yml` now detects permission errors and opens an alert directing maintainers to the exact setting toggle. `scripts/promote_forward_rows.py` was refactored to ensure byte-identical row promotion (D-092), and discovery tests were isolated from master data (D-093). Verified by PR #17 from run `41927342216`.

---

## 6. Market Evidence Run IDs

- **Daily Workflow Run `41925558666`**: Successfully created and committed `data/evidence/market/2026-11-02_nifty.raw` and `data/evidence/market/2026-11-02_nifty.json` (commit `c8b14bb`).
- **Watchdog Workflow Run `41926847918`**: Executed `verify_extra.py` in cloud CI (`Check (f) [Verification Extra Guard]: PASS`).
- **Monthly Retraining Workflow Run `41927342216`**: Successfully evaluated challenger and opened compliant PR #17 with real branch verification summaries.

---

## 7. Consistency-Test Proof on Old and New Text

Regression test `tests/test_reporting.py::test_quoted_verify_results_match_saved_files` guarantees that every verification figure quoted in Phase 14-17 documents matches the underlying output files:
- Running against historical commit `d814892` (pre-ERRATA Phase 16) fails with explicit mismatch detection (`71 pass, 0 warn, 0 fail != 71 pass, 1 warn, 3 fail`).
- Running against the current repository state with ERRATA passes 100%.

---

## 8. Self-Audit (Yes/No, with Pasted Evidence)

| Audit Question | Verdict | Pasted Evidence / Verification |
|---|:---:|---|
| Did any report number come from anywhere but a script over the log, corrections or evidence? | **NO** | All figures sourced via `forward_report.py`, `verify_all.py`, and `verify_extra.py`. |
| Does every quoted verify or pytest result equal its output file? | **YES** | Verified by `test_quoted_verify_results_match_saved_files` across Phases 14-17. |
| Was any evidence file written by hand or from this computer? | **NO** | `data/evidence/market/2026-11-02_nifty.{raw,json}` committed solely by `github-actions[bot]` in run `41925558666`. |
| Did `verify_extra.py` change? | **NO** | `git log -- scripts/verify_extra.py` shows zero changes in Phase 17. |
| Did any earlier-phase file change except by ERRATA? | **NO** | Verified by `verify_all.py` check `earlier-phase artifacts unchanged since phase17-gate-a`. |
| Does any FIXED row rely on something not proven in the cloud? | **NO** | D-083, D-087, D-092, D-093 proven by PR #17 (run `41927342216`); D-086 proven by run `41926847918`; D-094 proven by run `41925558666`. |
| Did any existing row of `data/ipo_master.csv` change? | **NO** | PR #17 git diff shows `+9 / -0` additions only; existing 731 rows byte-identical. |
| Was PR #12 merged or pushed to? | **NO** | PR #12 was closed unmerged by user. |
| Was the key kept out of the repo, logs, issues and snapshots? | **YES** | `git grep sk-or-` prints nothing; `verify_all.py` passes hygiene checks. |

---

## 9. Handover State

- Repository status on `main`: clean, verified, all workflows operational.
- Daily forward prediction pipeline is fully unblocked and committing evidence automatically.
- Open PRs: PR #17 (`retrain/challenger-20261104-224119`) awaiting maintainer review (DO NOT PROMOTE challenger verdict).
- Open issues: 0 open issues. All prior failure alerts resolved and closed.
