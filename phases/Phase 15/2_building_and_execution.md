# Phase 15: Building & Execution Log

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Final Status**: All Phase 15 deliverables complete across Gate A15, Workstreams A, B, and C, pull request workflow (PR #7 merged), and cloud post-merge verification.

---

## 1. Summary of Workstreams & Milestones

Phase 15 resolves outcome recording inaccuracies, establishes audited append-only corrections, closes the runner probe gap, and eliminates execution divergence between local development and cloud workflows:

1. **Gate A15 Re-Verification & Preregistration**:
   - Initial test suites captured:
     - `phases/Phase 15/verify_start.txt`: 68 pass, 0 warn, 0 fail.
     - `phases/Phase 15/verify_extra_start.txt`: 7 pass, 0 warn, 0 fail.
     - `scripts/ci_local.py`: `CI_LOCAL: PASS`.
   - Gate audits completed:
     - G1: 10 sampled Phase 14 claims verified with seed 15 in `phases/Phase 15/prior_phase_recheck.csv`, 5 headline recomputations, and saved trading-day bar analysis for Jio and Paras.
     - G2: Defect regression tests verified; unverified runner probe identified on D-068.
     - G3: Scheduled runs and closed Issue #6 documented in `phases/Phase 15/actions_status.md`. All 15 commits since `phase14-gate-a` mapped to defect IDs, identifying commits `06ff884` and `9dd1b7d` as process defects (D-076).
     - G4: Paras Healthcare trading bars printed side-by-side with Chittorgarh quote page, proving the log recorded the 2026-10-29 session bar rather than listing-day 2026-10-28.
     - G5: Secret hygiene confirmed (`gh secret list` and `git grep sk-or-` clean).
   - Gate A committed on `main` (`phase15-gate-a`, commit `da1ce53`).
   - Preregistration committed on `main` (`phase15-preregistration`, commit `fe6f83a`).
   - Feature branch `feat/phase15-workstreams` created.

2. **Workstream A: Enforce Listing-Day Date Equality (D-072)**:
   - Modified `fetch_yfinance_first_session_open` in `opi/actuals.py`:
     - Converted timestamps to `Asia/Kolkata`.
     - Required exact bar date equality to `listing_date`.
     - Deleted the `iloc[0]` fallback. Returns `(None, "LISTING_DAY_BAR_MISSING: first bar is <date>, listing date <date>", raw_bytes)`.
     - The Tier 2 caller returns `SKIPPED_NO_MATCH` and never records another day's price.
   - Added 5 unit tests in `tests/test_actuals_job.py`: Paras two-bar failure, valid bar pass, UTC midnight rollover (`18:30Z` previous day is next IST day), Jio data pass, and `SKIPPED_NO_MATCH` status.
   - Committed on branch: `phase15-workstream-a: enforce listing-day date equality in yfinance (D-072)` (`bf57012`).

3. **Workstream B: Audited Append-Only Corrections Engine & Paras Correction (D-073)**:
   - Committed `phases/Phase 15/preregistration_amendment.md` specifying the Tier 2b multi-source verification protocol (relative tolerance $\le 1.0\%$ across two independent code-fetched pages, neither Yahoo Finance).
   - Implemented audited corrections framework in `opi/outcomes.py`:
     - `effective_outcome(row)`: Dynamically merges the latest correction from `predictions/outcome_corrections.csv` without modifying `predictions/prediction_log.csv`.
     - `get_effective_predictions_df()`: Returns the full dataset with effective values and `outcome_source_effective`.
     - `record_outcome_correction()`: Appends audited records to `predictions/outcome_corrections.csv`.
     - `fetch_tier2b_independent_sources()`: Automated fetcher for Chittorgarh and Groww.
   - Applied Paras Healthcare correction via `scripts/apply_paras_correction.py`:
     - Chittorgarh Quote: ₹720.00
     - Groww Research: ₹720.00
     - Relative divergence: 0.00% ($\le 1.0\%$).
     - Saved evidence: `data/evidence/actuals/2026-10-28_paras-healthcare-limited_chittorgarh_tier2b.*` and `..._groww_tier2b.*`.
     - Raw log (+4.04%) preserved; effective outcome updated to +3.90% (₹720.00).
     - Verified `predictions/prediction_log.csv` is 100% byte-identical (`git diff` clean).
   - Updated reporting pipeline (`opi/report.py`, `scripts/forward_report.py`, `scripts/final_evaluation.py`) to query outcomes through `get_effective_predictions_df()`.
   - Added unit tests in `tests/test_outcomes_corrections.py`.
   - Committed on branch: `phase15-workstream-b: append-only outcome corrections engine, Tier 2b protocol, and Paras correction (D-073)` (`278f80d`).

4. **Workstream C: Cloud Runner Probe & Workflow Smoke Testing (D-074, D-075, D-076)**:
   - Updated `.github/workflows/probe_sources.yml` and `scripts/probe_sources.py` to write `phases/Phase 15/source_probe_runner.md` from the runner with OS, Python version, and `GITHUB_RUN_ID`.
   - Created standalone workflow smoke test in `tests/test_workflow_entrypoints.py`:
     - Dynamically parses all `.github/workflows/*.yml`.
     - Runs each Python entrypoint with `--help` and `PYTHONPATH` unset.
     - Proved that pre-fix `scripts/watchdog.py` (`06ff884`) fails with `ModuleNotFoundError: No module named 'scripts'` while current code passes.
   - Integrated entrypoints smoke test into `scripts/ci_local.py` as Step 1.
   - Updated `PHASE_PROTOCOL.md` to require defect registration, feature branch, PR, and `ci_local.py` before push (D-076).
   - Committed on branch: `phase15-workstream-c: workflow entrypoints smoke test, runner probe config, and protocol rules (D-075, D-076)` (`7fa8d15`).
   - Dispatched cloud runner probe (`gh workflow run probe_sources.yml --ref feat/phase15-workstreams`, run `41128632410`). The runner completed on Ubuntu Linux (`Python 3.12.15 on linux`) and committed `phases/Phase 15/source_probe_runner.md` directly.
   - Added regression test `tests/test_actuals_job.py::test_runner_probe_committed_and_verified` and marked D-074 `FIXED`.
   - Committed on branch: `phase15-workstream-c: mark D-074 fixed with runner probe test` (`79869f6`).

5. **Pull Request & Cloud Verification**:
   - Opened PR #7: `Phase 15: Correct Paras outcome, listing-day enforcement, runner parity, and workflow smoke tests`.
   - Merged PR #7 into `main` via `gh pr merge 7 --merge` (commit `eca59d2`).
   - Checked out `main` and pulled latest merge.
   - Dispatched workflows on `main`:
     - `daily.yml`: Run `41129785639` (Success, 1m56s).
     - `watchdog.yml`: Run `41129797926` (Success, 33s).
   - Pulled bot commit from scheduled run (`predictions/run_log.csv` and `dashboard/index.html`).

---

## 2. Scripts & Workflows Created / Modified

- `opi/actuals.py`: Enforced bar date equality in `fetch_yfinance_first_session_open`; deleted `iloc[0]` fallback; returns `LISTING_DAY_BAR_MISSING`.
- `opi/outcomes.py`: Implemented append-only corrections logic (`effective_outcome`, `get_effective_predictions_df`, `record_outcome_correction`, `fetch_tier2b_independent_sources`).
- `predictions/outcome_corrections.csv`: Append-only audited corrections store.
- `scripts/apply_paras_correction.py`: Code-fetched multi-source fetcher and verification script for Paras Healthcare.
- `scripts/recompute_phase15.py`: Computes headline numbers from effective outcomes.
- `scripts/forward_report.py`: Integrated `get_effective_predictions_df()` and added `Tier` column to markdown table.
- `scripts/final_evaluation.py`: Updated to use `get_effective_predictions_df()`.
- `opi/report.py`: Updated dashboard generation to use `get_effective_predictions_df()`.
- `.github/workflows/probe_sources.yml`: Configured permissions, step summary, artifact upload, and bot commit.
- `scripts/probe_sources.py`: Added `--output` CLI argument and GitHub Actions run ID detection.
- `phases/Phase 15/source_probe_runner.md`: Cloud runner empirical probe report produced by GitHub Actions run `41128632410`.
- `tests/test_workflow_entrypoints.py`: Smoke test parsing all GitHub workflows and proving pre-fix failure on `watchdog.py`.
- `scripts/ci_local.py`: Integrated entrypoint smoke test as Step 1.
- `PHASE_PROTOCOL.md`: Added rule requiring defect registration, branch, PR, and `ci_local.py` pre-push check (D-076).
- `DEFECTS.md`: Seeded D-072 through D-076; marked D-072, D-073, D-074, D-075, D-076 as `FIXED`.
- `tests/test_actuals_job.py`: Added 5 regression tests for D-072 and 1 test for D-074 runner probe.
- `tests/test_outcomes_corrections.py`: Added 5 unit tests for D-073.
- `tests/test_ci.py`: Added `test_phase15_process_rule_defect_registration_and_branch_pr` for D-076.
- `dashboard/index.html`: Refreshed with effective outcomes and defect counts.

---

## 3. Evidence Artifacts & Recomputation Reference

All recomputed metrics are produced deterministically by `scripts/recompute_phase15.py`:

```text
======================================================================
  PHASE 15 RECOMPUTED HEADLINE METRICS (EFFECTIVE OUTCOMES)
======================================================================
Listed Forward IPOs (n)           : 8
Model MAE (n=8)                     : 5.9913 pp (5.99 pp)
GMP MAE (n=7)                       : 6.1471 pp (6.15 pp)
Model MAE on GMP subset (n=7)        : 6.6743 pp (6.67 pp)
Model MAE excluding Bonfiglioli (n=7): 3.8329 pp (3.83 pp)
----------------------------------------------------------------------
Paras Healthcare Actual (raw)     : +4.04%
Paras Healthcare Actual (eff)     : +3.90%
Paras Healthcare Model Error Before: 6.60 pp
Paras Healthcare Model Error After : 6.46 pp
Paras Healthcare GMP Error Before  : 2.45 pp
Paras Healthcare GMP Error After   : 2.31 pp
======================================================================
```
