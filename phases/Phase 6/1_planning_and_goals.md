# Phase 6: Planning & Goals - Data Integrity, Honest Status Reporting, Prediction Intervals, Real Forward Test

> Place at `phases/Phase 6/1_planning_and_goals.md`. This phase is **strict**. Phase 5 improved the process, but it left data errors in the dataset, marked partly finished work as fixed, and logged an inconsistent forward prediction. **No new modelling or feature work may start until Gate A6 (Section 1) passes.** If something cannot be done, say so plainly and mark it `NOT FIXED`. Do not rename it, reword it, or call it done.

## 0. Non-Negotiable Rules

1. **Follow `RULES.md`.** Exactly three files in `phases/Phase 6/`: `1_planning_and_goals.md`, `2_building_and_execution.md`, `3_outcome_and_verdict.md`.
2. **Status vocabulary.** Every item is exactly one of `FIXED`, `PARTIAL`, `NOT FIXED`. `FIXED` is allowed only if its verification command or check passes and its output is pasted in `2_building_and_execution.md`. If a deliverable is 60% complete, it is `PARTIAL`.
3. **"Unfixed items: None" is allowed only if literally true.** Any `PARTIAL` or `NOT FIXED` item must be listed under "Targets missed and unfixed items".
4. **Never fabricate.** No estimated, guessed, imputed or back-filled data values, sources, predictions or metrics. Unverifiable = empty.
5. **Never delete data silently.** Removing a row requires an entry in `data/excluded_rows.csv` (company, listing_date, reason, source URL, date of decision). Nothing is removed unless it appears there.
6. **Before/after for every data change.** Any change to the dataset must be accompanied by a table showing the same metrics before and after, on the rows that remain in both.
7. **Never cherry-pick.** Example tables must be complete, randomly sampled (seed stated) or explicitly labelled "best N / worst N".
8. **Evidence language.** "Beats", "wins", "improves", "falsified", "significant" require a paired bootstrap (2,000 resamples, fixed seed) whose 95% interval excludes zero. If the interval straddles zero the only allowed wording is "no demonstrated difference/effect".
9. **No test-set tuning.** Anything chosen from data (hyperparameters, features, weights, thresholds, calibration, interval method) is chosen on training or validation data only. The new final test is never read for decisions.
10. **Pre-registration.** Commit `phases/Phase 6/preregistration.md` before training or evaluating anything after the data cleaning. Changes later need a dated "Amendment" section; the original text stays.
11. **Do not rewrite earlier phase files.** Corrections go in a dated `## ERRATA (Phase 6)` section at the top, with the original text kept below.
12. **Relative links only.** No `file` + `:///` or `/` `Users/...` paths.
13. **Every number in a report must come from a script output file** committed in `phases/Phase 6/`. Hand-typed numbers are forbidden.
14. Decision aid only, not financial advice. State this in the final verdict.

## 1. Gate A6 - Defects From Phase 5 (fix first; commit as `phase6-gate-a`)

In `2_building_and_execution.md` include a table: item, status, evidence, pasted command output.

