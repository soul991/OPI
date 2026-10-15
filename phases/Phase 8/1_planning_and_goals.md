# Phase 8: Planning & Goals - Verification Gate, Evidence Standard, Pipeline Refactor, Automated Forward Test & Dashboard

> Place at `phases/Phase 8/1_planning_and_goals.md`. Follow `RULES.md` and the new `PHASE_PROTOCOL.md`. This phase is **strict**. Phase 7 produced a large GMP backfill that cannot currently be trusted (see D-001, D-002 in `DEFECTS.md`). **No automation or dashboard work may start until Gate A8 (Section 1) passes.** If something cannot be done, mark it `NOT FIXED` and say why. Do not rename, reword, or work around it.

## 0. Rules (summary; full text in PHASE_PROTOCOL.md)
1. Three files in `phases/Phase 8/` (`1_planning_and_goals.md`, `2_building_and_execution.md`, `3_outcome_and_verdict.md`) plus `verify_start.txt`, `verify_end.txt`, `prior_phase_recheck.csv`.
2. Status words: `FIXED`, `PARTIAL`, `NOT FIXED` only. `FIXED` needs a passing regression test or command with pasted output.
3. Never fabricate or estimate data, URLs, dates, predictions, or metrics. Unverifiable = empty or `NOT_RECORDED`.
4. Evidence standard (Protocol Section 4): URL + page date + access date + **saved snapshot** for every collected value; independent second sources must differ by their measured amounts; the time-realism rule applies.
5. Do not edit `scripts/verify_all.py` to make a check pass. You may add checks.
6. Evidence-language rule (bootstrap interval excluding zero, else "no demonstrated difference"). Explanations are "Hypothesis (untested)".
7. No test-set tuning; never read `data/ipo_phase5_final_test.csv` for decisions.
8. Do not rewrite earlier phase files; add `## ERRATA (Phase 8)` at the top.
9. Relative links only. Secrets (API keys, tokens) never in the repo.
10. Commit per workstream. `phase8-gate-a` and `phase8-preregistration` must be committed before other work.
11. Decision aid only, not financial advice.

## 1. Gate A8 - Re-Verify Phase 7 and Clear Carried Defects (commit `phase8-gate-a`)

