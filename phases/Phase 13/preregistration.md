# Phase 13: Pre-Registration of Self-Monitoring Automation, Final Evaluation Protocols, and Handover

> Pre-registration document for Phase 13 per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 13/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Automation Self-Monitoring & Alerting Protocol (Workstream A, D-057, D-058, D-059)

1. **Failure Alerting (D-057)**:
   - In `.github/workflows/daily.yml`, add an `if: failure()` step that opens (or updates) an issue titled `Daily run failed: <run id>`.
   - Contains failed step name and run URL.
   - Deduplication: opens only one open issue per failure streak; the subsequent successful scheduled run automatically closes the open failure issue.
   - Zero secrets or token values in issue body (`git grep sk-or-` clean).
2. **Watchdog Workflow & Schedule Lag Monitoring (D-058)**:
   - Authored `.github/workflows/watchdog.yml` running daily on cron offset from `daily.yml`.
   - Checks three conditions:
     a) Last successful scheduled `daily.yml` run is within 36 hours.
     b) Live GitHub Pages dashboard (`scripts/verify_pages.py`) timestamp is within 36 hours.
     c) OpenRouter free models endpoint returns at least one model from `config/research_models.json`.
   - If any condition fails, watchdog fails and opens an alert issue.
3. **Repository Keepalive**:
   - To prevent GitHub from suspending scheduled cron workflows after 60 days of repo inactivity, watchdog writes a timestamp line to `predictions/heartbeat.txt` at most once every 30 days if no commit occurred.
4. **Dependency Pinning & Canary (D-059)**:
   - Generate `requirements.lock` pinning exact package versions that satisfy the test suite. Workflows install from `requirements.lock`.
   - Author `.github/workflows/canary.yml` running weekly with unpinned `requirements.txt` to detect upstream package deprecations and breaks before daily jobs fail.
5. **Data Source Failure Policy**:
   - If a source is blocked, empty, or structurally changed, log `SKIPPED_<reason>` per IPO. Never guess or hallucinate values. Runs with all IPOs skipped trigger an alert issue.

---

## 2. Outcome Recording & Live Research Agent Proof Protocol (Workstream B, D-026)

1. **Automated Exchange Outcome Recording**:
   - Automated post-listing execution of `scripts/update_actuals.py` on official exchange quote pages (BSE/NSE) with saved snapshots.
   - If blocked or unavailable, log `SKIPPED_BLOCKED_SOURCE`.
2. **Jio Platforms & Paras Healthcare (2026-10-28)**:
   - Scored on 2026-10-23 as `status: FORWARD, confidence: LOW`.
   - Outcomes recorded only after official exchange listing on 2026-10-28 with saved exchange snapshots.
   - Headline metrics reported with and without LOW-confidence rows.
3. **Research Agent Proof Criteria (D-026)**:
   - Remains `NOT FIXED` until a green scheduled cloud run (`event=schedule`) extracts inputs for a newly discovered, genuine IPO.
   - Must log provider, model id, request count, and grounding rate.
   - Zero creation of synthetic or mock IPOs.

---

## 3. Final Prospective Evaluation Protocol (n = 30) (Workstream C, D-060)

1. **Target Population**:
   - Genuine prospective `FORWARD` rows logged in `predictions/prediction_log.csv` before listing.
2. **Evaluation Readiness**:
   - Evaluator script `scripts/final_evaluation.py` outputs `NOT_READY (n=<k> of 30)` while completed listed count $n < 30$.
   - When $n \ge 30$, automatically generates `phases/Final Evaluation/report.md` and updates dashboard banner.
3. **Primary Evaluation Metrics**:
   - MAE of Model vs Actual Gain.
   - MAE of Naive GMP vs Actual Gain (on rows with observed GMP).
   - MAE of Model vs Historical Mean Baseline.
   - Directional accuracy (% predicting correct gain sign).
   - 80% Conformal Prediction Interval coverage (Wilson score 95% CI).
4. **Statistical Rigor & Decision Rules**:
   - Paired bootstrap test (seed 42, 2,000 resamples).
   - No claim of "beats", "wins", or "superiority" unless the bootstrap 95% confidence interval strictly excludes zero. Otherwise report "no demonstrated difference".
   - Stratified breakdown reporting results with and without LOW-confidence rows.

---

## 4. Runbook & Handover Protocol (Workstream D, D-061)

1. **Runbook Requirements**:
   - Documented in `docs/RUNBOOK.md` with required sections: System Overview, Monitoring Dashboards, Alert Issues, Key Rotation, Manual Rerun Procedures, Model Configuration, Monthly Maintenance Checklist (10 minutes), and Investment Disclaimer.
   - Checked via regression test `tests/test_docs.py::test_runbook_sections`.

---

## 5. Retraining Governance Protocol (Workstream E)

1. **Retraining Safety Guards**:
   - `monthly_retrain.yml` creates a pull request for review and never auto-promotes champion.
   - Uses `requirements.lock`.
   - Preserves baseline champion `v4.0.0-champion` and historical replay artifacts.
