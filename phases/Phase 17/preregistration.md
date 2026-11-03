# Phase 17: Preregistration of Market Evidence Automation, Visible Verification, Honest Statuses, and Named Failures

> Committed prior to any Workstream implementation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 17/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Epistemic Statement**: This project is a quantitative research decision aid, not financial, trading, or investment advice. Sample size is $n = 9$ listed of 30 target forward predictions (4 unlisted pending). All forward error distributions and headline metrics remain provisional and descriptive. No statistical superiority claims ("beats GMP", "unbeatable", "proven edge") are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## 1. Market Evidence Ingestion Rule (D-085)

1. **Automated Evidence Persistence**:
   - For every listed IPO whose outcome is recorded (and for every historical listing date still lacking market evidence), the daily workflow automatically fetches Nifty 50 and India VIX historical data via `opi/market.py`.
   - The raw HTTP/API response is saved verbatim to `data/evidence/market/<listing_date>_nifty.raw`.
   - The parsed JSON structure containing `listing_date`, `nifty_close`, `nifty_prev_close`, `nifty_1d_return_pct`, and `india_vix` is saved to `data/evidence/market/<listing_date>_nifty.json`.
2. **Strict Operational Constraints**:
   - **Never Created by Hand**: No market evidence file may ever be manually authored or saved from a local computer. All production evidence is written by scheduled or dispatched GitHub Actions cloud workflows.
   - **Never Overwritten**: If `<listing_date>_nifty.{raw,json}` already exists, the job must never overwrite or mutate the file.
   - **Never Guessed or Typed**: If market data for a date is unavailable from yfinance (e.g. trading holiday, API downtime), the job logs `MARKET_EVIDENCE SKIPPED_<reason>` and retries on subsequent runs.
   - **No Circular Mocking**: Test fixtures must reside exclusively under `tests/fixtures/` and be explicitly marked synthetic.

---

## 2. Visible Verification Guardrails (D-086)

1. **Continuous Verification Execution**:
   - `scripts/verify_extra.py` is integrated into `scripts/watchdog.py` as an automated daily health check.
   - Any non-zero exit from `verify_extra.py` triggers an alert issue (or adds a comment to an open issue) detailing each failing check line.
   - `scripts/ci_local.py` runs `scripts/verify_extra.py` and prints its summary.
2. **Non-Blocking Ingestion**:
   - `verify_extra.py` failures alert the repository maintainers but do **NOT** block the daily collection pipeline (`opi.run_daily`).
   - Data collection for incoming IPOs and listing day outcomes must proceed uninterrupted regardless of audit report warnings.

---

## 3. Retraining PR Verification Standard (D-087, D-083)

1. **Governance & Permission Proof**:
   - Defect D-083 / D-087 cannot be marked `FIXED` solely from unit test assertions.
   - Marking `FIXED` requires a verified green cloud workflow execution on `main` that successfully opened an automated Pull Request via GitHub Actions without personal access tokens.
   - The workflow `monthly_retrain.yml` catches permission failures during `gh pr create` and alerts the user naming the exact setting:
     `Settings -> Actions -> General -> Workflow permissions -> Allow GitHub Actions to create and approve pull requests`.
   - The champion model file `model/ipo_model.joblib` remains strictly immutable in automated retraining; automated merging is strictly prohibited.

---

## 4. Report & Verification Output Consistency Standard (D-088)

1. **Verbatim Output Matching**:
   - Every verification summary quoted in markdown documentation beside an output file (`verify_start.txt`, `verify_extra_start.txt`, `verify_end.txt`, `verify_extra_end.txt`) must equal the exact `SUMMARY: N pass, N warn, N fail` line of that file.
   - Automated regression test `tests/test_reporting.py::test_quoted_verify_results_match_saved_files` enforces this consistency across all phases (Phase 14 through Phase 17).
2. **Prior Phase Errata Policy**:
   - Discrepancies or misquoted lines in prior phase deliverables are corrected exclusively via a top `## ERRATA` section.
   - Historical text and logs below the ERRATA heading remain immutable snapshots.
3. **Register Alignment (D-089)**:
   - Defect counts in reporting tools and dashboard cards must reflect all non-closed states: `OPEN`, `PARTIAL`, and `NOT FIXED`.

---

## 5. Daily Alert Precision Specification (D-091)

1. **Granular Step Identification**:
   - Every step in `daily.yml` has a distinct identifier.
   - On step failure, the alert generation job receives the name of the failing step and the sanitized tail (last 40 lines) of its console output.
   - Alert issue title format: `Daily run failed: <run_id> (<failed_step>)`.
   - Generic "Execution" step titles without log context are prohibited.
2. **Secret Sanitization**:
   - The alert body and all log excerpts are scrubbed for sensitive patterns.
   - `OPENROUTER_API_KEY` and raw bearer tokens must never appear in any issue, log, or commit. Pre-push scan `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` must return 0 lines.

---

## 6. Small-Sample Epistemic Rules

1. **Provisional Sample Accounting ($n < 30$)**:
   - The prospective target remains $n = 30$ verified listings.
   - Current sample count is $n = 9$ listed ($n = 8$ with GMP, 4 pending unlisted).
   - All evaluation metrics are purely descriptive. Claims of statistical edge or model superiority are forbidden until $n \ge 30$.
