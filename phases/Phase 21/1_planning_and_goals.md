# >>> READ THIS FIRST (USER AND ANTIGRAVITY) <<<

## SECRETS (the user fills in the PAT only, saves, and gives this file to Antigravity)

> The file may live anywhere, including the repo folder. Antigravity masks the real values (replaces them with `xxx`) as its very first action, before any `git add` or commit.

```
GITHUB_PAT=xxx
TELEGRAM_BOT_TOKEN=xxx
```

- `GITHUB_PAT`: fine-grained PAT for `soul991/OPI` with all repository permissions (read and write). The user pastes it after `=`.
- `TELEGRAM_BOT_TOKEN`: the user's existing bot token, copied from a screenshot by Claude. Some characters (`I` vs `l`, `1`) may be misread. **Pre-flight must validate it with `getMe`.** If it fails, stop and tell the user to paste the exact token here. Do not guess variants.
- Not secret: bot ID `9196287140`, chat ID `2006803662`, repo `soul991/OPI`.

## Secret handling rules (Antigravity: follow first, before anything else)
1. Read `GITHUB_PAT` and `TELEGRAM_BOT_TOKEN` from the block above into environment variables for this terminal session only.
2. **Immediately mask this file:** replace both real values with `xxx` (`GITHUB_PAT=xxx`, `TELEGRAM_BOT_TOKEN=xxx`). Do this before any `git add`, commit, or push. Confirm with a search that neither real value appears anywhere in the file.
3. Never print a secret, put one on a command line, or write one to a repo file, log, PR, issue, commit message, or chat reply. Pass values to `gh secret set` through stdin.
4. Before every commit, scan the staged diff for the PAT and the bot token (compare by hash or pattern; never print them). If found, abort the commit and mask them first.
5. This file is the Phase 21 planning file (`1_planning_and_goals.md`, per `RULES.md`). Once masked, it may be saved as `phases/Phase 21/1_planning_and_goals.md`. Create `2_building_and_execution.md` and `3_outcome_and_verdict.md` in the same folder as the phase proceeds.
6. Use the tokens only for this task.

---

# OPI Phase 21: Telegram Alert System (Zoho Catalyst trigger + GitHub Actions compute)

> Follows `RULES.md` and `PHASE_PROTOCOL.md`. Decision aid, not financial advice.
> Written from a read of `soul991/OPI` at commit `2ed6aae` (2026-11-12). Claude read the repo but did **not** run tests or `verify_all.py`. Everything under "Candidate faults" is unverified until Gate A confirms it.

---

## 0. Where the project stands (read from the repo)

- Phases 1 to 20 are complete. Phase 20 verdict: **ACCEPT**. The system is an autonomous GitHub Actions autopilot: `daily.yml`, `watchdog.yml`, `canary.yml`, `probe_sources.yml`, `monthly_retrain.yml`. Live dashboard: https://soul991.github.io/OPI/dashboard/
- Champion model: `v4.0.0-champion`. Shadow model `v4.2.0-202611` registered. Monthly retraining and promotion rules are automated.
- Forward test: **12 of 30** listed (provisional). Forward MAE 5.67 pp, per `scripts/forward_mae.py`. No performance claims below n = 30.
- Defects: 112 tracked. Open or partial: **D-013** (PARTIAL), **D-026** (NOT FIXED, research agent live-web proof / `OPENROUTER_API_KEY`), **D-096** (PARTIAL, Tier 2b fallback). Next free defect ID: **D-113**.
- Existing alerting: GitHub issues via `scripts/manage_alerts.py`, plus dashboard banners. There is **no phone notification yet**.
- Last commits are daily bot runs (2026-11-12). The pipeline currently finds no active IPOs (all discovered ones are `SKIPPED_ALREADY_LISTED`).

