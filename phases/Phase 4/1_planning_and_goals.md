# Phase 4: Planning & Goals - Honest Testing, Calibration, Real Fundamentals

> Place this file at `phases/Phase 4/1_planning_and_goals.md`. Follow `RULES.md` (three files per phase, never overwrite earlier phases). Phase 4 is **evaluation-first**: the aim is trustworthy numbers, not bigger headline scores.

## 1. Objectives & Scope

Phase 3 results are promising but rest on weak evidence (10 hand-picked IPOs, over-confident probabilities, tuning that overlapped test data, model not beating raw GMP). Phase 4 fixes this in five workstreams:

1. **Clean three-way split with a frozen final test set**
   - Train: listings before 2025-06-01.
   - Validation (tuning and calibration only): 2025-06-01 to 2026-05-31.
   - **Final test (frozen): listings on or after 2026-06-01.** Touched exactly once, at the end of the phase. No tuning, feature choice or threshold choice may look at it.
   - Save as `data/ipo_train.csv`, `data/ipo_val.csv`, `data/ipo_final_test.csv`. Record row counts and date ranges in the report. Also score the **Phase 2 model** on the final test so Phase 4 can be compared fairly.
2. **Probability calibration**
   - Calibrate the >10% classifier (isotonic if validation size allows, else Platt/sigmoid) using the validation set only.
   - Report a reliability table (10 bins), Brier score and ECE, before and after calibration.
   - Re-run the 10 landmark backtests with calibrated probabilities and report them as "illustrative only, not evidence" because those IPOs are hand-picked and some influenced earlier tuning (Tata Technologies).
3. **Real fundamentals for 2021-2026 listings (about 380 IPOs)**
   - Fill `roe`, `roce`, `revenue_growth_pct`, `pat_margin_pct`, `debt_equity`, `pe_ratio`, `peer_median_pe` from the RHP/prospectus or exchange filings (screener-style sites are acceptable second sources).
   - Every filled cell needs a source in `source_urls`. Leave empty if unverifiable. **Never estimate or invent values.**
   - Spot-check 30 random filled rows against a second source and report the match rate.
   - If coverage for a column is below 70% in 2021-2026, report that and exclude the column from the model.
4. **GMP-aware comparison**
   - On the subset with GMP, compare four predictors: (a) raw GMP, (b) model without GMP, (c) model with GMP, (d) simple blend (e.g. weighted average of GMP and the model, weight chosen on validation).
   - State plainly which one wins on the final test.
5. **Forward prediction log**
   - Create `predictions/prediction_log.csv` with columns: `scored_at`, `company`, `open_date`, `close_date`, `listing_date`, `features_snapshot_json`, `pred_gain_pct`, `pred_prob_gt10`, `gmp_pct_at_scoring`, `actual_gain_pct`, `notes`.
   - Add `scripts/log_prediction.py` (score a `new_ipo.csv`, append a row **before** listing) and `scripts/update_actuals.py` (fill `actual_gain_pct` after listing). Rows are append-only; never edit a past prediction.

Also in scope (small cleanups):
- Add a `README` section "Data sources and licensing". Check the terms of Moneycontrol, Chittorgarh and the Kaggle/GitHub datasets. If redistribution is not allowed, add `data/raw/` to `.gitignore`, keep `scripts/download_all_raw_data.py`, and document how to rebuild.
- 2012-2014 have only 3-11 IPOs per year. Try to fill them from exchange archives; if that fails, document the gap and run a sensitivity check training on 2016+ only.
- Replace the catch-all "Industrial & Manufacturing" sector label (about 33% of rows) with a finer taxonomy, and report how many rows changed.

Out of scope: SME IPOs, deep learning, long-term (post-listing) returns.

## 2. Hypotheses & Research Questions

- **H1:** Real fundamentals (profitability, valuation vs peers) improve MAE and ROC-AUC on the validation set versus the Phase 2 feature set.
- **H2:** Calibration lowers Brier score and ECE; the 99%+ probabilities seen in Phase 3 shrink to defensible levels.
- **H3:** On IPOs with GMP, a blend of GMP and the model beats raw GMP alone. (Phase 2 showed the model alone does not: 7.14% vs 6.38% MAE.)
- **H4:** The model's advantage over GMP is concentrated where GMP is missing (older and smaller IPOs).
- **Null result is acceptable.** If H1 and H3 fail, the report must say so and recommend using GMP plus judgment rather than the model.

## 3. Data Strategy

- **Leakage rules (unchanged):** every feature must be knowable before listing (final-day subscription, final-day GMP, 30-day prior Nifty return, VIX on close date). Fundamentals must come from documents published before the issue opened.
- **Tuning discipline:** hyperparameters, feature selection, calibration method and blend weights are chosen on validation only. The final test set is evaluated once; the result is reported even if disappointing.
- **No retrospective cherry-picking:** do not select, drop or re-label IPOs after seeing results. Log any data corrections with a reason and date in `phases/Phase 4/data_corrections.csv`.
- **Provenance:** keep `data/ipo_master.csv` as the single master; every change goes through a script in `scripts/` that can be re-run.
- **Reproducibility:** fix random seeds, pin versions in `requirements.txt`, and record exact commands in `2_building_and_execution.md`.

## 4. Success Criteria & Metrics

Targets are goals to measure against, not promises. Report the actual numbers either way.

| Goal | Metric | Target | Reported on |
|---|---|---|---|
| Honest generalization | MAE and ROC-AUC vs Phase 2 model | Phase 4 model no worse than Phase 2 | Final test |
| Beats naive mean | MAE vs historical mean | Lower | Final test |
| Beats raw GMP | MAE vs raw GMP (GMP subset) | Blend lower than raw GMP | Final test |
| Calibrated probabilities | ECE and Brier score | ECE <= 0.10; Brier lower than uncalibrated | Validation and final test |
| Fundamentals coverage | % non-empty per column, 2021-2026 | >= 70% (else column dropped) | Master dataset |
| Data accuracy | Spot-check match rate (30 rows) | >= 95% | Master dataset |
| Forward log live | Log files and scripts working | Created, with at least one scored upcoming IPO | `predictions/` |
| Documentation | Three phase files plus README licensing note | Complete | Repo |

## 5. Task List for the Executing Agent (in order)

1. Create the three-way split and freeze `data/ipo_final_test.csv`; score the Phase 2 model on it for reference.
2. Fix sector taxonomy; fill 2012-2015 gaps if possible (or document).
3. Collect fundamentals for 2021-2026; spot-check 30 rows; log corrections.
4. Retrain on the train split with the new features; tune on validation only.
5. Calibrate the classifier on validation; produce reliability table, Brier and ECE.
6. Run the GMP-subset comparison (raw GMP, model without GMP, model with GMP, blend).
7. Evaluate once on the final test set; fill `3_outcome_and_verdict.md` including: key metrics, baselines (mean and raw GMP), holdout table, honest verdict and failure modes, and recommendations for Phase 5.
8. Build the forward prediction log and scripts; score at least one currently open or upcoming IPO and commit the log **before** it lists.
9. Update README (data sources and licensing, how to run Phase 4) and write `2_building_and_execution.md`.

> Reminder to the agent: this is a decision aid, not financial advice. If results are weak, say so plainly in the verdict.
