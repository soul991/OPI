# Phase 13: Outcome & Verdict - Close Open Defects, Harden Automation, Hand Over to Maintenance Mode

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 13/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following target remains unfixed per project rules:

1. **D-026: Live Web Research Agent Proof (OpenRouter)**
   - Status: **NOT FIXED (awaiting real new IPO in scheduled run)**
   - Audit: `OPENROUTER_API_KEY` repository secret is configured and confirmed present. In strict accordance with user rules ("Never create fake IPOs to prove the research agent; leave D-026 NOT FIXED until a scheduled run handles a real new IPO"), D-026 remains NOT FIXED until an upcoming IPO bidding window appears in live scheduled runs. No fake IPOs were created.
2. **Jio Platforms Limited and Paras Healthcare Limited Listing Outcomes**
   - Status: **PENDING (Listing scheduled 2026-10-28)**
   - Audit: As of phase conclusion date 2026-10-24, neither IPO has listed. Both rows remain carried over with status `FORWARD` in `predictions/prediction_log.csv`. In accordance with user rules, their actuals will be recorded strictly post-listing (after 2026-10-28) from verified exchange snapshots.

---

## 2. Defect Ledger

All 61 defects tracked in [`DEFECTS.md`](../../DEFECTS.md):

| Defect ID | Phase Introduced | Description | Severity | Status Before Phase 13 | Status After Phase 13 | Due Phase | Verification Proof |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** to **D-044** | 1-11 | Historical defects resolved or accepted in earlier phases | Various | FIXED / ACCEPTED | **FIXED / ACCEPTED** | - | See `DEFECTS.md` |
| **D-045** | 11 | Phase 11 verdict Workstream B table contains figures that contradict prediction log | High | PARTIAL | **FIXED** | 13 | `tests/test_reporting.py::test_phase11_postmortem_has_errata` |
| **D-046** | 11 | `forward_postmortem.md` states Bonfiglioli QIB 3.4x (log 120.78x) | High | FIXED | **FIXED** | 12 | `tests/test_postmortem.py::test_narrative_numbers_from_log` |
| **D-047** | 11 | `forward_report.py` writes BSE code 544994 as evidence note for every listed IPO | Medium | FIXED | **FIXED** | 12 | `tests/test_reporting.py::test_forward_report_exchange_matches_source` |
| **D-048** | 11 | Listing-day Nifty moves hard-coded in forward_postmortem.py; no market evidence files | High | FIXED | **FIXED** | 12 | `tests/test_postmortem.py::test_narrative_numbers_from_log` |
| **D-049** | 11 | Champion interval coverage 91.2% vs 87.94% not reconciled across docs | Medium | FIXED | **FIXED** | 12 | `tests/test_conformal_experiment.py::test_coverage_reconciliation_script_and_readme` |
| **D-050** | 11 | Dashboard publishing unproven on live GitHub Pages | Medium | FIXED | **FIXED** | 12 | `tests/test_ci.py::test_pages_published_and_guarded` |
| **D-051** | 11 | Scheduled runs start 4 to 5 hours late; no freshness monitoring | Low | FIXED | **FIXED** | 12 | `tests/test_ci.py::test_schedule_lag_recorded` |
| **D-052** | 11 | Process: Phase 11 ran all workstreams without stop after gate | Medium | FIXED | **FIXED** | 12 | `tests/test_gate_a.py::test_phase12_process_stop_and_results_log` |
| **D-053** | 12 | `phases/Phase 11/forward_postmortem.md` has no ERRATA block; wrong Bonfiglioli 3.4x | Medium | OPEN | **FIXED** | 13 | `tests/test_reporting.py::test_phase11_postmortem_has_errata` |
| **D-054** | 12 | Macro snapshot labelled 2026-10-23 contains 2026-10-22 values | Low | OPEN | **FIXED** | 13 | `tests/test_gate_a.py::test_gate_a13_macro_correction` |
| **D-055** | 12 | `data/evidence/market/*_nifty.raw` is parsed output, not original response | Low | OPEN | **FIXED** | 13 | `tests/test_gate_a.py::test_gate_a13_market_raw_decision` |
| **D-056** | 12 | Dashboard defect counter is stale (1 vs 2) and does not show last cloud run date | Low | OPEN | **FIXED** | 13 | `tests/test_dashboard.py::test_dashboard_shows_last_cloud_run` |
| **D-057** | 12 | No alert when a scheduled run fails | Medium | OPEN | **FIXED** | 13 | `tests/test_alerts.py::test_handle_failure_creates_new_issue_when_none_open` |
| **D-058** | 12 | Schedule risks: runs start 4.7 h late; GitHub 60-day pause risk | Medium | OPEN | **FIXED** | 13 | `tests/test_watchdog.py::test_scheduled_run_freshness_fresh` |
| **D-059** | 12 | Dependencies not pinned | Medium | OPEN | **FIXED** | 13 | `tests/test_ci.py::test_requirements_lock_and_ci_pinning` |
| **D-060** | 12 | The n = 30 evaluation is not preregistered or automated | Medium | OPEN | **FIXED** | 13 | `tests/test_final_evaluation.py::test_full_evaluation_on_synthetic_fixture` |
| **D-061** | 12 | No runbook for the user | Low | OPEN | **FIXED** | 13 | `tests/test_docs.py::test_runbook_sections_and_headings` |

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