**Step 0.** Add `PHASE_PROTOCOL.md`, `DEFECTS.md` and `scripts/verify_all.py` to the repo; add "All phases must follow PHASE_PROTOCOL.md" to `RULES.md`. Run `python scripts/verify_all.py` and save the full output as `phases/Phase 8/verify_start.txt`. (Expected baseline: FAILs for the GMP second-source check, missing GMP snapshots, the HD Fire Protect forward row, Mukka's GMP value, and a missing test file for D-xxx items. Report anything else it finds as new defects D-015 onward.)

**Step 1.** Re-verify Phase 7 per Protocol Section 2 Step 1: re-run its scripts from a clean checkout; recompute 5 headline numbers; check 10 random claims in the Phase 7 verdict and record them in `prior_phase_recheck.csv` (claim, file, result, note).

Then fix the items below. Each needs: code or data change, regression test, `DEFECTS.md` update.

| # | Defect | Required fix | Done when |
|---|---|---|---|
| **U1** | **D-001 / D-002: GMP backfill unverified (Critical).** | For **every one of the 77** backfilled values: save a snapshot to `data/evidence/gmp/<listing_date>_<company-slug>.<ext>` (saved page or archived copy) showing the GMP value and the page's date/time. A value counts as supported only if the snapshot shows it within 3 percentage points of the recorded number **and** its date is on or before the last bidding day. Values without a supporting snapshot are reverted to `NOT_RECORDED` through `data_corrections.csv` (company, old, new, reason). Redo the second-source check: for a random 30 of the supported values (seed fixed) get the value from a **different publisher**, record both numbers and the **measured** difference (expect some spread), and report mean and maximum absolute difference. Replace the single `confidence=high` with an honest level (`high` = snapshot of a dated historical table; `medium` = dated article/post; `low` = unclear). Report coverage by quarter after the revert. If pages cannot be fetched or saved at all, revert all 77, mark U1 `NOT FIXED`, and continue. | `verify_all.py`: snapshot check PASS, second-source check PASS (non-zero measured differences), `gmp_status` consistent with the evidence folder. |
| **U2** | **D-003: Mukka Proteins GMP 321.43%.** | Verify against dated sources. Correct or set `NOT_RECORDED`. Then flag **every** row with `gmp_pct` above 150% or below -30% and verify each; record outcomes in `phases/Phase 8/gmp_outlier_review.csv`. | Test `test_gmp_outliers_verified` passes; review file lists every flagged row. |
| **U3** | **D-004: HD Fire Protect forward row used Day-1 subscription.** | Do not edit the old row. Set its status to `INVALID_NONFINAL_FEATURES` and explain in `notes`. If the system date is before the listing date (2026-10-21), re-score **only** with final subscription (after bidding closed) and final-day GMP, each with a URL and snapshot, using the same scoring function as the evaluation, and append a new `FORWARD` row. If bidding has not closed or the listing date has passed, do not score; say so. Record the prediction before listing; never backfill. | Test `test_forward_rows_scored_after_bidding_closed` passes; `verify_all.py` forward checks PASS. |
| **U4** | **D-005: record the HD Fire Protect outcome.** | After listing (2026-10-21 or later), run `scripts/update_actuals.py` and store a snapshot of the listing price from an exchange or equivalent source. State the result as a single data point with no performance claim. If not yet listed, mark `PARTIAL` and carry over. | Actual recorded with source, or carried over explicitly. |
| **U5** | **D-013: 15-row duplicate verification and 40-row random audit lack snapshots.** | Open 10 random rows from each file, save snapshots of the sources, and record match or mismatch in `prior_phase_recheck.csv`. If any mismatch occurs, re-verify the whole file and correct. | Snapshots saved; match rates reported. |
| **U6** | **D-011 / D-012.** | Report the actual share of "Industrial & Manufacturing" rows and the number of IPOs per year for 2010-2016 with a note on whether they are complete (compare against an exchange or Chittorgarh year list). Fix or document as `ACCEPTED`. | Tests pass; README updated. |
| **U7** | **D-009: wording.** | ERRATA on the Phase 7 verdict: "H1 rejected" becomes "no demonstrated effect (interval straddles zero)"; "proves" becomes "indicates" or states the specific evidence. | Erratum present. |
| **U8** | **Re-run the Phase 7 evaluation** after U1-U3 changes (same code and seeds). | Produce a matched-rows before/after table versus Phase 7 (same rows both sides; rows that changed GMP status listed separately) and update the README "What the evidence shows" section with the new numbers. | `verify_all.py` recompute check PASS; README matches. |
| **U9** | **D-014: independent verification.** | Make sure `verify_all.py` runs in CI (Workstream B) and that the regression test `test_verify_all_runs` exists. | Test passes. |

Gate exit: `verify_all.py` has 0 FAIL (every WARN explained in writing); `DEFECTS.md` updated; commit `phase8-gate-a`.

## 2. Objectives & Scope (after Gate A8)
1. **A. Pipeline refactor:** one tested package that both automation and the future chat interface will call.
2. **B. Automated daily forward test** (GitHub Actions) that logs predictions before listing and records actual results afterwards.
3. **C. Dashboard** that shows predicted vs actual and the health of the model and data.
4. **D. Retraining governance** (policy and a challenger-comparison script; no automatic promotion).

Out of scope: chat interface (Phase 9), new features, SME IPOs, tail-handling improvements (D-007, D-008, Phase 9).

## 3. Workstream A - Pipeline Refactor
- Create package `opi/` with: `collect.py` (fetch structured IPO details, save snapshots, return sourced values), `validate.py` (schema checks, leakage checks such as "GMP as of last bidding day", "subscription is final"), `score.py` (**the only scoring function**, used by evaluation, logging and dashboard), `log.py` (append-only forward log), `report.py` (metrics and charts).
- Existing scripts (`log_prediction.py`, `forward_report.py`, `update_actuals.py`, evaluation scripts) must call these modules; remove duplicated logic.
- **Model registry:** `model/registry.json` records `model_version` (hash of training data + code + parameters), training window, and creation date. Each FORWARD row stores its `model_version`. No silent retraining.
- Tests: unit tests with saved HTML fixtures for the parsers; a test that the logged probability equals the evaluation pipeline output for a fixed input; a leakage test.
- Entry point: `python -m opi.run_daily [--dry-run]`.

## 4. Workstream B - Automated Daily Forward Test
- **Runner:** `.github/workflows/daily.yml` (cron, twice daily, plus manual trigger) running `opi.run_daily`, tests, and `verify_all.py`. If you prefer Antigravity's automation feature, it must call the same entry point; the logic must not live only inside an app.
- **Run logic:**
  1. Discover mainboard IPOs that are open, or closed and not yet listed (exclude SME, FPOs, rights issues; same inclusion rule as the dataset).
  2. Score an IPO **only after bidding closes** (after 18:00 IST on the close date) using **final** subscription and final-day GMP, each with a URL and snapshot. Missing inputs: score only if the model supports missing values, else write a `SKIPPED_<reason>` line to `predictions/run_log.csv`. Never guess.
  3. Append a `FORWARD` row (append-only) with `scored_at`, `model_version`, features snapshot with sources, estimate, interval, probability, and which rule applies (GMP present or not).
  4. After listing, fetch the actual listing price with a snapshot, update actuals via the script, and append the row to `data/ipo_phase5_final_test.csv`.
  5. Commit through a bot with a clear message. Git history provides the timestamp proof.
- **Failure handling:** a failing source yields a `SKIPPED_` entry and a visible warning on the dashboard; never fill with defaults. Respect each site's terms and rate limits; prefer official exchange pages where possible.
- **Secrets:** tokens in repository secrets only.

## 5. Workstream C - Dashboard
- Generate a static site (`dashboard/`, published with GitHub Pages) from CSV files by `opi/report.py`. No hand-typed numbers.
- Content: (1) table of all FORWARD rows with status (pending, listed, skipped, invalid); (2) predicted vs actual scatter for listed FORWARD rows; (3) cumulative MAE of model vs mean baseline vs raw GMP; (4) interval coverage; (5) calibration table (shown only when n >= 30); (6) model version in use; (7) data and defect health: latest `verify_all.py` summary and counts of open defects; (8) a banner: "Provisional (n=...)" until 30 listed FORWARD rows exist; "Decision aid, not financial advice".
- No performance claim in the dashboard text below n = 30.

## 6. Workstream D - Retraining Governance
- Write `docs/retraining_policy.md`: retrain no more often than quarterly or after at least 30 new rows that passed the audit and evidence standard; challenger vs champion on the same rolling-origin split with a paired bootstrap; promote only if the challenger is not worse (interval does not exclude zero in the wrong direction) **and** calibration/coverage checks pass; every promotion gets a new `model_version` and a note in the dashboard.
- `scripts/retrain_challenger.py` produces the comparison report only; it never replaces the champion.
- Rows from the forward test join training only after they pass the audit (D-style evidence) and only for models with a new `model_version`.

## 7. Verification Commands
```bash
python scripts/verify_all.py | tee /tmp/verify.txt        # 0 FAIL required
python -m pytest -q
python -m opi.run_daily --dry-run                         # must not write to the log
grep -rn "file:///" phases README.md | grep -v "grep" || echo "OK no local links"
test -d data/evidence/gmp && ls data/evidence/gmp | wc -l
git log --reverse --format=%s | grep -n "phase8-"
```

## 8. Success Criteria (measured, not promised)
| Question | Metric | Rule |
|---|---|---|
| Gate A8 | U1-U9 statuses | Each `FIXED`, `PARTIAL`, `NOT FIXED` with pasted evidence |
| GMP data | Share of GMP values with a supporting snapshot | 100% of values kept as `OBSERVED`; others `NOT_RECORDED` |
| Second-source check | Measured differences (mean, max) | Reported as measured; zero spread is a failure |
| Phase 7 results after cleaning | Matched-rows before/after | Report which Phase 7 conclusions survive |
| Automation | Scheduled run executes; forward rows logged before listing | At least one real FORWARD row logged by the automation, or an honest "no IPO was open" |
| Dashboard | Generated from data only | Live on GitHub Pages; shows provisional banner below n = 30 |
| Defect register | `verify_all.py` 0 FAIL; ledger in verdict | Carried defects listed with status |

## 9. Task List (strict order)
1. Read `RULES.md`, `PHASE_PROTOCOL.md`, this file; confirm in `2_building_and_execution.md`.
2. Step 0: install the control files; save `verify_start.txt`; log new defects.
3. Gate A8: do U3 and U4 first (time-sensitive: the HD Fire Protect listing is 2026-10-21), then U1, U2, U5-U9; commit `phase8-gate-a`.
4. Commit `phases/Phase 8/preregistration.md` (timing rules, inputs required for scoring, metrics, dashboard content, promotion rule) as `phase8-preregistration`.
5. Workstream A, then B, then C, then D (commit each).
6. Run `verify_all.py` and pytest; save `verify_end.txt`.
7. Write `2_building_and_execution.md` and `3_outcome_and_verdict.md` (Section 10); update `DEFECTS.md`; attach the self-audit.

## 10. Required Structure of `3_outcome_and_verdict.md`
1. **Targets missed and unfixed items** ("None" only if `DEFECTS.md` has no OPEN or PARTIAL rows).
2. **Defect Ledger:** opened, fixed, carried over, regressed (IDs and statuses).
3. Gate A8 table with evidence; the Phase 7 re-check results (`prior_phase_recheck.csv` summary).
4. GMP evidence results: values supported vs reverted, coverage by quarter, second-source differences (mean, max).
5. Matched-rows re-evaluation and which Phase 7 conclusions survive.
6. Automation: what ran, what was logged, what was skipped and why; HD Fire Protect outcome.
7. Dashboard link and what it shows.
8. Honest verdict, hypotheses labelled, practical-use guidance, Phase 9 recommendations.
9. Statement: decision aid only, not financial advice.

## 11. Self-Audit (yes/no with evidence)
- Does any `FIXED` lack a passing test or pasted command?
- Is any collected value without URL, page date, access date and snapshot still marked `OBSERVED`?
- Does any second-source check show zero difference across many values?
- Does `verify_all.py` pass with 0 FAIL, and are all WARNs explained?
- Was any editing done to `verify_all.py` to make a check pass? (must be no)
- Was any FORWARD row scored before bidding closed or with non-final data? (must be no)
- Does every number in the verdict match a committed script output?
- Was `data/ipo_phase5_final_test.csv` read for any decision? (must be no)
