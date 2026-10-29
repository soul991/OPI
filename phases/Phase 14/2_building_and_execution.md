# Phase 14: Building & Execution Log (Gate A14)

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Current Status**: Gate A14 Complete; stopped at Step 5 awaiting user "continue" confirmation prior to starting Workstreams A through C.

---

## 1. Pipeline Architecture & Data Flow

Phase 14 executes Gate A14 re-verification of Phase 13, seeds defects D-066 through D-070, prepares automated cloud listing outcome recording, and designs alerting for missing outcomes:
- **Independent Verification Suites**: `scripts/verify_all.py` and `scripts/verify_extra.py` (read-only, unmodified).
- **Gate A14 Re-verification**: Audit of 10 claims from Phase 13 outcome and verdict (seed 14) in `phases/Phase 14/prior_phase_recheck.csv`, 5 headline number recomputations via `scripts/recompute_gate_a14.py`.
- **Defects Seeded**: Seeded D-066 through D-070 in `DEFECTS.md` covering automated outcome recording gaps, missing outcome watchdog alert, cloud runner source probe, same-day market hours logic, and dashboard pending listing visibility.
- **Local CI Automation (`scripts/ci_local.py`)**: Authored local CI test runner enforcing secret scanning (`sk-or-`), pytest suite, `verify_all.py`, and `verify_extra.py` before git pushes.
- **Actions Health & Secrets Verification (G3, G5)**: Audited live via GitHub CLI (`gh`): verified 100% green scheduled runs post-Phase 13, 0 open alert issues, `OPENROUTER_API_KEY` configured in GitHub secrets, and 0 secret keys committed in the repository.

---

## 2. Scripts Created / Modified
- `DEFECTS.md`: Seeded defects D-066 through D-070 as `OPEN`.
- `scripts/ci_local.py`: Authored local CI pre-push gate runner.
- `scripts/recompute_gate_a14.py`: Script to recompute 5 headline numbers and evaluate 10 sampled claims (seed 14) from Phase 13.
- `phases/Phase 14/verify_start.txt`: Baseline output of `scripts/verify_all.py` at phase start.
- `phases/Phase 14/verify_extra_start.txt`: Baseline output of `scripts/verify_extra.py` at phase start.
- `phases/Phase 14/prior_phase_recheck.csv`: 10 sampled claims (seed 14) and 5 headline recomputations.
- `phases/Phase 14/actions_status.md`: Audit log of GitHub Actions scheduled runs, issues, and secret presence.

---

## 3. Data Purification & Engineering Steps
- Recomputed all 5 headline metrics directly from `predictions/prediction_log.csv`, `data/ipo_master.csv`, and `DEFECTS.md`.
- Verified zero modifications to logged feature or prediction rows in `predictions/prediction_log.csv`.
- Confirmed zero secret keys (`sk-or-`) committed across the entire repository.

---

## 4. Exact Terminal Commands Executed
```bash
# 1. Dependency verification and baseline verification runs
pip install -r requirements.lock pytest
python -c "import subprocess, pathlib; out = subprocess.run(['python', 'scripts/verify_all.py'], capture_output=True, text=True, encoding='utf-8').stdout; pathlib.Path('phases/Phase 14/verify_start.txt').write_text(out, encoding='utf-8')"
python -c "import subprocess, pathlib; out = subprocess.run(['python', 'scripts/verify_extra.py'], capture_output=True, text=True, encoding='utf-8').stdout; pathlib.Path('phases/Phase 14/verify_extra_start.txt').write_text(out, encoding='utf-8')"

# 2. Local CI suite execution
python scripts/ci_local.py

# 3. Gate A14 checks and recomputations
python scripts/recompute_gate_a14.py
gh run list --event schedule -L 12 --json databaseId,status,conclusion,name,createdAt,updatedAt
gh api repos/soul991/OPI/issues
gh secret list
git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"

# 4. Regression tests check for D-053 through D-061
pytest tests/test_reporting.py::test_phase11_postmortem_has_errata tests/test_gate_a.py::test_gate_a13_macro_correction tests/test_gate_a.py::test_gate_a13_market_raw_decision tests/test_dashboard.py::test_dashboard_shows_last_cloud_run tests/test_alerts.py::test_handle_failure_creates_new_issue_when_none_open tests/test_watchdog.py::test_scheduled_run_freshness_fresh tests/test_ci.py::test_requirements_lock_and_ci_pinning tests/test_final_evaluation.py::test_full_evaluation_on_synthetic_fixture tests/test_docs.py::test_runbook_sections_and_headings
```

---

## 5. Artifacts and Generated Data Files
- `phases/Phase 14/verify_start.txt`: Baseline `verify_all.py` output.
- `phases/Phase 14/verify_extra_start.txt`: Baseline `verify_extra.py` output.
- `phases/Phase 14/prior_phase_recheck.csv`: 10 sampled claims (seed 14) and 5 headline recomputations.
- `phases/Phase 14/actions_status.md`: Audit of secret presence and last 10 scheduled runs.
