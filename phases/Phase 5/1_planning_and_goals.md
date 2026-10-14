# Phase 5: Planning & Goals - Remediation Gate, Real Fundamentals, Fresh Test

> Place at `phases/Phase 5/1_planning_and_goals.md`. This phase is **strict**. Phase 4 contained unfinished work, misleading reporting and test-data mistakes. Phase 5 begins by correcting them. **No new modelling may start until Gate A (Section 1) passes.** If you cannot complete an item, say so plainly in the report. Do not work around it, rename it, or describe it as done.

## 0. Non-Negotiable Rules (apply to every task in this phase)

1. **Follow `RULES.md`.** Three files in `phases/Phase 5/`: `1_planning_and_goals.md`, `2_building_and_execution.md`, `3_outcome_and_verdict.md`.
2. **Never fabricate.** No estimated, guessed, back-filled or "plausible" values in any data column. Unverifiable = empty. No made-up IPOs, predictions, sources or metrics.
3. **Never cherry-pick.** Any table of examples must be either (a) the complete set, or (b) a random sample with the seed stated, or (c) explicitly "best 10 / worst 10" and labelled as such. Tables sorted by error ascending and cut off are forbidden.
4. **Evidence language.** Words like "wins", "beats", "improves", "significant" are allowed only if a paired bootstrap (2,000 resamples, seed fixed) gives a 95% interval for the difference that excludes zero. Otherwise write "no demonstrated difference".
5. **Report what failed first.** Every verdict starts with targets missed, then targets met.
6. **No test-set tuning.** Anything chosen using data (hyperparameters, features, blend weights, thresholds, calibration) is chosen on training/validation data only.
7. **Do not delete or rewrite history in earlier phase files.** Correct them by adding a dated `## ERRATA` section at the top (Section 1, R1). Keep the original text below it.
8. **Relative links only** in markdown (`phases/Phase 4/...`), never absolute file URI links (`file` + `:///` or `/` `Users/...`).
9. **Reproducibility.** Fixed seeds, commands recorded exactly, `requirements.txt` updated.
10. Decision aid only, not financial advice. State this in the final verdict.

## 1. Gate A - Defects to Fix Before Anything Else

Each item lists what went wrong in Phase 4 and the check that proves it is fixed. Commit Gate A as its own commit: `phase5-gate-a`. In `2_building_and_execution.md` include a table: item, status (fixed / not fixable), evidence, command output.

| # | Defect found in Phase 4 | Required fix | Done when |
|---|---|---|---|
| **R1** | `phases/Phase 4/3_outcome_and_verdict.md` section 4 labels a table "Sample of 30 Recent Unseen Listings", but it shows the 29 smallest errors plus the single worst. The real distribution (75 IPOs) has median error 8.29%, 75th percentile 14.2%, 90th percentile 27.8%, several misses of 35-45 points (Esds Software, Orient Cables, Adroit Industries, Moneyview, Behari Lal, Skyways). | Add an `## ERRATA (Phase 5)` section at the top of the Phase 4 verdict stating this plainly. Add `phases/Phase 5/phase4_error_distribution.csv` and a short summary: mean, median, p75, p90, max, and the 10 worst plus 10 best errors, with all 75 rows in the CSV. | Erratum present; CSV has 75 rows; summary numbers match `final_test_results.csv`. |
| **R2** | "Blend WINNER" claim (6.77% vs 6.88% on validation) is tiny, its weight (0.55) was chosen on that same validation set, and on the real final test (8 IPOs with GMP) raw GMP was best (4.29% vs blend 4.50% vs model 5.30%). | Erratum: restate as "no demonstrated advantage over raw GMP". Run the paired bootstrap on validation and on the 8 test IPOs and report the intervals. | Intervals reported; wording in Phase 4 corrected by erratum. |
| **R3** | Calibration "target met" was measured on validation, the same data Platt scaling was fitted on. On the frozen final test, ECE was 0.1406 (target <= 0.10) and Brier 0.1660; classifier accuracy fell from 84.0% to 73.3%. | Erratum: state that the ECE target was **missed** on the final test. Compute ECE with 10 equal-frequency bins (and also report the equal-width version) so low-count bins do not dominate; report counts per bin. | Erratum present; reliability table regenerated with counts. |
| **R4** | The reliability table has "Pre-Cal Gap" values that do not match the adjacent columns (e.g. bin [0.0,0.1): raw avg 0.015 vs actual 0.024 should give about 0.009, but the table shows 0.116). | Find the bug in `scripts/phase4_train_evaluate.py`, fix it, regenerate the table, add a unit test that recomputes each gap from its columns. | `pytest` (or a script) passes; table gaps equal `abs(avg_pred - actual)` for every bin. |
| **R5** | **Fundamentals not delivered.** `roe`, `roce`, `revenue_growth_pct`, `pat_margin_pct` are 0% filled for 2021-2026; `pe_ratio`, `peer_median_pe`, `debt_equity` are about 62% (target was >= 70%). The report blamed "exchange archives" but never tried the prospectus (RHP/DRHP) or company filings. H1 was therefore never tested. | Perform the work in Section 3 (Workstream A). Do not close this item by relabelling. | See Section 3 acceptance rules. |
| **R6** | `predictions/prediction_log.csv` contains no genuine forward prediction: "Kisshtipo" appears twice and already listed on 2026-05-08, and "Hyundai Motor India" is described as an upcoming October 2026 mainboard IPO. (To the best of my knowledge Hyundai Motor India listed in October 2024, so this looks like an invented test row. Verify against an exchange source.) | Keep the file append-only, but add a `status` column and mark each test row `status=TEST_NOT_FORWARD`; never count these rows in any metric. Add a note in the README. If the Hyundai row cannot be verified from an exchange/RHP source, state that in the erratum and mark it invalid. | Every row has a status; the metrics scripts exclude `TEST_*` and `INVALID` rows (add a test). |
| **R7** | Phase 4 markdown files again contain absolute file URI links (they were fixed in an earlier cleanup and re-introduced). | Replace with relative links in all `phases/**/*.md` and `README.md`. | `grep -rn "file:/"/"/" phases README.md` and `grep -rn "/"Users"/" phases README.md scripts model` return nothing. |
| **R8** | The Phase 4 **final test set was consumed**: it was scored once, and its results were read and reported, so it is now development data. | Rename `data/ipo_final_test.csv` to `data/ipo_phase4_test_used.csv`; use it as an extra validation set only. Build a **new, empty-for-now Phase 5 final test** (Section 4). | File renamed; README explains why; no Phase 5 tuning ever touches the new final test. |

