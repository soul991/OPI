# Phase 18: Building & Execution Log

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Final Status**: All Phase 18 workstreams (A, B, C, D) completed, verified by regression tests, and audited.

---

## 1. Summary of Workstreams & Milestones

Phase 18 resolves the root cause of the daily workflow failure (Actions run `42107747479`), isolates alerting from data persistence, enables cloud Tier 2b outcome resolution, ensures market index evidence coverage for all past listing dates, and provides transparent pending-outcome reporting on the dashboard and pre-listing documentation.

### Workstream A: Alerts Never Block Data (D-095) & Failed Step Detection (D-091)
- **Problem**: When an IPO's listing outcome was overdue (> 2 days), `opi/run_daily.py` raised `RuntimeError: Overdue listing outcomes missing`, aborting the runner before the `commit_and_push` step. Consequently, genuine forward predictions, discovery updates, and dashboard refreshes were blocked. Furthermore, daily failure alerts reported a generic step name ("Execution") rather than the specific failing workflow step.
- **Implementation**:
  - In `opi/run_daily.py`: Steps 4 and 5 log `MISSING_OUTCOME_ALERT` and `COVERAGE_ALERT` to `predictions/run_log.csv` and stdout, but do not raise `RuntimeError`. Added optional parameters `log_path`, `run_log_path`, and `missed_path`.
  - In `opi/log.py`: Updated `append_run_log` to support parameter `run_log_path: Optional[Path] = None`.
  - In `scripts/watchdog.py`: Implemented `run_overdue_and_coverage_check()` and exposed it via the `--check-overdue-and-coverage` CLI flag.
  - In `.github/workflows/daily.yml`: Placed `Check overdue outcomes and coverage` (id: `check_overdue_outcomes_and_coverage`) strictly after `Commit and push changes`. Updated `alert_on_failure` step detection to record step name explicitly.
- **Verification**: `tests/test_watchdog.py::test_missing_outcomes_alert_does_not_block_run_daily` and `tests/test_alerts.py::test_daily_alert_includes_failed_step_name_and_trace`.
- **Cloud Proof**:
  - Merged to `main` via PR #19 (`63cb6d0`).
  - Dispatched `daily.yml` with `force_fail=true` (Run ID: `42207678334`). Issue #18 comment 1 confirmed:
    `- **Failed Step / Component**: \`Check Forced Failure Flag\`` (accurately identifying the failing step, proving D-091).

### Workstream B: Tier 2b Cloud Verification (D-096)
- **Problem**: Tier 2b verification (requiring dual independent non-Yahoo sources with <= 1.0% tolerance) existed only as a manual procedure. Late or absent Yahoo Finance listing-day price bars left outcomes pending indefinitely.
- **Probe Grounding**: Executed `probe_sources.yml` on cloud runners (Run ID: `42190713193`). Results committed to `phases/Phase 18/source_probe_runner.md` confirmed Chittorgarh overview/quote (200 OK, 66 ms) and yfinance (200 OK) reachable, with official exchange endpoints returning 403.
- **Implementation**:
  - In `opi/log.py`: Expanded allowed evidence domains to include `groww.in` and permitted verification statuses `VERIFIED_TIER2B_DUAL_SOURCE` and `VERIFIED_TIER2B_CROSS_CHECKED`.
  - In `opi/actuals.py`: Implemented `record_actual_from_tier2b`, enforcing:
    1. Two independent non-Yahoo sources (Chittorgarh and Groww/NSE/BSE).
    2. Both sources dated on or after the listing date.
    3. Both sources naming the target company.
    4. Opening prices agreeing within <= 1.0% tolerance (`diff <= 1.0%`).
    5. Verbatim raw page manifests saved under `data/evidence/actuals/` with SHA-256 digests.
    6. Exact listing gain formula: `round(((open_price - issue_price) / issue_price) * 100, 2)`.
  - Integrated into `execute_two_tier_outcome_chain` to invoke Tier 2b when Tier 2 returns `LISTING_DAY_BAR_MISSING` or empty history and `listing_date < today_ist`.
