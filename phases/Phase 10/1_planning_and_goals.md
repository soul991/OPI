# Phase 10: Planning & Goals - First Real Results, Mock-Data Quarantine, Built-In Grounding, Real IPO Discovery

> Place at `phases/Phase 10/1_planning_and_goals.md`. Follow `RULES.md` and `PHASE_PROTOCOL.md`. This phase is **strict**. The last work (the patch and the four-IPO scoring on 2026-10-20) was good: `verify_all.py` v2 passed (48/0/0) and I independently confirmed the scored inputs appear in real saved pages. But several older problems remain, and `verify_all.py` v3 (supplied with this phase) finds three more. **Gate A10 (Section 2) comes first**, with one time-critical exception: recording the first real listing results (Section 2, item X1).

## 0. Context (as of 2026-10-21, 12:40 IST)
- HD Fire Protect listed today (2026-10-21). Fusion CX lists 2026-10-22. Zetwerk, Sahajanand Medical, Tonbo Imaging and Bonfiglioli list 2026-10-23.
- Jio Platforms and Paras Healthcare opened 2026-10-21 and close 2026-10-23; they can only be scored after bidding closes (D-023, D-024).
- No actual result is recorded yet in `predictions/prediction_log.csv`.

## 1. Rules (summary; full text in PHASE_PROTOCOL.md)
- Three files in `phases/Phase 10/` plus `verify_start.txt`, `verify_end.txt`, `prior_phase_recheck.csv`.
- Status words: `FIXED`, `PARTIAL`, `NOT FIXED`. `FIXED` needs a passing regression test or command with pasted output.
- Never fabricate or estimate data, URLs, dates, predictions or metrics. Every collected value needs URL, page date, access date and a snapshot **saved by code**; a typed-in value must be checked by code against that snapshot.
- **Mock or test output must never be written to `data/` or committed outside `tests/fixtures/`.**
- Replace `scripts/verify_all.py` with the supplied v3. Do not edit it to make a check pass; you may add checks.
- Earlier phase folders are immutable (errata may only add lines). Logs carry the real write-time timestamp with an offset. No secrets in the repo.
- Evidence-language rule (bootstrap interval excluding zero, else "no demonstrated difference"). With n below 30 listed forward predictions, results are descriptive only.
- Commit per workstream. `phase10-gate-a` and `phase10-preregistration` first (X1 results may be committed before them, in their own commits, because of the listing dates).
- Never use "apply / avoid / buy / sell" wording. Decision aid only, not financial advice.

## 2. Gate A10 - Re-Verify Previous Work and Clear Carried Defects (commit `phase10-gate-a`)

**Step 0.** Replace `scripts/verify_all.py` with v3. Run it and save the full output as `phases/Phase 10/verify_start.txt`. Expected baseline: FAIL for 20 mock research runs, 440 mock evidence files, and Fusion CX's issue price (289) not appearing in its saved snapshot. Add the new defects below to `DEFECTS.md`.

**Step 1.** Re-verify the previous work (Phase 9, the patch commit `bfe2820`, and the four-IPO scoring commit `7f7dc89`) per Protocol Section 2 Step 1, from a **fresh clone**:
- Re-run `opi.score.score_ipo` on the logged features of **each of the six FORWARD rows** and confirm the predicted gain and probability equal the logged values (tolerance 1e-6). Record in `prior_phase_recheck.csv`.
- Recompute 5 headline numbers from raw files; check 10 random claims in the Phase 9 verdict against the files.
- Confirm `verify_all.py` v3 is byte-identical to the supplied version at the gate commit.