## 4. Gate A13 Results & Independent Verification

### Verification Suite Outputs (Start vs End)

#### 1. Baseline Run (`verify_start.txt`):
```
SUMMARY: 61 pass, 1 warn, 3 fail
Failures: D-053 uncorrected Bonfiglioli text; verify_extra 2 FAIL on postmortem; dashboard count mismatch.
```

#### 2. Final Run (`verify_end.txt`):
```
[PASS] no absolute/local paths in docs or code                                              
[PASS] pytest suite passes                                                                  165 passed, 1 skipped, 1 warning in 22.53s
[PASS] no duplicate (company, listing_date)                                                 0 duplicates
[PASS] listing_gain_pct matches prices                                                      0 mismatches
[PASS] label_good matches gain                                                              0 mismatches
[PASS] date order open<=close<=listing                                                      0 rows
[PASS] no extreme listing/issue price ratios (FPO-type errors)                              
[PASS] gmp_pct in plausible range                                                           0 rows
[PASS] every excluded row has a source URL                                                  0 without URL
[PASS] every GMP value has URL, page date, access date                                      0 rows incomplete
[PASS] every sourced GMP row exists in master                                               0 unmatched
[PASS] GMP as_of_date not after last bidding day (no leakage)                               0 rows
[PASS] source page dated before listing                                                     0 rows dated on/after listing
[PASS] second-source check credible (Phase 7)                                               
[PASS] second-source check credible (Phase 8)                                               
[PASS] snapshot file for every sourced GMP row (<listing_date>_<company-slug>.*)            0 of 0 missing
[PASS] log statuses valid                                                                   0 invalid
[PASS] FORWARD rows logged                                                                  8 rows
[PASS] FORWARD rows scored before listing                                                   0 rows
[PASS] FORWARD rows scored after bidding closed (final subscription)                        
[PASS] FORWARD rows use final (not day-1/live) subscription                                 
[PASS] probabilities within [0,1]                                                           
[PASS] no duplicate FORWARD rows                                                            0
[PASS] FORWARD scored_at matches first commit time (no backdating)                          
[PASS] no actuals for unlisted IPOs                                                         
[PASS] FORWARD feature snapshots carry source URLs                                          0 rows with only site names
[PASS] final test rows <= FORWARD rows with actuals                                         0 rows vs 6
[PASS] Phase 1: three required files                                                        
[PASS] Phase 2: three required files                                                        
[PASS] Phase 3: three required files                                                        
[PASS] Phase 4: three required files                                                        
[PASS] Phase 5: three required files                                                        
[PASS] Phase 6: three required files                                                        
[PASS] Phase 7: three required files                                                        
[PASS] Phase 8: three required files                                                        
[PASS] Phase 9: three required files                                                        
[PASS] Phase 10: three required files                                                       
[PASS] Phase 11: three required files                                                       
[PASS] Phase 12: three required files                                                       
[PASS] Phase 13: three required files                                                       
[PASS] defect register parsed                                                               61 defects, 1 open/partial
[PASS] every FIXED defect has an existing regression test                                   
[PASS] Phase 13 verdict 'None unfixed' consistent with defect register                      
[PASS] Phase 6: gate + preregistration committed before other work                          
[PASS] Phase 7: gate + preregistration committed before other work                          
[PASS] Phase 8: gate + preregistration committed before other work                          
[PASS] Phase 9: gate + preregistration committed before other work                          
[PASS] Phase 10: gate + preregistration committed before other work                         
[PASS] Phase 11: gate + preregistration committed before other work                         
[PASS] Phase 12: gate + preregistration committed before other work                         
[PASS] Phase 13: gate + preregistration committed before other work                         
[PASS] Phase 7 headline metrics recompute from raw predictions                              
[PASS] CI can obtain the model (tracked artifact or training step)                          
[PASS] earlier-phase artifacts unchanged since phase13-gate-a (errata may only add lines)   
[PASS] extreme GMP values (>100% or <-30%) have a snapshot or are NOT_RECORDED              
[PASS] no mock research runs in data/research_runs                                          
[PASS] no mock evidence files under data/evidence/                                          
[PASS] grounding: HD Fire Protect Limited inputs appear in saved snapshots                  4 snapshot files
[PASS] grounding: Fusion CX Limited inputs appear in saved snapshots                        4 snapshot files
[PASS] grounding: Zetwerk Manufacturing Business Limited inputs appear in saved snapshots   5 snapshot files
[PASS] grounding: Sahajanand Medical Technologies Limited inputs appear in saved snapshots  5 snapshot files
[PASS] grounding: Tonbo Imaging India Limited inputs appear in saved snapshots              5 snapshot files
[PASS] grounding: Bonfiglioli Transmissions Limited inputs appear in saved snapshots        5 snapshot files
[PASS] grounding: Jio Platforms Limited inputs appear in saved snapshots                    3 snapshot files
[PASS] grounding: Paras Healthcare Limited inputs appear in saved snapshots                 3 snapshot files
[PASS] pytest passes on a fresh clone (no untracked/ignored files)                          165 passed, 1 skipped, 2 warnings in 41.24s

SUMMARY: 66 pass, 0 warn, 0 fail
```

