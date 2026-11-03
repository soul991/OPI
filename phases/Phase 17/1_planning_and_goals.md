# Phase 17: Close the Phase 16 Gaps (Market Evidence, Visible Verification, Honest Statuses, Named Failures)

> Follows `RULES.md` and `PHASE_PROTOCOL.md`. Research decision aid only, not financial advice.
> **STOP POINT:** after Gate A17 is committed and pushed, STOP and report. Do not start the workstreams until the user replies "continue".
> Use only FIXED / PARTIAL / NOT FIXED. FIXED needs a pasted passing check. Every number in a report comes from a committed script over `predictions/prediction_log.csv`, `predictions/outcome_corrections.csv` or `data/evidence/`. No hand-typed numbers.
> Goal: a listing never leaves a verification check failing without anyone being told; every status in the register and every number a report quotes matches the files it points to; and an alert names the step that failed.

## 0. Context (as of 2026-11-04, `main` after PR #10)
- Phase 16 is merged. On `main`: `verify_all.py` 77 PASS / 0 FAIL, `ci_local.py` PASS (219 tests), no open issues or PRs, scheduled daily and watchdog runs green since 2026-11-02 14:52 UTC. 9 of 30 listed (EAAA India Alternatives recorded +0.63% on 2026-11-03 from the listing-day bar, cross-checked against Chittorgarh). BLS Polymers and SFC Environmental listed 2026-11-03 and have no outcome yet (Yahoo returned no history for `BLSPOLY.NS` and `545009.BO`; the chain retries each run). M.K.Sons lists 2026-11-04, Bombay Coated 2026-11-05 (scored before listing).
- **`verify_extra.py` FAILS on `main`:** `each listed date has a parsed Nifty evidence file ... missing: 2026-11-02`. `opi/market.py` can write `data/evidence/market/<date>_nifty.{raw,json}` but nothing in the daily job calls it for a new listing date, and `verify_extra.py` is not run by `daily.yml`, `watchdog.yml` or `ci_local.py`, so the failure was silent. 2026-11-03 will be missing too.
- **Run failures on 2026-11-02:** (1) daily run `41463708776` failed at the step "Run Test Suite" because a 7-space-indented line was committed to `scripts/verify_all.py` (an IndentationError); PR #10 replaced it. The alert issue (#11) said only "Workflow step returned non-zero exit code" and named the step as "Execution". (2) Monthly retraining dispatch `41453047131` on the Phase 16 branch failed at the step **"Open Pull Request with Challenger Comparison"**. No later run exists. The likely cause is the repository setting that stops Actions from creating pull requests; only the user can check it.
- **Report vs file mismatches in Phase 16:** `phases/Phase 16/2_building_and_execution.md` says `verify_start.txt` is "71 pass, 0 warn, 0 fail"; the committed `verify_start.txt` ends "SUMMARY: 71 pass, 1 warn, 3 fail". `3_outcome_and_verdict.md` says "Targets Missed: None" while D-083 lacks cloud proof and `verify_extra` fails. D-083 is marked FIXED. D-071 is still PARTIAL although `scripts/verify_all.py` now counts `NOT FIXED`.
- The pre-listing table (`predictions/pre_listing_predictions.md` and the dashboard) prints the bidding window as "2026-10-30 to 2026-10-30": the close date appears twice.
- Do not edit `scripts/verify_all.py`, `scripts/verify_extra.py` or `scripts/verify_pages.py`.