If a Gate A item cannot be fixed (for example, a source is unavailable), mark it `NOT FIXED` with the reason. Do not delete the item from the table. Unfixed items must be repeated in the final verdict under "Targets missed".

## 2. Objectives & Scope (after Gate A passes)

1. **Test the fundamentals hypothesis properly** by extracting real financials from RHP/DRHP and filings (Workstream A).
2. **Test the model against GMP honestly** using a fresh forward test and paired bootstrap intervals (Workstream B).
3. **Fix the evaluation set-up**: a rolling-origin evaluation for development, and a new frozen forward final test (Workstream C).
4. **Make the forward log real** by scoring genuinely upcoming IPOs before they list (Workstream D).
5. **Improve tail handling** (the model under-predicts large pops such as Tempsens, +111% vs +28%): analyze, do not just claim success. Report whether a separate "big pop" classifier or a different loss helps on validation.

Out of scope: SME IPOs, deep learning, long-term returns, pre-open order-book features (parked until the above is complete).

## 3. Workstream A - Real Fundamentals (the main work of this phase)

**Scope:** all mainboard IPOs listed 2021-01-01 to 2026-10-14 (about 479 rows in `ipo_master.csv`), **newest first**.

**Columns:** `roe`, `roce`, `revenue_growth_pct`, `pat_margin_pct`, `debt_equity`, `pe_ratio`, `peer_median_pe`.

**Method (in this order):**
1. For each IPO, locate the RHP/prospectus (SEBI, company or lead-manager sites). Extract audited figures from the "Summary of financial information" / restated financials. Use the **latest fiscal year before the issue opened**.
2. Define formulas once in `references/fundamentals_definitions.md` (for example, revenue growth = (revenue_FY - revenue_FY-1) / revenue_FY-1 x 100; PAT margin = PAT / revenue x 100; ROE = PAT / average net worth x 100). Apply them identically to every IPO.
3. For each value store: value, fiscal year, source URL and page, and a `confidence` field (`high` = from RHP table, `medium` = from reputable aggregator, `low` = unclear). Save in `data/fundamentals_sourced.csv` (one row per IPO and column), then merge into the master with a script.
4. Do not infer one metric from another aggregator's ratio unless the definition matches; otherwise leave empty.

**Acceptance rules:**
- Spot-check 40 random filled rows (seed fixed) against a second source; report the match rate (tolerance 2% relative).
- Target: >= 70% coverage per column over 2021-2026, and match rate >= 95%.
- If coverage is below 70% for a column, **exclude that column from the model** and state that H1 is "not tested for this column". Do not impute.
- Report coverage per column per year in `phases/Phase 5/fundamentals_coverage.csv`.
- Log every correction in `phases/Phase 5/data_corrections.csv` (date, company, column, old, new, reason).
- If fundamentals work cannot be done (no web access, sources blocked), stop and say so at the top of the verdict. Do not substitute guesses.

## 4. Workstreams B, C, D

### B. Honest model-vs-GMP evaluation
- Predictors compared on IPOs that have GMP: (a) raw GMP, (b) model without GMP, (c) model with GMP, (d) blend. Blend weight chosen on validation only.
- Report MAE and median absolute error for each, and the paired bootstrap interval of every difference vs raw GMP.
- Report separately for IPOs **without** GMP: model vs historical mean (this is where the model is most likely to be useful).