### Facts that shape this phase
1. **GitHub Actions cron lags about 4 to 5 hours** (`phases/Phase 12/actions_schedule_lag.md`, mean 4.66 h). A "12 PM" alert cannot rely on a GitHub `schedule`. This is why the precise trigger comes from Catalyst Cron.
2. The model's inputs include `sub_qib`, `sub_nii`, `sub_retail`, `sub_total` and `gmp_pct`. The champion was trained on **final** subscription figures. A 12 PM alert on the close date sees **live** subscription. So the 12 PM alert is **PREVIEW**, not FORWARD.
3. `opi/validate.py::determine_prediction_mode` already defines PREVIEW (scored before 18:00 IST on the close date, or live data): "cannot be logged as FORWARD". The 12 PM alert must obey this. It must **never** write to `predictions/prediction_log.csv`.
4. Retail bidding closes about 5 PM on the close date. The existing 19:30 IST FORWARD run is **too late to apply**. The PREVIEW alert is the only actionable one.
5. README says raw GMP beat the model in the 321 IPOs that had GMP (8.86% MAE vs the model with GMP), and no advantage was demonstrated for the blend. Alerts must show **GMP and the model side by side** and must not present the model as the better signal.

### Telegram (already set up by the user)
- Bot ID `9196287140`. User chat ID `2006803662` (private chat).
- The bot token is the user's existing one (the user chose to keep it). It must **never** be in the repo, logs, issues, commits, or chat.
- Secrets: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` live in **GitHub Actions secrets** (the sender runs there) **and** in **Catalyst environment variables** (Catalyst sends a fallback alert if a trigger fails). A GitHub token for dispatch, `GITHUB_DISPATCH_TOKEN` (the user's single `GITHUB_PAT`) lives only in Catalyst env vars.

---

## 1. Non-negotiable rules
1. Follow `PHASE_PROTOCOL.md` exactly: `verify_start.txt` first, Gate A, then preregistration, then workstreams, then exit.
2. **No retraining, no model promotion, no change to model artifacts, `data/ipo_*.csv`, or `model/`.** The champion and shadow stay as they are.
3. Feature code goes on a **branch**, passes `python scripts/ci_local.py` (`CI_LOCAL: PASS`), and is merged by PR. Bots may direct-push **data files only**, in the same way `daily.yml` does today.
4. The Apply/Skip rule and every threshold must be **preregistered before building** (Section 3). No threshold may be tuned after seeing outcomes.
5. Never write PREVIEW rows to `prediction_log.csv`. Never present a PREVIEW as a FORWARD prediction.
6. No secret in any file, log, commit, or issue. Never print a token.
7. Do not edit `scripts/verify_all.py` to make a check pass. You may add checks.
8. Wording: use "no demonstrated difference" unless a paired bootstrap 95% interval excludes zero. Label untested explanations "Hypothesis (untested)". Show `n listed = X of 30` in every prediction alert until n >= 30.

---

## 2. Gate A: re-verify Phase 20 and fix faults (do this first)
Per `PHASE_PROTOCOL.md` Step 0 and Step 1.

1. Run `python scripts/verify_all.py` and save the complete output as `phases/Phase 21/verify_start.txt`. Any FAIL, or any WARN that is not already a defect, becomes a new defect (D-113 onward, status OPEN) **before** fixing.
2. Re-run Phase 20's main scripts from a clean checkout and compare with committed artifacts. Run `python -m pytest -q` and `python scripts/ci_local.py`.
3. Recompute at least 5 Phase 20 headline numbers from raw files: forward n (12 listed), forward model MAE (5.6675 pp via `scripts/forward_mae.py`), logged and FORWARD row counts in `predictions/prediction_log.csv`, defect totals in `DEFECTS.md` (112 tracked, 2 open or partial, 1 not fixed), and champion hash vs `model/registry.json`.
4. Check 10 random claims in `phases/Phase 20/3_outcome_and_verdict.md` against the files. Record claim, file, and result in `phases/Phase 21/prior_phase_recheck.csv`.
5. Confirm the live dashboard still returns HTTP 200 (`scripts/verify_pages.py`) and that the last 5 bot runs of `daily.yml` and `watchdog.yml` were successful.
6. Check the open defects: **D-026** (does the `OPENROUTER_API_KEY` secret exist, and has the research agent ever run live?), **D-096**, **D-013**. Fix what can be fixed with a regression test. For anything needing the user (secrets), list the exact manual step.

### Candidate faults seen while reading (verify each; open a defect if confirmed)
- **A. Docs disagree with the workflows.** `docs/AUTOPILOT.md` says the daily pipeline runs at 12:45 UTC and the watchdog at 21:30 UTC. `daily.yml` is `0 6,14 * * *` UTC and `watchdog.yml` is `0 10 * * *` UTC. Check `docs/RUNBOOK.md` too.
- **B. README Section 4 (Forward Test Status) looks stale.** It says 6 forward predictions logged and 1 listed, while the Phase 20 verdict says 12 listed of 30 and the log has 13 FORWARD rows. The text on Fusion CX "due to be compared after 2026-10-22" is also outdated. Phase 20 mentions `scripts/forward_mae.py` as the source of numbers, so the README should be generated from it or point to it.
- **C. Phase 20 verdict inconsistencies.** The first table lists Paras Healthcare at +4.04% while the errata table says +3.90%. Bombay Coated shows `SKIPPED_NO_MATCH (first bar is 2026-11-06)` with the outcome pending. Check what the log and `predictions/outcome_corrections.csv` say now, and whether Bombay Coated is resolved. The first table's original values are covered by an errata section: confirm it is correct and not duplicated.
- **D. Rule text vs. scheduling.** Any doc or test that assumes the 11:30 IST run happens at 11:30 IST is wrong given the measured 4 to 5 hour lag. Note it in the runbook.
- **E. `scripts/` contains many one-off phase scripts** (`recompute_gate_a12.py` to `a17.py`, `score_oct19_ipos.py`, etc.). Not a defect by itself; do not delete, since rules say earlier phases are immutable. Just do not add Phase 21 code there. New code goes in `opi/` and `.github/workflows/`.

Gate exit: `verify_all.py` has 0 FAIL, every WARN explained in writing, and commit `phase21-gate-a`. **Stop and report to the user if Critical or High defects remain that you cannot fix.**

---

## 3. Preregistration (commit `phases/Phase 21/preregistration.md` as `phase21-preregistration` before building)

Must fix these in writing:

1. **Alert triggers and exact times (IST).** Proposed:
   - `announce`: Catalyst Cron at 09:00 and 20:00 IST daily.
   - `preview`: Catalyst Cron at 11:45 IST on every day. The job acts only on IPOs with `close_date == today` and status `BIDDING_OPEN`.
   - `listing`: Catalyst Cron at 11:30 and 16:30 IST. The job acts only on IPOs whose listing date is today (or earlier and still without a sent listing alert) and whose outcome is **verified** in the repo.
   Antigravity must measure how quickly `workflow_dispatch` actually starts and finishes (5 test dispatches), and adjust the times if the measured latency makes them unrealistic. Record the measurements.
2. **Idempotency key:** `(company, close_date, alert_type)`. A repeated trigger must never send twice.
3. **Apply/Skip rule for the preview alert.** The user wants an Apply or Skip suggestion. Preregister one rule before building, for example: *Apply* if the raw GMP quote is observed and `GMP% >= T1`; if no GMP, use the model estimate with `T2`; otherwise *No suggestion (insufficient data)*. Thresholds `T1` and `T2` and the tie-break rule go in the file. Propose defaults and **ask the user to approve them** (the user decides the gain level at which they want to apply). Because the champion was trained on final subscription, the preview model number is labelled "PREVIEW (live subscription, model trained on final figures)".
4. **What is shown, always:** company, close and listing dates, issue price, lot size, live subscription (QIB, NII, retail, total) with its timestamp, GMP with its source and date or "no GMP recorded", model estimate and calibrated P(gain > 10%) if the score module provides it, the suggestion, the `n listed = X of 30` banner, and the disclaimer line.
5. **Listing alert content:** actual opening gain % (**verified outcome only**, from the existing evidence chain), issue price, listing open price, lot size, **profit or loss per lot = (listing open - issue price) x lot size**, the earlier model and GMP estimates, and the preview estimate if one was sent. Sent for every listed IPO regardless of whether the user applied. If the outcome is still pending verification, **do not send a number**. Send nothing (or one "listed, awaiting verified price" message, decided now in preregistration) and let the existing watchdog handle overdue cases.
6. **Dropped:** the allotment alert. Registrars have no public API, so no allotment status is fetched. Record this as a decision, not a defect.
7. **Success criteria:** see Section 8.

---

## 4. Architecture

```
Catalyst Cron (precise IST times)
   -> Catalyst Function: POST https://api.github.com/repos/soul991/OPI/actions/workflows/notify.yml/dispatches
        (input: stage = announce | preview | listing, token = GITHUB_DISPATCH_TOKEN)
   -> if dispatch fails: Catalyst sends a Telegram "trigger failed" message itself

