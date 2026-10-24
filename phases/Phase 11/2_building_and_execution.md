# Phase 11: Building & Execution Log

> Follows `RULES.md` and `PHASE_PROTOCOL.md`. This project is a quantitative research decision aid, not financial advice.
> Gate A11, preregistration, and all five workstreams (A through E) completed following strict sequential protocols.

---

## 1. Pipeline Architecture & Data Flow

Phase 11 executed complete Phase 10 re-verification, out-of-range guards, error post-mortems, conformal prediction walk-forward experiments, cloud research agent integration, and forward status tracking:

```
[ Gate A11 Audit & Recheck ]
  ├── 10 Random Phase 10 Claims Verified (prior_phase_recheck.csv)
  ├── 5 Headline Numbers Recomputed from Raw Data
  ├── Actions Runs #9 & #10 Investigated (actions_failures.md)
  └── DEFECTS.md Seeded with D-040..D-044
          │
          ▼
[ Formal Preregistration (preregistration.md) ]
  ├── Frozen decision thresholds, 20 quarters (2022Q1-2026Q4)
  └── Seed 42, 2,000 paired bootstrap resamples
          │
          ▼
[ Workstream A: Out-of-Range & Mega-Issue Guard (D-040) ]
  ├── model/feature_ranges.json computed from 731 master rows
  ├── check_feature_ranges() in opi/score.py
  ├── app/main.py & dashboard/index.html LOW confidence / probability suppression
  └── phases/Phase 11/mega_issue_analysis.md (13 mega-issues descriptive audit)
          │
          ▼
[ Workstream B: Forward Error Post-Mortem (D-041) ]
  ├── scripts/forward_postmortem.py
  ├── phases/Phase 11/forward_postmortem.md (Nifty listing-day moves, QIB/retail splits)
  └── Bonfiglioli (0.00% pop) & Zetwerk post-mortems (strictly labeled Hypothesis (untested))
          │
          ▼
[ Workstream C: Tail & Conformal Prediction Experiment (D-007, D-008) ]
  ├── scripts/evaluate_tail_and_intervals.py across 20 quarters (n = 398 holdouts)
  ├── Champion vs Candidate 1 (Mondrian) vs Candidate 2 (Quantile CQR)
  ├── Both candidates failed pre-registered adoption criteria; champion intact
  └── D-007 & D-008 transitioned to ACCEPTED limitations documented in README.md
          │
          ▼
[ Workstream D: OpenRouter Research Agent & Cloud Workflow (D-026) ]
  ├── config/research_models.json (Nemotron, Gemma free-tier models)
  ├── OpenRouterResearchProvider in opi/research_agent.py (404 fallback, 429 backoff)
  ├── .github/workflows/daily.yml concurrency and cloud secret integration
  └── D-026 marked NOT FIXED (awaiting user adding OPENROUTER_API_KEY in repo secrets; no mock data used)
          │
          ▼
[ Workstream E: Forward Tracking & App Hygiene (D-044) ]
  ├── scripts/generate_forward_status.py -> phases/Phase 11/forward_status.md
  ├── D-044 resolved: Jio sector flagged UNVERIFIED without altering logged row
  └── Calibrated probability bounds [0.091, 0.882] enforced
          │
          ▼
[ Final Verification Exit ]
  └── scripts/verify_all.py -> phases/Phase 11/verify_end.txt (62 PASS, 0 WARN, 0 FAIL)
```

---

## 2. Scripts and Files Created / Modified

### Gate A11 & Preregistration
- `DEFECTS.md`: Seeded D-040 through D-044; resolved D-042 and D-043 during Gate A.
- `phases/Phase 11/verify_start.txt`: Initial verification capture (58 pass on start).
- `phases/Phase 11/prior_phase_recheck.csv`: 10 randomly sampled claims (seed 11) + 5 recomputed headline numbers.
- `phases/Phase 11/actions_failures.md`: Audit of GitHub Actions runs #9 and #10 and Pages status.
- `phases/Phase 11/preregistration.md`: Formal preregistration of Workstreams A through E.
- `tests/test_ci.py`: Regression tests for Actions failure logging and dashboard publishing status.