### New defects to add to DEFECTS.md
| ID | Phase | Description | Severity | Status | Due | Test |
|---|---|---|---|---|---|---|
| D-025 | 9 | 20 mock research runs (`data/research_runs/*.json`) and 440 mock evidence files (`data/evidence/research/run_*`) are committed, with fake `chittorgarh.com/ipo/mock-ipo` URLs and 19-line synthetic pages; the daily bot keeps adding more. "VERIFIED_IN_SNAPSHOT" on them is circular. | High | OPEN | 10 | tests/test_data_integrity.py::test_no_mock_output_in_data_folders |
| D-026 | 9 | The research agent has never run against the live web in repo evidence; the Phase 9 verdict's "live Gemini" results are not visible in any committed run. | High | OPEN | 10 | tests/test_research_agent.py::test_live_run_log_has_provider_and_real_urls |
| D-027 | 8/9 | `run_daily` has no IPO discovery: it scores only the row(s) in `new_ipo.csv`. The "automation" does not find open or upcoming IPOs. | High | OPEN | 10 | tests/test_discover.py::test_discovers_closed_unlisted_mainboard_ipos_from_fixture |
| D-028 | 9 | `scripts/score_oct19_ipos.py` hard-codes all inputs and saves snapshots separately without checking that the values appear in them. (I verified the four IPOs externally; the code does not enforce it.) | Medium | OPEN | 10 | tests/test_ingest.py::test_mismatch_between_typed_value_and_snapshot_is_refused |
| D-029 | 9 | The app shows P(gain > 10%) up to 98% (hides only above 0.98) although README advises not to trust values above about 0.85 and the calibrated range was measured lower; its input table also shows fundamentals the model does not use. | Medium | OPEN | 10 | tests/test_app.py::test_probability_hidden_outside_calibrated_range |
| D-030 | 9 | Nifty 30-day return and India VIX come from `yfinance` (unofficial Yahoo data), saved only as a derived JSON, not as raw data with a hash. | Low | OPEN | 10 | tests/test_ingest.py::test_market_data_saved_raw_with_hash |
| D-031 | 9 | Fusion CX forward row has thin inputs (no GMP and about a dozen empty features) and its issue price (289) is not found in its saved snapshot. | Medium | OPEN | 10 | `verify_all.py` grounding check for Fusion CX |
| D-032 | 9 | Windows-only local workarounds (`-p no:pytest_ethereum`, `numpy>=2.0.0`) existed in uncommitted local state. | Low | OPEN | 10 | README "Windows setup" section |
| D-033 | 9 | Branch `local-work-2026-10-20` holds uncommitted-work leftovers: two useful changes (string-casting table values in `app/main.py`; date-format variants in `opi/collect.py` grounding) are not in `main`. | Low | OPEN | 10 | tests/test_app.py::test_table_values_are_strings; tests/test_ingest.py::test_grounding_accepts_date_format_variants |
(D-005, D-013 stay `PARTIAL`; D-007, D-008, D-023, D-024 stay `DEFERRED`.)

### Gate items
| # | Defect | Required fix | Done when |
|---|---|---|---|
| **X1** | **D-005: record the first real results (time-critical).** | After each listing, record the actual opening/listing price using `scripts/update_actuals.py` (official NSE/BSE URL, or `--evidence-file` with a page saved from the browser). Never type a gain by hand. Order: HD Fire Protect (after 10:00 IST on 2026-10-21), Fusion CX (2026-10-22), Zetwerk, Sahajanand Medical, Tonbo Imaging, Bonfiglioli (2026-10-23). Commit each result right away, then regenerate the dashboard. If a result cannot be evidenced, leave it empty and write why in `phases/Phase 10/results_log.md`. | Each result has a snapshot under `data/evidence/actuals/` and a manifest; `verify_all.py` passes. |
| **X2** | **D-025: quarantine mock data.** | Move the mock provider's output to a temporary or test location by default (`OPI_ENV=test` required to enable the mock provider; otherwise it must refuse). Remove all 20 mock runs and 440 mock evidence files from `data/` with `git rm`, writing every removed path and hash to `phases/Phase 10/mock_quarantine_manifest.csv`; keep at most two representative runs under `tests/fixtures/mock_runs/`. Real evidence (for example `data/evidence/research/2026-10-23_*.html` and the market, subscription, gmp and actuals folders) must not be touched. The daily workflow must never use the mock provider; with no live provider configured it records `SKIPPED_NO_LIVE_PROVIDER`. | `verify_all.py` mock checks PASS; test `test_no_mock_output_in_data_folders` passes; manifest lists every removed file. |
| **X3** | **D-029: probability rule.** | Compute the calibrated probability range from the rolling-origin calibration data (minimum and maximum of the out-of-sample calibrated probabilities) and store it in `model/registry.json`. The app and dashboard show P(gain > 10%) only inside that range (otherwise "not shown: outside measured range"). Align README text with the stored range. Label fundamentals in the input table "not used by the model", or remove them. | Test passes; README and app agree. |
| **X4** | **D-031: Fusion CX evidence.** | Do not edit the existing row. Find an official or primary source for the Fusion CX issue price, save a snapshot by code, and record whether 289 is correct (note in `results_log.md` and the dashboard "thin inputs" flag). If 289 is wrong, mark the row `INVALID_INPUT_ERROR` and re-score only if the listing has not yet happened (2026-10-22) and with real timestamps; otherwise leave it invalid. | Grounding check PASS, or row status updated with an explanation. |
| **X5** | **D-032 / D-033.** | Add a README "Windows setup" section (how to handle a globally installed pytest plugin without committing a workaround). Cherry-pick the two useful changes from `local-work-2026-10-20` with tests (see D-033). Do not merge anything else from that branch and do not delete branches; report that they can be removed. | Tests pass; README updated. |
| **X6** | **Register hygiene.** | Add D-025 to D-033 to `DEFECTS.md`. | `verify_all.py` register checks PASS. |

