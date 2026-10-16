# Phase 9: Planning & Goals - Gate A9 (Fix Phase 8 Faults), Then the Research Agent and Chat Interface (OPI Console)

> Place at `phases/Phase 9/1_planning_and_goals.md`. Follow `RULES.md` and `PHASE_PROTOCOL.md`. This phase is **strict**. Phase 8 fixed the biggest Phase 7 problems and was unusually honest, but it left new faults (Section 1). **No feature work starts until Gate A9 passes.** If something cannot be done, mark it `NOT FIXED` or `PARTIAL` and say why. Do not rename or work around it.

## 0. Requirements From the User (state in `2_building_and_execution.md` whether each is met)
1. **Web access permission** for the coding agent to fetch pages (exchange sites, Chittorgarh, GMP trackers). Phase 8 was blocked on this.
2. **An LLM API key** for the research agent, stored in `.env` / Streamlit secrets (never committed). Provider is configurable (`OPI_LLM_PROVIDER`).
3. **GitHub Actions enabled** (workflow permissions: read and write) and **GitHub Pages** enabled for the dashboard.
If any is missing, mark the dependent items `NOT FIXED (needs user action)` and continue with the rest. Never fake output.

## 1. Rules (summary; full text in PHASE_PROTOCOL.md)
- Three files in `phases/Phase 9/` plus `verify_start.txt`, `verify_end.txt`, `prior_phase_recheck.csv`.
- Status words: `FIXED`, `PARTIAL`, `NOT FIXED`. `FIXED` needs a passing regression test or command with pasted output.
- Never fabricate or estimate data, URLs, dates, predictions or metrics. Every collected value needs URL, page date, access date and a **snapshot saved by code** under `data/evidence/`.
- `scripts/verify_all.py` is replaced by the v2 version supplied with this phase. **Do not edit it to make a check pass**; you may add checks.
- **Earlier phase folders are immutable.** Re-runs write into the current phase folder. Corrections to earlier reports are `## ERRATA` sections that only add lines.
- **Timestamps:** logs record the real run time with a timezone offset (`datetime.now(timezone)`). Never hard-code or accept a caller-supplied time. Git history is the clock.
- Evidence-language rule (bootstrap interval excluding zero, else "no demonstrated difference"). Explanations are "Hypothesis (untested)".
- No test-set tuning; never read `data/ipo_phase5_final_test.csv` for decisions. No secrets in the repo.
- Commit per workstream. `phase9-gate-a` and `phase9-preregistration` first.
- Decision aid only, not financial advice. The app must never say "apply" or "avoid".

## 2. Gate A9 - Re-Verify Phase 8 and Clear Carried Defects (commit `phase9-gate-a`)

**Step 0.** Replace `scripts/verify_all.py` with the supplied v2. Run it and save the full output as `phases/Phase 9/verify_start.txt`. Add the new defects below to `DEFECTS.md` (IDs never reused). Expected baseline on the current repo: FAIL for fresh-clone tests (4 tests need an untracked model file), CI model availability, backdated forward timestamp, changed earlier-phase artifacts, and extreme GMP values without snapshots.

**Step 1.** Re-verify Phase 8 per Protocol Section 2 Step 1: re-run its scripts from a **fresh clone**, recompute 5 headline numbers, check 10 random claims in the Phase 8 verdict, record in `prior_phase_recheck.csv`.