### Workstream A (D-040)
- `model/feature_ranges.json`: Computed training feature distribution (min, max, p1, p99, hashes).
- `opi/score.py`: Added `check_feature_ranges` returning `input_flags`, `confidence`, and `display_probability`.
- `app/main.py`: Updated to suppress probability display and show amber alert banner when confidence is LOW.
- `opi/report.py` / `dashboard/index.html`: Added `LOW CONF` badge and suppressed probability display.
- `phases/Phase 11/mega_issue_analysis.md`: Descriptive audit of 13 historical issues > ₹10,000 Cr.
- `tests/test_scoring_guard.py`: 4 unit tests verifying guard behavior.

### Workstream B (D-041)
- `scripts/forward_postmortem.py`: Post-mortem table and analysis generator.
- `phases/Phase 11/forward_postmortem.md`: Audit table with listing-day Nifty return, subscription breakdown, and hypotheses.
- `tests/test_postmortem.py`: Verification test for post-mortem artifact generation.

### Workstream C (D-007, D-008)
- `scripts/evaluate_tail_and_intervals.py`: Walk-forward conformal interval and tail evaluator across 20 quarters.
- `phases/Phase 11/conformal_experiment.csv`: Holdout evaluation summary table.
- `phases/Phase 11/tail_and_intervals_report.md`: Detailed hypothesis testing and paired bootstrap results.
- `README.md`: Documented D-007 and D-008 under Known Limitations.
- `tests/test_conformal_experiment.py`: Regression tests for conformal experiment.

### Workstream D (D-026)
- `config/research_models.json`: OpenRouter free-tier model configuration.
- `opi/research_agent.py`: Integrated `OpenRouterResearchProvider` with 404 fallthrough and 429 retry.
- `.github/workflows/daily.yml`: Added `concurrency` group and passed `OPENROUTER_API_KEY` secret.
- `tests/test_openrouter_agent.py`: 6 unit tests verifying fallthrough, retry, key privacy, and schema grounding.

### Workstream E (D-044)
- `scripts/generate_forward_status.py`: Automated weekly forward tracking table generator.
- `phases/Phase 11/forward_status.md`: Weekly prospective prediction audit report.
- `tests/test_forward_log.py`: Added `test_jio_sector_flagged_unverified`.
- `phases/Phase 11/verify_end.txt`: Final verification run output (62 PASS, 0 WARN, 0 FAIL).

---

## 3. Exact Commands Executed

```bash
# Gate A11 & Preregistration
python scripts/verify_all.py | Out-File -FilePath "phases/Phase 11/verify_start.txt" -Encoding utf8
git commit -m "phase11-gate-a"
git commit -m "phase11-preregistration"

# Workstream A
python -c "import pandas as pd... compute model/feature_ranges.json"
pytest tests/test_scoring_guard.py
git commit -m "workstream-a: out-of-range and mega-issue guard (D-040)"

# Workstream B
python scripts/forward_postmortem.py
pytest tests/test_postmortem.py
git commit -m "workstream-b: forward prediction errors post-mortem table and analysis (D-041)"

# Workstream C
python scripts/evaluate_tail_and_intervals.py
pytest tests/test_conformal_experiment.py
git commit -m "workstream-c: tail and conformal prediction walk-forward experiment (D-007, D-008)"

# Workstream D
pytest tests/test_openrouter_agent.py
git grep sk-or-
git commit -m "workstream-d: openrouter research agent integration and cloud workflow (D-026)"

# Workstream E
python scripts/generate_forward_status.py
pytest tests/test_forward_log.py
git commit -m "workstream-e: forward status tracking and app hygiene (D-044)"

# Final Verification
python scripts/verify_all.py | Out-File -FilePath "phases/Phase 11/verify_end.txt" -Encoding utf8
```
