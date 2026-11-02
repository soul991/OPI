# Phase 16: Building & Execution Log (Gate A16)

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). Quantitative research decision aid only, not financial advice.  
> **Status at Gate A16**: Gate A16 Complete (G1–G7 verified). Work paused awaiting explicit user "continue" instruction.

---

## 1. Pipeline Architecture & Data Flow

Phase 16 establishes the pre-listing predictions list, automated GMP discovery, research agent integration into the scheduled pipeline, and reporting monthly retraining:
- **Baseline Verification Suites**:
  - `scripts/verify_all.py` -> `phases/Phase 16/verify_start.txt` (baseline captured at phase start).
  - `scripts/verify_extra.py` -> `phases/Phase 16/verify_extra_start.txt` (7 pass, 0 warn, 0 fail).
  - `scripts/ci_local.py` -> Clean run simulated locally.
- **Defects Seeded (DEFECTS.md)**:
  - `D-079` (High): No pre-listing predictions list; pending forward predictions visible only as "Pending" rows in audit trail; IPOs with bidding open invisible.
  - `D-080` (High): Four IPOs sat unscored for days (skipped every run) while their listing dates approached, with green runs and no alert.
  - `D-081` (High): `gmp_url` is never found automatically, so new IPOs are scored without GMP.
  - `D-082` (Medium): The research agent is not part of the daily job; D-026 is unprovable.
  - `D-083` (Medium): Monthly retraining never promotes listed rows (dry run), opens no pull request, and a Phase 13 claim says it does.
  - `D-084` (Medium): The four automatically scored rows (2026-11-01) have never been audited for provenance, final subscription and snapshots.
- **Gate A16 Audits (G1–G7)**:
  - **G1**: 10 random claims from `phases/Phase 15/3_outcome_and_verdict.md` (seed 16) audited against underlying files; 5 headline numbers recomputed directly from raw files via `scripts/recompute_gate_a16.py` and logged to `phases/Phase 16/prior_phase_recheck.csv`.
  - **G2**: Verified that all FIXED defects from D-066 through D-078 have passing regression tests (12 passed in 12.77s).
  - **G3**: Audited GitHub Actions scheduled runs, issues, commit mapping since `phase15-gate-a`, and logged to `phases/Phase 16/actions_status.md`.
  - **G4**: Effective outcomes checked for all 8 listed forward rows using `opi/outcomes.py`; `predictions/prediction_log.csv` is byte-identical and unmodified.
  - **G5**: Verified `gh secret list` confirms `OPENROUTER_API_KEY`; `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns strictly 0 matches.
  - **G6**: Audited the four 2026-11-01 automatically scored rows (M.K.Sons, BLS Polymers, SFC Environmental, EAAA India Alternatives); confirmed `scored_at` strictly before listing dates, final subscriptions, saved HTML snapshots, and documented missing GMP (D-081).
  - **G7**: Read real dates for Bombay Coated & Special Steels Limited directly from Chittorgarh using project discovery code: Bidding 2026-10-29 to 2026-11-02, Listing 2026-11-05, not yet in log, bidding open today (closes at 17:00 IST).

---

## 2. Scripts Created / Modified

- `DEFECTS.md`: Appended seeded defects D-079 through D-084 as `OPEN` with due phase 16.
- `scripts/recompute_gate_a16.py`: Recomputes headline numbers from raw files and samples 10 claims with seed 16.
- `phases/Phase 16/verify_start.txt`: Baseline output of `verify_all.py` at phase start.
- `phases/Phase 16/verify_extra_start.txt`: Baseline output of `verify_extra.py` at phase start.
- `phases/Phase 16/prior_phase_recheck.csv`: 10 sampled claims (seed 16) and 5 headline recomputations.
- `phases/Phase 16/actions_status.md`: Audit of secret presence, last 10 scheduled runs, issues, and commit history defect mapping.
- `phases/Phase 16/2_building_and_execution.md`: This execution log.
- `phases/Phase 16/3_outcome_and_verdict.md`: Gate A16 outcome and verdict document.
- `phases/Phase 16/preregistration.md`: Phase 16 preregistration specification.

---

## 3. Data Purification & Engineering Steps

1. **Recomputed 5 headline metrics** directly from raw files:
   - Overall Prospective Model MAE ($n=8$ listed): **5.99 pp** (5.9913 pp).
   - Raw GMP MAE ($n=7$ with GMP): **6.15 pp** (6.1471 pp).
   - Model MAE on GMP subset ($n=7$): **6.67 pp** (6.6743 pp).
   - Model MAE excluding Bonfiglioli ($n=7$): **3.83 pp** (3.8329 pp).
   - Master dataset row count: **731 rows** in `data/ipo_master.csv`.
2. **Effective Outcomes Audit (G4)**:
   - Confirmed `predictions/prediction_log.csv` has zero unstaged or uncommitted modifications.
   - Evaluated all 8 listed rows through `opi.outcomes.effective_outcome`.
   - Confirmed Paras Healthcare Limited displays effective gain of +3.90% (vs raw 4.04%) via `predictions/outcome_corrections.csv` (D-073).
3. **Four 2026-11-01 Forward IPOs Audit (G6)**:
   - Evaluated M.K.Sons Fine Jewels, BLS Polymers, SFC Environmental Technologies, and EAAA India Alternatives.
   - All scored at 2026-11-01T22:31 IST, strictly before scheduled listings (2026-11-02, 2026-11-03, 2026-11-04).
   - Final subscription figures match saved evidence snapshots in `data/evidence/subscription/`.
   - Identified missing GMP values as Defect D-081.
4. **Bombay Coated & Special Steels Status (G7)**:
   - Read overview page `https://www.chittorgarh.com/ipo/bombay-coated-and-special-steels-ipo/2671/` using `opi/discover.py`.
   - Extracted official timetable: Bidding Open 2026-10-29, Close 2026-11-02, Listing 2026-11-05.
   - Verified company is NOT in `prediction_log.csv` yet.
   - Bidding closes today (2026-11-02 at 17:00 IST); scoring must happen only after bidding close with final subscription and before listing.

