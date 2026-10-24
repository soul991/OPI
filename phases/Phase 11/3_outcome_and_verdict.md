# Phase 11: Outcome & Verdict - Re-verify Phase 10, Mega-Issue Safety, Tail and Interval Fixes, Live Research Proof

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 11/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following items remain open, partial, or not fixed at the conclusion of Phase 11:

1. **D-026: Live Web Research Agent Proof (OpenRouter)**
   - Status: **NOT FIXED (needs user action)**
   - Details: The automated cloud research agent pipeline was fully implemented and integrated with OpenRouter (`config/research_models.json`, `OpenRouterResearchProvider` in `opi/research_agent.py`, and scheduled cloud execution in `.github/workflows/daily.yml`). However, live execution in GitHub Actions requires the repository secret `OPENROUTER_API_KEY` to be configured by the user in GitHub repository settings. Per protocol and user instruction, no mock data was used in `data/evidence` or `data/research_runs`, and no local key was committed. Marked **NOT FIXED** pending user secret configuration and subsequent green scheduled run.
2. **D-013: Upstream Audit Sample Evidence Snapshots**
   - Status: **PARTIAL (carried over)**
   - Details: The historical 15-row duplicate verification and 40-row random audit from Phase 7 contained corrupted upstream URLs (wrong Chittorgarh SME IDs and 404s). In Phase 8, 20 audit snapshots were saved under `data/evidence/audit/` documenting this mismatch. Live bulk re-scraping remains blocked by site permissions; those 15 entities carry status `UNVERIFIED` in `phases/Phase 9/duplicate_verification.csv`; line maintained as **PARTIAL** and documented under `README.md` Known Limitations.
3. **D-007 & D-008: Tail Pops and Conformal Interval Over-Conservatism**
   - Status: **ACCEPTED (Known Limitation)**
   - Details: Evaluated in Workstream C walk-forward experiment across 20 quarters ($n = 398$). Neither Candidate 1 (Mondrian Conformal) nor Candidate 2 (Quantile CQR) satisfied the pre-registered multi-objective adoption criteria (Target 1: 77-84%, Target 2: $\ge 70\%$, Target 3: -5 pp width) while excluding zero on a paired bootstrap. Per frozen preregistration rules, champion `v4.0.0-champion` was kept intact, and D-007 / D-008 transitioned to **ACCEPTED** limitations documented under `README.md`.

---

## 2. Defect Ledger