GitHub Actions: .github/workflows/notify.yml (workflow_dispatch only)
   -> python -m opi.notify_run --stage <stage>
        discover_ipos() / existing ingest + score (PREVIEW) / existing outcomes (verified)
        -> opi/notify.py  send_telegram()  (token from env, never logged)
        -> state: predictions/alerts_sent.csv, predictions/preview_log.csv (bot direct-push, data files only)
```

Why this shape: it reuses the 7,000 lines and the model already verified in Actions, instead of porting them to Catalyst. Catalyst contributes only what GitHub cannot do reliably: precise timing. Alternatives (the whole model on Catalyst AppSail) are **out of scope**. If Antigravity finds a blocking problem with this design (for example `workflow_dispatch` also lagging badly), stop and report with measurements before changing the design.

---

## 5. Workstreams (one commit each, on branches, PR + `ci_local.py` PASS)

### WS-A: `opi/notify.py` (Telegram sender)
- `send_telegram(text)`: POST `https://api.telegram.org/bot<TOKEN>/sendMessage` with `chat_id`, `text`. Timeout 10 s, 3 retries with backoff, handle non-200 and `ok:false`, split text over 4096 chars, never log or print the token, never include it in exceptions.
- Reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`; clear error if missing; supports `--dry-run` that prints the message and sends nothing.
- Tests (`tests/test_notify.py`): mocked HTTP for success, retry, and failure; token never appears in logs or exceptions; message splitting; dry-run sends nothing.
- Acceptance: a test message "OPI alerts online" reaches the user's Telegram (manual `workflow_dispatch` once).

### WS-B: Alert state and idempotency
- `predictions/alerts_sent.csv` with columns: `sent_at_ist, company, close_date, listing_date, alert_type, stage, message_digest, run_id`.
- Dedupe helper: `already_sent(company, close_date, alert_type)`. Written **after** a successful send, in a way that survives a crash between sending and writing (state in the preregistration: at-most-once vs at-least-once, with reasoning).
- Add checks to `scripts/verify_all.py` (add only): `alerts_sent.csv` has no duplicate keys, all rows have a valid type, and **no preview or alert row is present in `prediction_log.csv`**.
- Git concurrency: the existing `daily.yml` direct-pushes too. Use a shared `concurrency` group for all workflows that write to `predictions/`, and `git pull --rebase` with retry before push. Test with two simultaneous dispatches.

### WS-C: Stage `announce`
- Use `opi.discover.discover_ipos()`. Statuses in code: `UPCOMING`, `BIDDING_OPEN`, `CLOSED_UNLISTED`, `LISTED`, `UNKNOWN_LISTING_DATE`.
- Send once per IPO when first seen with a mainboard flag, a known open or close date, and a listing date (or "listing date TBD" if preregistered). Skip SME issues and anything `SKIPPED_ALREADY_LISTED`.
- Tests with `tests/fixtures/discovery_page.html` and new fixtures: first sight sends, second does not, SME ignored, missing dates handled.

### WS-D: Stage `preview` (the 12 PM alert)
- For each candidate with `status == BIDDING_OPEN` and `close_date == today (IST)`: ingest live details via the existing `opi.ingest`, then `opi.score` in PREVIEW mode (confirm with `determine_prediction_mode`).
- Write the full feature snapshot to **`predictions/preview_log.csv`** (new file, never `prediction_log.csv`), with an immutable timestamp and the data source URLs. Keep evidence snapshots under `data/evidence/` the same way as other collected data (source URL, page date, access date, saved copy). A value with no snapshot is `NOT_RECORDED` and shown as such.
- Compute the Apply/Skip suggestion by the preregistered rule only.
- If critical inputs are missing (no live subscription, or no price band), send an honest "insufficient data, no suggestion" alert, not a guess.
- Later (at FORWARD scoring and listing), the existing pipeline will have the final prediction and actual. Add a read-only report script `scripts/preview_vs_forward.py` that compares preview estimate vs final FORWARD estimate vs actual. It informs a future decision on retraining with a day-3 snapshot. **No model change in this phase.**
- Tests: PREVIEW never writes to `prediction_log.csv`; correct behaviour on close date vs other days; rule boundaries (exactly at threshold); missing GMP; missing subscription.

### WS-E: Stage `listing`
- For IPOs with listing date today (or earlier and unsent): read the **verified** outcome via the existing chain (`opi/actuals.py::execute_two_tier_outcome_chain` and the logs under `predictions/` and `data/evidence/actuals/`). Do not add a new price scraper.
- Message per Section 3 item 5, including profit or loss per lot. Send once, only on a verified outcome (Tier 1, 2 or 2b as recorded).
- Tests: verified outcome sends; pending outcome does not send a price; per-lot arithmetic (e.g. HD Fire Protect: issue 271, listing 334.40, lot size from the log, gain +23.39%); duplicate suppressed.

### WS-F: `.github/workflows/notify.yml`
- `workflow_dispatch` only, with input `stage` (choices: announce, preview, listing) and `dry_run`.
- Same Python version and `requirements.lock` install as `daily.yml`; same shared concurrency group as other writers; permissions `contents: write` only.
- Run `pytest -q` and `scripts/verify_all.py` after the stage; commit only `predictions/alerts_sent.csv`, `predictions/preview_log.csv`, and new `data/evidence/` files.
- On failure: use the existing `scripts/manage_alerts.py` flow (GitHub issue) **and** send a Telegram "OPI notify failed at <step>" using the sender (secrets only, no log content that may contain secrets).
- Confirm secrets exist: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (and `OPENROUTER_API_KEY` for D-026). If a secret is missing, stop and list the exact manual step for the user.

### WS-G: Catalyst project (Catalyst access is available to you)
- Folder `catalyst/` in the repo (code only, no secrets). One Python function `opi_trigger` with Cron jobs matching the preregistered times.
- The function calls the GitHub dispatch endpoint with `GITHUB_DISPATCH_TOKEN`, checks for HTTP 204, retries twice, and on final failure sends a Telegram message directly ("trigger failed: <stage>, HTTP <code>"). No token in logs.
- Catalyst env vars (set by the user in the console, never in git): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` = `2006803662`, `GITHUB_DISPATCH_TOKEN`. Write `catalyst/ENV_SETUP.md` listing names only.
- Check Catalyst runtime and cron limits in the docs before choosing the runtime and schedule syntax; note any limit you hit.
- Deploy, run each stage once with `dry_run=true`, then once live.