| # | Defect found in Phase 5 | Required fix | Done when |
|---|---|---|---|
| **S1** | **Follow-on offers (FPOs) and non-listings are in the IPO dataset.** `Patanjali Foods` (listing_price 31.23 vs issue_price 650, gain -95.2%), `Adani Enterprises` (437.20 vs 3276, -86.65%) and `Vodafone Idea` (35.85 vs 75, -52.2%) appear as IPOs. To the best of my knowledge the Adani Enterprises FPO was withdrawn (no listing) and Vodafone Idea's FPO price was far below 75; verify both against exchange or SEBI sources and write what you actually find. These three are the only rows below -50% and three of the "10 worst errors". | (a) Define the inclusion rule in `references/inclusion_criteria.md`: fresh mainboard IPO of a company not previously listed; FPOs, rights issues, OFS-only sales of listed companies, withdrawn issues and re-listings are excluded. (b) Audit **every** row against the rule: automated flags (listing_price/issue_price < 0.4 or > 4.0, listing_date earlier than close_date, duplicate company, prior-listing indicators) plus manual verification of every flagged row. (c) Record decisions in `data/excluded_rows.csv`. (d) Re-run the Phase 5 evaluation on the cleaned data. | `data/data_audit_report.md` lists every flagged row and its verified outcome; excluded rows are only those in `excluded_rows.csv`; before/after metric table produced; unit test asserts no row in the master violates the inclusion criteria. |
| **S2** | **R5 was marked FIXED and "Unfixed: None", but it is not.** `roce` and `revenue_growth_pct` are 0% filled, `pe_ratio` (61.4%) and `peer_median_pe` (62.4%) are below 70% and unchanged from Phase 4, and 2026 coverage is about 36%. | ERRATA on the Phase 5 verdict changing R5 to `PARTIAL` (and "Unfixed items" to list it), with a column-by-column coverage table. | Erratum present; the Phase 5 "Unfixed Items" section no longer says "None". |
| **S3** | **Fundamentals were called "audited" but all 1,155 values are `confidence=medium` from Chittorgarh aggregator pages; none from RHP/DRHP or filings.** The "40/40 match" does not say which independent source was used. | Replace the word "audited" with "aggregator-sourced" in an erratum. Redo the spot-check: 40 random rows (seed fixed) verified against an **independent primary source** (RHP/DRHP, exchange filing, company filing), saved as `phases/Phase 6/fundamentals_spotcheck.csv` with columns company, metric, value, independent_source_url, page, independent_value, match (Y/N). If primary documents are unreachable, record `NOT INDEPENDENTLY VERIFIED` and do not report any match rate. | CSV exists with 40 rows and a primary source URL for each verified row, or the status is explicitly stated as unverified. |
| **S4** | **Wording violations.** H1 was called "FALSIFIED" although its interval was `[-0.022, +0.473]` (straddles zero), and only 3 of 7 fundamentals were tested. | ERRATA: "No demonstrated effect. Partially tested (3 of 7 columns); H1 remains open." | Erratum present. |
| **S5** | **Calibration reporting is too generous.** ECE passed at 0.0968, but the 0.574-0.693 bin predicted 0.62 against an actual 0.857, the highest calibrated probability never exceeded 0.866, and quarters with 4-6 IPOs were shown with AUC 1.0000 as if meaningful. | ERRATA noting top-bin under-confidence. In all Phase 6 tables, show per-quarter metrics only for quarters with n >= 20; combine smaller quarters into half-year buckets with n stated. Add a reliability table with counts and 95% intervals (Wilson) per bin. | Tables regenerated by script; bins have counts and intervals. |
| **S6** | **The only forward prediction is internally inconsistent.** `HD Fire Protect Limited` (listing 2026-10-21): predicted gain 11.09% but P(gain > 10%) = 0.9889, above anything the calibrated rolling-origin model ever produced (max 0.866). GMP was 33.21%. It is also unverified whether this is a mainboard (not SME) issue. | (a) Find why the log script produced a probability inconsistent with the evaluated pipeline (calibrated path vs raw path). (b) Make `scripts/log_prediction.py` call the **same** function as the evaluation pipeline. (c) Add a test that asserts the logged probability lies in the calibrated range and agrees with the pipeline output for a fixed input. (d) Verify the IPO's board from an exchange source. (e) The old row stays (append-only); set its status to `INVALID_SCRIPT_BUG` (or `INVALID_NOT_MAINBOARD` if applicable) and append a corrected re-score **before the listing date (2026-10-21)**. If the date has passed before the re-score is committed, do not backfill: leave it invalid and say so. | Tests pass; log has the new status and the corrected row with a `scored_at` earlier than the listing date. |
| **S7** | **R3/R6/R8 claims were not re-verified in the final verdict** and the verdict stated all Gate A items "fully resolved". | Re-run the Phase 5 verification commands (Section 7) and paste outputs. Any failure reopens that item. | Command outputs pasted. |

## 2. Objectives & Scope (after Gate A6 passes)