---

## 4. Exact Terminal Commands Executed

```bash
# 1. Dependency check and baseline verification
python -m pip install -r requirements.lock pytest
python -c "import subprocess, pathlib; out = subprocess.run(['python', 'scripts/verify_all.py'], capture_output=True, text=True, encoding='utf-8').stdout; pathlib.Path('phases/Phase 16/verify_start.txt').write_text(out, encoding='utf-8')"
python -c "import subprocess, pathlib; out = subprocess.run(['python', 'scripts/verify_extra.py'], capture_output=True, text=True, encoding='utf-8').stdout; pathlib.Path('phases/Phase 16/verify_extra_start.txt').write_text(out, encoding='utf-8')"
python scripts/ci_local.py

# 2. Gate A16 audits
python scripts/recompute_gate_a16.py
pytest -q tests/test_actuals_job.py::test_tier2_success_with_agreeing_second_source tests/test_watchdog.py::test_missing_outcomes_threshold_boundary tests/test_actuals_job.py::test_two_tier_probe_committed tests/test_actuals_job.py::test_is_listing_ready_for_actuals_market_hours_rule tests/test_dashboard.py::test_dashboard_shows_listed_outcome_pending_count_and_names tests/test_actuals_job.py::test_yfinance_rejects_missing_listing_day_bar_paras_data tests/test_outcomes_corrections.py::test_reports_agree_with_effective_value tests/test_actuals_job.py::test_runner_probe_committed_and_verified tests/test_workflow_entrypoints.py::test_workflow_entrypoints_smoke tests/test_ci.py::test_phase15_process_rule_defect_registration_and_branch_pr tests/test_discover.py::test_derive_subscription_url_from_overview_url tests/test_discover.py::test_derive_subscription_url_edge_cases
gh run list --event schedule -L 12
gh api "repos/soul991/OPI/issues?state=all"
gh secret list
git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"
```

---

## 5. Artifacts and Generated Data Files

- `phases/Phase 16/verify_start.txt`: Baseline `verify_all.py` output.
- `phases/Phase 16/verify_extra_start.txt`: Baseline `verify_extra.py` output.
- `phases/Phase 16/prior_phase_recheck.csv`: 10 sampled claims (seed 16), 5 headline recomputations.
- `phases/Phase 16/actions_status.md`: Audit of secret presence, last 10 scheduled runs, issues, and commit history defect mapping.