Gate exit: `verify_all.py` v3 has 0 FAIL on a fresh clone (every WARN explained); `DEFECTS.md` updated; commit `phase10-gate-a`.

## 3. Objectives & Scope (after Gate A10)
1. **A. Built-in grounding** for all forward-scoring inputs (D-028, D-030).
2. **B. Real IPO discovery and a real daily automation** (D-027).
3. **C. One live research-agent proof** (D-026), if the user's API key and web access are present.
4. **D. Results dashboard** showing predicted vs GMP vs actual for the forward test.
Out of scope: model changes, tail handling and interval width (D-007, D-008), SME IPOs, public hosting.

## 4. Workstream A - Built-In Grounding (`opi/ingest.py`)
- Given an IPO's URLs (overview, subscription, GMP), the **code** fetches each page, saves it under `data/evidence/<type>/<listing_date>_<company-slug>.html`, hashes it, and **parses the values with deterministic parsers** (one parser per source, tested on saved HTML fixtures from the real pages already in `data/evidence/`).
- If a value is supplied by a person or an LLM, ingest compares it to the parsed value and **refuses on mismatch**. Values that cannot be parsed from a saved page stay empty (never typed in).
- GMP: select the table row for the **last bidding day** evening (for example "19-Oct 23:37") and store its timestamp as `gmp_as_of`; never take the top (latest) row blindly.
- Market data: save the raw response (CSV or JSON), its hash, the source name, and the access time. State clearly that `yfinance` is an unofficial source (confidence `medium`); optionally cross-check one date against an NSE indices page snapshot.
- Replace `scripts/score_oct19_ipos.py` with `scripts/score_ipo.py --listing-date ... --company ... --urls ...` using ingest. Keep the old script for history, marked deprecated.

## 5. Workstream B - IPO Discovery and Daily Automation
- `opi/discover.py`: fetch the lists of mainboard IPOs that are open, or closed and not yet listed (use the same sources as ingest; keep saved HTML fixtures for tests). Apply the inclusion rule (mainboard only; no SME, FPO, rights issue). Confirm each candidate's listing date from a source.
- `opi/run_daily.py` flow: discover, then for each IPO whose bidding has closed (after 18:00 IST on the close date) run ingest, validate, score, append a FORWARD row; for each listed FORWARD row, run the actuals step. Failures become visible `SKIPPED_<reason>` lines, never defaults.
- `.github/workflows/daily.yml` runs this twice daily without the mock provider. If real fetching is blocked in Actions, the run records `SKIPPED_FETCH_BLOCKED` and the dashboard shows it. Never commit evidence unrelated to a real IPO.
- Jio Platforms and Paras Healthcare must be picked up automatically after their bidding closes on 2026-10-23, or the verdict must explain why not.

## 6. Workstream C - Live Research-Agent Proof (needs the user's API key and web access)
- Run the research agent **live** on one real open or recently closed IPO (for example Jio Platforms in PREVIEW mode while bidding is open). The run log must show a real provider and model name, real URLs, code-saved snapshots, hashes, and the grounding result per field.
- Compare the agent's proposed values with the deterministic ingest parsers for the six scored IPOs; report agreement per field. Report grounding rates **from live runs only**.
- If no API key or web access is available, mark this item `NOT FIXED (needs user action)` and say so at the top of the verdict. Do not substitute mock results.

