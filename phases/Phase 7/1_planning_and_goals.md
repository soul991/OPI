# Phase 7: Planning & Goals - GMP Backfill, Data Verification, Regime Re-evaluation, Forward Test

> Place at `phases/Phase 7/1_planning_and_goals.md`. This phase is **strict**. Phase 6 fixed the biggest Phase 5 problems, but it left GMP coverage collapsed for the most recent IPOs, deleted 15 rows with weak evidence, compared before/after on different rows, and made conclusions the data does not support. **No new modelling may start until Gate A7 (Section 1) passes.** If something cannot be done, mark it `NOT FIXED` and say why. Do not rename it, reword it, or call it done.

## 0. Non-Negotiable Rules

1. **Follow `RULES.md`.** Exactly three files in `phases/Phase 7/`: `1_planning_and_goals.md`, `2_building_and_execution.md`, `3_outcome_and_verdict.md`.
2. **Status vocabulary.** Every item is exactly `FIXED`, `PARTIAL` or `NOT FIXED`. `FIXED` only if the verification command or check passes and its output is pasted in `2_building_and_execution.md`.
3. **"Unfixed items: None" only if literally true.**
4. **Never fabricate.** No estimated, imputed, guessed or back-filled values, sources, URLs, dates, predictions or metrics. Unverifiable = empty.
5. **Every scraped or collected value needs a real source URL.** Generic labels such as "NSE Listing Circular" without a URL are not acceptable evidence. Store the URL, the page's own date, and the date you accessed it.
6. **Never delete or alter data silently.** Any removal or correction needs a row in `data/excluded_rows.csv` or `phases/Phase 7/data_corrections.csv` (company, listing_date, field, old, new, reason, source URL, decision date).
7. **Matched-rows comparisons.** Any before/after table must use exactly the same rows on both sides. Rows present on only one side are reported separately.
8. **Evidence language.** "Beats", "wins", "improves", "unbeatable", "calibrated", "significant" are allowed only with a paired bootstrap (2,000 resamples, fixed seed) whose 95% interval excludes zero, or an explicitly stated empirical test. Otherwise write "no demonstrated difference".
9. **Explanations are hypotheses.** Any statement about *why* something happens (lead-manager pricing, retail liquidity, dealer delays, etc.) must be labelled "Hypothesis (untested)" unless a test in this phase supports it.
10. **No test-set tuning.** Anything chosen from data (hyperparameters, features, weights, quantiles, calibration) is chosen on training or validation data only. Never read `data/ipo_phase5_final_test.csv` for decisions.
11. **Pre-registration.** Commit `phases/Phase 7/preregistration.md` before training or evaluating anything after the data changes. Later changes need a dated "Amendment" section; the original text stays.
12. **Do not rewrite earlier phase files.** Add a dated `## ERRATA (Phase 7)` at the top and keep the original text below.
13. **Every number in a report comes from a committed script output file.** No hand-typed numbers.
14. **Relative links only.** No `file:///` or `/Users/...`.
15. **Commit per workstream** (not one big commit), with clear messages. Do not push partial work that breaks tests.
16. **If blocked** (no access, source unreadable), stop that item, mark it `PARTIAL` or `NOT FIXED`, state the reason, and continue with items that do not depend on it. Never substitute guesses.
17. Decision aid only, not financial advice; say so in the final verdict.

## 1. Gate A7 - Defects From Phase 6 (commit as `phase7-gate-a`)

In `2_building_and_execution.md` include a table: item, status, evidence, pasted command output.