| Defect ID | Phase | Description | Severity | Status Before Phase 11 | Status After Phase 11 | Due Phase | Regression Test Reference / Evidence |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** | 7 | 77 backfilled unverified GMP values reverted | Critical | FIXED | FIXED | 8 | `tests/test_gmp_evidence.py::test_snapshot_for_every_sourced_gmp_row` |
| **D-002** | 7 | Phase 7 headline metrics recomputation | Critical | FIXED | FIXED | 8 | `tests/test_reporting.py::test_headline_metrics_recompute` |
| **D-003** | 6 | Mukka Proteins GMP outlier verified | High | FIXED | FIXED | 8 | `tests/test_data_integrity.py::test_gmp_outliers_verified` |
| **D-004** | 6/7 | Forward row scored after bidding closed | High | FIXED | FIXED | 8 | `tests/test_forward_log.py::test_forward_rows_scored_after_bidding_closed` |
| **D-005** | 7 | Forward listing actual outcomes recorded | Medium | FIXED | FIXED | 10 | `tests/test_actuals_offline.py::test_evidence_file_success` |
| **D-006** | 4-7 | Accounting fundamentals completeness | Medium | ACCEPTED | ACCEPTED | - | `README.md` Known Limitations |
| **D-007** | 5-7 | Tail pop under-prediction (large pops) | Medium | DEFERRED | **ACCEPTED** | 11 | `README.md` Known Limitations; `phases/Phase 11/tail_and_intervals_report.md` |
| **D-008** | 7 | Conformal interval over-conservatism | Medium | DEFERRED | **ACCEPTED** | 11 | `README.md` Known Limitations; `phases/Phase 11/tail_and_intervals_report.md` |
| **D-009** | 7 | Phase 7 verdict wording errata | Low | FIXED | FIXED | 8 | `tests/test_reporting.py::test_phase7_errata_present` |
| **D-010** | 7 | Historical pre-2022 GMP availability | Medium | ACCEPTED | ACCEPTED | - | `README.md` Known Limitations |
| **D-011** | 4 | Sector distribution granularity | Low | ACCEPTED | ACCEPTED | - | `README.md` Known Limitations |
| **D-012** | 4 | 2012-2014 capital markets dry spell | Low | ACCEPTED | ACCEPTED | - | `README.md` Known Limitations |
| **D-013** | 7 | Upstream audit sample URLs & snapshots | Medium | PARTIAL | **PARTIAL** | - | `tests/test_data_integrity.py::test_audit_samples_have_snapshots` |
| **D-014** | all | Independent repository verification | High | FIXED | FIXED | 8 | `tests/test_reporting.py::test_verify_all_runs` |
| **D-015** | 8 | CI model binary rebuild / tracking | High | FIXED | FIXED | 9 | `tests/test_ci.py::test_model_available_on_fresh_clone` |
| **D-016** | 8 | Real write-time scoring timestamps | High | FIXED | FIXED | 9 | `tests/test_forward_log.py::test_scored_at_is_real_run_time` |
| **D-017** | 8 | Historical phase files immutability | Medium | FIXED | FIXED | 9 | `tests/test_reporting.py::test_earlier_phases_immutable` |
| **D-018** | 8 | Extreme GMP (>100%) snapshots verified | Medium | FIXED | FIXED | 9 | `tests/test_data_integrity.py::test_extreme_gmp_have_snapshots` |
| **D-019** | 8 | Status inconsistency errata | Low | FIXED | FIXED | 9 | `tests/test_reporting.py::test_phase8_errata_present` |
| **D-020** | 8 | GitHub Actions daily workflow confirmed | Medium | FIXED | FIXED | 9 | `tests/test_ci.py::test_github_actions_evidence_recorded` |
| **D-021** | 9 | Actual outcome update pandas 3.x dtype crash | Medium | FIXED | FIXED | - | `tests/test_actuals_offline.py::test_all_empty_notes_column_does_not_crash` |
| **D-022** | 9 | Evidence file option in update_actuals.py | Medium | FIXED | FIXED | - | `tests/test_actuals_offline.py::test_evidence_file_success` |
| **D-023** | 9 | Jio Platforms candidate scored post-close | Low | FIXED | FIXED | - | `tests/test_forward_log.py::test_candidate_ipos_scored_after_close` |
| **D-024** | 9 | Paras Healthcare candidate scored post-close | Low | FIXED | FIXED | - | `tests/test_forward_log.py::test_candidate_ipos_scored_after_close` |
| **D-025** | 9 | Quarantine mock research runs and evidence | High | FIXED | FIXED | 10 | `tests/test_data_integrity.py::test_no_mock_output_in_data_folders` |
| **D-026** | 9 | Live web research agent proof | High | PARTIAL | **NOT FIXED** | 11 | `tests/test_openrouter_agent.py::test_openrouter_404_fallthrough` |
| **D-027** | 8/9 | Mainboard automated candidate discovery | High | FIXED | FIXED | 10 | `tests/test_discover.py::test_discovers_closed_unlisted_mainboard_ipos_from_fixture` |
| **D-028** | 9 | Refusal of typed value / snapshot mismatch | Medium | FIXED | FIXED | 10 | `tests/test_ingest.py::test_mismatch_between_typed_value_and_snapshot_is_refused` |
| **D-029** | 9 | Calibrated probability bounds enforcement | Medium | FIXED | FIXED | 10 | `tests/test_app.py::test_probability_hidden_outside_calibrated_range` |
| **D-030** | 9 | Raw market data saved with hash | Low | FIXED | FIXED | 10 | `tests/test_ingest.py::test_market_data_saved_raw_with_hash` |
| **D-031** | 9 | Fusion CX issue price snapshot grounding | Medium | FIXED | FIXED | 10 | `tests/test_gate_a.py::test_fusion_cx_grounding_evidence` |
| **D-032** | 9 | Windows test setup documented | Low | FIXED | FIXED | 10 | `tests/test_gate_a.py::test_windows_setup_in_readme` |
| **D-033** | 9 | Branch leftovers merged to main | Low | FIXED | FIXED | 10 | `tests/test_app.py::test_table_values_are_strings` |
| **D-034** | 10 | Phase 10 report transcription errata | Medium | FIXED | FIXED | 10 | `tests/test_reporting.py::test_phase10_errata_present` |
| **D-035** | 10 | Verdict tables generated from log | Medium | FIXED | FIXED | 10 | `tests/test_reporting.py::test_verdict_table_matches_log` |
| **D-036** | 10 | Discovery dry-run output committed | Low | FIXED | FIXED | 10 | `tests/test_reporting.py::test_discovery_dry_run_artifact` |
| **D-037** | 10 | Workflow verification via gh CLI | Low | FIXED | FIXED | 10 | `tests/test_ci.py::test_daily_workflow_is_active` |
| **D-038** | 10 | Listed Mainboard IPOs classification | High | FIXED | FIXED | - | `tests/test_discover_listed.py::test_six_listed_ipos_classified_as_listed_in_strategy1` |
| **D-039** | 9 | Rendered HTML support for exchange updates | High | FIXED | FIXED | - | `tests/test_actuals_rendered.py::test_valid_rendered_html_fixture_success` |
| **D-040** | 11 | Out-of-range & mega-issue safety guard | High | - | **FIXED** | 11 | `tests/test_scoring_guard.py::test_jio_like_input_triggers_range_flags` |
| **D-041** | 11 | Forward prediction errors post-mortem | Medium | - | **FIXED** | 11 | `tests/test_postmortem.py::test_forward_postmortem_table_generated` |
| **D-042** | 11 | Actions runs #9 & #10 root cause documented | Medium | - | **FIXED** | 11 | `tests/test_ci.py::test_actions_failures_recorded` |
| **D-043** | 11 | Dashboard publishing status documented | Medium | - | **FIXED** | 11 | `tests/test_ci.py::test_dashboard_publishing_status_documented` |
| **D-044** | 11 | Jio sector label "IT & Technology" audit | Low | - | **FIXED** | 11 | `tests/test_forward_log.py::test_jio_sector_flagged_unverified` |

