# Phase 12: Planning & Goals - Fix Phase 11's Report Errors, Evidence-Backed Market Data, Cloud Research Proof, Jio/Paras Results

> Follows `RULES.md` and `PHASE_PROTOCOL.md`. Research decision aid only, not financial advice.
> **STOP POINT:** after Gate A12 is committed and pushed, STOP and report. Do not start the workstreams until the user says continue. (Phase 11 ignored the equivalent stop.)
> Use only FIXED / PARTIAL / NOT FIXED. FIXED needs a pasted passing check. **Every number in any report must be produced by a committed script from `predictions/prediction_log.csv` or `data/evidence/`. No number may be typed by hand, including numbers inside "hypothesis" sentences.**

## 0. Context (as of 2026-10-24, HEAD `55d0002`)
- `verify_all.py`: 62 PASS / 0 FAIL. pytest: 129 passed, 1 skipped. No key material in the repo.
- Forward test: 8 genuine rows, 6 listed (model MAE 6.78 pp; GMP MAE 7.95 pp on 5). Jio Platforms and Paras Healthcare list 2026-10-28. n = 6 of 30: no performance claims.
- An independent script (`scripts/verify_extra.py`, supplied with this phase) finds problems that `verify_all.py` does not:
  - Phase 11 verdict, Workstream B table: Tonbo QIB "185.4x" (log: 293.56x), Zetwerk retail "11.8x" (log: 0.77x). Its self-audit says "no number typed by hand".
  - `forward_postmortem.md` line 37 says Bonfiglioli QIB "was only 3.4x" and builds a hypothesis on it; the log and the file's own table say 120.78x.
  - `scripts/forward_report.py` line 225 writes "BSE official opening trade (544994)" on every listed row; 544994 is HD Fire Protect's code, other rows were verified on NSE.
  - `scripts/forward_postmortem.py` lines 22-24 hard-code Nifty listing-day moves. There is no parsed Nifty evidence file for 2026-10-21, 22 or 23.
  - Champion interval coverage appears as 91.2% (README, D-008 text) and 87.94% (Phase 11 experiment) without a stated reason.
- Cloud workflow `daily.yml` has the OpenRouter step, but the user's GitHub secret `OPENROUTER_API_KEY` is not confirmed, so D-026 is NOT FIXED. Observed scheduled runs start 4 to 5 hours after the cron time (cron `0 6,14 * * *` UTC).
- GitHub Pages was enabled by the user on 2026-10-24 (branch `main`, `/ (root)`); no Pages build was visible in the Actions tab yet, and the live page has not been confirmed.

## 1. Seed these defects in DEFECTS.md first
| ID | Sev | Description | Verification |
|---|---|---|---|
| D-045 | High | Phase 11 verdict Workstream B table contains figures that contradict the prediction log; self-audit "no hand-typed numbers" is false. | `verify_extra.py` check 1 passes on Phase 11+ files after ERRATA + regenerated report |
| D-046 | High | `forward_postmortem.md` states Bonfiglioli QIB 3.4x (log 120.78x) and derives a hypothesis from it. | same check; `tests/test_postmortem.py::test_narrative_numbers_from_log` |
| D-047 | Medium | `forward_report.py` writes BSE code 544994 as evidence note for every listed IPO. | `verify_extra.py` check 2; test that each note's exchange matches the snapshot's source URL |
| D-048 | High | Listing-day Nifty moves hard-coded in `forward_postmortem.py`; no saved Nifty evidence for 2026-10-21/22/23. | `verify_extra.py` checks 3 and 4 |
| D-049 | Medium | Champion interval coverage 91.2% vs 87.94% not reconciled across README, DEFECTS D-008 and Phase 11 report. | README paragraph explaining the exact protocol difference, produced by a script that prints both |
| D-050 | Medium | Dashboard publishing unproven: Pages source was only just enabled (user, 2026-10-24); no confirmed build; `[skip ci]` bot commits may suppress rebuilds, leaving the live page stale. | `scripts/verify_pages.py` plus saved `pages_check.txt` (HTTP 200, fresh timestamp) |
| D-051 | Low | Scheduled runs start 4 to 5 hours late; no freshness monitoring. | `verify_all.py` or `verify_extra.py` warns if last scheduled run is older than 36 h |
| D-052 | Medium | Process: Phase 11 ran all workstreams without the requested stop after the gate. | Gate commit and later commits are separated by the user's "continue" (recorded in `results_log.md`) |
Existing: D-026 stays NOT FIXED until a green scheduled cloud run exists (see Workstream B).