## 7. Workstream D - Results Dashboard and Reporting
- Dashboard table for every FORWARD row: model estimate, interval, GMP at close, actual listing gain, error of model, error of GMP, status, "thin inputs" flag, model version. Provisional banner: **n listed = ... of 30**; no performance claims below 30; descriptive only.
- `scripts/forward_report.py`: per-IPO errors and simple averages, clearly labelled descriptive; comparisons with intervals only at n >= 30.
- README: "What the evidence shows" updated with the first results (n, not claims) and a Known limitations section (including D-006, D-010).

## 8. Verification Commands
```bash
python scripts/verify_all.py | tee "phases/Phase 10/verify_end.txt"   # 0 FAIL required (fresh clone)
python -m pytest -q
python -m opi.discover --dry-run          # lists candidates, writes nothing
python -m opi.run_daily --dry-run
python scripts/forward_report.py
git log --reverse --format=%s | grep -n "phase10-"
```

## 9. Success Criteria (measured, not promised)
| Question | Metric | Rule |
|---|---|---|
| Gate A10 | X1-X6 statuses | Each `FIXED`/`PARTIAL`/`NOT FIXED` with pasted evidence |
| First results | Results recorded with official evidence | List each of the six; any missing one explained |
| Mock quarantine | `verify_all.py` mock checks | PASS; manifest complete |
| Grounding | Typed value not matching snapshot | Refused (test) |
| Discovery | Fixture test plus a real dry run | Finds the open and not-yet-listed mainboard IPOs |
| Live agent proof | Grounding rate from live runs only | Reported as measured, or `NOT FIXED (needs user action)` |
| Dashboard | Table of predicted vs GMP vs actual | Live, with the provisional banner |
| Register | `verify_all.py` 0 FAIL; ledger in verdict | Carried defects listed |

## 10. Task List (strict order)
1. Read `RULES.md`, `PHASE_PROTOCOL.md`, this file; confirm the user requirements (web access, API key) in `2_building_and_execution.md`.
2. **X1 immediately and as each listing happens** (own commits).
3. Step 0: install v3 `verify_all.py`; save `verify_start.txt`; add D-025 to D-033.
4. Gate A10: X2, X3, X4, X5, X6; commit `phase10-gate-a`.
5. Commit `phases/Phase 10/preregistration.md` (parser rules, GMP-row rule, discovery rules, display rules) as `phase10-preregistration`.
6. Workstreams A, B, C, D (one commit each).
7. Run `verify_all.py`, pytest; save `verify_end.txt`.
8. Write `2_building_and_execution.md` and `3_outcome_and_verdict.md` (Section 11); update `DEFECTS.md`; attach the self-audit.

## 11. Required Structure of `3_outcome_and_verdict.md`
1. **Targets missed and unfixed items** ("None" only if `DEFECTS.md` has no OPEN or PARTIAL rows; `verify_all.py` checks this).
2. **Defect Ledger** (opened, fixed, carried over, regressed).
3. **First real results table** (company, listing date, issue price, listing price, actual gain, model estimate, GMP, errors), labelled provisional with n.
4. Gate A10 table with evidence; the Phase 9 re-check results.
5. Mock quarantine summary (files removed, manifest).
6. Grounding and discovery results.
7. Live research-agent results, or why not.
8. Honest verdict, hypotheses labelled, failure modes, Phase 11 recommendations (tail handling, interval width, calibration, retraining challenger).
9. Statement: decision aid only, not financial advice.

## 12. Self-Audit (yes/no with evidence)
- Does any `FIXED` lack a passing test or pasted command?
- Does `verify_all.py` pass with 0 FAIL on a fresh clone? Was it edited to pass? (must be no)
- Does any mock or test output exist under `data/`? (must be no)
- Is any input value in a FORWARD row not found in its saved snapshot? (must be no)
- Was any actual gain typed by hand? (must be no)
- Does any log timestamp differ from its commit time by more than the tolerance?
- Are any grounding rates reported that come from mock runs? (must be no)
- Does the app or dashboard show a probability outside the measured range or any "apply/avoid" wording? (must be no)
- Was `data/ipo_phase5_final_test.csv` read for any decision? (must be no)