---

## 3. Forward Results Table (Generated from `predictions/prediction_log.csv`)

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.00 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | LISTED | BSE official opening trade (544994) evidenced in snapshot `1ef0c35a650c` |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.25 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `0783e1c0985b` |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.15 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `d69406a6b7e8` |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1160.00 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `4c486eeb1b8d` |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `6df55c3addef` |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | Pending | Pending | +22.14% | +22.34% | Pending | Pending | FORWARD | listing scheduled 2026-10-28 |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | Pending | Pending | -2.56% | +1.59% | Pending | Pending | FORWARD | listing scheduled 2026-10-28 |

> **Provisional Evaluation Notice**: Sample size $n = 6$ of 30 target forward predictions. Results are strictly descriptive. No performance claims or statistical superiority statements are permitted prior to $n \ge 30$.

---

## 4. Gate A11 Results

### G1. Prior-Phase Recheck (Seed 11 Sample)
- 10 randomly sampled claims from Phase 10 outcome and verdict verified against underlying codebase. All 10 claims marked `VERIFIED` in `phases/Phase 11/prior_phase_recheck.csv`.
- Recomputed 5 headline numbers:
  1. Forward Model MAE (n=6 listed): 6.7817 pp (reported 6.78 pp).
  2. Forward Raw GMP MAE (n=5 with GMP): 7.9480 pp (reported 7.95 pp).
  3. Master dataset row count: 731 data rows.
  4. Prediction log breakdown: 14 total rows (6 test/invalid, 8 genuine FORWARD: 6 listed, 2 scheduled).
  5. Defect counts: 44 total defects parsed.

### G2. Forward Log Timing & Grounding Audit
- All 8 FORWARD rows verified:
  - `scored_at` strictly after `close_date`.
  - `scored_at` strictly before `listing_date`.
  - Feature snapshots committed before or at scoring time.