## 2. Gate A12 - Re-verify Phase 11 (commit `phase12-gate-a`)
Step 0: install `requirements.txt` + pytest; run `scripts/verify_all.py` -> `verify_start.txt`; copy `verify_extra.py` into `scripts/` (do not edit it) and run it -> `verify_extra_start.txt`. Expected at start: 5 FAIL. Every FAIL is a defect above.
- **G1** Prior-phase recheck: 10 random claims from `phases/Phase 11/3_outcome_and_verdict.md` (seed 12) into `prior_phase_recheck.csv`, **including at least 5 claims containing a number about a specific IPO** (QIB/retail/Nifty/error). Recompute 5 headline numbers from raw files.
- **G2** Add `## ERRATA` (top of file, originals untouched) to `phases/Phase 11/3_outcome_and_verdict.md` and `phases/Phase 11/forward_postmortem.md` listing every wrong figure with the log value (D-045, D-046). Correct the self-audit answer on hand-typed numbers.
- **G3** Fix `forward_report.py` (D-047): note text built from the snapshot's real source (exchange + URL); regenerate the results table into `phases/Phase 12/` (not over Phase 11).
- **G4** Reconcile coverage numbers (D-049): script prints both protocols (what rows, what window, what calibration) and the README states the exact difference.
- **G5** Verify the GitHub secret exists: `gh secret list` should show `OPENROUTER_API_KEY` (never its value). If missing, mark D-026 "NOT FIXED (needs user action)" and skip Workstream B.
- **G6** Scheduled-run freshness (D-051): record the last 10 scheduled run start times vs cron time in `phases/Phase 12/actions_schedule_lag.md` from `gh run list`.
- Gate exit: `verify_all.py` 0 FAIL, `verify_extra.py` 0 FAIL for G-items done (D-048 may remain until Workstream A), every WARN explained. Commit `phase12-gate-a`, push, then commit `phases/Phase 12/preregistration.md` as `phase12-preregistration`. **STOP and report.**

## 3. Workstream A - Evidence-backed market data and a number-safe post-mortem (D-045, D-046, D-048)
- `opi/market.py`: fetch ^NSEI daily history (and India VIX) for a date range, save the **raw** response under `data/evidence/market/<date>_nifty.raw` with SHA-256 and a parsed `<date>_nifty.json` containing `nifty_close`, `nifty_prev_close`, `nifty_day_return_pct`, `source`, `accessed_at`. If the source is unreachable, store nothing and print `NOT_AVAILABLE`; never estimate.
- `scripts/forward_postmortem.py` rewritten: reads the log and market evidence only. Remove the constants dict. Any narrative sentence is a template filled with log/evidence values (e.g. "QIB {sub_qib}x"). Hypothesis sentences are allowed only from a fixed list of templates that cite computed values and carry the label "Hypothesis (untested)". Delete free-text explanations (for example any claim about Nifty intraday levels) unless backed by a saved evidence file.
- Output to `phases/Phase 12/forward_postmortem.md`. Add `tests/test_postmortem.py::test_narrative_numbers_from_log` (every `\d+(\.\d+)?x` and `%` in the file maps to a log/evidence value).
- Acceptance: `verify_extra.py` 0 FAIL.

## 4. Workstream B - Cloud research-agent proof (D-026), only if the secret exists
- The `daily.yml` research step runs on schedule with `OPENROUTER_API_KEY` from the secret. Models from `config/research_models.json`.
- Required evidence for FIXED: a green **scheduled** run (`event=schedule`) whose log shows provider, model id, request count, per-field grounding rate; a bot commit containing snapshots; no key in the log (`gh run view <id> --log | grep -c sk-or-` prints 0). Manual `workflow_dispatch` runs may be used to test but do not count.
- Record per source whether the GitHub runner could fetch it (`SKIPPED_BLOCKED_SOURCE`). A blocked source must never produce a guessed value.
- Compare the 3 configured models on the same IPOs: grounding rate and field differences vs `opi.ingest`; descriptive only.

## 5. Workstream C - Jio Platforms and Paras Healthcare results (after 2026-10-28)
- Record the official actual with `scripts/update_actuals.py` and saved exchange evidence only. Regenerate the forward table. Jio stays flagged LOW confidence (issue size above the training maximum) and is reported separately from the main forward statistics: show the headline MAE both with and without LOW-confidence rows.
- n listed becomes 8 of 30. Keep the "no performance claims below 30" notice.