---

## 6. Setup: Antigravity does all of it, from the SECRETS block
Do not ask the user to click through consoles. The only input you were given is `GITHUB_PAT` (and the existing bot token).

1. Apply the secret handling rules at the top (read the values, then mask the file with `xxx`).
2. **Pre-flight (stop and report if any fails):**
   - `GITHUB_PAT` works: `gh auth status` or `GET /user`, and it can see `soul991/OPI`. Check it can list secrets, list workflows, read and write contents, open PRs, and dispatch workflows. If a permission is missing, tell the user which one. Do not work around it.
   - `TELEGRAM_BOT_TOKEN` is valid: `getMe` returns bot ID `9196287140`. Do not print the token.
   - Send one test message to chat `2006803662` ("OPI setup check").
   - Catalyst CLI is installed, logged in, and linked to the user's project.
3. **GitHub Actions secrets** (`gh secret set`, value via stdin): `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` = `2006803662`. Verify with `gh secret list` (names only). Report whether `OPENROUTER_API_KEY` exists (D-026). If missing, report it; do not invent one.
4. **Catalyst environment variables** for the function: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `GITHUB_DISPATCH_TOKEN` (= `GITHUB_PAT`; the user chose to use this single PAT). Use the Catalyst CLI or API. If the only route is a config file containing values, add it to `.gitignore` first and never commit it. If nothing works, give the user the exact console steps.
5. Deploy and run each stage once with `dry_run=true`, then live.
6. **Secret hygiene check at the end:** scan the working tree, full git history, workflow logs, and GitHub issues for the PAT and bot token (compare by hash or pattern; never print them). Paste the clean result in the verdict. If anything leaked, stop and tell the user.
7. **Cleanup:** unset the environment variables, confirm this file's values are still `xxx`, and note in the verdict that Catalyst holds the PAT.
8. The user still approves the Apply/Skip thresholds (Section 3, item 3). Pause there.
9. Reminder for the report: GitHub pauses scheduled workflows after 60 days with no commits.

