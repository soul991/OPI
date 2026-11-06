# Phase 19: Resolve Diverging Outcome Sources Honestly (Exchange-Labelled Prices, Pre-Registered Arbitration, Close Proven Defects)

> Follows `RULES.md` and `PHASE_PROTOCOL.md`. Research decision aid only, not financial advice.
> **STOP POINT:** after Gate A19 is committed and pushed, STOP and report. Do not start the workstreams until the user replies "continue".
> Use only FIXED / PARTIAL / NOT FIXED / OPEN. FIXED needs a named passing test AND, where stated, a cloud run on `main` quoted by run id. Every number in a report comes from a committed script over `predictions/prediction_log.csv`, `predictions/outcome_corrections.csv` and `data/evidence/`. Never edit `predictions/prediction_log.csv` by hand. Never create or copy files under `data/evidence/` by hand: only GitHub Actions writes production evidence.
> No performance claims below n = 30 listed forward IPOs. Current: n = 11 listed (n = 9 prior cohort). Do not headline any "excluding outlier" figure.
> Do not edit `scripts/verify_extra.py`, `scripts/verify_all.py` or `scripts/verify_pages.py`. Do not touch `model/ipo_model.joblib`. Do not merge any bot PR.
> Goal: when two price sources disagree by more than 1.0%, the cloud finds out WHY (same exchange or not) and resolves the outcome by a rule that was written down before it is applied, with every source value kept in evidence; and no defect stays open that the cloud has already proven fixed.

