# Phase 21: Building and Execution

## 1. Overview and Pre-flight Verification

Phase 21 implements the automated Telegram alert and notification system for OPI, integrating real-time subscription snapshots, market listing outcomes, idempotent multi-stage dispatching, and cron scheduling via Zoho Catalyst and GitHub Actions compute.

### Pre-flight Checks (Protocol Section 6)
1. **GitHub PAT Scope Verification**: Confirmed GitHub Personal Access Token (PAT) possesses complete repository permissions (`repo`, `workflow`, `contents:write`, `pull_requests:write`, `issues:write`).
2. **Telegram Bot Identity Verification**: Invoked Telegram API `getMe` endpoint; returned authenticated bot `id: 9196287140`, `username: @xperia42_bot`.
3. **Telegram Test Delivery**: Dispatched acceptance message `"OPI setup check"` to user chat `2006803662`; delivered with HTTP 200 (`ok: true`).
4. **Zoho Catalyst Connectivity**: Connected to Zoho Catalyst organization `60093168915` (`ISTAK`), project `Project-Rainfall` (`101585000000013024`), environment `Development`, timezone `Asia/Kolkata`.

---

## 2. Gate A Verification

At the initiation of Phase 21, `scripts/verify_all.py` was executed to inspect the state left by Phase 20. Output captured in `verify_start.txt`:

```text
[PASS] no absolute/local paths in docs or code                                              
[PASS] pytest suite passes                                                                  287 passed, 1 skipped, 9 warnings in 237.71s (0:03:57)
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
[PASS] final test rows <= FORWARD rows with actuals                                         0 rows vs 13
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
[PASS] Phase 17: three required files                                                       
[PASS] Phase 18: three required files                                                       
[PASS] Phase 19: three required files                                                       
[PASS] Phase 20: three required files                                                       
[WARN] Phase 21: three required files                                                       phase in progress
[PASS] defect register parsed                                                               112 defects, 3 open/partial
[PASS] every FIXED defect has an existing regression test                                   
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
[PASS] Phase 17: gate + preregistration committed before other work                         
[PASS] Phase 18: gate + preregistration committed before other work                         
[PASS] Phase 19: gate + preregistration committed before other work                         
[PASS] Phase 20: gate + preregistration committed before other work                         
[FAIL] Phase 21: gate and preregistration commits exist                                     
[PASS] Phase 7 headline metrics recompute from raw predictions                              
[PASS] CI can obtain the model (tracked artifact or training step)                          
[WARN] earlier-phase files unchanged                                                        phase21-gate-a commit not found
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
[PASS] grounding: M.K.Sons Fine Jewels inputs appear in saved snapshots                     4 snapshot files
[PASS] grounding: BLS Polymers inputs appear in saved snapshots                             4 snapshot files
[PASS] grounding: SFC Environmental Technologies inputs appear in saved snapshots           4 snapshot files
[PASS] grounding: EAAA India Alternatives inputs appear in saved snapshots                  4 snapshot files
[PASS] grounding: Bombay Coated & Special Steels inputs appear in saved snapshots           5 snapshot files
[PASS] pytest passes on a fresh clone (no untracked/ignored files)                          287 passed, 1 skipped, 9 warnings in 129.49s (0:02:09)

SUMMARY: 83 pass, 2 warn, 1 fail
```

### Explanation of Gate A Warnings and Initial Failure
1. `[WARN] Phase 21: three required files (phase in progress)`: Expected status at the start of Phase 21 before building and verdict files are generated.
2. `[WARN] earlier-phase files unchanged (phase21-gate-a commit not found)` and `[FAIL] Phase 21: gate and preregistration commits exist`: Expected at step 0 before Gate A is committed. Resolved immediately by committing Gate A as `phase21-gate-a` (`c6c1b20`).
3. Gate A Candidate Faults Resolved:
   - **D-113**: Fixed schedule divergence between `docs/AUTOPILOT.md` (`0 9,17 * * *`) and GitHub workflows (`0 6,14 * * *` / `0 10 * * *`).
   - **D-114**: Reconciled `README.md` Section 4 forward tracking status from 6 logged/1 listed to 13 logged/13 listed with resolved actuals (MAE 5.2962 pp via `scripts/forward_mae.py`).

---

## 3. Preregistration v2 & Decision Thresholds

Preregistration v2 was committed as `phase21-preregistration-v2` (`454227d`) and approved by the user:
- **Decision Signal Hierarchy**: Observed Raw GMP is primary point estimator. ML model provides contextual bounding and calibrated probability.
- **Hurdle Threshold**: $T1 = 10.0\%$ (conservative hurdle, descriptive context from 349 historical IPOs in `data/ipo_master.csv`).
- **Marginal Band**: $[5.0\%, 10.0\%)$ on observed GMP only: delivers explicit notice `"MARGINAL: small expected gain, your call"`.
- **Model Fallback (Regime B)**: When GMP is missing, model strictly requires predicted listing gain $\ge 15.0\%$ AND calibrated probability $P(\text{gain} > 10\%) \ge 0.60$. Per user instruction, marginal band was completely excluded from the model fallback.
- **Preview Isolation**: Model estimate is explicitly labelled `"PREVIEW (live subscription, model trained on final figures)"`. Feature snapshots are saved strictly to `predictions/preview_log.csv` and never to `predictions/prediction_log.csv`.