- **Verification**: `tests/test_actuals_job.py::test_tier2b_dual_source_agreement_recorded` and `test_tier2b_divergence_beyond_tolerance_rejected`.

### Workstream C: Market Evidence for Every Listing Date (D-097)
- **Problem**: `opi/market.py::ensure_market_evidence_for_listed_dates` previously collected Nifty market index evidence only for forward rows that had already recorded `actual_gain_pct`. Listing dates with pending outcomes lacked market evidence, causing `verify_extra.py` failures.
- **Implementation**:
  - Updated `opi/market.py::ensure_market_evidence_for_listed_dates` to collect and verify Nifty evidence for all `FORWARD` rows where `listing_date <= today_ist`, regardless of whether `actual_gain_pct` is recorded.
  - Existing evidence files are never overwritten; network failures log `MARKET_EVIDENCE SKIPPED_<reason>` and retry next run.
- **Verification**: `tests/test_market_evidence_job.py::test_job_records_nifty_evidence_for_unrecorded_past_listing`.

### Workstream D: Pending-Outcome Visibility (D-098) & Symbol Resolution (D-099)
- **Problem**: When an IPO passed its listing date without a recorded outcome, the daily job gave no visibility into why it was pending; users only learned of stuck rows via alerts. Furthermore, symbol resolution failed for newly listed IPOs whose overview pages embedded symbols inside Next.js JSON or script tags (e.g. Bombay Coated: "Could not resolve NSE/BSE symbols").
- **Implementation**:
  - In `opi/actuals.py` (`resolve_company_symbols_and_urls`): Added robust regex fallbacks matching Next.js embedded JSON fields `nse_symbol`, `il_nse_script_symbol`, `bse_scripcode`, `il_bse_script_code`, handling escaped quotes. Resolves `BCSSL` for Bombay Coated.
  - In `opi/report.py`: Updated `get_pre_listing_data` to compile `listed_outcome_pending` items from `prediction_log.csv` and `run_log.csv` for past-listed unrecorded rows (`days_to_listing < 0`), capturing sanitized reason text.
  - In `predictions/pre_listing_predictions.md`: Added `## Listed, Outcome Pending` table showing Company, Listing Date, Days Since Listing, Last Logged Status, and Reason / Detail.
  - In `dashboard/index.html`: Added a dedicated `Listed, outcome pending` responsive table and card indicators.
- **Verification**: `tests/test_dashboard.py::test_dashboard_shows_pending_outcomes_table` and `tests/test_actuals_symbol_resolution.py::test_symbol_resolution_fallbacks`.

---

## 2. Modified Files & Execution Summary

- `.github/workflows/daily.yml`: Post-commit overdue check and step failure reporting.
- `opi/actuals.py`: Tier 2b dual-source engine, symbol resolution fallbacks, outcome chain integration.
- `opi/log.py`: Tier 2b allowed domains and status validation, custom run log path support.
- `opi/market.py`: Comprehensive market evidence coverage for all past listing dates.
- `opi/report.py`: Pending outcome table data pipeline and markdown/HTML renderers.
- `opi/run_daily.py`: Decoupled alert logging from process exit.
- `scripts/watchdog.py`: `--check-overdue-and-coverage` CLI and checker method.
- `DEFECTS.md`: Updated status for D-091, D-095, D-096, D-097, D-098, D-099 to FIXED.
- `dashboard/index.html`: Re-rendered with pending outcome visibility.
- `predictions/pre_listing_predictions.md`: Re-rendered with pending outcome visibility.
- `tests/test_actuals_job.py`: Tier 2b unit and integration tests.
- `tests/test_actuals_symbol_resolution.py`: Symbol resolution fallback regression tests.
- `tests/test_market_evidence_job.py`: Market evidence unrecorded past listing date test.
- `tests/test_dashboard.py`: Dashboard pending outcome table regression test.
- `tests/test_watchdog.py`: Non-blocking overdue alert regression test.
- `tests/test_pre_listing.py`: Calendar rollover assertion update.