---

## 7. Data and leakage rules
- A PREVIEW feature may use only information available at preview time (live subscription as of its timestamp, GMP as of its date, price band). No listing-day or later information in any pre-listing alert.
- Every collected value has source URL, page date, access date, and a saved snapshot (Evidence Standard, Section 4 of the protocol); otherwise `NOT_RECORDED`.
- No financial advice language. Every prediction alert ends with: "Decision aid only, not financial advice."

---

## 8. Success criteria and decision rules
1. Gate A exits with 0 FAIL and a complete `prior_phase_recheck.csv`.
2. `python scripts/ci_local.py` -> `CI_LOCAL: PASS` before every push; `verify_all.py` 0 FAIL at exit.
3. **Delivery proof** (paste evidence in the verdict): one real Telegram message for each of `announce`, `preview`, `listing` (a live IPO if one exists in the window; otherwise a clearly labelled replay or dry run using a past IPO, **not** passed off as live).
4. Idempotency proof: re-trigger every stage twice, and show that 0 duplicate messages were sent.
5. Timing proof: the measured delay between Catalyst cron time and message arrival, for at least 5 triggers, reported as measured. Do not claim "on time at 12 PM" unless measured.
6. Failure proof: a forced failure sends a Telegram alert and a GitHub issue, and a later success closes the issue (existing `manage_alerts.py` behaviour).
7. Zero secrets in the repo history (run a scan and paste the result).
8. Model, data, and registry hashes unchanged (show `git diff --stat` for `model/` and `data/ipo_*.csv`: empty).
9. If the live preview alert cannot be produced because no IPO is open in the window, record that honestly. The preview path must still pass its tests on fixtures.