---

## 4. Swarm Collaboration & Quality Verification

Per instructions, an autonomous swarm message board was deployed to review and evaluate every single workstream step-by-step:
- **Coordinator**: Directed workstream branches, test execution, CI sandbox runs, PR creation/merging, and secret scans.
- **Evaluator** (`46bacceb-5c30-43bb-b5f5-f0bbe29eb418`): EGM Goldfish & Superpowers Quality Auditor evaluating code against `1_planning_and_goals.md`, verifying unit tests, regression safety, defect ledger entries, and secret hygiene.
- **Monitor** (`b38e6945-5beb-4839-a61e-d59329218b3f`): Monitored board turn status and broken communication stalls.

### Swarm Evaluation Verdicts
- **WS-A**: `VERDICT: PASS (APPROVED)` (Message #3)
- **WS-B**: `VERDICT: PASS (APPROVED)` (Message #4)
- **WS-C**: `VERDICT: PASS (APPROVED)` (Message #5)
- **WS-D**: `VERDICT: PASS (APPROVED)` (Message #6)
- **WS-E**: `VERDICT: PASS (APPROVED)` (Message #12)
- **WS-F**: `VERDICT: PASS (APPROVED)` (Message #12)
- **WS-G**: `VERDICT: PASS (APPROVED)` (Message #16)

---

## 5. Workstream Implementations (WS-A through WS-G)

Every workstream was executed on an isolated Git branch, registered a defect in `DEFECTS.md`, validated in `scripts/ci_local.py`, scanned for secrets, and merged via Pull Request with squash commits.

### WS-A: Telegram Alert Sender (`opi/notify.py`)
- **Deliverable**: Telegram Bot API integration with 4096-character chunking (`split_message`), configurable timeouts (default 10s), exponential backoff retries, secret sanitization (`sanitize_text`), and `--dry-run` CLI.
- **Tests**: 12 unit tests in `tests/test_notify.py` covering mock HTTP success, retry on 500, non-retryable 400, missing tokens/chat_ids, chunking edge cases, dry-run, and caplog secret sanitization.
- **Defect**: **D-115** registered as FIXED in `DEFECTS.md`.
- **Merge**: PR #36 merged as commit `631bac2` on `main`.

### WS-B: Idempotency State Store (`opi/alert_state.py`)
- **Deliverable**: Persistent idempotency state tracker in `predictions/alerts_sent.csv` with deduplication key `(company, close_date, alert_type)`. Extended `scripts/verify_all.py` with `check_phase21_alerts()` verifying 0 duplicate keys, 0 invalid alert types, and 0 preview/alert pollution in `prediction_log.csv`.
- **Tests**: 5 unit tests in `tests/test_alert_state.py`.
- **Defect**: **D-116** registered as FIXED in `DEFECTS.md`.
- **Merge**: PR #37 merged as commit `b3a6796` on `main`.

### WS-C: Stage `announce` Runner (`opi/stage_announce.py`)
- **Deliverable**: Mainboard IPO discovery filter (skipping SME issues, `SKIPPED_ALREADY_LISTED`, and `CLOSED_UNLISTED`). Standardized announcement message formatting with required regulatory disclaimer `"Decision aid only, not financial advice."` and at-most-once delivery guarantee.
- **Tests**: 4 unit tests in `tests/test_stage_announce.py`.
- **Defect**: **D-117** registered as FIXED in `DEFECTS.md`.
- **Merge**: PR #38 merged as commit `406c22e` on `main`.

### WS-D: Stage `preview` Runner (`opi/stage_preview.py`)
- **Deliverable**: 11:45 AM IST snapshot evaluator capturing live subscription demand and timestamped GMP for IPOs closing today. Evaluates 3-regime decision rules ($T1=10\%$, marginal band $[5\%, 10\%)$, model fallback $T2=15\%$ with $P(\text{gain} > 10\%) \ge 0.60$). Ingests snapshots strictly to `predictions/preview_log.csv`. Created read-only comparison tool `scripts/preview_vs_forward.py`.
- **Tests**: 6 unit tests in `tests/test_stage_preview.py`.
- **Defect**: **D-118** registered as FIXED in `DEFECTS.md`.
- **Merge**: PR #39 merged as commit `65631ac` on `main`.

### WS-E: Stage `listing` Runner (`opi/stage_listing.py`)
- **Deliverable**: Listing day outcome delivery based strictly on verified exchange prices from the existing two-tier chain (`opi/actuals.py`). Suppresses delivery for unverified/pending outcomes. Computes per-lot profit/loss arithmetic (`(open - issue) * lot_size`) and performs pre-listing signal audit comparing listing gain against Raw GMP, Model Final, and 12 PM Preview estimates.
- **Tests**: 3 unit tests in `tests/test_stage_listing.py`.
- **Defect**: **D-119** registered as FIXED in `DEFECTS.md`.
- **Merge**: PR #40 merged as commit `cb53b32` on `main`.

### WS-F: Notification Workflow (`.github/workflows/notify.yml` & `opi/notify_run.py`)
- **Deliverable**: Unified notification CLI runner `opi/notify_run.py` supporting `--stage {announce,preview,listing}` and `--dry-run`. GitHub Actions workflow `.github/workflows/notify.yml` triggered via `workflow_dispatch` only, protected by shared concurrency group `opi-predictions-writer`, limited to `contents: write` and `issues: write` permissions, executing post-run verification, committing state files only, and providing failure alerting via Telegram + GitHub issues with automated green-run auto-closure. Harmonized `daily.yml` to shared concurrency group `opi-predictions-writer`.
- **Tests**: 5 unit tests in `tests/test_notify_run.py`.
- **Defect**: **D-120** registered as FIXED in `DEFECTS.md`.
- **Merge**: PR #41 merged as commit `bb09bad` on `main`.

### WS-G: Zoho Catalyst Serverless Function (`catalyst/opi_trigger/`)
- **Deliverable**: Python serverless trigger function `catalyst/opi_trigger/main.py` supporting Cron function, Basic I/O, Advanced I/O, and CLI invocation. Dispatches workflow_dispatch requests to GitHub Actions with `GITHUB_DISPATCH_TOKEN` (or fallback `GITHUB_PAT`). Verifies HTTP 204, performs 2 retries with exponential backoff on errors, and triggers direct emergency Telegram alerts on final failure. Secret hygiene enforced via `sanitize_text`. Created complete project structure (`catalyst.json`, `catalyst-config.json`, `requirements.txt`) and setup guide `catalyst/ENV_SETUP.md`.
- **Tests**: 9 unit tests in `tests/test_catalyst.py`.
- **Defect**: **D-121** registered as FIXED in `DEFECTS.md`.
- **Merge**: PR #42 merged as commit `026f578` on `main`.

---

## 6. Empirical Verification & Final Gate Check

At the conclusion of Phase 21, `scripts/verify_all.py` was executed across the full repository. Output captured in `verify_end.txt`:

```text
[PASS] no absolute/local paths in docs or code                                              
[PASS] pytest suite passes                                                                  333 passed, 1 skipped, 9 warnings in 138.39s (0:02:18)
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
[PASS] final test rows <= FORWARD rows with actuals                                         0 rows vs 13
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
[PASS] Phase 17: three required files                                                       
[PASS] Phase 18: three required files                                                       
[PASS] Phase 19: three required files                                                       
[PASS] Phase 20: three required files                                                       
[WARN] Phase 21: three required files                                                       phase in progress
[PASS] defect register parsed                                                               121 defects, 3 open/partial
[PASS] every FIXED defect has an existing regression test                                   
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
[PASS] Phase 17: gate + preregistration committed before other work                         
[PASS] Phase 18: gate + preregistration committed before other work                         
[PASS] Phase 19: gate + preregistration committed before other work                         
[PASS] Phase 20: gate + preregistration committed before other work                         
[PASS] Phase 21: gate + preregistration committed before other work                         
[PASS] Phase 7 headline metrics recompute from raw predictions                              
[PASS] CI can obtain the model (tracked artifact or training step)                          
[PASS] earlier-phase artifacts unchanged since phase21-gate-a (errata may only add lines)   
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
[PASS] grounding: M.K.Sons Fine Jewels inputs appear in saved snapshots                     4 snapshot files
[PASS] grounding: BLS Polymers inputs appear in saved snapshots                             4 snapshot files
[PASS] grounding: SFC Environmental Technologies inputs appear in saved snapshots           4 snapshot files
[PASS] grounding: EAAA India Alternatives inputs appear in saved snapshots                  4 snapshot files
[PASS] grounding: Bombay Coated & Special Steels inputs appear in saved snapshots           5 snapshot files
[PASS] alerts_sent.csv has no duplicate keys                                                0 duplicates
[PASS] alerts_sent.csv rows have valid alert_type                                           0 invalid
[PASS] no preview or alert row in prediction_log.csv                                        0 invalid rows
[PASS] pytest passes on a fresh clone (no untracked/ignored files)                          333 passed, 1 skipped, 9 warnings in 151.27s (0:02:31)

SUMMARY: 88 pass, 1 warn, 0 fail
```

Final verification confirms: **88 PASS, 1 WARN (Phase 21 phase in progress, resolved on commit), 0 FAIL**.
