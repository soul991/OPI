# Phase 15: Building & Execution Log (Gate A15)

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). Quantitative research decision aid only, not financial advice.  
> **Status at Gate A15**: Gate A15 Complete (G1–G5 verified). Workstreams A, B, and C paused awaiting user "continue" instruction.

---

## 1. Pipeline Architecture & Data Flow

Phase 15 conducts Gate A15 re-verification of Phase 14, seeds defects D-072 through D-076, diagnoses the wrong-day outcome recorded for Paras Healthcare Limited, prepares the append-only corrections engine and Tier 2b multi-source fetcher, and designs entry-point workflow smoke tests:
- **Control & Verification Suites**: `scripts/verify_all.py` and `scripts/verify_extra.py` (read-only, unmodified).
- **Gate A15 Re-verification**: Audit of 10 claims from Phase 14 outcome and verdict (seed 15) in `phases/Phase 15/prior_phase_recheck.csv`, 5 headline number recomputations via `scripts/recompute_gate_a15.py`, and verification of the two new prospective outcomes (Jio Platforms and Paras Healthcare).
- **Defects Seeded**: Seeded D-072 through D-076 in `DEFECTS.md` covering:
  - D-072: Tier 2 wrong-session price fallback (Paras 2026-10-29 bar used instead of 2026-10-28).
  - D-073: Audited append-only correction mechanism (`predictions/outcome_corrections.csv`) preserving byte-identical prediction log.
  - D-074: Measurement of cloud runner reachability to exchanges and aggregators (`source_probe_runner.md`).
  - D-075: Workflow entry-point standalone smoke test catching missing environment paths / import regressions (as in run 41090951686, issue #6).
  - D-076: Governance rule preventing direct commits to `main` without defect registration, branches, and PRs.
- **Local CI Automation (`scripts/ci_local.py`)**: Runs daily pipeline simulation, pytest suite, and verification suites in a clean throwaway copy before pushing.
- **Actions Health & Secrets Verification (G3, G5)**: Audited via `gh run list`, `gh api repos/soul991/OPI/issues`, and `gh secret list`.

---

## 2. Scripts Created / Modified
- `DEFECTS.md`: Seeded defects D-072 through D-076 as `OPEN`.
- `scripts/recompute_gate_a15.py`: Script to recompute 5 headline numbers and evaluate 10 sampled claims (seed 15) from Phase 14.
- `phases/Phase 15/verify_start.txt`: Baseline output of `scripts/verify_all.py` at phase start.
- `phases/Phase 15/verify_extra_start.txt`: Baseline output of `scripts/verify_extra.py` at phase start.
- `phases/Phase 15/prior_phase_recheck.csv`: 10 sampled claims (seed 15), 5 headline recomputations, and outcome trading session verification.
- `phases/Phase 15/actions_status.md`: Audit log of GitHub Actions scheduled runs, closed issue #6, commit history mapping since `phase14-gate-a`, and secret presence.

---

## 3. Data Purification & Engineering Steps
- Recomputed all 5 headline metrics directly from `predictions/prediction_log.csv`, `data/ipo_master.csv`, and `DEFECTS.md`.
- Evaluated trading sessions for Jio Platforms Limited and Paras Healthcare Limited from saved evidence in `data/evidence/actuals/`:
  - Jio Platforms: Earliest bar timestamp `2026-10-27T18:30:00.000Z` (+05:30 IST) corresponds to `2026-10-28 00:00:00 IST` (correct listing session).
  - Paras Healthcare: Earliest bar timestamp `2026-10-28T18:30:00.000Z` (+05:30 IST) corresponds to `2026-10-29 00:00:00 IST` (wrong session; day after listing).
- Confirmed zero modifications to `predictions/prediction_log.csv`.
- Confirmed zero secret keys (`sk-or-`) committed across the entire repository.

---

## 4. Exact Terminal Commands Executed
```bash
# 1. Dependency verification and baseline verification runs
python -m pip install -r requirements.lock
python scripts/verify_all.py > "phases/Phase 15/verify_start.txt"
python scripts/verify_extra.py
python scripts/ci_local.py

# 2. Gate A15 recomputations and audits
python scripts/recompute_gate_a15.py
pytest -v tests/test_reporting.py::test_phase11_postmortem_has_errata tests/test_gate_a.py::test_gate_a13_macro_correction tests/test_gate_a.py::test_gate_a13_market_raw_decision tests/test_dashboard.py::test_dashboard_shows_last_cloud_run tests/test_alerts.py::test_handle_failure_creates_new_issue_when_none_open tests/test_watchdog.py::test_scheduled_run_freshness_fresh tests/test_ci.py::test_requirements_lock_and_ci_pinning tests/test_final_evaluation.py::test_full_evaluation_on_synthetic_fixture tests/test_docs.py::test_runbook_sections_and_headings tests/test_ci.py::test_workflows_pin_runner_and_node24_actions tests/test_ci.py::test_ci_local_replicates_ci_order tests/test_watchdog.py::test_check_a_never_falls_back_to_a_stored_date tests/test_watchdog.py::test_alert_reason_file_is_used tests/test_actuals_job.py::test_tier2_success_with_agreeing_second_source tests/test_watchdog.py::test_missing_outcomes_threshold_boundary tests/test_actuals_job.py::test_two_tier_probe_committed tests/test_actuals_job.py::test_is_listing_ready_for_actuals_market_hours_rule tests/test_dashboard.py::test_dashboard_shows_listed_outcome_pending_count_and_names
gh run list --event schedule -L 12
gh api "repos/soul991/OPI/issues?state=all"
gh secret list
git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"
```

---

## 5. Artifacts and Generated Data Files
- `phases/Phase 15/verify_start.txt`: Baseline `verify_all.py` output.
- `phases/Phase 15/verify_extra_start.txt`: Baseline `verify_extra.py` output.
- `phases/Phase 15/prior_phase_recheck.csv`: 10 sampled claims (seed 15), 5 headline recomputations, and outcome trading session verification.
- `phases/Phase 15/actions_status.md`: Audit of secret presence, last 10 scheduled runs, issue #6 closure, and commit history defect mapping.