---

## 9. Task order (strict)
1. `verify_start.txt`, Gate A, fixes, commit `phase21-gate-a`.
2. Preregistration (including thresholds; **pause for user approval of thresholds**), commit `phase21-preregistration`.
3. WS-A, then WS-B, then WS-C, then WS-D, then WS-E, then WS-F, then WS-G. One branch, one PR, one commit per workstream, each with a `DEFECTS.md` entry before its commit and a regression test.
4. Cloud proof runs (Section 8), then `verify_end.txt`.
5. Phase files: `phases/Phase 21/1_planning_and_goals.md`, `2_building_and_execution.md`, `3_outcome_and_verdict.md`, plus `verify_*.txt`, `prior_phase_recheck.csv`, `preregistration.md`.

## 10. Required verdict structure (`3_outcome_and_verdict.md`)
1. **Targets missed and unfixed items** (may say "None" only if `DEFECTS.md` has no OPEN or PARTIAL rows; D-013, D-026 and D-096 must be accounted for).
2. Defect Ledger: opened, fixed, carried over, regressed (IDs and statuses).
3. Delivery, idempotency, timing, and failure proofs with pasted output.
4. Preview vs final comparison status (n and values, descriptive only).
5. Risks: `workflow_dispatch` latency, source layout changes, token expiry, 60-day inactivity pause.
6. Self-audit, and recommendations for Phase 22.

## 11. Report to the user, then STOP
Short report: Gate A result, faults found and fixed, what was built, proofs obtained, manual steps still needed, and risks. Do not start Phase 22 until the user approves.