#### 3. `scripts/verify_extra.py` Output (v2, Err-Free):
```
[PASS] subscription figures in Phase 11+ reports equal prediction_log values                    0 mismatches
[PASS] no company other than HD Fire cites BSE code 544994                                      0 lines
[PASS] no hard-coded dated numeric constants in scripts/ or opi/                                0 lines
[PASS] each listed date has a parsed Nifty evidence file (close + prev close or day return)     missing: none
[PASS] no 'weak/only/subdued demand' text for IPOs with QIB > 50x                               0 lines
[PASS] README's two champion coverage figures (91.2% vs 87.94%) are reconciled in text          
[PASS] no OpenRouter key material in tracked files                                              

SUMMARY: 7 pass, 0 warn, 0 fail
```

---

## 5. Workstream Results & Verification Evidence

### Workstream A: Self-Monitoring Automation (D-057, D-058, D-059)
- **Live Failure Alerting**: Triggered forced failure via `gh workflow run daily.yml -f force_fail=true` (Run [`40115747239`](https://github.com/soul991/OPI/actions/runs/40115747239)). The workflow automatically opened GitHub Issue [**#1**](https://github.com/soul991/OPI/issues/1) with the failure trace and link. Deduplication was verified when run `40116091389` appended a streak comment rather than duplicating the issue.
- **Watchdog & Keepalive**: Added `.github/workflows/watchdog.yml` and `scripts/watchdog.py`. Unit-tested all thresholds (`tests/test_watchdog.py` - 8 passed). Verifies scheduled run freshness (<36h), dashboard freshness (<36h, `NOT_CHECKED` treated strictly as failure), and OpenRouter model availability. Heartbeat keepalive configured to touch `predictions/heartbeat.txt` at most once every 30 days of inactivity.
- **Dependency Pinning**: Generated `requirements.lock` with exact pinned versions. Configured `daily.yml` and `monthly_retrain.yml` to install from it. Authored `.github/workflows/canary.yml` to run weekly unpinned tests and alert on regressions.

### Workstream B: Outcome Recording & Research Proof (D-026)
- **Outcome Recording**: Updated `opi/run_daily.py` to identify passed listings and enforce the `SKIPPED_BLOCKED_SOURCE` policy when exchange data cannot be fetched, preventing silent green runs without evidence.
- **D-026 Status**: Maintained as **NOT FIXED** in `DEFECTS.md` awaiting a genuine new IPO during a live scheduled run. No mock data or fake candidates were created.

### Workstream C: Preregister & Automate n=30 Final Evaluation (D-060)
- **Preregistration**: Authored `phases/Phase 13/preregistration_final_eval.md` fixing the population, metrics (Model MAE, GMP MAE, Conformal Coverage with Wilson CI, Directional Accuracy, Brier score), paired bootstrap (seed 42, 2,000 resamples), and strict wording constraints.
- **Automation**: Authored `scripts/final_evaluation.py`. Verified that on the current repo ($n=6$), it prints `NOT_READY (n=6 of 30)`. Verified on synthetic 30-row fixture (`tests/fixtures/synthetic_n30_prediction_log.csv`) via `tests/test_final_evaluation.py` (5 passed).

### Workstream D: Runbook and Handover (D-061)
- **Runbook**: Authored `docs/RUNBOOK.md` containing all 9 required operational sections (what the system does, three places to look, alert meanings, key rotation, manual reruns, free models, final evaluation reading, monthly 10-minute checklist, and non-investment advice disclaimer). Linked from `README.md`.
- **Test Suite**: Added `tests/test_docs.py` (2 passed).

### Workstream E: Retraining Governance Check
- Verified `monthly_retrain.yml` installs from `requirements.lock`, opens pull requests, and strictly prevents auto-promotion. Champion `v4.0.0-champion` and historical replay remain untouched.

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
| Did any report number come from anywhere but a script over the log/evidence? | **NO** | All headline metrics generated via `scripts/recompute_gate_a13.py` and `scripts/forward_report.py --markdown`. |
| Did any claim in the summary say a file was changed when it was not? | **NO** | Verified each commit with `git diff --stat` prior to staging and commit. |
| Did any earlier-phase file change except by ERRATA? | **NO** | `phases/Phase 11/forward_postmortem.md` modified only by adding top `## ERRATA (patch)` (0 lines deleted). |
| Did any value enter a feature without a snapshot? | **NO** | Zero modifications to logged feature values in `predictions/prediction_log.csv`. |
| Did the work stop after the gate? | **YES** | Work stopped after Gate A13 (`8c94d86`) and preregistration (`23baa8a`) until continuation instruction. |
| Was the key kept out of the repo, logs, issues, and snapshots? | **YES** | `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. |

---

## 8. Handover State

### What Runs by Itself in GitHub Cloud
1. **Daily Forward Test & Verification** (`daily.yml`):
   - Runs twice daily at 06:00 UTC (11:30 IST) and 14:00 UTC (19:30 IST).
   - Installs from `requirements.lock`.
   - Discovers Mainboard IPOs, scores unlisted closed IPOs, updates outcomes from exchange evidence, runs pytest and `verify_all.py`, commits updates, and publishes GitHub Pages.
   - On failure: opens/comments on GitHub alert issue. On success: auto-closes open failure issues.
2. **Watchdog Freshness & Provider Health** (`watchdog.yml`):
   - Runs daily at 10:00 UTC.
   - Monitors run freshness (<36h), dashboard freshness (<36h), and OpenRouter free models.
   - Commits keepalive heartbeat to `predictions/heartbeat.txt` at most once every 30 days if repository is inactive.
3. **Weekly Canary Build** (`canary.yml`):
   - Runs weekly on Sunday at 03:00 UTC.
   - Tests unpinned dependencies (`requirements.txt`) against test suite to catch upstream breakages.
4. **Monthly Challenger Evaluation** (`monthly_retrain.yml`):
   - Runs on the 1st of every month at 00:00 UTC.
   - Evaluates prospective candidate models via pull request; strictly prohibits automated champion model promotion.

### Active Alert Mechanisms
- **Failure Notification**: Opens GitHub issue `Daily run failed: <run_id>` or `Watchdog run failed: <run_id>`.
- **Deduplication**: Successive failures append comments to the active open streak issue.
- **Resolution**: Next green scheduled run automatically closes the issue.

### Monthly 10-Minute Maintainer Checklist (from `docs/RUNBOOK.md`)
- [ ] **Dashboard Freshness**: Open [https://soul991.github.io/OPI/dashboard/](https://soul991.github.io/OPI/dashboard/); confirm the "Last Cloud Run" badge is within 24 hours.
- [ ] **Issues Tab Empty**: Confirm zero open alert issues.
- [ ] **Defect Counter**: Confirm dashboard defect counter equals open/partial rows in `DEFECTS.md` (currently 1: D-026).
- [ ] **Scheduled Runs**: Verify last 5 scheduled runs in Actions tab are green.
- [ ] **Secret Verified**: Confirm `OPENROUTER_API_KEY` exists in `gh secret list`.
- [ ] **Data Completeness**: Check `predictions/prediction_log.csv` to ensure no recently listed Mainboard IPOs were skipped without logged reasons.

---

## 9. Final Phase 13 Verdict

**PASS**: Phase 13 goals achieved. All open engineering defects (D-045, D-053 through D-061) are **FIXED** with passing regression tests. The cloud automation is hardened, self-monitoring, and fully handed over to autonomous cloud operation. D-026 remains appropriately carried over as NOT FIXED awaiting a real scheduled IPO extraction.