## 6. Workstream D - Dashboard publishing (D-050) - Antigravity handles it end to end
The user already set GitHub Pages to deploy from branch `main`, folder `/ (root)` (2026-10-24). Expected URL: `https://soul991.github.io/OPI/dashboard/`. Antigravity must make this work and prove it, not assume it:
- **D1 Check state:** `gh api repos/soul991/OPI/pages` (expect HTTP 200 with `html_url`), and `gh run list --workflow "pages-build-deployment"` (or `gh api repos/soul991/OPI/actions/runs` filtered by name `pages build and deployment`). Save the output.
- **D2 If no Pages build has run:** make one legitimate commit on `main` without `[skip ci]` (for example regenerating the dashboard or adding the dashboard URL to the README) and re-check. Do not use an empty or fake commit.
- **D3 Live check:** `curl -sS -o dashboard_check.html -w "%{http_code}" https://soul991.github.io/OPI/dashboard/` returns 200, and the page contains the latest `scored_at` or run timestamp from `predictions/prediction_log.csv`. Save the check output under `phases/Phase 12/pages_check.txt` with the time of the check.
- **D4 `[skip ci]` risk (test, do not assume):** the daily bot commits use `[skip ci]`, which may also suppress the Pages build. After the next scheduled run that changes `dashboard/index.html`, compare the commit time with the latest `pages build and deployment` run and with the timestamp shown on the live page. If the live page is stale, fix it by (a) removing `[skip ci]` from the commit that updates the dashboard, taking care that this does not cause a workflow loop (the daily workflow must ignore pushes made by the bot, for example with `paths-ignore` or an actor check), or (b) replacing the branch deploy with a Pages deployment step in `daily.yml` (`actions/configure-pages`, `actions/upload-pages-artifact`, `actions/deploy-pages`, with `pages: write` and `id-token: write` permissions). Choose one, document the reason, and re-test. If (b) is chosen and the repo Pages source must be switched to "GitHub Actions", tell the user exactly which setting to change and stop on that item (NOT FIXED, needs user action) rather than guessing.
- **D5 Staleness guard:** add to `verify_extra.py`'s companion file `scripts/verify_pages.py` (a new file; do not edit `verify_extra.py`) a check that fetches the live dashboard and fails or warns if its latest timestamp is more than 36 hours older than the last scheduled run. If the sandbox cannot reach the site, print `NOT_CHECKED` and never `PASS`.
- **D6 Content:** the dashboard shows predicted vs actual per IPO, a LOW-confidence marker, running MAE (model vs GMP, with n and "provisional"), and the date of the last cloud run. Add the live URL to the README.
- Acceptance: D-050 FIXED only with saved HTTP 200 output plus a live page showing a timestamp no older than the last dashboard commit by more than the Pages build time; otherwise PARTIAL or NOT FIXED with the reason.

## 7. Success criteria (measured)
1. `verify_all.py` and `verify_extra.py`: 0 FAIL on a fresh clone, with pytest output pasted.
2. D-045, D-046, D-047, D-048, D-049 FIXED with tests; `git grep -n "544994"` shows it only for HD Fire.
3. D-026 FIXED only with a green scheduled cloud run; otherwise NOT FIXED (needs user action).
4. Jio and Paras outcomes recorded from exchange evidence; headline MAE shown with and without LOW-confidence rows.
5. No performance claims while n listed < 30.

## 8. Task list (strict order)
1. Install deps; `verify_all.py` -> `verify_start.txt`; add `verify_extra.py`; run -> `verify_extra_start.txt`.
2. Seed D-045..D-052.
3. Gate A12 G1-G6; commit `phase12-gate-a`; push; commit preregistration (`phase12-preregistration`). **STOP and report.**
4. After the user says continue: Workstream A; commit.
5. Workstream B if the secret exists; commit.
6. Workstream D (Pages: check, fix, prove, guard); commit.
7. After 2026-10-28 listings: Workstream C; commit.
8. `verify_all.py` and `verify_extra.py` -> `verify_end.txt`; write `2_building_and_execution.md`, `3_outcome_and_verdict.md`.

## 9. Required structure of `3_outcome_and_verdict.md`
1. Targets missed and unfixed items. 2. Defect ledger (opened, fixed, carried). 3. Forward table generated by `forward_report.py --markdown`. 4. Gate A12 results with pasted outputs, including the verify_extra start/end diff. 5. Workstream results, before/after on the same rows. 6. Wording check ("beats/proves" only with an interval excluding zero; explanations labelled Hypothesis (untested) and generated from templates). 7. Self-audit with commands whose output is pasted (for "typed by hand": the `verify_extra.py` pass).

## 10. Self-audit (yes/no, with pasted evidence)
Did any report number come from anywhere other than a script over the log/evidence? Did any earlier-phase file change except by ERRATA? Did any value enter a feature without a snapshot? Did the work stop after the gate? Was the key kept out of the repo, logs and snapshots?
