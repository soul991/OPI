# Phase 14: Automatic Listing-Outcome Recording in the Cloud, and an Alert When It Does Not Happen

> Follows `RULES.md` and `PHASE_PROTOCOL.md`. Research decision aid only, not financial advice.
> **STOP POINT:** after Gate A14 is committed and pushed, STOP and report. Do not start the workstreams until the user replies "continue".
> Use only FIXED / PARTIAL / NOT FIXED. FIXED needs a pasted passing check. Every number in a report comes from a committed script over `predictions/prediction_log.csv` or `data/evidence/`. No hand-typed numbers.
> Goal: after a listing date passes, the scheduled GitHub Actions run records the listing outcome by itself from evidence it saved, or opens an alert issue within 2 days saying exactly why it could not. No step depends on the user's computer.

## 0. Context (as of 2026-10-29, HEAD `bbd5218`)
- Phase 13 is merged (PRs #2 and #4). `verify_all.py` 66 PASS / 0 FAIL, pytest 171 passed / 1 skipped on `main`. The last 10 cloud runs are green and issues #1 to #4 are closed.
- **The gap this phase closes.** Jio Platforms and Paras Healthcare listed on 2026-10-28. Both daily runs after that (run ids `40684222624`, and the 2026-10-28 19:17 UTC run) finished green and logged `ACTUALS ... SKIPPED_BLOCKED_SOURCE "Official exchange snapshot required"`. Reading `opi/run_daily.py` lines 155 to 180: **the job never attempts a fetch.** It logs "blocked" for every listed-but-unrecorded row and prints "use scripts/update_actuals.py". So the label is wrong (nothing was blocked, nothing was tried), the outcome stays empty, the dashboard stays at 6 of 30, and no alert fires.
- `opi/actuals.py` already has `record_actual_from_exchange` (fetches an NSE or BSE HTTPS page, validates redirects, finds the opening price, writes the actual through `update_actual_outcome`) and `record_actual_from_evidence_file` (saved page from a browser). Neither is called by the daily job.
- Open question that must be measured, not assumed: **can a GitHub-hosted runner fetch NSE and BSE pages at all?** Exchange sites often block cloud IP ranges and need cookies or JavaScript. The sandbox the user's assistant works in cannot reach them, which says nothing about GitHub runners. Phase 14 starts by probing from a real runner.
- Decided and recorded: **Zerodha Kite Connect is not used.** Its free tier has no market data, its paid tier needs a manual login with 2FA every day, and scripting that login is not allowed. It cannot run unattended in GitHub Actions.
- Sanity expectation only (press reports, not evidence; never type them into any file): Jio listed at about ₹1,358 against ₹1,119, Paras at about ₹720 against ₹693. If the pipeline output is far from these, investigate before recording.

## 1. Seed these defects in DEFECTS.md first
| ID | Sev | Description | Verification |
|---|---|---|---|
| D-066 | Medium | `opi/run_daily.py` logs `SKIPPED_BLOCKED_SOURCE` for listed IPOs without attempting any fetch. Jio and Paras stayed unrecorded after 2026-10-28 with green runs. | Daily job calls the outcome recorder for every due row and logs the real result (`RECORDED`, `SKIPPED_FETCH_FAILED`, `SKIPPED_NO_MATCH`, `PENDING_REVIEW`); `tests/test_actuals_job.py` |
| D-067 | Medium | No alert when a listed row has an empty outcome for more than 2 days. The Phase 13 data-source policy ("a run that skipped what it needed must not be silently green") is not enforced for outcomes. | Watchdog check (d) and a run-end check open an issue naming the rows; unit tests for the 2-day threshold |
| D-068 | Medium | There is no outcome source the cloud is known to reach. Exchange access from a runner has never been measured. | `source_probe.md` from a real runner; a documented source chain with a preregistered acceptance rule (Workstream A and B) |
| D-069 | Low | The job compares only dates, so on the listing date itself it cannot tell whether the market has opened. | Rule: attempt when `listing_date < today (IST)`, or when it is the listing date and IST time is after 16:00; tested with a fixed clock |
| D-070 | Low | The dashboard shows "N of 30" but not how many listed rows still lack an outcome, so a stuck row is invisible. | Dashboard shows "listed, outcome pending: K" with the company names; `tests/test_dashboard.py` |
Existing: D-026 stays NOT FIXED until a green **scheduled** run handles a real new IPO. Carry D-045 as it stands.

## 2. Gate A14 - Re-verify Phase 13 (commit `phase14-gate-a`)
Step 0: install `requirements.lock` and pytest; run `verify_all.py` -> `phases/Phase 14/verify_start.txt`; run `scripts/verify_extra.py` (do not edit it) -> `verify_extra_start.txt`; run `scripts/ci_local.py` and paste `CI_LOCAL: PASS/FAIL`.
- **G1** Prior-phase recheck: 10 random claims from `phases/Phase 13/3_outcome_and_verdict.md` (seed 14) into `prior_phase_recheck.csv`, **at least 5 about a specific IPO number and at least 3 of the form "file X contains Y"**. Recompute 5 headline numbers from raw files.
- **G2** Confirm D-053 to D-065 statuses in `DEFECTS.md` each have a named passing test; list any FIXED row whose test does not exist or fails.
- **G3** `gh run list` and `gh api repos/soul991/OPI/issues`: last 10 scheduled runs green, no open alert issues. Record in `phases/Phase 14/actions_status.md` (no stored dates used as a fallback, per D-064).
- **G4** Confirm the dashboard row count and the log agree (8 forward rows, 6 with outcomes) and list the two pending rows.
- **G5** `gh secret list` shows `OPENROUTER_API_KEY`; `git grep sk-or-` prints nothing.
- Gate exit: `verify_all.py` 0 FAIL, `verify_extra.py` 0 FAIL, every WARN explained. Commit `phase14-gate-a`, push, then commit `phases/Phase 14/preregistration.md` (Section 6) as `phase14-preregistration`. **STOP and report.**

## 3. Workstream A - Measure what a runner can reach (D-068)
- Add `.github/workflows/probe_sources.yml` (`workflow_dispatch` only, `permissions: contents: read`, pinned runner and actions as in D-062). A script `scripts/probe_sources.py` makes one request per target and writes `phases/Phase 14/source_probe.md`: HTTP status, content length, whether a price is parseable, elapsed time. Targets, for Jio and Paras: the NSE quote and corporate pages, the BSE equity page, the BSE announcements API the existing code uses (if any), `yfinance` history for `<symbol>.NS` and `<symbol>.BO`, and the Chittorgarh listing page.
- Resolve each company's NSE and BSE symbol from a page the code fetches and cite the URL; never type a symbol by hand.
- Run it with `gh workflow run`, wait, copy the output into the phase folder. The result decides the chain in Workstream B. If every target fails, say so, mark D-068 NOT FIXED and stop on that item; do not invent a source.

## 4. Workstream B - Record outcomes automatically (D-066, D-069)
- **Source chain** (first success wins, every step saves the real response next to a parsed `.json`, the lesson of D-055):
  1. **Tier 1, official:** the existing `record_actual_from_exchange` against NSE or BSE.
  2. **Tier 2, cloud-reachable:** the first-session **open** of `<symbol>.NS` from `yfinance` for the listing date (and `.BO` when the IPO lists only on BSE), saved as the raw response. Accept it only if a second, independent source (a page parsed by code, for example the Chittorgarh listing section or an exchange announcement) gives a listing price within 1.0% of it. Both values and both URLs go into the evidence file.
  3. If Tier 2 has no second source, or the two differ by more than 1.0%: write status `PENDING_REVIEW`, record nothing, alert (Workstream C).
- Use the same exchange the six existing rows used for the listing price; read this from the committed evidence, record it in the preregistration, do not guess.
- Gain is computed by the existing function from the issue price in the logged row. Never overwrite an existing outcome; never edit other columns of logged rows. The notes field gets `outcome_source=tier1|tier2` and the evidence path.
- `run_daily.py` step 2: for each due row (rule D-069) call the chain; log `RECORDED`, `SKIPPED_FETCH_FAILED`, `SKIPPED_NO_MATCH` or `PENDING_REVIEW` with the reason. Delete the `SKIPPED_BLOCKED_SOURCE` path for this case. The bot commit includes the new evidence files.
- Tests with mocked HTTP and synthetic fixtures under `tests/fixtures` (labelled synthetic, never in `data/`): Tier 1 success, Tier 2 success with agreeing second source, Tier 2 disagreement, no second source, listing-day-before-close, row already recorded, redirect to a non-exchange host.
- **Jio and Paras:** the first live use. Dispatch the daily workflow on `main` after the merge, confirm both rows get an outcome from the chain, then regenerate the tables and dashboard. Report headline MAE for model vs GMP with and without the LOW-confidence Jio row. If the chain cannot record them, keep them pending, say why, and mark the item NOT FIXED. Do not paste numbers from news sites into any file.

## 5. Workstream C - Alert when outcomes are missing (D-067, D-070)
- Extend `scripts/watchdog.py` with check (d): any FORWARD row with `listing_date` more than 2 days ago and an empty `actual_gain_pct` fails the watchdog and the alert names each company and the last logged reason. Also run the same check at the end of the daily job so the alert comes the same day.
- Dashboard: add "listed, outcome pending: K" with names (D-070).
- Tests: threshold boundary (exactly 2 days passes, 3 days fails), recorded rows ignored, alert text contains the company name and no key material.

## 6. Preregistration (committed before any outcome is recorded by the new code)
`phases/Phase 14/preregistration.md` fixes: the source chain and order; the 1.0% agreement rule; which exchange's price is the listing price (taken from the committed evidence of earlier rows); that a failed or disputed fetch records nothing; that Tier 2 rows are marked in notes and counted in the final evaluation exactly like Tier 1 rows but reported with a tier column; that no performance claim is made below n = 30 listed.

## 7. Runbook (D-070 doc part)
Update `docs/RUNBOOK.md`: what `PENDING_REVIEW` means and the manual path (`scripts/update_actuals.py` with a saved exchange page), the 2-day outcome alert, why Kite is not used. The existing test that checks required headings must still pass.

## 8. Success criteria (measured)
1. `verify_all.py`, `verify_extra.py`, `ci_local.py`: 0 FAIL on a fresh clone.
2. D-066 to D-070 FIXED with named tests, or PARTIAL / NOT FIXED with the reason.
3. `source_probe.md` exists from a real runner run.
4. Jio and Paras recorded from the chain with evidence files, or kept pending with the reason and an open alert.
5. A forced "row older than 2 days with no outcome" fixture opens an alert in test.
6. D-026 stays NOT FIXED unless a scheduled run handles a new IPO.
7. No performance claims while n listed < 30.

## 9. Task list (strict order)
1. Install deps; `verify_all.py`; `verify_extra.py`; `ci_local.py` -> `*_start.txt`.
2. Seed D-066..D-070.
3. Gate A14 G1-G5; commit `phase14-gate-a`; commit preregistration (`phase14-preregistration`). **STOP and report.**
4. After "continue": Workstream A (probe) on a branch; run it; commit its result.
5. Workstream B; commit. Run `ci_local.py` before every push.
6. Workstream C; commit.
7. Runbook update; commit.
8. Open a pull request; after the user merges, dispatch the daily workflow on `main`, record Jio and Paras, regenerate tables and dashboard; commit.
9. `verify_all.py`, `verify_extra.py` -> `*_end.txt`; write `2_building_and_execution.md` and `3_outcome_and_verdict.md`.

## 10. Required structure of `3_outcome_and_verdict.md`
1. Targets missed and unfixed items. 2. Defect ledger (opened, fixed, carried). 3. Forward table from `forward_report.py --markdown`. 4. Gate A14 results with pasted outputs. 5. Probe result and the chain actually used, with run ids. 6. Jio and Paras outcomes with evidence paths, MAE with and without the LOW row, and the wording check (no claims below n = 30). 7. Self-audit with pasted command output. 8. Handover state: what now runs by itself, what alerts exist.

## 11. Self-audit (yes/no, with pasted evidence)
Did any report number come from anywhere but a script over the log or evidence? Did any summary line claim a file changed when `git diff --stat` shows otherwise? Did any earlier-phase file change except by ERRATA? Was any outcome recorded without a saved real response? Did the work stop after the gate? Was the key kept out of the repo, logs, issues and snapshots?
