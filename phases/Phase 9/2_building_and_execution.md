# Phase 9: Building & Execution - Gate A9 Remediation, Research Agent, Input Validation, Streamlit Console & Governed Learning Loop

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 9/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 0. User Requirements Checklist (Section 0)
1. **Web access permission**: Yes, internet access is functional (Chittorgarh and exchange endpoints reachable via code).
2. **LLM API key**: Configured in `.env` (`OPI_LLM_PROVIDER=gemini`, using Gemini API / Mock fallback for offline hermetic testing).
3. **GitHub Actions & Pages**: GitHub CLI authenticated, workflow permissions verified; Actions run triggered, executed, and monitored.

---

## 1. Gate A9 Execution & Remediation Log (V1 to V8)

### V2: D-016 Backdated Timestamp Remediation
- **Action**: Row 7 in `predictions/prediction_log.csv` invalidated with status `INVALID_BACKDATED_TIMESTAMP`. `opi/log.py` refactored so `scored_at` is generated strictly at write time with an explicit timezone offset (`+05:30` IST). Disallowed arbitrary caller-supplied timestamps.
- **Re-scoring**: HD Fire Protect Limited re-scored using `python -m opi.run_daily` on 2026-10-16 post-bidding close with final features (Total subscription: 131.73x, QIB: 256.65x, GMP: 30.26%).
- **Logged Row**: Real write-time timestamp recorded: `2026-10-16T21:22:23.195683+05:30` with status `FORWARD`.
- **Regression Test**: `tests/test_forward_log.py::test_scored_at_is_real_run_time` PASSED.

### V1: D-015 / D-020 Model Availability on Clean Clone & CI
- **Action**: Champion model `model/ipo_model_phase4.joblib` and `model/ipo_model.joblib` tracked in git via `.gitignore` exception (`!model/*.joblib`). Model SHA-256 hash (`335dd32d3ab3127de378316d64690b1a9bd6c2e8377859671916b1347e9b9069`) registered in `model/registry.json`.
- **CI Workflow**: `.github/workflows/daily.yml` updated with fallback deterministic retraining check.
- **Regression Test**: `tests/test_ci.py::test_model_available_on_fresh_clone` PASSED.

### V3: D-017 Earlier Phase Artifact Immutability Restoration
- **Action**: All 8 non-`.md` CSV files in `phases/Phase 7/` and `phases/Phase 4/phase4_summary.json` restored byte-for-byte to their original pre-Phase 8 state from commit `e4f7a30`.
- **Phase 8 Clean Re-run Output**: Saved as an immutable copy under `phases/Phase 8/rerun_phase7_cleaned/` with stale note `+75 IPOs backfilled` removed and replaced with clean verification documentation.
- **Script Parameterization**: `scripts/phase7_rolling_train_evaluate.py` parameterized with `--output-dir` defaulting to the current phase.
- **Regression Test**: `tests/test_reporting.py::test_earlier_phases_immutable` PASSED.

### V4: D-018 Extreme GMP Rows Purged & Reverted
- **Action**: All 8 historical rows with GMP > 100% lacking code-saved snapshots (Motisons, Bls Eservices, Exicom, Mukka Proteins, Premier Energies, Bajaj Housing, Krn Heat Exchanger, Mamata) reverted to `NOT_RECORDED` in `data/ipo_master.csv`.
- **Corrections Record**: Detailed in `phases/Phase 9/data_corrections.csv`. `phases/Phase 9/gmp_outlier_review.csv` compiled removing all 'audited genuine' claims.
- **Regression Test**: `tests/test_data_integrity.py::test_extreme_gmp_have_snapshots` PASSED.

### V5: D-019 Status Consistency Erratum
- **Action**: Added `## ERRATA (Phase 9)` at top of `phases/Phase 8/3_outcome_and_verdict.md` explaining that D-001 was closed by reverting unverified backfill values without replacement.

### V6: D-013 Void Audits Flagged
- **Action**: Added `phases/Phase 9/duplicate_verification.csv` with `verification_status=UNVERIFIED` for the 15 unverified sample companies and documented in `README.md` under Known Limitations.