### New defects to add to DEFECTS.md
| ID | Phase | Description | Severity | Status | Due | Test |
|---|---|---|---|---|---|---|
| D-015 | 8 | `model/ipo_model.joblib` is git-ignored and never built in CI. 4 tests fail on a clean clone ("42 passed" held only on the author's machine); the daily GitHub workflow runs the scorer and tests without the model. | High | OPEN | 9 | tests/test_ci.py::test_model_available_on_fresh_clone |
| D-016 | 8 | The only FORWARD row has `scored_at=2026-10-15T19:30:00.000000` (exact round time) but was first committed at 2026-10-16 03:34 IST, about 8 hours later: backdated. | High | OPEN | 9 | tests/test_forward_log.py::test_scored_at_is_real_run_time |
| D-017 | 8 | Phase 8 overwrote 9 Phase 7 files (and `Phase 4/phase4_summary.json`) in place; originals survive only in git history; a stale note ("+75 backfilled") remains. | Medium | OPEN | 9 | tests/test_reporting.py::test_earlier_phases_immutable |
| D-018 | 8 | Eight GMP values above 100% (Motisons, Bls Eservices, Exicom, Mukka Proteins, Premier Energies, Bajaj Housing, Krn Heat Exchanger, Mamata) are marked "verified" with generic URLs and no snapshots. The Mukka "correction" to 125% cites a Chittorgarh ID and has no snapshot. | Medium | OPEN | 9 | tests/test_data_integrity.py::test_extreme_gmp_have_snapshots |
| D-019 | 8 | Status inconsistency: D-001 is `FIXED` in the register but U1 is `NOT FIXED (REVERTED)` in the verdict. | Low | OPEN | 9 | N/A: documentation (erratum) |
| D-020 | 8 | The daily GitHub workflow has never been confirmed to run successfully on GitHub. | Medium | OPEN | 9 | evidence file `phases/Phase 9/actions_run_evidence.md` |
(D-013 stays `PARTIAL` and continues in item V6; D-005 continues in V8.)

### Gate items
| # | Defect | Required fix | Done when |
|---|---|---|---|
| **V1** | **D-015 / D-020: clean-clone failure and CI.** | Make the model available on a clean clone: either track `model/ipo_model.joblib` (small file; add a `.gitignore` exception) with its hash in `model/registry.json`, or add a deterministic training step to the workflow and tests. The registry hash must match the file. Then trigger the workflow manually (`workflow_dispatch`) and save the run URL and the log tail in `phases/Phase 9/actions_run_evidence.md`. If Actions is not enabled, mark D-020 `NOT FIXED (needs user action)`. | `verify_all.py`: fresh-clone and CI-model checks PASS; run evidence saved or honestly marked. |
| **V2** | **D-016: backdated timestamp.** | Do not edit the old row. Set its status to `INVALID_BACKDATED_TIMESTAMP` (explain in `notes`). If the system date is before the listing date (2026-10-21) and bidding has closed, re-score with final subscription and final-day GMP (URL and code-saved snapshot for each) using `opi.run_daily`, and append a new FORWARD row with the **real** timestamp including offset. If the listing has passed, do not re-score. Change `opi/log.py` so `scored_at` is always generated at write time with a timezone offset, never taken from arguments or constants (tests may use an explicit, flagged fixture clock). | `verify_all.py` backdating check PASS; regression test passes. |
| **V3** | **D-017: earlier phases overwritten.** | Restore all non-`.md` files in `phases/Phase 7/` and `phases/Phase 4/` to their state before Phase 8 (`git checkout e4f7a30 -- <files>`; confirm that hash is the parent of the `phase8-gate-a` commit). Save the Phase 8 re-run outputs (cleaned data) under `phases/Phase 8/rerun_phase7_cleaned/` as a **copy**, with a correct before/after note (remove the stale "+75 backfilled" text). Change the evaluation scripts so their output folder is a parameter that must equal the current phase folder. | `verify_all.py` immutability check PASS; test `test_earlier_phases_immutable` passes. |
| **V4** | **D-018: extreme GMP rows.** | For each of the 8 rows: save a code-fetched snapshot of a dated source showing the GMP and its date (on or before the last bidding day); otherwise set the row to `NOT_RECORDED` through `data_corrections.csv`. Correct `gmp_outlier_review.csv` to cite only snapshot-backed sources, and remove the label "audited genuine" for anything without a snapshot. | `verify_all.py` extreme-GMP check PASS. |
| **V5** | **D-019: status consistency.** | ERRATA on the Phase 8 verdict: state that D-001 was closed by reverting (no verified replacement values; 350 of 731 rows keep older, unverified-by-snapshot GMP) and align the label. | Erratum present. |
| **V6** | **D-013: void audits.** | With web permission, rebuild the 15-row duplicate check and the 40-row random audit using correct source pages and code-saved snapshots (report match rates). If not possible, add a column `verification_status=UNVERIFIED` for those 15 companies and state it in README. | Snapshots and rates reported, or the unverified flag in place and documented. |
| **V7** | **Register hygiene.** | Add D-015 to D-020 to `DEFECTS.md`. | `verify_all.py` register checks PASS. |
| **V8** | **D-005: HD Fire Protect outcome.** | After listing (2026-10-21 or later) run `scripts/update_actuals.py`; store a code-fetched snapshot of the listing price. Report as one data point, no performance claim. If not yet listed, carry over. | Recorded with snapshot, or carried over explicitly. |

Gate exit: `verify_all.py` has 0 FAIL (every WARN explained); `DEFECTS.md` updated; commit `phase9-gate-a`.

## 3. Objectives (after Gate A9): OPI Console - Research Agent + Chat Interface
Build the interface you described: you type an IPO name; a research agent searches the web and prepares the model input with evidence; you review it; the trained model predicts; results are shown with charts; the actual result is compared after listing and feeds a governed data pipeline.

**Design principles:** (1) the LLM only *proposes* values; **code** fetches pages, saves snapshots, and verifies that each value appears in the saved page (grounding check); (2) a human confirms inputs before scoring; (3) the scoring function is the single `opi.score` used everywhere; (4) personal research tool, local-first; (5) no investment recommendations.

Out of scope: auto-retraining or auto-promotion of models, tail-handling research (D-007, D-008), SME IPOs, public hosting (only if explicitly requested and after a SEBI/legal check by the user).

## 4. Workstream A - Research Agent (the "secondary model")
- `opi/schema.py`: typed input schema (pydantic). Each field is `{value, source_url, page_date, accessed_on, snapshot_path, grounding_status, confidence, edited_by_user}`.
- `opi/research_agent.py`: provider-agnostic LLM wrapper (`OPI_LLM_PROVIDER`, key from environment). Given an IPO name, it uses a web-search tool to propose, per schema field, a value, a URL, and a short verbatim quote from the page.
- **Grounding check (`opi/collect.py`):** for each proposal the code fetches the URL, saves the page to `data/evidence/research/<run_id>/...`, hashes it, and checks that the number or quote appears in the saved text (numeric tolerance stated in the preregistration). `grounding_status` is `VERIFIED_IN_SNAPSHOT`, `NOT_FOUND_IN_SNAPSHOT`, or `FETCH_FAILED`. Fields that are not verified stay null; no field is filled from the LLM's memory.
- **Untrusted content:** page text is data, never instructions; a test must include a page that says "ignore previous instructions" and prove it has no effect.
- **Budget and logs:** per-run caps on tool calls and tokens; every run is logged in `data/research_runs/<run_id>.json` (inputs, URLs, hashes, token counts, model used).
- **Manual cross-check mode (keeps your original idea):** a button exports the research prompt (from `skills/ipo-research-analyst`) for other AI tools and lets you paste their reports; reconciliation follows the skill's rules and fills conflicts as unresolved, never guessed.
- **Offline tests:** a mock provider with recorded responses and saved HTML fixtures so tests run without network or keys.

## 5. Workstream B - Validation and Human Confirmation
- `opi/validate.py` rules: mainboard only (not SME/FPO/rights); final subscription only after bidding closes (before that, only a clearly labelled **PREVIEW** with live data; PREVIEW results are never logged as FORWARD); GMP must be as of the last bidding day; leakage and range checks.
- **Review screen:** table of every field with value, source link, snapshot link, grounding status, and an editable cell. The user must press **Confirm inputs** before scoring. Edits are stored with `edited_by_user=true`.
- Missing fields are allowed only where the model supports missing values; the screen lists what is missing and how it affects reliability.

## 6. Workstream C - Interface and Output Methods (Streamlit app in `app/`)
- Run locally: `streamlit run app/main.py`. Chat-style input ("Analyze <IPO name>"), progress steps shown while the agent works, clarifying question if the name is ambiguous.
- **Result page:** (1) headline card with estimated listing gain and 80% interval, probability of >10% only when it lies in the calibrated range (otherwise hidden), and which rule applies ("GMP observed: GMP is the primary signal, model is context" or "no GMP: model estimate with interval"); (2) interval bar with the GMP marker; (3) histogram of historical listing gains with this IPO's estimate; (4) table of the 5 most similar past IPOs (sector, size, subscription) with actual outcomes; (5) data-quality panel (missing and unverified fields, sources with snapshot links); (6) **track record panel** read live from the forward log (n listed, model vs GMP vs mean MAE) with the provisional banner below n = 30; (7) global feature-importance chart (permutation importance computed on rolling-origin data, not hand-made).
- **Actions:** download inputs and outputs (JSON and CSV); **Log this prediction** writes a FORWARD row only if all rules pass (button disabled with the reason otherwise).
- **Wording:** every page shows "Decision aid, not financial advice". Never use "apply/avoid/buy/sell" language; use "estimated listing gain range".
- Smoke tests with Streamlit's `AppTest`.

## 7. Workstream D - Learning Loop (governed, not automatic)
- The daily workflow (Phase 8) records actual listing results. Add `scripts/promote_forward_rows.py`: moves a listed FORWARD row into the training data **only if** it passes `audit_dataset.py`, has snapshot-backed inputs and outcome, and meets the inclusion rules; every promotion is written to `data/promotions.csv` (company, model_version, date, evidence paths).
- Add a **monthly** workflow that runs `scripts/retrain_challenger.py` and opens a **pull request** with the challenger report; it never promotes a model. Promotion follows `docs/retraining_policy.md`, requires your approval, and gets a new `model_version`.
- Set expectations in README: about 8 to 10 new IPOs per month, so accuracy improves slowly; data quality matters more than volume.

## 8. Workstream E - Tests and Docs
- Tests: schema; grounding (value present vs absent vs fetch failure); prompt-injection page; validation rules (no FORWARD before close, GMP as-of rule); end-to-end with the mock provider from IPO name to input JSON, prediction and chart data; the logged row equals the evaluation pipeline output for a fixed input; fresh-clone test run.
- README: quickstart (setup, `.env` keys, running the app), architecture diagram (text), "What the evidence shows", "Known limitations".

## 9. Verification Commands
```bash
python scripts/verify_all.py | tee phases/"Phase 9"/verify_end.txt     # 0 FAIL required
python -m pytest -q
streamlit run app/main.py        # manual smoke test; also AppTest in pytest
python -m opi.run_daily --dry-run
git log --reverse --format=%s | grep -n "phase9-"
```

## 10. Success Criteria (measured, not promised)
| Question | Metric | Rule |
|---|---|---|
| Gate A9 | V1-V8 statuses | Each `FIXED`/`PARTIAL`/`NOT FIXED` with pasted evidence |
| Clean-clone reproducibility | `verify_all.py` fresh-clone check | PASS |
| Timestamps honest | Backdating check | PASS |
| Earlier phases untouched | Immutability check | PASS |
| Research agent grounded | Share of agent-proposed values `VERIFIED_IN_SNAPSHOT` on real runs | Report as measured; unverified fields stay null |
| End-to-end demo | Real run on an open or upcoming IPO, or an honest "none available" | Saved run log and snapshots |
| UI | All result-page elements present; AppTest passes | Yes/no per element |
| Governance | No automatic model promotion exists | Verified by test |
| Defect register | `verify_all.py` 0 FAIL; ledger in verdict | Carried defects listed |

## 11. Task List (strict order)
1. Read `RULES.md`, `PHASE_PROTOCOL.md`, this file; confirm the three user requirements in Section 0.
2. Step 0: install v2 `verify_all.py`; save `verify_start.txt`; add D-015 to D-020.
3. Gate A9: V2 first (time-sensitive), then V1, V3, V4, V5, V6, V7, V8; commit `phase9-gate-a`.
4. Commit `phases/Phase 9/preregistration.md` (grounding tolerance, validation rules, UI contents, wording rules, cost caps) as `phase9-preregistration`.
5. Workstreams A, B, C, D, E (one commit each).
6. Run `verify_all.py`, pytest; save `verify_end.txt`.
7. Write `2_building_and_execution.md` and `3_outcome_and_verdict.md` (Section 12); update `DEFECTS.md`; attach the self-audit.

## 12. Required Structure of `3_outcome_and_verdict.md`
1. **Targets missed and unfixed items** ("None" only if `DEFECTS.md` has no OPEN or PARTIAL rows; `verify_all.py` checks this).
2. **Defect Ledger** (opened, fixed, carried over, regressed).
3. Gate A9 table with evidence; Phase 8 re-check results.
4. Research agent results: runs, share of fields grounded, failures, cost.
5. Interface walkthrough: which result-page elements exist (with screenshots saved in the phase folder).
6. Learning-loop status: promotions made, challenger report, what needs your approval.
7. Honest verdict, hypotheses labelled, failure modes, Phase 10 recommendations (tail handling, calibration, interval width).
8. Statement: decision aid only, not financial advice.

## 13. Self-Audit (yes/no with evidence)
- Does any `FIXED` lack a passing test or pasted command?
- Does `verify_all.py` pass with 0 FAIL on a fresh clone?
- Was any earlier-phase artifact modified? Was `verify_all.py` edited to pass? (must be no)
- Does every collected value have URL, page date, access date and a code-saved snapshot that contains it?
- Can the LLM fill any field without the grounding check? (must be no)
- Does any log timestamp differ from the commit time by more than the tolerance?
- Does the UI ever show "apply/avoid" language or an unlabelled number?
- Does any code path promote a model or retrain automatically? (must be no)
- Was `data/ipo_phase5_final_test.csv` read for any decision? (must be no)