| # | Defect found in Phase 6 | Required fix | Done when |
|---|---|---|---|
| **T1** | **GMP coverage collapsed and Workstream D was not done.** 2026Q3 has GMP for 5 of 62 IPOs (8.1%) and 2026Q4 for 0 of 10. The verdict attributes this to "dealer aggregation delays", which no evidence supports, and presents a coverage table as if Workstream D had been performed. | ERRATA: mark Phase 6 Workstream D as `NOT DONE` (reporting a gap is not collecting data); label the "dealer delays" sentence "Hypothesis (untested)". The real fix is Workstream A below. | Erratum present. |
| **T2** | **15 rows were deleted as "duplicates" with no source URLs** (Aeroflex, Ags Transact, Anthem Biosciences, Arisinfra, Gopal Snacks, Innovision, Irm Energy, Mankind Pharma, Mukka Proteins, Plaza Wires, Pyramid Technoplast, Travel Food Services, Utkarsh Small Finance Bank, Veranda Learning, Western Carriers). At least two look suspicious to me from memory: Utkarsh Small Finance Bank listed around 21 July 2023 and IRM Energy around 26 October 2023, yet those are the dates that were removed (the kept rows are 2023-07-24 and 2023-10-31). I may be wrong; verify. | For each of the 15, find the primary evidence (exchange listing notice or equivalent) showing the true listing date and which row is correct. Create `phases/Phase 7/duplicate_verification.csv` with company, removed_row_date, kept_row_date, true_listing_date, source_url, page_date, outcome (`KEEP_AS_IS`, `RESTORE_REMOVED`, `FIX_KEPT_DATE`, `UNVERIFIED`). Apply any restores or fixes through `data_corrections.csv`. If a row cannot be verified, mark `UNVERIFIED` and flag it in the dataset (`notes`); do not guess. | CSV has 15 rows with URLs or `UNVERIFIED`; dataset matches the outcomes; audit script passes. |
| **T3** | **Overclaims in the Phase 6 verdict:** "Raw GMP is unbeatable" (evidence: no demonstrated advantage over it); "Conformal intervals provide calibrated uncertainty" (its own table shows 59.7% and 60.0% coverage in two subsets); "OPI adds significant value in non-GMP regimes ... the true operational utility" (the no-GMP group is 67 of 77 rows from just the last six months, so it is mostly missing data, not genuinely unquoted issues); untested causal explanations (lead-manager pricing, retail liquidity); "Mukka Proteins +50.9% vs +321.4%" mixes a gain with a subscription figure. | ERRATA listing each statement and its corrected wording. | Erratum present, one item per statement. |
| **T4** | **Before/after table was not like-for-like** (416 rows vs 398). The claimed "improved generalization" is mostly the removal of outliers. | Regenerate on the rows common to both sides; list rows present in only one side. Re-state the conclusion from the matched numbers. | `phases/Phase 7/before_after_matched.csv` exists; row counts equal on both sides. |
| **T5** | **The "no-GMP regime" analysis is confounded** (see T3). | Split IPOs without GMP into (i) GMP not recorded in our data and (ii) GMP confirmed unavailable after a source search. Keep (i) out of "no-GMP" conclusions after Workstream A. | Two groups defined in `references/gmp_status_definitions.md`; column `gmp_status` added with values `OBSERVED`, `NOT_RECORDED`, `CONFIRMED_UNAVAILABLE`. |
| **T6** | **The only forward prediction is still unresolved:** HD Fire Protect Limited (listing 2026-10-21). | Do not edit the row. Verify board and listing outcome from an exchange source; run `scripts/update_actuals.py` once it has listed; if it has not listed at run time, say so. Report predicted +11.09%, GMP-implied 33.21%, interval and the actual result, as a single data point with no performance claim. | Row updated by script only; verdict states the real outcome or "not yet listed". |
| **T7** | **Phase 6 verification not re-checked.** | Re-run all Phase 6 verification commands (Section 7) and paste outputs. A failing command reopens its item. | Outputs pasted. |

## 2. Objectives & Scope (after Gate A7)

1. **A. GMP backfill** for 2025-2026 IPOs with GMP missing, newest first, with dated sources.
2. **B. Data verification v2** (the 15 rows plus a random audit of other rows).
3. **C. Re-evaluation** on the corrected data with redefined regimes.
4. **D. Regime-conditional conformal intervals.**
5. **E. Forward test** (ongoing; the most important long-term item).
6. **F. User-facing status** (README and predict output reflect what is actually shown by the evidence).
7. **G. Optional: anchor-investor features**, only if A-F are complete.

Out of scope: fundamentals (closed in Phase 6), SME IPOs, deep learning, long-term returns.