1. **Data integrity (Workstream A):** a documented, script-checked dataset where every row satisfies the inclusion criteria.
2. **Re-evaluation on clean data (Workstream B):** repeat the rolling-origin comparison; report old vs new.
3. **Prediction intervals (Workstream C):** give users an error bar, not just a point estimate.
4. **GMP coverage (Workstream D):** GMP is the strongest signal but is missing for most recent IPOs (2026Q3: only 5 of 62 rows have GMP). Fix coverage honestly.
5. **Real forward test (Workstream E):** accumulate genuine pre-listing predictions.
6. **Fundamentals decision (Workstream F):** either complete it properly from primary sources or formally close it.
7. **Tail handling (Workstream G, optional, last):** only if everything above is done.

Out of scope: SME IPOs, deep learning, long-term returns, order-book/pre-open features.

## 3. Workstream A - Data Integrity Audit
- Implement `scripts/audit_dataset.py` with these checks, printing counts: inclusion-criteria violations, price-ratio outliers, date-order errors, duplicates, impossible values (negative subscription, gain inconsistent with prices), GMP recorded after the last bidding day (leakage), missing issue price.
- Every flagged row is verified manually against an exchange/Chittorgarh/RHP source and resolved as `KEEP (verified)`, `CORRECTED (old -> new)`, or `EXCLUDED (reason)`. Log in `data/excluded_rows.csv` and `phases/Phase 6/data_corrections.csv`.
- Re-split train, validation and the already-used Phase 4 test set using the same date cuts as before so results are comparable. Do not touch `data/ipo_phase5_final_test.csv`.

## 4. Workstream B - Re-evaluation (after A)
Re-run the Phase 5 rolling-origin pipeline (same code, same seeds) on the cleaned data, with only the Phase 6 reporting changes (S5). Produce a single before/after table: pooled MAE (mean baseline, model without fundamentals, model with fundamentals, raw GMP, blend), ROC AUC, ECE (equal-frequency), Brier, tail error; each with paired bootstrap intervals for the same comparisons as Phase 5. State which Phase 5 conclusions survive and which change.

## 5. Workstream C - Prediction Intervals
- Method (pre-registered): split-conformal intervals (or quantile gradient boosting if justified) computed from rolling-origin residuals available **before** each quarter; target 80% nominal coverage.
- Report empirical coverage per half-year and pooled, mean interval width, and coverage separately for IPOs with and without GMP and for the top 10% largest gains.
- Success rule: pooled coverage within 80% +/- 5 points. If not, report the gap; do not tune on the evaluation quarters.
- `predict.py` must output the estimate **and** the interval, and print which rule applies ("GMP available: rely on GMP; model is context only" vs "GMP not available: model estimate with interval").

## 6. Workstreams D-G

**D. GMP coverage.** Produce `phases/Phase 6/gmp_coverage.csv` (by quarter: rows, with GMP, %). For 2025-2026 rows missing GMP, collect GMP only if it can be sourced **as of the last bidding day** (archived or dated sources), recording the URL and capture date. Never use listing-day GMP. Leave empty otherwise. Report coverage before and after; re-run Workstream B on the improved data as a labelled sensitivity analysis (not replacing the main result).

**E. Forward test.**
- Score every upcoming mainboard IPO before listing using the **same** pipeline, with final-day subscription and final-day GMP; append `status=FORWARD`. Rows are append-only.
- After listing run `scripts/update_actuals.py`; also append the row to `data/ipo_phase5_final_test.csv` (the post-2026-10-14 final test).
- `scripts/forward_report.py` prints n, MAE vs mean baseline and vs raw GMP (where available), interval coverage, and "n too small" below 30. No performance claim before n = 30; label everything "provisional (n=...)".
- State in the verdict how many genuine FORWARD rows exist at commit time, even if zero or one.

**F. Fundamentals decision (time-boxed).** Choose one path and pre-register it:
1. *Complete:* source `roce` and `revenue_growth_pct` (and the P/E columns) from RHP/DRHP financial tables for 2024-2026 listings, with `confidence=high`, fiscal year, page and URL per value. Stop and declare "not feasible" if a random sample of 40 IPOs yields under 60% obtainable values. Include a primary-source spot-check of 40 rows.
2. *Close:* formally close the fundamentals line ("no demonstrated effect with 3 of 7 columns; remaining columns not feasible from available sources") and drop it from further phases.
Either way, do not use aggregator values for any column that is claimed to be primary-sourced.

