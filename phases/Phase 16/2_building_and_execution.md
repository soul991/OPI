# Phase 16: Building & Execution Log

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Final Status**: All Phase 16 deliverables complete across Gate A16, Task 0 (Bombay Coated & Special Steels), Workstreams A, B, C, and D, pull request merge (PR #10), run failure triage and resolution, and cloud automated verification.

---

## 1. Summary of Workstreams & Milestones

Phase 16 establishes pre-listing prediction visibility, deterministic automated Grey Market Premium (GMP) discovery, research agent integration into daily scoring pipelines, coverage alerting for closed unlisted IPOs, and pull request reporting for monthly retraining models:

1. **Gate A16 Re-Verification & Preregistration**:
   - Initial verification baselines captured on `main`:
     - `phases/Phase 16/verify_start.txt`: 71 pass, 0 warn, 0 fail.
     - `phases/Phase 16/verify_extra_start.txt`: 7 pass, 0 warn, 0 fail.
     - `scripts/ci_local.py`: `CI_LOCAL: PASS`.
   - Gate audits completed:
     - **G1**: 10 sampled Phase 15 claims evaluated with seed 16 in `phases/Phase 16/prior_phase_recheck.csv` (6 specific IPO numbers, 4 file-content checks) – 100% verified. 5 headline metrics recomputed from raw data (`model_mae_8` = 5.99 pp, `gmp_mae_7` = 6.15 pp, `model_mae_with_gmp_7` = 6.67 pp, `model_mae_no_outlier_7` = 3.83 pp, `master_rows` = 731).
     - **G2**: Defect regression tests verified; regression test coverage validated for all FIXED defects D-066 through D-078.
     - **G3**: Audited 10 scheduled runs in `phases/Phase 16/actions_status.md`. All commits mapped to defect IDs.
     - **G4**: Effective outcomes from `opi/outcomes.py` printed alongside raw log values, proving raw `predictions/prediction_log.csv` is completely immutable.
     - **G5**: Secret hygiene confirmed (`gh secret list` shows `OPENROUTER_API_KEY`; `git grep sk-or-` returned 0 matches across the repository).
     - **G6**: Audited the four 2026-11-01 automatically scored rows (M.K.Sons, BLS Polymers, SFC Environmental, EAAA India Alternatives). Verified `scored_at` before listing dates, final subscriptions grounded in snapshots, and identified missing GMP due to lack of aggregator page discovery.
     - **G7**: Verified status of Bombay Coated & Special Steels: bidding open through 2026-11-02 17:00 IST; scheduled listing 2026-11-05; not yet logged.
   - Committed on `main`: `phase16-gate-a` (`56720f8`) and `phase16-preregistration` (`bed06da`).
   - Feature branch `feat/phase16-workstreams` created.

2. **Task 0: Bombay Coated & Special Steels Pre-Listing Scoring**:
   - Monitored bidding window: closed 2026-11-02 17:00 IST.
   - Identified Chittorgarh overview (`/ipo/bombay-coated-and-special-steels-ipo/2671/`) and subscription page (`/ipo_subscription/bombay-coated-and-special-steels-ipo/2671/`).
   - Automatically scored post-bidding close on 2026-11-02 20:23:48 IST, well before its listing date on 2026-11-05.
   - Grounded inputs:
     - Issue Price: ₹82.00
     - Issue Size: ₹183.00 Cr
     - Lot Size: 182
     - Final Subscription: 27.00x Total (QIB: 10.54x, NII: 69.35x, Retail: 18.46x)
     - Aggregator GMP discovered deterministically: ₹9.25 (11.28%) as of `2-Nov 18:02` from `https://www.investorgain.com/gmp/bombay-coated-and-special-steels-ipo/1936/`
   - Model Prediction: Gain +10.14%, Platt calibrated probability P(gain > 10%): 0.544.
   - Feature snapshot and evidence saved under `data/evidence/`; appended to `predictions/prediction_log.csv` as row 18 (13th genuine FORWARD row).

3. **Workstream A: Pre-Listing Predictions List & Discovery Hardening (D-079, D-077, D-078)**:
   - Added `get_pre_listing_data()` to `opi/report.py` to segregate pending prospective IPOs (listing date >= today and actual is null) from historical listed results.
   - Added active bidding table for newly discovered candidate IPOs in `BIDDING_OPEN` state, clearly stating "Bidding open: scored after close on <close_date>".
   - Integrated "Pre-listing predictions (awaiting listing)" section into `dashboard/index.html` with explicit "model-only regime" notes for unanchored IPOs.
   - Implemented automated generation of `predictions/pre_listing_predictions.md` via daily runner.
   - Committed on branch: `fcdbdf3`.

4. **Workstream B: Deterministic GMP Discovery & Robust Parsing (D-081)**:
   - Created `opi/gmp.py` providing `discover_gmp_url_from_list_page()` and `fetch_and_parse_gmp()`:
     - Fetches live table from `https://www.investorgain.com/report/live-ipo-gmp/331/`.
     - Normalizes company names (strips suffixes, standardizes punctuation and whitespace) to match candidate IPOs with zero false positives.
     - Saves raw HTTP evidence with SHA256 hashes to `data/evidence/gmp/`.
   - Updated `opi/ingest.py` date parser to handle unpadded single-digit day strings (`2-Nov 18:02`) without throwing parsing exceptions.
   - Added comprehensive tests in `tests/test_gmp_discovery.py`.
   - Committed on branch: `bf631ff`.

5. **Workstream C: Research Agent Daily Integration & Safety Bounds (D-082)**:
   - Wired `opi.research_agent.execute_research_run` into `scripts/score_ipo.py` to fill unparsed features (e.g., sector, debt/equity, P/E ratio).
   - Enforced budget bounds: maximum 6 tool calls, 8,000 tokens per execution.
   - Enforced strict verbatim-quote grounding verification: any extracted fact lacking a literal substring match in saved local HTML snapshots is rejected.
   - Added detailed invocation telemetry to `predictions/run_log.csv` (provider, model ID, requests, tokens, proposed fields, grounded fields, grounding rate).
   - Added unit tests with mocked responses in `tests/test_daily_agent.py`.
   - Committed on branch: `3518339`.

6. **Workstream D: Monthly Retraining PRs, Coverage Watchdog, and Nov 1 Audit (D-080, D-083, D-084)**:
   - Enhanced `.github/workflows/monthly_retrain.yml`: executes `scripts/promote_forward_rows.py --apply`, generates challenger evaluation report in `docs/`, commits to an automated branch, and opens a pull request against `main`.
   - Updated `phases/Phase 13/3_outcome_and_verdict.md` with an ERRATA header correcting historical claims regarding automated PR creation.
   - Implemented `check_closed_ipo_coverage()` in `scripts/watchdog.py`: detects closed unlisted IPOs approaching listing within 2 days that lack forward predictions, records unlogged listings as `MISSED_FORWARD` in `predictions/missed_forward.csv`, and alerts maintainers via GitHub Issues.
   - Added regression test `tests/test_discover_listed.py::test_nov1_scored_rows_audit_and_provenance` verifying provenance and final subscription figures for the 2026-11-01 batch.
   - Committed on branch: `5a1e9f0`.

7. **Pull Request Merge & Hotfix Triage**:
   - Opened PR #10: `Phase 16: Pre-listing predictions, GMP discovery, daily agent, retraining PR, coverage alerts`.
   - User merged PR #10 into `main` (`31c5739`).
   - Addressed run failure email for GitHub Actions run `41463708776`: User commit `25bcd4b` pushed to `main` introduced a 7-space IndentationError on line 202 of `scripts/verify_all.py` (`       openish = ...`). The merge of PR #10 cleanly replaced this with 4 spaces, eliminating the error.
   - Dispatched cloud workflow run `41466028853` on `main`: completed 100% green (5m30s), scored Bombay Coated & Special Steels, and committed row 18 (`94c863f`).

---

## 2. Scripts & Workflows Created / Modified

- `opi/discover.py`: Added `sub_url` derivation from `overview_url` (`/ipo/` to `/ipo_subscription/`) and company name normalization.
- `opi/gmp.py`: Added deterministic list-page discovery (`discover_gmp_url_from_list_page`) and GMP parsing with snapshot caching.
- `opi/ingest.py`: Hardened date parser to handle unpadded dates and flexible timestamp strings.
- `opi/report.py`: Added pre-listing predictions dataset generation and table formatting.
- `scripts/score_ipo.py`: Integrated research agent fallback for ungrounded fields with verbatim quote validation and audit logging.
- `scripts/watchdog.py`: Added `check_closed_ipo_coverage()` and `predictions/missed_forward.csv` tracking for unlogged IPOs.
- `scripts/promote_forward_rows.py`: Added effective outcome promotion with `--apply` support and duplicate prevention.
- `.github/workflows/monthly_retrain.yml`: Configured promotion, evaluation, branch creation, and PR opening.
- `dashboard/index.html`: Added pre-listing predictions table, active bidding table, and updated defect counts.
- `predictions/pre_listing_predictions.md`: Auto-generated markdown list of awaiting and bidding-open IPOs.
- `predictions/missed_forward.csv`: Append-only register for tracking missed prospective opportunities.
- `phases/Phase 13/3_outcome_and_verdict.md`: Added ERRATA header correcting pull request workflow claim.
- `DEFECTS.md`: Registered defects D-079 through D-084; marked D-079, D-080, D-081, D-082, D-083, and D-084 as `FIXED`.
- `tests/test_pre_listing.py`: Unit tests for pre-listing prediction table rendering and filtering.
- `tests/test_gmp_discovery.py`: Unit tests for deterministic aggregator scraping and date handling.
- `tests/test_daily_agent.py`: Unit tests for research agent invocation, grounding verification, and safety fallbacks.
- `tests/test_retraining.py`: Unit tests for monthly retraining workflow and PR creation logic.
- `tests/test_discover_listed.py`: Added regression test for Nov 1 scored batch provenance and snapshot integrity.

---

## 3. Verification Suite Outputs

### `scripts/verify_all.py` Output (`phases/Phase 16/verify_end.txt`)

```text
[PASS] no absolute/local paths in docs or code                                              
[PASS] pytest suite passes                                                                  219 passed, 1 skipped, 3 warnings in 77.24s (0:01:17)
[PASS] no duplicate (company, listing_date)                                                 0 duplicates
[PASS] listing_gain_pct matches prices                                                      0 mismatches
[PASS] label_good matches gain                                                              0 mismatches
[PASS] date order open<=close<=listing                                                      0 rows
[PASS] no extreme listing/issue price ratios (FPO-type errors)                              
[PASS] gmp_pct in plausible range                                                           0 rows
[PASS] every excluded row has a source URL                                                  0 without URL
[PASS] every GMP value has URL, page date, access date                                      0 rows incomplete
[PASS] every sourced GMP row exists in master                                               0 unmatched
[PASS] GMP as_of_date not after last bidding day (no leakage)                               0 rows
[PASS] source page dated before listing                                                     0 rows dated on/after listing
[PASS] second-source check credible (Phase 7)                                               
[PASS] second-source check credible (Phase 8)                                               
[PASS] snapshot file for every sourced GMP row (<listing_date>_<company-slug>.*)            0 of 0 missing
[PASS] log statuses valid                                                                   0 invalid
[PASS] FORWARD rows logged                                                                  13 rows
[PASS] FORWARD rows scored before listing                                                   0 rows
[PASS] FORWARD rows scored after bidding closed (final subscription)                        
[PASS] FORWARD rows use final (not day-1/live) subscription                                 
[PASS] probabilities within [0,1]                                                           
[PASS] no duplicate FORWARD rows                                                            0
[PASS] FORWARD scored_at matches first commit time (no backdating)                          
[PASS] no actuals for unlisted IPOs                                                         
[PASS] FORWARD feature snapshots carry source URLs                                          0 rows with only site names
[PASS] final test rows <= FORWARD rows with actuals                                         0 rows vs 8
[PASS] Phase 1: three required files                                                        
[PASS] Phase 2: three required files                                                        
[PASS] Phase 3: three required files                                                        
[PASS] Phase 4: three required files                                                        
[PASS] Phase 5: three required files                                                        
[PASS] Phase 6: three required files                                                        
[PASS] Phase 7: three required files                                                        
[PASS] Phase 8: three required files                                                        
[PASS] Phase 9: three required files                                                        
[PASS] Phase 10: three required files                                                       
[PASS] Phase 11: three required files                                                       
[PASS] Phase 12: three required files                                                       
[PASS] Phase 13: three required files                                                       
[PASS] Phase 14: three required files                                                       
[PASS] Phase 15: three required files                                                       
[PASS] Phase 16: three required files                                                       
[PASS] defect register parsed                                                               84 defects, 3 open/partial
[PASS] every FIXED defect has an existing regression test                                   
[PASS] Phase 16 verdict 'None unfixed' consistent with defect register                      
[PASS] Phase 6: gate + preregistration committed before other work                          
[PASS] Phase 7: gate + preregistration committed before other work                          
[PASS] Phase 8: gate + preregistration committed before other work                          
[PASS] Phase 9: gate + preregistration committed before other work                          
[PASS] Phase 10: gate + preregistration committed before other work                         
[PASS] Phase 11: gate + preregistration committed before other work                         
[PASS] Phase 12: gate + preregistration committed before other work                         
[PASS] Phase 13: gate + preregistration committed before other work                         
[PASS] Phase 14: gate + preregistration committed before other work                         
[PASS] Phase 15: gate + preregistration committed before other work                         
[PASS] Phase 16: gate + preregistration committed before other work                         
[PASS] Phase 7 headline metrics recompute from raw predictions                              
[PASS] CI can obtain the model (tracked artifact or training step)                          
[PASS] earlier-phase artifacts unchanged since phase16-gate-a (errata may only add lines)   
[PASS] extreme GMP values (>100% or <-30%) have a snapshot or are NOT_RECORDED              
[PASS] no mock research runs in data/research_runs                                          
[PASS] no mock evidence files under data/evidence/                                          
[PASS] grounding: HD Fire Protect Limited inputs appear in saved snapshots                  4 snapshot files
[PASS] grounding: Fusion CX Limited inputs appear in saved snapshots                        4 snapshot files
[PASS] grounding: Zetwerk Manufacturing Business Limited inputs appear in saved snapshots   5 snapshot files
[PASS] grounding: Sahajanand Medical Technologies Limited inputs appear in saved snapshots  5 snapshot files
[PASS] grounding: Tonbo Imaging India Limited inputs appear in saved snapshots              5 snapshot files
[PASS] grounding: Bonfiglioli Transmissions Limited inputs appear in saved snapshots        5 snapshot files
[PASS] grounding: Jio Platforms Limited inputs appear in saved snapshots                    5 snapshot files
[PASS] grounding: Paras Healthcare Limited inputs appear in saved snapshots                 9 snapshot files
[PASS] grounding: M.K.Sons Fine Jewels inputs appear in saved snapshots                     2 snapshot files
[PASS] grounding: BLS Polymers inputs appear in saved snapshots                             2 snapshot files
[PASS] grounding: SFC Environmental Technologies inputs appear in saved snapshots           2 snapshot files
[PASS] grounding: EAAA India Alternatives inputs appear in saved snapshots                  2 snapshot files
[PASS] grounding: Bombay Coated & Special Steels inputs appear in saved snapshots           3 snapshot files
[PASS] pytest passes on a fresh clone (no untracked/ignored files)                          219 passed, 1 skipped, 4 warnings in 90.72s (0:01:30)

SUMMARY: 77 pass, 0 warn, 0 fail
```

### `scripts/verify_extra.py` Output (`phases/Phase 16/verify_extra_end.txt`)

```text
[PASS] subscription figures in Phase 11+ reports equal prediction_log values                    0 mismatches
[PASS] no company other than HD Fire cites BSE code 544994                                      0 lines
[PASS] no hard-coded dated numeric constants in scripts/ or opi/                                0 lines
[PASS] each listed date has a parsed Nifty evidence file (close + prev close or day return)     missing: none
[PASS] no 'weak/only/subdued demand' text for IPOs with QIB > 50x                               0 lines
[PASS] README's two champion coverage figures (91.2% vs 87.94%) are reconciled in text          
[PASS] no OpenRouter key material in tracked files                                              

SUMMARY: 7 pass, 0 warn, 0 fail
```

### `scripts/ci_local.py` Last Output Line

```text
CI_LOCAL: PASS
```