## 3. Workstream A - GMP Backfill

- **Order:** 2026Q3 and 2026Q4 first (about 67 missing), then 2026Q1-Q2 and 2025 gaps (about 15 more).
- **Rule:** the GMP must be as of the **last bidding day** (or the evening before listing at the latest, and never listing-day or post-listing). Record `gmp_as_of_date` and `gmp_rule` (`last_bidding_day` or `day_before_listing`). A source that shows only a current or undated GMP is unusable.
- **Store** in `data/gmp_sourced.csv`: company, listing_date, gmp_inr, gmp_pct, as_of_date, rule, source_url, page_date, accessed_on, confidence (`high` = dated historical table, `medium` = dated article/post, `low` = unclear). Merge into the master by script; rows with `low` confidence are excluded from model features but kept in the file.
- **Check:** verify 30 random newly sourced values against a second independent dated source (seed fixed). Report the match rate (tolerance 2 percentage points).
- **Coverage report:** `phases/Phase 7/gmp_coverage.csv` by quarter, before and after.
- **Target:** >= 80% coverage in 2026Q3 and 2026Q4. If not achievable, report the actual coverage and the reason; do not impute. Mark remaining rows `gmp_status=NOT_RECORDED` or `CONFIRMED_UNAVAILABLE` per the T5 definitions.

## 4. Workstreams B-D

**B. Verification v2.** Beyond the 15 rows: draw a random sample of 40 other rows (seed fixed) and verify listing date, issue price, listing price and final subscription against exchange or equivalent primary sources, saved as `phases/Phase 7/random_audit.csv` with URLs. Report the match rate; fix mismatches through `data_corrections.csv`.

**C. Re-evaluation.** Re-run the rolling-origin pipeline (same code, seeds, windows) on the corrected data. Report: pooled and per-period metrics (periods with n < 20 merged into half-year buckets), mean baseline, model without GMP, model with GMP, raw GMP, blend; paired bootstrap intervals; matched-rows before/after vs Phase 6. Regimes: `OBSERVED` vs `CONFIRMED_UNAVAILABLE` (never lump `NOT_RECORDED` in). Say plainly which Phase 6 conclusions survive.

**D. Regime-conditional conformal.** Pre-register and compute separate split-conformal quantiles for GMP-observed and GMP-unavailable IPOs, using only residuals available before each evaluation period. Report empirical coverage per regime and for the top 10% of gains, mean width, and n. Target 80% +/- 5 points. If a regime has fewer than 40 evaluated IPOs, report "insufficient n for a coverage claim". Do not tune on the evaluation periods.

## 5. Workstream E - Forward Test (strict)

- At the time of each run, score **every mainboard IPO that is open or has closed but not yet listed**, using the same pipeline as evaluation and the final-day subscription and final-day GMP (with sources). Append rows with `status=FORWARD`. Past rows are never edited.
- After listing, run `scripts/update_actuals.py` and append the row to `data/ipo_phase5_final_test.csv`.
- `scripts/forward_report.py` prints n, MAE vs mean baseline, vs raw GMP (where available), interval coverage; below n = 30 it prints "provisional, no claims".
- State in the verdict exactly how many genuine FORWARD rows exist and how many have listed.
- If no IPO is open or upcoming at run time, say so. Never log a past IPO as FORWARD.

## 6. Workstreams F-G

**F. User-facing status.** Update `README.md` with a plain "What the evidence shows" section: where the model helps (and how much, with intervals), where raw GMP is the better signal, known weaknesses (large pops under-predicted, intervals under-cover in some regimes), forward-test status, and a "do not rely on probabilities above about 0.85 or below about 0.10" note. `predict.py` output must state which rule applies ("GMP observed: GMP is the primary signal, model is context" vs "no GMP: model estimate with the regime-specific interval").

**G. Optional: anchor-investor features.** Only if A-F are complete. Anchor allocation is announced the day before the issue opens, so it is usable before bidding if collected with a dated source. Pre-register one feature set (for example anchor amount as % of QIB portion, number of anchors). Require >= 70% coverage for 2024-2026 with sources, otherwise drop. Accept only with a bootstrap interval excluding zero on rolling-origin data, and report "no demonstrated effect" otherwise.

