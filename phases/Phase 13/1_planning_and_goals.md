# Phase 13 (Final Build Phase): Close Open Defects, Harden the Automation, Hand Over to Maintenance Mode

> Follows `RULES.md` and `PHASE_PROTOCOL.md`. Research decision aid only, not financial advice.
> **STOP POINT:** after Gate A13 is committed and pushed, STOP and report. Do not start the workstreams until the user replies "continue".
> Use only FIXED / PARTIAL / NOT FIXED. FIXED needs a pasted passing check. Every number in a report comes from a committed script over `predictions/prediction_log.csv` or `data/evidence/`. No hand-typed numbers.
> Goal of this phase: after it, the system runs on GitHub's cloud with no help from the user's computer, tells the user when it breaks, and needs only a short monthly check.

## 0. Context (as of 2026-10-24, HEAD `605e827`)
- `verify_all.py`: 64 PASS / 0 FAIL. Cloud daily workflow works (scheduled runs green since #11), Pages dashboard is live at `https://soul991.github.io/OPI/dashboard/`, OpenRouter secret is set. Forward test: 8 genuine rows, 6 listed (model MAE 6.78 pp, GMP MAE 7.95 pp on 5). Jio Platforms (LOW confidence) and Paras Healthcare list 2026-10-28.
- User's modified `verify_extra.py` (v2, errata-aware) replaces the earlier copy in `scripts/`. Do not edit it. On the current repo it reports 2 FAIL, both from `phases/Phase 11/forward_postmortem.md`, which has **no ERRATA block** although the Phase 12 report says it was added (D-046 cannot be closed until it is).
- User verified on 2026-10-24 that yfinance returns the same Nifty values as `data/evidence/market/2026-10-21/22/23_nifty.json`. The data is correct; the `.raw` files are the program's parsed output, not the API response.
- Known leftovers: macro snapshot `2026-10-23_market_macro` holds 2026-10-22 values (close 22,687.65, VIX 15.76); Jio and Paras were scored with it. Dashboard "open/partial defects" shows 1, the register has 2. Observed scheduled-run lag about 4.7 h.

## 1. Seed these defects in DEFECTS.md first
| ID | Sev | Description | Verification |
|---|---|---|---|
| D-053 | Medium | `phases/Phase 11/forward_postmortem.md` has no ERRATA block (Phase 12 report claims it does); wrong Bonfiglioli "QIB 3.4x" statement stands uncorrected. | `verify_extra.py` 0 FAIL; `tests/test_reporting.py::test_phase11_postmortem_has_errata` |
| D-054 | Low | Macro snapshot labelled 2026-10-23 contains 2026-10-22 values; Jio and Paras rows used it (nifty_30d_return -3.24, VIX 15.76). | Annotation file `data/corrections/macro_2026-10-23.md` (no edit of logged rows) listing the true Oct 23 values from the market evidence; test that the daily job labels snapshots with the data's own date |
| D-055 | Low | `data/evidence/market/*_nifty.raw` is parsed output, not the original response; hash claims overstate. | Either save the real response (`.raw`) next to the parsed `.json`, or rename and document; test |
| D-056 | Low | Dashboard defect counter is stale (1 vs 2) and does not show the last cloud run date. | Dashboard generator reads `DEFECTS.md` and the latest run time; `tests/test_dashboard.py` |
| D-057 | Medium | No alert when a scheduled run fails (runs #9/#10 were found only by manual inspection). | Failing run opens a GitHub issue (see Workstream A); tested with a forced failure on a branch or `workflow_dispatch` input |
| D-058 | Medium | Schedule risks: runs start about 4.7 h late; GitHub may pause schedules after 60 days without repo activity. | Keepalive + freshness watchdog (Workstream A) |
| D-059 | Medium | Dependencies are not pinned; yfinance is unofficial and pandas 3.x already broke a script once (D-021). | `requirements.lock` (or pinned versions) + weekly canary run; test that CI installs from it |
| D-060 | Medium | The n = 30 evaluation is not preregistered or automated; risk of ad-hoc claims later. | `scripts/final_evaluation.py` + `preregistration_final_eval.md` committed before n reaches 30 |
| D-061 | Low | No runbook for the user (rotate key, rerun, read alerts, what each file is). | `docs/RUNBOOK.md` exists and is checked by a test for required sections |
Existing: D-026 stays NOT FIXED until a green **scheduled** run extracts inputs for a new IPO; D-045 stays PARTIAL until D-053 is done.

## 2. Gate A13 - Re-verify Phase 12 (commit `phase13-gate-a`)
Step 0: install `requirements.txt` + pytest; run `verify_all.py` -> `verify_start.txt`; ensure `scripts/verify_extra.py` is the user's v2 and run it -> `verify_extra_start.txt`.
- **G1** Prior-phase recheck: 10 random claims from `phases/Phase 12/3_outcome_and_verdict.md` (seed 13) into `prior_phase_recheck.csv`, **at least 5 about a specific IPO number and at least 3 of the form "file X contains Y"** (the Phase 12 summary claimed an ERRATA in a file that has none). Recompute 5 headline numbers from raw files.
- **G2** Add the missing `## ERRATA` block at the top of `phases/Phase 11/forward_postmortem.md` naming the wrong figure (Bonfiglioli QIB 3.4x vs log 120.78x) and the invalid "subdued demand" reasoning (D-053). Originals stay.
- **G3** D-054 annotation file; do not edit logged rows. D-055 decision recorded.
- **G4** Regenerate the dashboard so the defect counter equals the register (D-056) and shows the last cloud run time.
- **G5** Check `gh secret list` shows `OPENROUTER_API_KEY`; check the last 10 scheduled runs are green; record in `phases/Phase 13/actions_status.md`.
- Gate exit: `verify_all.py` 0 FAIL, `verify_extra.py` 0 FAIL, every WARN explained. Commit `phase13-gate-a`, push, then commit `phases/Phase 13/preregistration.md` as `phase13-preregistration`. **STOP and report.**

## 3. Workstream A - Make the automation self-monitoring (D-057, D-058, D-059)
- **Failure alert:** at the end of `daily.yml` add a job `if: failure()` that opens (or comments on) a GitHub issue titled `Daily run failed: <run id>` with the failed step name and a link. GitHub emails the repo owner for issues, so no secrets or third-party service are needed. Deduplicate: one open issue per failure streak; close it automatically on the next green scheduled run.
- **Watchdog:** a second scheduled workflow `watchdog.yml` (runs once a day at a different hour) that fails and opens an issue if (a) the last successful scheduled `daily.yml` run is older than 36 h, or (b) the live dashboard timestamp is older than 36 h (use `scripts/verify_pages.py`, `NOT_CHECKED` is never PASS), or (c) the OpenRouter free model list has none of the models in `config/research_models.json`.
- **Keepalive:** to avoid GitHub pausing schedules after 60 days of repo inactivity, the watchdog makes one small commit (a timestamp line in `predictions/heartbeat.txt`, no secrets) at most once every 30 days when there has been no other commit. Make sure it cannot trigger a loop.
- **Pin dependencies (D-059):** create `requirements.lock` with exact versions that pass the current test suite; workflows install from it. Add a weekly `canary.yml` that installs the **unpinned** requirements in a fresh environment, runs pytest and opens an issue on failure, so breakage by new library versions is noticed before it hits the daily job.
- **Data-source failure policy:** if a source is blocked, empty or changed, the job logs `SKIPPED_<reason>` per IPO, never guesses a value, never marks the run green silently: a run that skipped everything it needed to process opens the same alert issue with the skip reasons.
- Tests: forced-failure test (use `workflow_dispatch` with an input `force_fail=true` that is ignored on schedule) opens an issue and the next green run closes it; watchdog thresholds unit-tested; no secret in any issue text.

## 4. Workstream B - Automate outcome recording and the live research proof (D-026)
- **Outcomes:** the daily job, after each listing date, runs `scripts/update_actuals.py` against the official exchange pages (with saved snapshots) for every FORWARD row whose listing date has passed and whose actual is empty. If the runner cannot fetch the exchange page, write `SKIPPED_BLOCKED_SOURCE` and alert (above); do not fill from other sources without a snapshot. The user can still run the manual path (documented in the runbook).
- **Jio and Paras (2026-10-28):** ensure they are recorded by this automation or, if blocked, by the manual path with exchange evidence. Report headline MAE both with and without LOW-confidence rows.
- **D-026 proof:** FIXED only when a green **scheduled** run (`event=schedule`) shows provider, model id, request count and grounding rate for a newly discovered IPO, with the bot commit containing snapshots, and `gh run view <id> --log | grep -c sk-or-` printing 0. Until a new IPO appears, keep NOT FIXED and say so. Never create a fake IPO.
- **Model list upkeep:** the agent refreshes the free model list on each run and writes the model actually used into the run log; if all configured models fail, alert and fall back to the built-in `opi.ingest` path only for fields it can ground.

## 5. Workstream C - Preregister and automate the n = 30 evaluation (D-060)
- Commit `phases/Phase 13/preregistration_final_eval.md` **before** n listed reaches 30. It fixes: the population (genuine FORWARD rows only), the primary metrics (MAE model vs MAE GMP on rows with GMP; MAE model vs historical-mean baseline; interval coverage with Wilson CI; direction accuracy), the statistics (paired bootstrap, seed 42, 2,000 resamples), the wording rules (no "beats" unless the interval excludes zero), how LOW-confidence rows are handled (reported separately and with them excluded), and what happens if n < 30 (no claims).
- `scripts/final_evaluation.py`: reads the log, prints `NOT_READY (n=<k> of 30)` below 30, and when n >= 30 writes `phases/Final Evaluation/report.md` and updates the dashboard banner from "provisional" to "evaluated" only if the script says so. The daily job runs it; it never edits the preregistration.
- Tests with synthetic fixtures (clearly labelled, kept under `tests/fixtures`, never in `data/`).

## 6. Workstream D - Runbook and handover (D-061)
`docs/RUNBOOK.md` (short, plain language) must contain: what the system does; the three places to look (Actions tab, the dashboard, DEFECTS.md); what each alert issue means and the first thing to do; how to rotate the OpenRouter key (GitHub secret, no code change); how to re-run a failed day manually; how to add or change a free model in `config/research_models.json`; how to read the final evaluation; what to do each month (a 10-minute checklist: dashboard fresh, issues empty, defect counter, last scheduled run, secret present, any new IPO skipped); and what the system must never be used for (investment advice). A test checks the required headings exist. Link it from the README.

## 7. Workstream E - Monthly retraining governance check (existing)
Verify `monthly_retrain.yml` still opens a pull request (never auto-promotes), runs from `requirements.lock`, writes its comparison with same-row before/after, and that the champion `v4.0.0-champion` and its replay are untouched. Record the last run status in `phases/Phase 13/actions_status.md`.

## 8. Success criteria (measured)
1. `verify_all.py` and `verify_extra.py`: 0 FAIL on a fresh clone, pytest pasted.
2. D-053 to D-061 each FIXED with a named test, or PARTIAL / NOT FIXED with the reason.
3. A forced failure opens an issue and the next green run closes it (evidence: issue and run links).
4. Watchdog runs on schedule and is green; `verify_pages.py` prints PASS (not NOT_CHECKED) in CI.
5. Jio and Paras actuals recorded from exchange evidence; table generated by script.
6. D-026 FIXED only with the scheduled-run evidence above.
7. No performance claims while n listed < 30.

## 9. Task list (strict order)
1. Install deps; `verify_all.py` -> `verify_start.txt`; user's `verify_extra.py` v2 -> `verify_extra_start.txt`.
2. Seed D-053..D-061.
3. Gate A13 G1-G5; commit `phase13-gate-a`; push; commit preregistration (`phase13-preregistration`). **STOP and report.**
4. After "continue": Workstream A; commit.
5. Workstream B; commit (the Oct 28 listings may need to wait; if so commit the code first, results later).
6. Workstream C; commit.
7. Workstream D; commit.
8. Workstream E check; commit.
9. After 2026-10-28 record Jio and Paras; regenerate tables; commit.
10. `verify_all.py` and `verify_extra.py` -> `verify_end.txt`; write `2_building_and_execution.md`, `3_outcome_and_verdict.md`.

## 10. Required structure of `3_outcome_and_verdict.md`
1. Targets missed and unfixed items. 2. Defect ledger (opened, fixed, carried). 3. Forward table generated by `forward_report.py --markdown`. 4. Gate A13 results with pasted outputs and the verify_extra start/end diff. 5. Workstream results with links to the evidence (issue numbers, run ids). 6. Wording check. 7. Self-audit with commands whose output is pasted. 8. "Handover state": the list of everything that now runs by itself, what alerts exist, and the monthly checklist.

## 11. Self-audit (yes/no, with pasted evidence)
Did any report number come from anywhere but a script over the log/evidence? Did any claim in the summary say a file was changed when it was not (check each by `git diff --stat`)? Did any earlier-phase file change except by ERRATA? Did any value enter a feature without a snapshot? Did the work stop after the gate? Was the key kept out of the repo, logs, issues and snapshots?

## 12. After this phase
No new phase is needed unless an alert or the n = 30 evaluation demands one. Any new defect gets a row in `DEFECTS.md` and is handled by a short maintenance phase that starts with `verify_all.py` and `verify_extra.py`.
