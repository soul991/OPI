# Phase 13: Building & Execution Log

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.
> **Final Status**: All Phase 13 deliverables complete across Gate A13 and Workstreams A through E.

---

## 1. Pipeline Architecture & Data Flow

Phase 13 completes the final build phase of the OPI quantitative IPO listing predictor framework, establishing self-monitoring cloud automation, prospective evaluation preregistration, and an operational maintainer runbook:
- **Independent Verification Suites**: `scripts/verify_all.py` (66 PASS / 0 FAIL) and `scripts/verify_extra.py` (7 PASS / 0 FAIL).
- **Gate A13 Re-verification**: Audit of 10 claims from Phase 12 outcome and verdict (seed 13) in `phases/Phase 13/prior_phase_recheck.csv`, 5 headline number recomputations via `scripts/recompute_gate_a13.py`.
- **Errata Correction (D-053)**: Appended `## ERRATA (patch)` to `phases/Phase 11/forward_postmortem.md` documenting Bonfiglioli QIB 3.4x vs log 120.78x and invalidating the subdued demand hypothesis.
- **Market Data Annotations (D-054, D-055)**: Authored `data/corrections/macro_2026-10-23.md` and `phases/Phase 13/market_raw_decision.md`.
- **Dashboard Synchronization (D-056)**: Updated `opi/report.py` to extract last cloud run timestamp and regenerated `dashboard/index.html` with exact register defect count.
- **Self-Monitoring Automation (Workstream A / D-057, D-058, D-059)**:
  - Authored `scripts/manage_alerts.py` to open GitHub issues upon workflow failures and automatically close them upon green runs. Tested cloud issue opening via forced failure workflow dispatch (`run 40115747239`, Issue #1).
  - Authored `scripts/watchdog.py` and `.github/workflows/watchdog.yml` to audit run freshness (<36h), dashboard freshness (<36h; `NOT_CHECKED` strictly treated as fail), OpenRouter free models, and commit heartbeat at most once every 30 days.
  - Authored `requirements.lock` pinning all core dependencies; updated `.github/workflows/daily.yml` and `monthly_retrain.yml` to install from it; added `.github/workflows/canary.yml` for unpinned weekly canary builds.
- **Outcome Recording Automation & Research Agent Upkeep (Workstream B / D-026)**:
  - Updated `opi/run_daily.py` to detect passed listing dates, log `SKIPPED_BLOCKED_SOURCE` if exchange scraping is blocked without silent green execution.
  - Confirmed D-026 remains `NOT FIXED` awaiting real upcoming IPO extraction in a green scheduled run.
- **Prospective n=30 Evaluation Protocol (Workstream C / D-060)**:
  - Authored `phases/Phase 13/preregistration_final_eval.md` before $n=30$ is reached.
  - Authored `scripts/final_evaluation.py` printing `NOT_READY (n=6 of 30)` on current repo and executing full paired bootstrap with seed 42 when $n \ge 30$.
  - Created synthetic fixture `tests/fixtures/synthetic_n30_prediction_log.csv` and unit tests in `tests/test_final_evaluation.py`.
- **Maintainer Runbook & Handover (Workstream D / D-061)**:
  - Authored `docs/RUNBOOK.md` with all 9 required operational sections and linked from `README.md`.
  - Added test suite `tests/test_docs.py`.
- **Monthly Retraining Governance (Workstream E)**:
  - Verified `monthly_retrain.yml` locks dependencies, opens pull requests, and enforces zero model auto-promotion.

---

## 2. Scripts & Workflows Created / Modified

- `DEFECTS.md`: Seeded D-053 through D-061; updated D-045, D-053..D-061 to FIXED with regression test pointers. D-026 remains NOT FIXED.
- `requirements.lock`: Fully pinned dependency lockfile.
- `scripts/manage_alerts.py`: GitHub issue alerting, deduplication, and resolution script.
- `scripts/watchdog.py`: Freshness auditor, model validator, and keepalive heartbeat.
- `.github/workflows/daily.yml`: Added `issues: write` permission, `force_fail` input, `requirements.lock` installation, and failure/success alert hooks.
- `.github/workflows/watchdog.yml`: Daily health watchdog workflow running at 10:00 UTC.
- `.github/workflows/canary.yml`: Weekly unpinned canary dependency test workflow.
- `.github/workflows/monthly_retrain.yml`: Updated to install from `requirements.lock`.
- `phases/Phase 13/preregistration_final_eval.md`: Preregistered $n=30$ evaluation protocol.
- `scripts/final_evaluation.py`: Automated evaluation script enforcing Wilson intervals, paired bootstrap, and wording rules.
- `tests/fixtures/synthetic_n30_prediction_log.csv`: 30-row synthetic test fixture.
- `docs/RUNBOOK.md`: Plain-language maintainer operating runbook.
- `README.md`: Linked to `docs/RUNBOOK.md`.
- `dashboard/index.html`: Regenerated to display active defect count and last cloud run timestamp.
- `tests/test_alerts.py`: Unit tests for alert creation, deduplication, auto-close, and key sanitization.
- `tests/test_watchdog.py`: Unit tests for staleness thresholds, dashboard checks, model queries, and keepalive logic.
- `tests/test_final_evaluation.py`: Unit tests for $n < 30$ refusal, bootstrap reproducibility, and wording rules.
- `tests/test_docs.py`: Unit tests verifying required headings in `docs/RUNBOOK.md` and link in `README.md`.
- `tests/test_ci.py`: Regression tests for lockfile pinning, watchdog/canary configuration, and force-fail flags.
- `tests/test_gate_a.py`: Regression tests for Gate A13 macro corrections and market raw decision.

---

## 3. Data Purification & Engineering Steps

- All 5 Gate A13 headline numbers recomputed directly from `predictions/prediction_log.csv` and `data/ipo_master.csv`.
- Confirmed zero modified rows in `predictions/prediction_log.csv`.
- Confirmed zero mock data files in `data/` or `data/evidence/`. All synthetic fixtures restricted to `tests/fixtures/`.
- Verified zero OpenRouter secret key occurrences in tracked files via `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"`.

---

## 4. Exact Terminal Commands Executed

```bash
# 1. Gate A13 verification and baselines
python scripts/verify_all.py
python scripts/verify_extra.py
python scripts/recompute_gate_a13.py

# 2. Workstream A: Alerts, Watchdog, Lockfile
python scripts/watchdog.py --dry-run
pytest tests/test_alerts.py tests/test_watchdog.py tests/test_ci.py
gh workflow run daily.yml -f force_fail=true
gh issue list

# 3. Workstream B: Outcome recording & research agent
pytest tests/test_discover_listed.py

# 4. Workstream C: Final evaluation automation
python scripts/final_evaluation.py
pytest tests/test_final_evaluation.py

# 5. Workstream D: Runbook
pytest tests/test_docs.py

# 6. Workstream E: Retraining governance
pytest tests/test_retraining.py tests/test_governance.py

# 7. Final verification suites
python -c "import subprocess; res = subprocess.run(['python', 'scripts/verify_all.py'], capture_output=True, text=True); open('phases/Phase 13/verify_end.txt', 'w', encoding='utf-8').write(res.stdout)"
python -c "import subprocess; res = subprocess.run(['python', 'scripts/verify_extra.py'], capture_output=True, text=True); open('phases/Phase 13/verify_extra_end.txt', 'w', encoding='utf-8').write(res.stdout)"
```

---

## 5. Artifacts and Generated Data Files

- `phases/Phase 13/verify_start.txt`: Baseline verify_all output (61 pass, 1 warn, 3 fail).
- `phases/Phase 13/verify_extra_start.txt`: Baseline verify_extra output (5 pass, 0 warn, 2 fail).
- `phases/Phase 13/verify_end.txt`: Final verify_all output (66 pass, 0 warn, 0 fail).
- `phases/Phase 13/verify_extra_end.txt`: Final verify_extra output (7 pass, 0 warn, 0 fail).
- `phases/Phase 13/prior_phase_recheck.csv`: 10 sampled claims (seed 13) and 5 headline recomputations.
- `phases/Phase 13/actions_status.md`: Audit of secret presence, last 10 scheduled runs, and retraining governance.
- `phases/Phase 13/market_raw_decision.md`: Decision record on market payload definitions.
- `data/corrections/macro_2026-10-23.md`: Annotation of Oct 23 market snapshot.
- `phases/Phase 13/preregistration_final_eval.md`: Registered protocol for $n=30$ prospective evaluation.
- `docs/RUNBOOK.md`: Production maintainer manual and handover checklist.