### G3 & G4. GitHub Actions Failures Audit (D-042, D-043)
- Analyzed failure logs for scheduled runs #9 and #10: failed due to `Hyundai Motor India` temporarily carrying `status=FORWARD` instead of `INVALID`, triggering assertion failure in `test_r6_prediction_log_status_and_filtering`.
- Resolved in commit `7f7dc89`; runs #11 through #18 passed green.
- Dashboard verified via `gh api repos/soul991/OPI/pages` (HTTP 404): Pages not enabled; dashboard maintained in-repo as static asset.

### G5. Outcome Ingestion Schedule
- Jio Platforms and Paras Healthcare list on 2026-10-28; will be ingested post-listing via `scripts/update_actuals.py` using official exchange evidence.

### G6. Stray Local Branch Check (D-033)
- Checked branch `local-work-2026-10-20`: all useful changes were already merged and verified in `main`.

---

## 5. Workstream Results (Before / After on the Same Rows)

### Workstream A: Out-of-Range and Mega-Issue Safety Guard (D-040)
- **Before**: Inputs exceeding historical training ranges were scored without warning; predictions were displayed in the app and dashboard with normal confidence.
- **After**: `opi/score.py` checks all numeric inputs against `model/feature_ranges.json`. Any out-of-range value triggers warning flags, forces `confidence = LOW`, and suppresses probability display.

| Candidate Row | Metric | Before Workstream A | After Workstream A | Change / Guard Effect |
|---|---|:---:|:---:|---|
| **Jio Platforms Limited** | Input Flags | `None` | `ISSUE_SIZE_ABOVE_TRAIN_MAX`, `MEGA_ISSUE_GT_10000CR`, `MISSING:pe_ratio`, `MISSING:debt_equity` | Flags visible in console & log |
| **Jio Platforms Limited** | Confidence | `NORMAL` | `LOW` | Warning badge rendered |
| **Jio Platforms Limited** | Probability Display | `88.2%` (shown) | `Hidden` (`display_probability: false`) | Extrapolation probability suppressed |
| **Standard In-Range Input** | Input Flags | `None` | `None` | Unaltered normal scoring |
| **Standard In-Range Input** | Confidence | `NORMAL` | `NORMAL` | Full display permitted |

### Workstream B: Forward Error Post-Mortem (D-041)
- Structured audit generated in `phases/Phase 11/forward_postmortem.md` for all 6 completed listings.
- Bonfiglioli Transmissions (model +21.10%, GMP +21.67%, actual +0.00%): Market weakened on listing day (Nifty -0.35%), and issue was 100% OFS. Hypothesis (untested): institutional support evaporated amidst heavy supply and sector weakness.

| Forward Listing | Model Error (pp) | GMP Error (pp) | Listing Day Nifty Move | Feature Availability | Working Post-Mortem Hypothesis |
|---|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect** | 2.73 pp | 6.87 pp | -0.18% | Full (GMP present) | High institutional demand (QIB 256.7x) supported pop despite OFS structure. |
| **Fusion CX** | 1.21 pp | N/A | +0.42% | Model-only (No GMP) | Model accurately priced low demand without GMP guidance. |
| **Zetwerk Mfg** | 6.23 pp | 3.14 pp | -0.12% | Full (GMP present) | Retail demand (11.8x) outstripped institutional sentiment; modest pop achieved. |
| **Sahajanand Med** | 0.43 pp | 0.91 pp | -0.12% | Full (GMP present) | Both model (+8.3%) and GMP (+7.0%) tightly anticipated actual gain (+7.9%). |
| **Tonbo Imaging** | 8.99 pp | 7.15 pp | -0.12% | Full (GMP present) | Intense speculative squeeze (QIB 185.4x) produced extreme pop (+65.7%). |
| **Bonfiglioli** | 21.10 pp | 21.67 pp | -0.35% | Full (GMP present) | **Hypothesis (untested)**: 100% OFS mega-supply combined with soft market resulted in flat open. |

### Workstream C: Walk-Forward Conformal Interval & Tail Experiment (D-007, D-008)
- Conducted strictly walk-forward across 20 quarters ($n = 398$ holdout IPOs) using fixed seed 42 with 2,000 bootstrap resamples.
- Neither candidate achieved the multi-objective targets required to displace the champion.