## 7. Verification Commands
```bash
grep -rn "file:///" phases README.md || echo "OK no file:/// links"
grep -rn "/Users/" phases README.md scripts model tests || echo "OK no absolute user paths"
python scripts/audit_dataset.py data/ipo_master.csv     # 0 unresolved violations
python -m pytest -q                                     # all tests pass
python scripts/forward_report.py                        # prints n; excludes TEST_*/INVALID_* rows
head -5 "phases/Phase 6/3_outcome_and_verdict.md"       # must show ERRATA (Phase 7)
test -s phases/Phase\ 7/duplicate_verification.csv && echo "15-row verification present"
python - <<'PY'
import pandas as pd
d=pd.read_csv("phases/Phase 7/duplicate_verification.csv")
assert len(d)==15 and (d.source_url.notna() | (d.outcome=="UNVERIFIED")).all()
print("duplicate verification OK")
PY
```

## 8. Success Criteria & Decision Rules (measured, not promised)

| Question | Metric | Decision rule |
|---|---|---|
| Gate A7 complete? | T1-T7 table | Each `FIXED`, `PARTIAL` or `NOT FIXED` with evidence |
| GMP coverage | % with dated, sourced GMP, 2026Q3-Q4 | Target >= 80%; report actual and method |
| GMP data accuracy | 30-value second-source check | Report match rate; >= 90% to keep values as `high` |
| Data verification | 15 rows + 40 random rows | Report match rates and all corrections |
| Conclusions after cleaning | Paired bootstrap, matched rows | Use evidence language only |
| Interval coverage by regime | Empirical coverage | 75-85% where n >= 40; else "insufficient n" |
| Forward test | n listed FORWARD rows | No claims below 30 |
| README / predict.py | Reflect measured evidence | No unsupported claims |

## 9. Task List (strict order)
1. Read `RULES.md` and this file; confirm in `2_building_and_execution.md`.
2. Gate A7: do T6 first (check HD Fire Protect), then T1-T5 and T7; commit `phase7-gate-a`.
3. Commit `phases/Phase 7/preregistration.md` (GMP rules, regime definitions, conformal method, metrics, evidence rules).
4. Workstream A (commit per quarter), then B.
5. Workstream C, then D.
6. Workstream E at every run; update actuals for anything that has listed.
7. Workstream F; Workstream G only if all else is complete.
8. Write `2_building_and_execution.md` and `3_outcome_and_verdict.md` using Section 10; attach the self-audit (Section 11).

## 10. Required Structure of `3_outcome_and_verdict.md`
1. **Targets missed and unfixed items** (first; "None" only if literally true).
2. Gate A7 table with statuses and pasted evidence.
3. GMP backfill results: coverage before/after, accuracy check, remaining gaps and their `gmp_status`.
4. Data verification results (15 rows, random audit) and all corrections.
5. Re-evaluation on matched rows with bootstrap intervals; which Phase 6 conclusions survive.
6. Conformal coverage by regime (with n) and the verdict on the Phase 6 under-coverage.
7. Forward test status (n logged, n listed, HD Fire Protect outcome).
8. Honest verdict, labelled hypotheses, failure modes, practical-use guidance, Phase 8 recommendations.
9. Statement: decision aid only, not financial advice.

## 11. Self-Audit (yes/no with evidence)
- Does any status say `FIXED` without a pasted passing check?
- Is anything `PARTIAL` or `NOT FIXED`, and is it under "Targets missed"?
- Does every collected value have a real URL, page date and access date?
- Was any row removed or changed that is not in a corrections or exclusions file?
- Does every before/after table use identical rows on both sides?
- Does any "beats / wins / unbeatable / calibrated / significant" claim lack the required evidence?
- Is any explanation of *why* stated as fact instead of "Hypothesis (untested)"?
- Was any GMP value taken from listing day or later? (must be no)
- Was `data/ipo_phase5_final_test.csv` read for any decision? (must be no)
- Is any value estimated or imputed? (must be no)
- Does every number come from a committed script output?