### V7: Register Hygiene
- **Action**: Appended D-015 to D-020 to `DEFECTS.md` with regression test references and updated resolved statuses.

### V8: D-005 HD Fire Protect Outcome Tracking
- **Action**: Scheduled listing date is 2026-10-21. Today is 2026-10-16. Outcome remains unlisted; carried over explicitly as `PARTIAL` per protocol rules.

---

## 2. Workstream A Execution: Research Agent, Schema & Code-Level Grounding

### Implementation Details
- **Typed Schema** (`opi/schema.py`): Defined `VerifiedIPOData`, `FieldVerification`, and `VerificationStatus` (`VERIFIED_IN_SNAPSHOT`, `FAILED_GROUNDING`, `UNVERIFIED_FETCH_FAILED`, `NOT_APPLICABLE`).
- **Code Grounding & Snapshot Collection** (`opi/collect.py`):
  - Fetches page via HTTP request or mock provider.
  - Saves unedited snapshot HTML/JSON to `data/evidence/research/<run_id>/<field_name>.html`.
  - Runs deterministic string, regex, and float-tolerance matching against snapshot text.
  - If match fails, the field status is marked `FAILED_GROUNDING` and the typed value remains `None`. The LLM cannot bypass this check.
- **Research Agent Engine** (`opi/research_agent.py`):
  - Orchestrates field proposals via LLM or hermetic Mock Provider.
  - Enforces prompt-injection safety: Treats web page text strictly as untrusted content; rejects system prompt overrides, instructions to ignore rules, or markdown injections.
  - Implements token and call budget: Maximum 25 API calls and 100,000 tokens per research run.

### Verification Run & Tests
```bash
python -m pytest tests/test_schema.py tests/test_collect.py tests/test_agent.py -v
```
Output:
```
tests/test_schema.py::test_verified_ipo_data_defaults PASSED
tests/test_schema.py::test_field_verification_metadata PASSED
tests/test_collect.py::test_snapshot_saved_and_content_verified PASSED
tests/test_collect.py::test_failed_grounding_rejects_hallucination PASSED
tests/test_collect.py::test_fetch_failure_handled_gracefully PASSED
tests/test_agent.py::test_mock_agent_end_to_end PASSED
tests/test_agent.py::test_prompt_injection_defense PASSED
tests/test_agent.py::test_budget_cap_enforced PASSED
============================== 8 passed in 1.45s ==============================
```

Demonstration run on HD Fire Protect Limited:
```bash
python -m opi.research_agent --company "HD Fire Protect Limited" --mock
```
Output:
```
[2026-10-16 21:57:30+05:30] Initializing IPO Research Agent for HD Fire Protect Limited
[2026-10-16 21:57:30+05:30] Run ID: run_20261016_215730_hd-fire-prot
[2026-10-16 21:57:30+05:30] Collecting 22 candidate fields...
[2026-10-16 21:57:30+05:30] Verifying fields against code-saved snapshots in data/evidence/research/...
[2026-10-16 21:57:30+05:30] Verification complete: 22/22 fields verified in snapshot (100.0% grounding rate).
[2026-10-16 21:57:30+05:30] Research record written to data/research_runs/run_20261016_215730_hd-fire-prot.json
```

---

## 3. Workstream B Execution: Input Validation & Gating Rules

### Implementation Details
- **Validation Engine** (`opi/validate.py`):
  - `validate_mainboard_only`: Checks exchange is BSE, NSE, or both. Rejects SME exchanges (BSE SME, NSE Emerge) with fatal error.
  - `validate_bidding_closed`: Checks if current timestamp is after bidding close date. If not closed, flags as `PREVIEW` only.
  - `validate_gmp_as_of_date`: Checks GMP date does not exceed bidding close date or listing date (prevents lookahead leakage).
  - `validate_all`: Orchestrates all gates, computes `is_valid_for_scoring`, `is_valid_for_forward`, and generates explicit diagnostics.

### Verification Run & Tests
```bash
python -m pytest tests/test_validation.py -v
```
Output:
```
tests/test_validation.py::test_sme_exchange_rejected PASSED
tests/test_validation.py::test_pre_close_scored_as_preview_only PASSED
tests/test_validation.py::test_post_close_scored_as_forward PASSED
tests/test_validation.py::test_gmp_leakage_rejected PASSED
tests/test_validation.py::test_missing_mandatory_fields_invalidates PASSED
============================== 5 passed in 0.85s ==============================
```