## 1. Seed these defects in DEFECTS.md first
| ID | Sev | Description | Verification |
|---|---|---|---|
| D-085 | Medium | No Nifty market evidence is saved for new listing dates; `verify_extra.py` fails on `main` for 2026-11-02 (and will for 2026-11-03). | Daily job saves real `<date>_nifty.{raw,json}` for every listed date that lacks one, from the saved yfinance response; `tests/test_market_evidence_job.py`; `verify_extra.py` 0 FAIL after a cloud run |
| D-086 | Medium | `verify_extra.py` is not run by any workflow or by `ci_local.py`, so its failures are invisible. | Watchdog runs it daily and opens an alert on a non-zero exit; `ci_local.py` runs it and prints its summary; the daily job is **not** blocked by it (data collection must continue); tests |
| D-087 | Medium | D-083 (monthly retraining opens a PR) is marked FIXED but its only cloud run failed at the PR step and needs a repository setting. | Status PARTIAL until a green monthly run on `main` opens a PR; workflow detects the permission failure and opens an alert issue that names the exact setting; test |
| D-088 | Low | Phase 16 reports quote verification results that differ from the committed output files, and "Targets Missed: None" contradicts open items. | ERRATA blocks at the top of `phases/Phase 16/2_building_and_execution.md` and `3_outcome_and_verdict.md`; `tests/test_reporting.py` compares every "N pass, N warn, N fail" quoted beside a `verify_*.txt` name with that file's SUMMARY line, for Phases 14 to 17 |
| D-089 | Low | D-071 is stale: `verify_all.py` counts NOT FIXED now, the register still says PARTIAL. | Test reads `scripts/verify_all.py` and the dashboard code and asserts both count OPEN, PARTIAL and NOT FIXED; then mark FIXED |
| D-090 | Low | Pre-listing table shows the close date twice as the bidding window. | Fixture row with open date different from close date; test asserts both dates appear |
| D-091 | Low | Daily failure alerts name the step "Execution" with a generic reason (issue #11), so the cause needs the run log. | Daily alert step receives the name and outcome of each earlier step and the tail of its output (same `--reason-file` pattern as the watchdog); no key material; test |
Existing: D-026 stays NOT FIXED until a green **scheduled** run uses the agent for a new IPO. D-013 stays PARTIAL.

## 2. Gate A17 - Re-verify Phase 16 (commit `phase17-gate-a`)
Step 0: install `requirements.lock` and pytest; `verify_all.py` -> `phases/Phase 17/verify_start.txt`; `verify_extra.py` -> `verify_extra_start.txt` (expect 1 FAIL; do not hide it); `ci_local.py`, paste its last line.
- **G1** Prior-phase recheck: 10 random claims from `phases/Phase 16/3_outcome_and_verdict.md` (seed 17) into `prior_phase_recheck.csv`, **at least 5 about a specific IPO number (include Bombay Coated and EAAA), at least 3 of the form "file X contains Y", and at least 2 quoting a verify or pytest result against the output file it names**. Recompute 5 headline numbers from raw files.
- **G2** Confirm every FIXED row D-071 to D-084 has a passing named test; list any that depends on something not proven in the cloud (D-083 first).
- **G3** Record in `actions_status.md`: last 10 scheduled runs, issue #11 and its run id, the failed monthly run id and failing step. No stored dates as fallback.
- **G4** Outcome status table for the five pending rows (BLS Polymers, SFC Environmental, M.K.Sons, Bombay Coated, and any new one): listing date, last `ACTUALS` run-log line, days since listing. Script output only.
- **G5** `gh secret list` shows `OPENROUTER_API_KEY`; `git grep sk-or-` prints nothing.
- Gate exit: `verify_all.py` 0 FAIL; `verify_extra.py` result reported as it is; every WARN explained. Commit `phase17-gate-a`, push, then commit `phases/Phase 17/preregistration.md` (Section 6) as `phase17-preregistration`. **STOP and report.**

## 3. Workstream A - Market evidence for every listing (D-085, D-086)
- After an outcome is recorded (and also for any listed date still lacking a file), the daily job calls `opi/market.py` for that date, saves the raw response and parsed `.json` under `data/evidence/market/`, and logs `MARKET_EVIDENCE RECORDED` or `SKIPPED_<reason>`. Use the dates from the log only; never type a date. If the data is not yet available, skip and retry next run; never guess a value.
- Do not create 2026-11-02 or 2026-11-03 evidence by hand or from this computer. After the PR is merged, dispatch the daily workflow on `main` so the cloud writes them; then show `verify_extra.py` at 0 FAIL.
- Watchdog check (e): run `scripts/verify_extra.py`; non-zero exit opens or comments on one alert issue naming each failing check line. Add the same run to `scripts/ci_local.py` as a printed result (not a blocker for local pushes if the only failure is a date whose evidence the cloud has not written yet; say so in the output).
- Tests: job writes evidence for a missing date (mocked response), skips on failure, never overwrites an existing file; watchdog alert text lists the failing check.

## 4. Workstream B - Monthly retraining proof (D-087)
- Make `monthly_retrain.yml` check that it can create a pull request before it tries (for example by catching the `gh pr create` error). On that error it opens an alert issue whose text names the setting: `Settings -> Actions -> General -> Workflow permissions -> Allow GitHub Actions to create and approve pull requests`.
- Do not touch the champion. Set D-083 to PARTIAL in the register. FIXED only when a monthly run on `main` (dispatch or schedule) is green and a pull request exists; paste the run id and PR number.
- If the user has not changed the setting by the end of the phase, leave D-087 NOT FIXED (needs user action) and say so; do not work around it with a personal access token.

## 5. Workstream C - Reports that match their files (D-088, D-089, D-090)
- ERRATA blocks at the top of the two Phase 16 files (originals stay below), quoting the real `verify_start.txt` SUMMARY line and listing the open items.
- The report-vs-file consistency test (D-088 row). It must fail on the pre-ERRATA Phase 16 text (show it failing on commit `d814892`, then passing).
- D-089 test, then mark D-071 FIXED. D-090 fix in the code that builds the pre-listing table and the dashboard section.

## 6. Workstream D - Alerts that name the failure (D-091)
- Give each daily step an id; the alert step receives each step's outcome and the last 40 lines of the failed step's output saved to a file; the issue states `Failed step: <name>` and the reason (sanitised: no key material, no raw tokens). Reuse `--reason-file`.
- Prove it with a forced failure via the existing `force_fail` input, then confirm the issue closes on the next green scheduled run. Use `workflow_dispatch` on a branch.

## 7. Preregistration (committed before any workstream)
`phases/Phase 17/preregistration.md` fixes: the market-evidence rule (real response saved, never typed, never overwritten, skip when unavailable); that `verify_extra` failures alert but never block data collection; that D-087 is FIXED only with a green monthly run and a PR; that report numbers quoted beside an output file must equal that file; and that no performance claim is made below n = 30.

## 8. Success criteria (measured)
1. `verify_all.py` 0 FAIL; `verify_extra.py` 0 FAIL after the post-merge cloud run; `ci_local.py` PASS.
2. D-085 to D-091 FIXED with named tests, or PARTIAL / NOT FIXED with the reason (D-087 may be NOT FIXED (needs user action)).
3. Cloud run ids showing the two missing Nifty files created by the job.
4. A forced daily failure opens an issue that names the step; the next green run closes it.
5. The consistency test fails on `d814892` and passes now.
6. D-026 NOT FIXED unless a scheduled run handled a new IPO. No performance claims while n listed < 30.

## 9. Task list (strict order)
1. Install deps; `verify_all.py`, `verify_extra.py`, `ci_local.py` -> `*_start.txt`.
2. Seed D-085..D-091.
3. Gate A17 G1-G5; commit `phase17-gate-a`; commit preregistration (`phase17-preregistration`). **STOP and report.**
4. After "continue", on a branch: Workstream A; commit.
5. Workstream B; commit. Workstream C; commit. Workstream D; commit. Run `ci_local.py` before every push.
6. Open a pull request for the user to merge. After the merge: dispatch the daily workflow on `main`, record run ids, show `verify_extra.py` at 0 FAIL. If the user has changed the PR setting, dispatch the monthly workflow and record the PR.
7. Record any BLS, SFC, M.K.Sons or Bombay outcomes that the cloud has written by then; do not record any by hand.
8. `verify_all.py`, `verify_extra.py` -> `*_end.txt`; write `2_building_and_execution.md` and `3_outcome_and_verdict.md`. **Every verify or pytest result quoted in those files must be copied from the `*_end.txt` files by a script, not typed.**

## 10. Required structure of `3_outcome_and_verdict.md`
1. Targets missed and unfixed items (D-026, D-087 if open, D-013). 2. Defect ledger. 3. Forward table from `forward_report.py --markdown` with a tier column. 4. Gate A17 results with pasted outputs. 5. The two cloud failures of 2026-11-02 and how each is now handled. 6. Market evidence run ids. 7. Consistency-test proof on old and new text. 8. Self-audit with pasted output. 9. Handover state.

## 11. Self-audit (yes/no, with pasted evidence)
Did any report number come from anywhere but a script over the log, corrections or evidence? Does every quoted verify or pytest result equal its output file? Was any evidence file written by hand or from this computer? Did `verify_extra.py` or `verify_all.py` change? Did any earlier-phase file change except by ERRATA? Does any FIXED row rely on something not proven in the cloud? Did the work stop after the gate? Was the key kept out of the repo, logs, issues and snapshots?
