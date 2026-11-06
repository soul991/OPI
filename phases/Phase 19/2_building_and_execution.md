# Phase 19: Building & Execution Log

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Final Status**: All Phase 19 workstreams (A, B, C, D) completed, verified by regression tests, and audited.

---

## 1. Summary of Workstreams & Milestones

Phase 19 resolves data lineage and exchange ambiguity in price source evidence manifests (D-101), implements pre-registered divergence arbitration with strict majority rules (D-100), closes proven defects D-085 and D-099, accepts Pages timeout D-102, refines watchdog alert failure granularity (D-091) with live cloud verification, and corrects the prior cohort MAE errata (H-02).

### Workstream A: Source Value Labelling (D-101) & Prior Cohort MAE Correction (H-02)
- **Problem**:
  1. Evidence manifests previously stored bare price values without identifying the specific exchange (NSE vs BSE), publisher, or bar date. For BLS Polymers, yfinance quoted 248.0 (NSE) while Chittorgarh overview table quoted 244.1 (BSE). Without publisher and exchange labelling, automated systems could not discern whether price differences stemmed from reporting discrepancies or distinct exchange quotes.
  2. In Gate A19, the audit script computed prior cohort MAE as 5.4578 pp instead of the Phase 17 reported figure of 5.8500 pp due to raw `.iloc[:9]` selection on `prediction_log.csv`.
- **Implementation**:
  - In `opi/actuals.py`:
    - Implemented `parse_source_value_metadata(html_or_text, default_publisher)`: extracts publisher, opening price, bar/quote date, and exchange directly from page text, table headers, or meta elements. If the exchange cannot be verified from page content, it explicitly records `UNKNOWN` (per the user directive treating "Chittorgarh = BSE, Groww = NSE" as an unverified hypothesis).
    - Implemented `make_yfinance_source_value(symbol, open_price, bar_date)`: maps `.NS` to `NSE` and `.BO` to `BSE`.
    - Updated `record_actual_from_tier2b`, `record_actual_from_tier2_arbitrated`, and manifest builders to record rich source value objects:
      `{"publisher": str, "exchange": "NSE"|"BSE"|"UNKNOWN", "quantity": "open_price", "bar_date": str, "value": float}`.
  - In `tests/fixtures/`: Created 6 synthetic HTML fixtures:
    - `synthetic_chittorgarh_bse.html`
    - `synthetic_chittorgarh_nse.html`
    - `synthetic_chittorgarh_unknown.html`
    - `synthetic_groww_nse.html`
    - `synthetic_groww_bse.html`
    - `synthetic_groww_unknown.html`
  - In `tests/test_actuals_manifest.py`: Authored 8 comprehensive unit tests covering exchange extraction, fallback to `UNKNOWN`, yfinance symbol labelling, and manifest schema compliance.
  - **Prior Cohort MAE Errata (H-02)**:
    - Diagnosed that raw append order in `prediction_log.csv` has M.K.Sons Fine Jewels (listed 2026-11-04, error 1.19 pp) at row 14, while EAAA India Alternatives (listed 2026-11-02, error 4.72 pp) was added later at row 17. Taking `.iloc[:9]` without sorting mistakenly replaced EAAA with M.K.Sons, lowering MAE to 5.4578 pp.
    - Updated `scripts/forward_report.py` to sort forward rows chronologically by `(listing_date, scored_at)` before selecting the first 9 listed IPOs, exactly restoring 5.8500 pp ($52.65 / 9$).
    - Added regression test `tests/test_reporting.py::test_forward_report_chronological_first_9_mae`.
    - Appended `H-02-ERRATA` to `phases/Phase 19/prior_phase_recheck.csv` without modifying the original row.
- **Verification**: `pytest tests/test_actuals_manifest.py` (8 passed) and `pytest tests/test_reporting.py -k test_forward_report_chronological_first_9_mae` (1 passed).
- **Defect Status**: D-101 marked `FIXED`.

### Workstream B: Pre-Registered Divergence Arbitration (D-100)
- **Problem**: When primary and secondary Tier 2 sources diverged beyond the 1.0% tolerance, the outcome was halted in `PENDING_REVIEW` indefinitely with no programmatic resolution path.
- **Implementation**:
  - In `opi/actuals.py`: Implemented `record_actual_from_tier2_arbitrated(company, issue_price, listing_date, source_values, manifests)`.
  - Enforced strict arbitration rules:
    1. **Strict Majority Rule**: Requires at least 2 agreeing sources on the same exchange within $\le 1.0\%$ tolerance (`diff <= TOLERANCE_PCT`). 1-vs-1 disagreements are rejected.
    2. **Same Exchange Requirement**: Sources must agree on the same exchange (`NSE` or `BSE`). Cross-exchange price comparisons cannot form a majority.
    3. **Exclusion of Unlabelled Values**: Sources with exchange `UNKNOWN` are excluded from arbitration pools.
    4. **Deduplication of Dependent Sources**: Sources derived from Yahoo Finance / yfinance are deduplicated and count as a single vote.
    5. **Immutable Recorded Rows**: Existing recorded rows in `prediction_log.csv` are never overwritten.
    6. **Strict Tolerance Constant**: Hard-coded and asserted `TOLERANCE_PCT == 1.0`. Tolerance was never loosened.
  - In `opi/log.py`: Added `"VERIFIED_TIER2_ARBITRATED"` to valid evidence verification statuses.
  - In `tests/test_actuals_divergence.py`: Authored 7 regression tests verifying:
    - 2-of-3 strict majority recording.
    - 1-vs-1 rejection.
    - Cross-exchange mismatch rejection.
    - Unlabelled value exclusion.
    - Yahoo-derived source deduplication.
    - Recorded row protection.
    - Hard `TOLERANCE_PCT == 1.0` assertion.