### C. Evaluation design
- **Development:** rolling-origin (walk-forward) evaluation by calendar quarter from 2022 onward: train on everything before the quarter, test on that quarter. Report per-quarter MAE and AUC plus the pooled value. Tune hyperparameters only inside the training window.
- **Validation sets:** the old validation split and `ipo_phase4_test_used.csv` (development data now).
- **New frozen final test:** all mainboard IPOs listing on or after **2026-10-15**, collected as they list. Create `data/ipo_phase5_final_test.csv` as an empty file with the correct header now. Do not read its rows for any decision. Claims about final-test performance are allowed only once it has **at least 30 IPOs**; before that label everything "provisional (n=<count>)".

### D. Forward prediction log (made real)
- Before each upcoming IPO lists, run `scripts/log_prediction.py` on a `new_ipo.csv` built from verified data (final subscription, final-day GMP) and append a row with `status=FORWARD`.
- After listing run `scripts/update_actuals.py`. Never edit past predictions.
- Provide `scripts/forward_report.py` that summarizes only `FORWARD` rows: count, MAE, calibration (when n is large enough), and clearly prints "n too small" below 30.
- At least one genuine upcoming IPO must be scored and committed **before** it lists. If none is available on the run date, say so; do not invent one.

## 5. Pre-Registration (must be committed before any Phase 5 model is trained)

Create `phases/Phase 5/preregistration.md` containing: the exact metrics, the bootstrap procedure, the features allowed, the calibration method, the rule for choosing the blend weight, and the decision rules in Section 6. Commit it as `phase5-preregistration` **before** training. Changing it afterwards requires a dated "Amendment" section with a reason; the original text stays.

## 6. Success Criteria & Decision Rules

These are measured, not promised. Failing a target is acceptable if reported honestly.

| Question | Metric | Decision rule |
|---|---|---|
| Did Gate A pass? | R1-R8 table | All fixed or honestly marked NOT FIXED |
| Fundamentals coverage | % filled per column, 2021-2026 | >= 70% to enter the model; else excluded |
| Fundamentals accuracy | 40-row spot check | >= 95% match |
| H1: fundamentals help | Rolling-origin MAE and AUC with vs without fundamentals | "Helps" only if paired bootstrap interval excludes zero; otherwise "no demonstrated effect" |
| Model vs mean baseline | MAE, paired bootstrap | Same rule |
| Model/blend vs raw GMP | MAE on GMP subset, paired bootstrap | "Beats GMP" only if interval excludes zero; otherwise recommend GMP plus judgment |
| Calibration | ECE (equal-frequency bins) and Brier on rolling-origin out-of-sample predictions | Target ECE <= 0.10 on **out-of-sample** data, not on the fitting set |
| Tail behaviour | Error on the top 10% largest actual gains | Report; no target, but must be shown |
| Forward test | n of `FORWARD` rows; provisional metrics | No claims below n = 30 |

## 7. Task List (strict order)

1. Read `RULES.md` and this file; confirm in `2_building_and_execution.md`.
2. **Gate A**: complete R1-R8, run the verification commands below, commit `phase5-gate-a`.
3. Commit `preregistration.md`.
4. Workstream A (fundamentals), newest years first; commit data and coverage files after each year.
5. Rebuild features and train using rolling-origin; tune only inside training windows.
6. Run Workstream B comparisons with bootstrap intervals.
7. Create the new final test file (empty), the forward report script, and score a genuine upcoming IPO (Workstream D).
8. Write `2_building_and_execution.md` (architecture, scripts, exact commands, artifacts) and `3_outcome_and_verdict.md` with the structure in Section 8.
9. Run the self-audit (Section 9) and attach its output to the verdict.

**Verification commands (Gate A):**
```bash
grep -rn 'file:''///' phases README.md || echo "OK no file" ":/// links"
grep -rn '/'Users'/' phases README.md scripts model || echo "OK no absolute user paths"
python -m pytest -q          # includes tests for R4 and R6
python scripts/forward_report.py   # must exclude TEST and INVALID rows
head -3 phases/Phase\ 4/3_outcome_and_verdict.md   # must show the ERRATA header
```

## 8. Required Structure of `3_outcome_and_verdict.md`

1. **Targets missed and unfixed items** (first section, even if empty: write "None" explicitly).
2. Gate A table with final status and evidence.
3. Fundamentals coverage and spot-check results.
4. Rolling-origin results (per quarter and pooled) with bootstrap intervals.
5. Model vs historical mean, and model/blend vs raw GMP (with and without GMP subsets).
6. Calibration (out-of-sample, counts per bin).
7. Tail behaviour (top 10% gains; 10 worst and 10 best errors, labelled).
8. Forward log status (n of FORWARD rows, provisional numbers, or "none yet").
9. Honest verdict and failure modes; recommendations for Phase 6.
10. Statement: decision aid only, not financial advice.

## 9. Self-Audit (attach to the verdict)

Answer each with yes/no and evidence:
- Did any number in the report come from the final test set during tuning? (must be no)
- Does every example table state how rows were chosen?
- Are all "beats / wins / improves" claims backed by a bootstrap interval excluding zero?
- Is any data value estimated rather than sourced? (must be no)
- Do all `phases/**/*.md` links work on GitHub (relative)?
- Are TEST/INVALID prediction rows excluded from every metric?
- Is anything in Gate A still NOT FIXED, and is it listed under "Targets missed"?