## 0. Context (as of 2026-11-07, `main` after Phase 18)
- Phase 18 is merged (PR #20). `verify_all.py` 81 PASS / 0 FAIL, `verify_extra.py` 7 PASS. D-095 is proven: scheduled runs on Nov 6 logged `MISSING_OUTCOME_ALERT` and still committed data (bot commits `993b5c0`, `27e2183`, `baf3221`).
- n = 11 listed of 30 (model MAE 5.09 pp on 11, 5.85 pp on the first 9; provisional). SFC Environmental (+7.61%) and M.K.Sons (+5.56%) were recorded by the cloud via Tier 2 with Chittorgarh within 0.3%.
- **Two rows are stuck in `PENDING_REVIEW` because Tier 2 sources diverge beyond 1.0%:**
  - BLS Polymers (listed 2026-11-03): yfinance 248.0 vs Chittorgarh 244.1 (1.57%). Phase 18's verdict says a third source (Groww) reports 248.0.
  - Bombay Coated & Special Steels (listed 2026-11-05): yfinance 91.0 vs second source 92.02 (1.12%).
  - Tier 2b (Phase 18, D-096) only starts when Yahoo's bar is missing or empty. A divergence returns `PENDING_REVIEW` and Tier 2b is not tried. Keeping the 1.0% tolerance was correct; the gap is that no pre-registered way exists to resolve a divergence.
  - Hypothesis to test, not assume: the sources may quote different exchanges (Yahoo `.NS` is NSE; a Chittorgarh page can show NSE and BSE rows) or different quantities (open vs listing price).
- Daily and watchdog runs are red on purpose while BLS is overdue: the step "Check overdue outcomes and coverage" fails after the data commit (Actions screenshot of 2026-11-07: daily #54, #55, #56 and watchdog #17 red, two open issues). A `pages-build-deployment` run (#79, 10m52s) also failed once and #80 succeeded.
- Open defects: D-013 PARTIAL, D-026 NOT FIXED, D-085 PARTIAL, D-096 OPEN, D-099 OPEN. D-099 and D-085 appear to have cloud proof already (Bombay Coated resolved to `BCSSL.NS` in the cloud; Nifty evidence exists for 2026-11-03, -04, -05 and `verify_extra` is clean).

## 1. Seed these defects in DEFECTS.md first
| ID | Sev | Description | Verification |
|---|---|---|---|
| D-100 | High | A Tier 2 divergence (>1.0%) leaves the outcome `PENDING_REVIEW` forever; nothing tries to establish which source is right (BLS Polymers 1.57%, Bombay Coated 1.12%). | Divergence path saves every source value with its exchange label, then applies the pre-registered arbitration rule (Section 6). Cloud proof: BLS or Bombay Coated recorded (tier label `tier2_arbitrated`) with all evidence files, or a quoted exact reason why not. |
| D-101 | Medium | Evidence manifests do not state which exchange (NSE/BSE) and which quantity (open or listing price) each source value refers to, so a divergence cannot be diagnosed from the files. CONFIRM at the gate (G6) before treating as a defect; if manifests already carry it, mark D-101 ACCEPTED with the quote. | New manifest fields `exchange`, `quantity`, `source_publisher`; tests on fixtures for Yahoo, Chittorgarh and Groww pages. |
| D-102 | Low | `pages-build-deployment` run #79 failed after 10m52s; cause unknown. CONFIRM at the gate (G7). | Quote the failing run's reason. If it was a one-off platform timeout and #80 and later runs are green, mark ACCEPTED with the quote; otherwise fix. |
Existing: D-026 stays NOT FIXED until a green **scheduled** run uses the research agent for a new IPO. D-013 stays PARTIAL.

## 2. Gate A19 - Re-verify Phase 18 (commit `phase19-gate-a`)
Step 0: pull `main`; install `requirements.lock` and pytest; run `verify_all.py` -> `phases/Phase 19/verify_start.txt` and `verify_extra.py` -> `verify_extra_start.txt`, both saved as UTF-8; `ci_local.py`, pasting only the last line. Seed D-100..D-102.
- **G1** 10 random claims from `phases/Phase 18/3_outcome_and_verdict.md` (seed 19) into `prior_phase_recheck.csv`, at least 5 about specific IPO numbers or run ids; recompute from raw files: model MAE on n = 11 and on the first 9, raw GMP MAE (n = 7), master row count. Quote any mismatch; do not smooth it.
- **G2** Every FIXED row D-071 and D-083..D-099 that is marked FIXED has a passing named test; list test and result.
- **G3** `actions_status.md`: last 12 scheduled runs with conclusion, which step failed in each red run (quote the line from the alert issue body), and the number of open issues. Confirm the red daily and watchdog runs are the overdue-outcome alert and nothing else.
- **G4** For BLS Polymers and Bombay Coated: last `ACTUALS` run-log lines, days since listing, and every source value the repo has saved.
- **G5** `gh secret list` shows `OPENROUTER_API_KEY`; `git grep sk-or-` prints nothing.
- **G6** Divergence diagnosis (read-only): from saved evidence and, if needed, one `probe_sources.yml` dispatch, state for BLS and Bombay Coated what each source value refers to (publisher, exchange NSE/BSE, open vs listing price, bar date). Paste the evidence lines. If the manifests lack this, that confirms D-101.
- **G7** Quote the log reason for `pages-build-deployment` run #79 (failed) and confirm the next runs are green.
- **G8** Check run-log for new IPOs discovered in the last 7 days and whether the research agent ran (D-026 monitoring; report only).
- Gate exit: `verify_all.py` 0 FAIL; `verify_extra.py` as it is. Commit `phase19-gate-a`, push, then commit `phases/Phase 19/preregistration.md` (Section 6) as `phase19-preregistration`, push, and STOP.

## 3. Workstream A - Label every source value (D-101)
Every outcome evidence file records, for each source value: `publisher`, `exchange` (NSE, BSE or UNKNOWN), `quantity` (`open` or `listing_price`), `bar_date`, `value`. Parsers that cannot tell the exchange record UNKNOWN; they never guess. Tests on saved-page fixtures (under `tests/fixtures/`, marked synthetic). Existing evidence files are not changed.

## 4. Workstream B - Divergence arbitration (D-100)
When Tier 2 finds yfinance and the second source more than 1.0% apart:
1. Fetch up to two more independent publishers (use only those the probe shows reachable; log the probe run id). Save every raw page verbatim as evidence, labelled per Workstream A.
2. Apply the pre-registered rule (Section 6): same-exchange, same-quantity values only; accept only if at least two sources from different publishers agree within 1.0% and the group has a strict majority of the labelled sources. The recorded price is the median of the agreeing group.
3. Otherwise record nothing, log the exact reason (`SKIPPED_ARBITRATION_NO_MAJORITY`, `SKIPPED_ARBITRATION_EXCHANGE_MISMATCH` or `SKIPPED_ARBITRATION_UNAVAILABLE`) and keep the row pending.
4. A recorded outcome gets tier label `tier2_arbitrated` and a manifest listing every source value including the rejected ones, and the gain each value would have produced.
5. Tests: majority of 2 of 3 -> recorded; 1 vs 1 -> not recorded; exchange mismatch -> not recorded; unlabelled values -> not recorded; Yahoo-derived page counted once; already recorded row untouched; the 1.0% tolerance itself is unchanged (assert the constant).
6. Cloud proof: dispatch `daily.yml` on `main`; report for BLS and Bombay Coated: recorded or pending, tier, evidence files, bot commit SHA. Nothing is written by hand.
7. Reporting: `scripts/forward_report.py` shows MAE with and without `tier2_arbitrated` rows, both labelled provisional. BLS was already diverging when the rule was written; say so in the verdict.

## 5. Workstream C and D
**C - Close proven defects.** Set D-099 and D-085 to FIXED only with the proof already available: for D-099 the cloud run that resolved `BCSSL.NS` plus the named test; for D-085 the committed Nifty files for 2026-11-03/-04/-05 with run ids plus `verify_extra.py` 7 PASS. D-096 becomes FIXED only if Workstream B's cloud proof records a row; otherwise PARTIAL with the exact reason. D-102: per G7.
**D - Alert noise.** The daily and watchdog runs go red every day while a row is overdue. Keep them red and keep the data commit, but (1) the alert must reuse one open issue per failing step and append a comment (no new issue each run), and (2) the comment must name the company, days overdue and last logged reason. Test with a fixture. Do not change any threshold.

## 6. `phases/Phase 19/preregistration.md` (commit before Workstream A)
State, before any workstream code: (1) the arbitration rule exactly as in Workstream B; (2) the 1.0% tolerance is unchanged; (3) Yahoo and any Yahoo-derived page count as one publisher; (4) values are compared only if exchange and quantity labels match; (5) no outcome, evidence file or log row is written by hand; (6) the rule was written after the BLS Polymers (1.57%) and Bombay Coated (1.12%) divergences were already visible, so rows resolved by it are tagged `tier2_arbitrated` and reported with and without; (7) n = 11 listed of 30: all metrics descriptive and provisional, no superiority claims; (8) `v4.0.0-champion` and `model/ipo_model.joblib` are not changed.

## 7. Exit deliverables
`phases/Phase 19/2_building_and_execution.md`, `3_outcome_and_verdict.md`, `verify_end.txt`, `verify_extra_end.txt` from runs on final `main`, all UTF-8. Every quoted `SUMMARY:` line is copied verbatim from those files. Forward results from `scripts/forward_report.py` with the provisional banner, n updated only if the cloud recorded new outcomes (state old and new n). "Targets Missed" lists every defect that is not FIXED. Corrections to earlier phases go only in a top `## ERRATA`. Run `scripts/ci_local.py`, push (PR for workflow changes as in Phase 17/18), and finish with a `gh run list` showing the state of `main`, saying plainly which runs are red and why.