**G. Tail handling (optional, only if A-F are complete).** Test, on rolling-origin data only, one pre-registered change: a two-stage approach (probability of gain > 50% plus a conditional magnitude model) or quantile loss. Accept only if top-decile MAE improves with a bootstrap interval excluding zero **and** pooled MAE is not worse (interval does not exclude zero in the wrong direction). Otherwise report "no improvement" and keep the current model.

## 7. Verification Commands (Gate A6 and final)
```bash
grep -rn 'file:''///' phases README.md || echo "OK no file" ":/// links"
grep -rn '/'Users'/' phases README.md scripts model tests --exclude-dir=__pycache__ || echo "OK no absolute user paths"
python scripts/audit_dataset.py data/ipo_master.csv      # must report 0 unresolved violations
python -m pytest -q                                      # includes inclusion-criteria and log-consistency tests
python scripts/forward_report.py                         # excludes TEST_*/INVALID_* rows; prints n
head -5 "phases/Phase 5/3_outcome_and_verdict.md"        # must show the ERRATA (Phase 6) header
test -s data/excluded_rows.csv && echo "excluded rows documented"
```

## 8. Success Criteria & Decision Rules (measured, not promised)

| Question | Metric | Decision rule |
|---|---|---|
| Is Gate A6 complete? | S1-S7 table | Each item `FIXED`, `PARTIAL` or `NOT FIXED` with evidence |
| Dataset clean? | Audit script | 0 unresolved violations; every exclusion documented |
| Do Phase 5 conclusions hold on clean data? | Paired bootstrap, same comparisons | Report which survive; use evidence language only |
| Are intervals trustworthy? | Empirical coverage of 80% intervals | 75-85% pooled; else report the gap |
| GMP coverage | % rows with GMP by quarter | Report before/after; no imputation |
| Forward test | n of FORWARD rows | No claims below n = 30 |
| Fundamentals | Path 1 or Path 2 decision recorded | Pre-registered; no aggregator data labelled as primary |
| Tail handling (optional) | Top-decile MAE and pooled MAE | Accept only with bootstrap evidence |

## 9. Task List (strict order)
1. Read `RULES.md` and this file; confirm in `2_building_and_execution.md`.
2. Gate A6 (S1-S7); verification commands; commit `phase6-gate-a`.
3. Commit `phases/Phase 6/preregistration.md` (metrics, interval method, fundamentals path, blend rule, evidence rules).
4. Workstream A (audit), then B (re-evaluation).
5. Workstream C (intervals), then D (GMP coverage).
6. Workstream F decision; Workstream E running in parallel (log upcoming IPOs before they list).
7. Workstream G only if everything else is complete.
8. Write `2_building_and_execution.md` and `3_outcome_and_verdict.md` using Section 10.
9. Attach the self-audit (Section 11).

## 10. Required Structure of `3_outcome_and_verdict.md`
1. **Targets missed and unfixed items** (first; write "None" only if literally true).
2. Gate A6 table with final statuses and pasted evidence.
3. Data audit results and before/after metrics.
4. Rolling-origin results (per-quarter only for n >= 20, otherwise half-year buckets) with bootstrap intervals.
5. Model vs mean baseline; model/blend vs raw GMP (with and without GMP subsets).
6. Calibration (reliability table with counts and intervals) and prediction-interval coverage.
7. GMP coverage change.
8. Fundamentals decision and evidence.
9. Forward log status (n of FORWARD rows, provisional numbers or "none yet").
10. Honest verdict, failure modes, recommended practical use, next steps.
11. Statement: decision aid only, not financial advice.

## 11. Self-Audit (attach to the verdict; yes/no with evidence)
- Does any status say `FIXED` without a pasted passing check?
- Is anything still `PARTIAL` or `NOT FIXED`, and is it listed under "Targets missed"?
- Was any row removed that is not in `data/excluded_rows.csv`?
- Does every data change have a before/after table?
- Does any "beats / wins / improves / falsified" claim lack a bootstrap interval that excludes zero?
- Was the new final test file read for any decision? (must be no)
- Is any value estimated or imputed? (must be no)
- Is any aggregator-sourced value described as primary or "audited"? (must be no)
- Does `log_prediction.py` use the same pipeline as the evaluation, and is that tested?
- Does every number in the reports come from a committed script output?
