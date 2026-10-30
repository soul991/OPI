# Phase 15: Correct the Paras Outcome, Stop Wrong-Day Prices, Prove the Cloud Probe, Close the CI/Local Gap

> Follows `RULES.md` and `PHASE_PROTOCOL.md`. Research decision aid only, not financial advice.
> **STOP POINT:** after Gate A15 is committed and pushed, STOP and report. Do not start the workstreams until the user replies "continue".
> Use only FIXED / PARTIAL / NOT FIXED. FIXED needs a pasted passing check. Every number in a report comes from a committed script over `predictions/prediction_log.csv`, `predictions/outcome_corrections.csv` or `data/evidence/`. No hand-typed numbers.
> Goal: every recorded outcome comes from the listing-day session and nothing else; a wrong recorded outcome can be corrected without editing the log; and a script that passes local tests can no longer fail on the runner because of how it is launched.

## 0. Context (as of 2026-10-31, HEAD `890773b`)
- Phase 14 is merged (PR #5). Cloud runs are green, no open alert issues, 8 of 30 listed, `verify_all.py` 68 PASS / 0 FAIL, pytest 184 passed.
- **Defect A, wrong-day price.** `opi/actuals.py::fetch_yfinance_first_session_open` (lines about 508 to 509) uses the first bar in the history when no bar matches the listing date. For Paras Healthcare (listed 2026-10-28) Yahoo returned only two bars, both after the listing day (`source_probe.md`: "Earliest 2026-10-29 Open=721"; the saved evidence has two bars). The log holds actual gain 4.04% (open 721, the 2026-10-29 bar). Chittorgarh's quote page and a second listing page give 720 for 2026-10-28, which is +3.90% on the issue price 693. The 1.0% cross-check passed because the two prices are close, so it did not catch the wrong session. Jio (21.36%) is correct: the bar for 2026-10-28 exists.
- **Defect B, probe not from a runner.** D-068 was marked FIXED, but `phases/Phase 14/source_probe.md` says "Python 3.12.10 on win32" (the user's computer). A "Probe Outcome Sources" run exists on the runner (run `41038115389`, 2026-10-30 10:05 UTC) but its output was not committed. NSE and BSE returned 403 in the file that is committed, so runner reachability to the exchanges is still unmeasured.
- **Defect C, CI/local gap (third time: D-063, D-064, now).** Watchdog run `41090951686` (2026-10-30 16:33 UTC, issue #6) failed with `ModuleNotFoundError: No module named 'scripts'`: Phase 14 added `from scripts.manage_alerts import ...` to `scripts/watchdog.py`, which fails when the workflow runs `python scripts/watchdog.py`. Tests and `ci_local.py` never launched the script the way the workflow does. The alert worked and showed the real traceback (D-065 proved itself). Commit `9dd1b7d` fixed it and added `test_watchdog_script_standalone_execution`, but **no defect was registered for it**. The fix went straight to `main`.
- User action pending (not Antigravity's): `scripts/verify_all.py` line 202 still counts only OPEN and PARTIAL, so D-071 stays PARTIAL. The user will change the status tuple to include `"NOT FIXED"`. Do not edit that file.

## 1. Seed these defects in DEFECTS.md first
| ID | Sev | Description | Verification |
|---|---|---|---|
| D-072 | Medium | Tier 2 silently falls back to the first bar in the history when the listing-date bar is missing; Paras was recorded from the 2026-10-29 bar (721, +4.04%) instead of the 2026-10-28 listing price (720, +3.90%). | `fetch_yfinance_first_session_open` returns a `LISTING_DAY_BAR_MISSING` error and never another day's price; regression test built from the real two-bar Paras data in `data/evidence/actuals/2026-10-28_paras-healthcare-limited_*.txt` |
| D-073 | Medium | A recorded outcome can be wrong and the rules forbid editing the log; there is no audited way to correct it. | Append-only `predictions/outcome_corrections.csv` plus one function that gives every report the effective outcome; test that forward report, final evaluation and dashboard all show the corrected value and the log file is byte-identical |
| D-074 | Medium | D-068 was marked FIXED from a probe run on win32, not on a runner; runner reachability to NSE, BSE, yfinance and Chittorgarh has no committed evidence. | `phases/Phase 15/source_probe_runner.md` produced by the runner (environment line shows Linux and a run id); D-068 stays PARTIAL until then |
| D-075 | Medium | Watchdog failed on the runner (run 41090951686, issue #6) because `scripts/watchdog.py` imported `scripts.manage_alerts`; tests and `ci_local.py` did not launch scripts the way workflows do. Fixed in `9dd1b7d` without a register entry. | Entry-point smoke test (Workstream C); `tests/test_watchdog.py::test_watchdog_script_standalone_execution` |
| D-076 | Low | Process: fixes were pushed to `main` without a defect id, a branch or a PR. | Gate check that every commit since `phase14-gate-a` touching `scripts/`, `opi/` or `.github/` is covered by a register entry; `PHASE_PROTOCOL.md` line added |
Existing: D-026 stays NOT FIXED until a scheduled run handles a real new IPO. D-071 stays PARTIAL (user action). Mark D-075 FIXED only after Workstream C passes, not on the strength of the old commit alone.

## 2. Gate A15 - Re-verify Phase 14 (commit `phase15-gate-a`)
Step 0: install `requirements.lock` and pytest; `verify_all.py` -> `phases/Phase 15/verify_start.txt`; `verify_extra.py` (do not edit) -> `verify_extra_start.txt`; `ci_local.py`, paste its last line.
- **G1** Prior-phase recheck: 10 random claims from `phases/Phase 14/3_outcome_and_verdict.md` (seed 15) into `prior_phase_recheck.csv`, **at least 5 about a specific IPO number (at least 2 about Jio or Paras), and at least 3 of the form "file X contains Y"**. Recompute 5 headline numbers from raw files. For each of the two new outcomes, recompute the gain from the saved evidence and state which trading day each saved price belongs to.
- **G2** Confirm every FIXED row D-053 to D-070 has a passing named test. List each defect whose "FIXED" depends on a file that was produced off the runner (D-068 first).
- **G3** `gh run list` and `gh api repos/soul991/OPI/issues`: record the last 10 scheduled runs and the closed issue #6 with its run id in `actions_status.md`. List commits since `phase14-gate-a` and map each to a defect id (D-076).
- **G4** Print both Paras prices and dates side by side (saved Yahoo bars, Chittorgarh quote page) and show that the log value came from the 2026-10-29 bar.
- **G5** `gh secret list` shows `OPENROUTER_API_KEY`; `git grep sk-or-` prints nothing.
- Gate exit: `verify_all.py` 0 FAIL, `verify_extra.py` 0 FAIL, every WARN explained. Commit `phase15-gate-a`, push, then commit `phases/Phase 15/preregistration.md` (Section 6) as `phase15-preregistration`. **STOP and report.**

## 3. Workstream A - Never record another day's price (D-072)
- In `fetch_yfinance_first_session_open`: convert each bar's index to Asia/Kolkata, require the bar's date to equal the listing date, and return `(None, "LISTING_DAY_BAR_MISSING: first bar is <date>, listing date <date>", raw_bytes)` otherwise. Delete the first-row fallback. Keep saving the real response.
- The chain then logs `SKIPPED_NO_MATCH` or `PENDING_REVIEW` with that reason and alerts under the existing rules (D-067). Nothing is recorded.
- Tests: the real Paras two-bar data (now fails with the new reason); a bar with the right date (passes); timezone edge case: a bar stamped `18:30Z` the day before is the next IST day; Jio's saved data still passes.
- Check every other place that selects a price by "first" or "earliest" (`grep -rn "iloc\[0\]\|first" opi scripts`) and list the result.

## 4. Workstream B - Correct Paras without editing the log (D-073)
- **Preregistered amendment first** (`phases/Phase 15/preregistration_amendment.md`, original untouched): add a "Tier 2b" for the case where Yahoo lacks the listing-day bar. Tier 2b accepts a listing-day price only when **two independent pages fetched by code**, neither Yahoo, each stating the listing date and an opening or listing price, agree within 1.0%. Candidates the plan has seen: the Chittorgarh quote page and a second listing-price page (for example `gmpipowatch.in`). Each response is saved as raw evidence. Tier 2b rows are marked `outcome_source=tier2b` and reported with their own tier label. Anything else records nothing.
- `predictions/outcome_corrections.csv` (append-only; columns: `company, listing_date, field, old_value, new_value, reason, evidence_path, tier, corrected_at`). One function, for example `opi/outcomes.py::effective_outcome(row)`, applies the newest correction for a row; the log itself is never edited. `forward_report.py`, `final_evaluation.py`, the dashboard and `recompute_gate_a*.py` read outcomes only through it.
- Apply it to Paras: new price from Tier 2b (expected about 720 and +3.90%, but the numbers must come out of the code and saved evidence, never typed). Keep the old 4.04% visible in the corrections file and in the Phase 15 report.
- Report model and GMP errors for Paras before and after the correction, and the forward MAE before and after (script output only). No performance claims below n = 30.
- Tests: byte-identical log before and after; a second correction supersedes the first; reports agree with the effective value; correction rejected without evidence files.

## 5. Workstream C - Make the runner and the tests agree (D-074, D-075)
- **Runner probe.** Run `probe_sources.yml` (`gh workflow run`). Make it write `phases/Phase 15/source_probe_runner.md` from the runner with an environment line (OS, Python, `GITHUB_RUN_ID`) and either commit it with the bot pattern the daily job already uses or upload it as an artifact plus step summary that Antigravity copies in. Check first whether run `41038115389` kept any output (`gh run view 41038115389 --log`, if `gh` allows it). If the runner is also blocked by NSE and BSE, say so; do not hide it. D-068 becomes FIXED only with this file.
- **Entry-point smoke test.** `tests/test_workflow_entrypoints.py` parses every `.github/workflows/*.yml`, extracts each `python scripts/...` or `python -m ...` command, and runs the script with `--help` (or a documented dry-run flag) from the repository root **with `PYTHONPATH` unset unless the workflow sets it itself**. Fail if any exits non-zero. Add the same step to `scripts/ci_local.py` so it runs before every push. Prove it works: check out the pre-fix `scripts/watchdog.py` (commit before `9dd1b7d`) into a temp copy and show the smoke test failing on it.
- `PHASE_PROTOCOL.md`: add the rule "every fix gets a register entry before its commit, goes on a branch, and passes `ci_local.py`" (D-076).

## 6. Preregistration (committed before any correction is applied)
`phases/Phase 15/preregistration.md` fixes: the listing-day-only rule; what happens when the bar is missing (record nothing, alert); Tier 2b and its 1.0% two-page rule; that corrections are append-only and every report reads the effective value; that corrected and original values are both shown; that no performance claim is made below n = 30; that D-068 and D-075 are FIXED only with the runner file and the smoke test failing on the old code.

## 7. Success criteria (measured)
1. `verify_all.py`, `verify_extra.py`, `ci_local.py`: 0 FAIL on a fresh clone.
2. D-072 to D-076 FIXED with named tests, or PARTIAL / NOT FIXED with the reason.
3. Paras corrected through the corrections file with two saved independent pages; the log file is byte-identical.
4. Smoke test fails on the pre-fix watchdog and passes now.
5. Runner probe file committed, or D-068 PARTIAL with the reason.
6. D-026 NOT FIXED unless a scheduled run handled a new IPO; D-071 PARTIAL until the user edits `verify_all.py`.
7. No performance claims while n listed < 30.

## 8. Task list (strict order)
1. Install deps; `verify_all.py`, `verify_extra.py`, `ci_local.py` -> `*_start.txt`.
2. Seed D-072..D-076.
3. Gate A15 G1-G5; commit `phase15-gate-a`; commit preregistration (`phase15-preregistration`). **STOP and report.**
4. After "continue", on a branch: Workstream A; commit.
5. Workstream B (amendment first, then code, then the correction); commit.
6. Workstream C; commit; run `ci_local.py` before every push.
7. Open a pull request for the user to merge. After the merge, dispatch the daily and watchdog workflows on `main` and record the run ids.
8. `verify_all.py`, `verify_extra.py` -> `*_end.txt`; write `2_building_and_execution.md` and `3_outcome_and_verdict.md`.

## 9. Required structure of `3_outcome_and_verdict.md`
1. Targets missed and unfixed items (D-026, D-071, anything else). 2. Defect ledger. 3. Forward table from `forward_report.py --markdown` with the corrected Paras row and a tier column. 4. Gate A15 results with pasted outputs. 5. The Paras story: both bars, both pages, old and new gain, the code that allowed it. 6. Runner probe result. 7. Smoke test proof on old and new code. 8. Self-audit with pasted command output. 9. Handover state.

## 10. Self-audit (yes/no, with pasted evidence)
Did any report number come from anywhere but a script over the log, corrections or evidence? Did any summary line claim a file changed when `git diff --stat` shows otherwise? Was the log edited at all (`git diff` on `predictions/prediction_log.csv`)? Did any earlier-phase file change except by ERRATA? Was any outcome recorded without a saved real response? Does any FIXED row rely on a file produced off the runner? Did the work stop after the gate? Was the key kept out of the repo, logs, issues and snapshots?