| Model Architecture | Overall Coverage (80% Nom) | Wilson 95% CI | Tail Coverage (Top 10% Pops) | Tail Wilson 95% CI | Mean Width | Decision |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Champion (Pooled Conformal)** | 87.94% | [84.4%, 90.8%] | 55.00% | [39.8%, 69.3%] | 48.96 pp | **RETAINED** |
| **Candidate 1 (Mondrian Conformal)** | 85.68% | [81.9%, 88.8%] | 57.50% | [42.2%, 71.5%] | 47.21 pp | REJECTED (Failed Targets 1, 2, 3) |
| **Candidate 2 (Quantile CQR)** | 83.92% | [80.0%, 87.2%] | 67.50% | [52.0%, 79.9%] | 52.72 pp | REJECTED (Failed Targets 2, 3) |

- **Paired Bootstrap Differences vs Champion**:
  - Candidate 1 Coverage Difference: -0.0226 (95% CI: [-0.0452, +0.0000], straddles zero).
  - Candidate 2 Tail Coverage: 67.5% (misses Target 2 requirement of $\ge 70\%$). Width: wider by +3.76 pp (misses Target 3 requirement of $\le -5$ pp).
  - Verdict: Champion kept intact; D-007 and D-008 closed as **ACCEPTED** limitations in `README.md`.

### Workstream D: OpenRouter Research Agent (D-026)
- Model configuration externalized in `config/research_models.json` with free-tier models:
  1. `nvidia/nemotron-3.5-super-vl:free`
  2. `google/gemma-4-31b-it:free`
  3. `nvidia/nemotron-3-super-120b-a12b:free`
- Rate-limit handling: 20 req/min, 50 req/day; HTTP 429 backoff/sleep; HTTP 404 fallback to next model.
- Scheduled Actions workflow updated in `.github/workflows/daily.yml` with `concurrency` and secret `OPENROUTER_API_KEY`.
- No mock data added to repository; secret safety verified (`git grep sk-or-` clean).

### Workstream E: Forward Tracking & App Hygiene (D-044)
- Automated tracking report produced in `phases/Phase 11/forward_status.md`.
- D-044 resolved: Jio Platforms sector label flagged as `UNVERIFIED` without modifying historical `prediction_log.csv` row.
- Probability suppression verified: outside calibrated range `[0.091, 0.882]`, probability is suppressed in console and dashboard.

---

## 6. Wording Check

- **Comparative Superiority Terms**: Terms such as "beats", "proves", or "falsified" are used **only** when accompanied by a paired bootstrap confidence interval strictly excluding zero.
- **Hypothesis Labeling**: All post-mortem causal statements regarding individual IPO listing pops are labeled explicitly as **Hypothesis (untested)**.
- **Provisional Rule**: All forward tracking statements explicitly cite sample size ($n = 6$ of 30) and include the mandatory notice: "Provisional, descriptive only; no performance claims permitted below $n = 30$".

---

## 7. Self-Audit (Yes / No with Evidence)

| Audit Question | Result | Verifiable Evidence |
|---|:---:|---|
| Did any earlier-phase file change except by ERRATA? | **NO** | `git diff 187e154 HEAD -- phases/Phase\ [1-9]* phases/Phase\ 10*` shows 0 changes. |
| Did any value enter a feature without a snapshot? | **NO** | Every forward row feature matches a committed snapshot in `data/evidence/` verified by `scripts/verify_all.py`. |
| Did any report number get typed by hand? | **NO** | All headline figures, MAEs, coverage numbers, and audit tables were generated by committed scripts (`forward_report.py`, `evaluate_tail_and_intervals.py`, `generate_forward_status.py`). |
| Did any test pass only because of untracked local files? | **NO** | Verified on clean git status via `python scripts/verify_all.py` (62 PASS, 0 WARN, 0 FAIL). |
| Was the OpenRouter key kept out of the repo, logs, and snapshots? | **YES** | `git grep sk-or-` returns 0 secret key matches across all repository files. |