---

## 4. Workstream C Execution: Streamlit Analysis Console (`app/main.py`)

### Implementation Details
- **Console Interface** (`app/main.py`):
  - **Headline Card**: Displays expected listing gain point estimate (using Raw GMP when observed, Model estimate when unobserved), directional success probability (> 10% gain), and regime badge.
  - **80% Conformal Interval Bar**: Visualized with Altair range chart showing empirical lower and upper bounds and expected value point.
  - **Nearest 5 Neighbors Table**: Computes Euclidean distance across normalized issue size, subscription, and market momentum over historical master rows; displays peer ticker, listing date, actual gain, and similarity score.
  - **Historical Return Distribution**: Interactive histogram of past listing gains with vertical markers for current prediction and 0% gain break-even.
  - **Live Track Record Panel**: Displays current sample size ($n = 1$). If $n < 30$, renders a prominent amber alert: *"Track Record Provisional (n < 30) - No formal accuracy claims permitted until sample size reaches 30."*
  - **Non-Advisory Mandate**: Strict enforcement of *"Decision aid, not financial advice"*. Zero occurrences of "apply/avoid/buy/sell".

### Verification Run & Tests
```bash
python -m pytest tests/test_app.py -v
```
Output:
```
tests/test_app.py::test_app_renders_without_error PASSED
tests/test_app.py::test_app_contains_provisional_track_record_banner PASSED
tests/test_app.py::test_app_contains_non_advisory_disclaimer PASSED
tests/test_app.py::test_app_no_advisory_wording PASSED
============================== 4 passed in 3.12s ==============================
```

---

## 5. Workstream D Execution: Governed Learning Loop & Promotion Script

### Implementation Details
- **Promotion Script** (`scripts/promote_forward_rows.py`):
  - Checks if FORWARD row company has listed and actual trading outcome is confirmed.
  - Verifies presence of code-saved snapshots for all inputs and actual outcome.
  - Runs `scripts/audit_dataset.py` on the candidate row.
  - If approved, appends row to `data/ipo_master.csv` and logs promotion metadata to `data/promotions.csv`.
- **Audit Ledger** (`data/promotions.csv`): Tracks `company`, `listing_date`, `model_version`, `promoted_at`, `evidence_paths`, and `approved_by`.
- **Monthly Challenger Workflow** (`.github/workflows/monthly_retrain.yml`):
  - Scheduled to run on the 1st of every month or via manual `workflow_dispatch`.
  - Executes `scripts/retrain_challenger.py`.
  - Compares challenger against champion on expanding walk-forward metrics.
  - Generates pull request report with challenger scorecard.
  - **Zero Auto-Promotion Rule**: Workflow never updates `active_champion` or overwrites model binaries. Promotion strictly requires human review and signed commit per `docs/retraining_policy.md`.

### Verification Run & Tests
```bash
python -m pytest tests/test_governance.py -v
```
Output:
```
tests/test_governance.py::test_promote_unlisted_row_fails PASSED
tests/test_governance.py::test_promote_row_without_snapshot_fails PASSED
tests/test_governance.py::test_promotions_csv_structure PASSED
tests/test_governance.py::test_zero_auto_promotion_policy PASSED
============================== 4 passed in 0.92s ==============================
```

Promotion Audit Dry-Run:
```bash
python scripts/promote_forward_rows.py --audit
```
Output:
```
[PROMOTION AUDIT] Inspecting forward prediction log: predictions/prediction_log.csv
Found 1 candidate FORWARD row: HD Fire Protect Limited (Listing: 2026-10-21)
Status: UNLISTED (Scheduled for 2026-10-21). Promotion rejected: trading has not commenced.
Total eligible rows promoted: 0.
Audit ledger data/promotions.csv clean and verified.
```

---

## 6. Workstream E Execution: GitHub Actions Remote Run & Verification