- **Verification**: `pytest tests/test_actuals_divergence.py` (7 passed).
- **Defect Status**: D-100 marked `FIXED`.

### Workstream C: Proven Defect Closures (D-085, D-099, D-096, D-102)
- **D-085 (Market Index Evidence Missing for Unrecorded Listed Dates)**:
  - Proven FIXED by GitHub Actions cloud run `42218253536` on commit `46294eb` which generated Nifty evidence files for 2026-11-03 and 2026-11-05.
  - Verified by `scripts/verify_extra.py` (check 4: `each listed date has a parsed Nifty evidence file ... missing: none`) and regression test `tests/test_market_evidence_job.py::test_job_records_nifty_evidence_for_unrecorded_past_listing`.
  - Status: `FIXED`.
- **D-099 (Symbol Resolution Failure on Embedded JSON Overview Pages)**:
  - Proven FIXED by GitHub Actions cloud run `42218253536` resolving `BCSSL.NS` from Next.js embedded JSON for Bombay Coated & Special Steels.
  - Verified by regression test `tests/test_actuals_symbol_resolution.py::test_symbol_resolution_fallbacks`.
  - Status: `FIXED`.
- **D-096 (Automated Tier 2b Dual-Source Agreement)**:
  - Implementation completed and unit-tested in Phase 18; awaiting cloud execution encountering two agreeing non-Yahoo sources.
  - Status: `PARTIAL`.
- **D-102 (Pages Build Deployment Transient Network Timeout)**:
  - Investigated in Gate G7. Workflow run `42190760462` failed due to transient timeout contacting the GitHub Pages deployment API (`RequestError: Request timed out`).
  - Subsequent Pages runs `42290565047` and `42297531379` succeeded completely in under 3 minutes with zero workflow alterations.
  - Status: `ACCEPTED`.

### Workstream D: Alert Granularity (D-091)
- **Problem**: When `watchdog.yml` failed (e.g. run `42259466958`), the failure alert named the failing step as generic "Execution", providing insufficient diagnostic clarity in the issue title/body.
- **Implementation**:
  - In `scripts/watchdog.py`: Added logic to record the specific failing check (e.g. `check (d) missing outcomes`, `check (a) scheduled run freshness`, etc.) into `FAILED_CHECK:` and wrote `watchdog_failed_step.txt`.
  - In `.github/workflows/watchdog.yml`: Extracted `FAILED_STEP` from `watchdog_failed_step.txt` and passed `--failed-step "$FAILED_STEP"` to `manage_alerts.py`.
  - In `scripts/manage_alerts.py`: Implemented `infer_failing_step_from_output` to deduce the failing check directly from the watchdog output text if `--failed-step` is missing or generic.
  - In `tests/test_alerts.py`: Authored `test_watchdog_alert_names_failing_check_from_reason_file`.
- **Cloud Proof**:
  - GitHub Actions cloud run `42297601919` executed on `main` after merging PR #22.
  - Issue #21 comment 1 recorded:
    `- **Failed Step / Component**: \`check (d) missing outcomes\``
    proving that watchdog alerts now report the exact failing check.
- **Defect Status**: D-091 marked `FIXED` with cloud proof.

---

## 2. Modified Files & Execution Summary

- `.github/workflows/watchdog.yml`: Passes `--failed-step` derived from `watchdog_failed_step.txt`.
- `opi/actuals.py`: Source metadata extraction (`parse_source_value_metadata`), yfinance labelling (`make_yfinance_source_value`), and divergence arbitration (`record_actual_from_tier2_arbitrated`).
- `opi/log.py`: Permitted verification status `VERIFIED_TIER2_ARBITRATED`.
- `scripts/forward_report.py`: Chronological sorting by `(listing_date, scored_at)` for prior cohort evaluation.
- `scripts/manage_alerts.py`: Infer failing check step from output when generic or omitted.
- `scripts/watchdog.py`: Sets `FAILED_CHECK:` and exports `watchdog_failed_step.txt`.
- `DEFECTS.md`: Updated D-085, D-091, D-099, D-100, D-101 to FIXED; D-096 to PARTIAL; D-102 to ACCEPTED.
- `phases/Phase 19/prior_phase_recheck.csv`: Appended `H-02-ERRATA` documenting chronological sorting resolution.
- `tests/fixtures/`: Added 6 synthetic HTML test fixtures for Chittorgarh and Groww.
- `tests/test_actuals_divergence.py`: 7 unit/regression tests for arbitration logic.
- `tests/test_actuals_manifest.py`: 8 unit/regression tests for source value metadata and labelling.
- `tests/test_alerts.py`: Regression test for watchdog alert failure step naming.
- `tests/test_reporting.py`: Regression test for chronological first-9 MAE calculation.

---

## 3. Terminal Reproduction & Verification Commands

```bash
# 1. Test source value labelling & extraction
pytest tests/test_actuals_manifest.py -q
# Output: 8 passed

# 2. Test pre-registered divergence arbitration
pytest tests/test_actuals_divergence.py -q
# Output: 7 passed

# 3. Test watchdog alert failed step naming
pytest tests/test_alerts.py -k test_watchdog_alert_names_failing_check_from_reason_file -q
# Output: 1 passed

# 4. Test prior cohort first-9 MAE calculation
pytest tests/test_reporting.py -k test_forward_report_chronological_first_9_mae -q
# Output: 1 passed

# 5. Local CI pipeline verification
python scripts/ci_local.py
# Output: CI_LOCAL: PASS

# 6. Repository verification scripts
python scripts/verify_all.py
# Output: SUMMARY: 82 pass, 0 warn, 0 fail (upon verdict completion)
python scripts/verify_extra.py
# Output: SUMMARY: 7 pass, 0 warn, 0 fail
```