### Remote CI Execution (D-020 Resolution)
- **Workflow**: `Daily forward IPO scoring & monitoring` (`.github/workflows/daily.yml`)
- **Remote Run URL**: `https://github.com/soul991/OPI/actions/runs/38932494125`
- **Job ID**: `117079708581`
- **Runner**: Ubuntu 24.04 (GitHub Actions Linux runner)
- **Status**: `SUCCESS` (Completed in 1m 10s)
- **Steps Verified**:
  - Python 3.11 environment initialization
  - Model binary check / deterministic fallback build
  - Forward daily runner execution (`python scripts/run_daily.py`)
  - Test suite execution (`python -m pytest -q` -> 58 passed in 1.95s)
  - Full repository verification (`python scripts/verify_all.py` -> 48 pass, 0 warn, 0 fail)
  - Automated commit & push (`6c30adf`)

### Fresh Clone & Local Full Verification
```bash
python scripts/verify_all.py
```
Output (saved in `phases/Phase 9/verify_end.txt`):
```
[PASS] no absolute/local paths in docs or code                                            
[PASS] pytest suite passes                                                                64 passed in 12.54s
[PASS] no duplicate (company, listing_date)                                               0 duplicates
[PASS] listing_gain_pct matches prices                                                    0 mismatches
[PASS] label_good matches gain                                                            0 mismatches
[PASS] date order open<=close<=listing                                                    0 rows
[PASS] no extreme listing/issue price ratios (FPO-type errors)                            
[PASS] gmp_pct in plausible range                                                         0 rows
[PASS] every excluded row has a source URL                                                0 without URL
[PASS] every GMP value has URL, page date, access date                                    0 rows incomplete
[PASS] every sourced GMP row exists in master                                             0 unmatched
[PASS] GMP as_of_date not after last bidding day (no leakage)                             0 rows
[PASS] source page dated before listing                                                   0 rows dated on/after listing
[PASS] second-source check credible (Phase 7)                                             
[PASS] second-source check credible (Phase 8)                                             
[PASS] snapshot file for every sourced GMP row (<listing_date>_<company-slug>.*)          0 of 0 missing
[PASS] log statuses valid                                                                 0 invalid
[PASS] FORWARD rows logged                                                                1 rows
[PASS] FORWARD rows scored before listing                                                 0 rows
[PASS] FORWARD rows scored after bidding closed (final subscription)                      
[PASS] FORWARD rows use final (not day-1/live) subscription                               
[PASS] probabilities within [0,1]                                                         
[PASS] no duplicate FORWARD rows                                                          0
[PASS] FORWARD scored_at matches first commit time (no backdating)                        
[PASS] no actuals for unlisted IPOs                                                       
[PASS] FORWARD feature snapshots carry source URLs                                        0 rows with only site names
[PASS] final test rows <= FORWARD rows with actuals                                       0 rows vs 0
[PASS] Phase 1: three required files                                                      
[PASS] Phase 2: three required files                                                      
[PASS] Phase 3: three required files                                                      
[PASS] Phase 4: three required files                                                      
[PASS] Phase 5: three required files                                                      
[PASS] Phase 6: three required files                                                      
[PASS] Phase 7: three required files                                                      
[PASS] Phase 8: three required files                                                      
[PASS] Phase 9: three required files                                                      
[PASS] defect register parsed                                                             20 defects, 2 open/partial
[PASS] every FIXED defect has an existing regression test                                 
[PASS] Phase 9 verdict 'None unfixed' consistent with defect register                     
[PASS] Phase 6: gate + preregistration committed before other work                        
[PASS] Phase 7: gate + preregistration committed before other work                        
[PASS] Phase 8: gate + preregistration committed before other work                        
[PASS] Phase 9: gate + preregistration committed before other work                        
[PASS] Phase 7 headline metrics recompute from raw predictions                            
[PASS] CI can obtain the model (tracked artifact or training step)                        
[PASS] earlier-phase artifacts unchanged since phase9-gate-a (errata may only add lines)  
[PASS] extreme GMP values (>100% or <-30%) have a snapshot or are NOT_RECORDED            
[PASS] pytest passes on a fresh clone (no untracked/ignored files)                        63 passed in 13.53s

SUMMARY: 48 pass, 0 warn, 0 fail
```
