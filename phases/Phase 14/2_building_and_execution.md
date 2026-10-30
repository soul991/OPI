# Phase 14: Building & Execution Log

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Final Status**: All Phase 14 deliverables complete across Gate A14, Workstreams A through D, defect resolution (D-066, D-067, D-068, D-069, D-070, D-071), live outcome recording for Jio Platforms and Paras Healthcare, and verification suites.

---

## 1. Pipeline Architecture & Data Flow

Phase 14 operationalizes automated listing-outcome recording within GitHub Actions cloud infrastructure, closing the operational gap where daily runs previously skipped outcome fetches with `SKIPPED_BLOCKED_SOURCE`:

1. **Gate A14 Audit & Preregistration**:
   - Initial verification logs captured: `phases/Phase 14/verify_start.txt` (68 pass, 0 fail), `phases/Phase 14/verify_extra_start.txt` (7 pass, 0 fail), `scripts/ci_local.py` (`CI_LOCAL: PASS`).
   - Prior phase recheck conducted with seed 14 in `phases/Phase 14/prior_phase_recheck.csv` (10 sampled Phase 13 claims, 5 headline recomputations).
   - Preregistered protocol committed in `phases/Phase 14/preregistration.md` (`phase14-preregistration`, commit `5c3c04c`) prior to authoring any outcome recording code.
2. **Defect D-071 Fix (Dashboard Defect Accounting)**:
   - Fixed `opi/report.py` defect parsing (`parse_defects_summary`) and dashboard card renderer to include `NOT FIXED` defects (`D-026`) in the unresolved counter (`OPEN + PARTIAL + NOT FIXED`).
   - Added regression test `tests/test_dashboard.py::test_dashboard_counts_not_fixed_defects`.
   - Marked `verify_all.py` portion as `PARTIAL (needs user action)` per user instructions.
3. **Workstream A: Cloud Runner Source Reachability Probe (D-068)**:
   - Created workflow `.github/workflows/probe_sources.yml` (`workflow_dispatch`, `ubuntu-24.04`, `checkout@v5`, `setup-python@v6`, permissions `contents: read`).
   - Authored `scripts/probe_sources.py` targeting Jio Platforms Limited and Paras Healthcare Limited.
   - Executed probe in GitHub Actions (`run 41038115389`): confirmed official exchange endpoints (NSE/BSE) return HTTP 403 (Akamai/WAF block) from cloud runners, while `yfinance` (`query1.finance.yahoo.com`) and Chittorgarh return HTTP 200 with matching prices. Documented in `phases/Phase 14/source_probe.md`.
4. **Workstream B: Automated Two-Tier Listing Outcome Engine (D-066, D-069)**:
   - Designed and implemented deterministic two-tier architecture in `opi/actuals.py`, `opi/log.py`, `opi/run_daily.py`, and `scripts/update_actuals.py`:
     - **Tier 1 (Official Exchanges)**: Direct scrape of NSE or BSE opening trade notice.
     - **Tier 2 (Cloud Fallback with 1.0% Cross-Check)**: `yfinance` first-session open validated against independent second source (Chittorgarh listing section) within 1.0% relative tolerance:
       $$\frac{|\text{Price}_{\text{Tier2}} - \text{Price}_{\text{SecondSource}}|}{\text{Price}_{\text{Tier2}}} \le 0.01$$
     - **D-069 Timing Rule**: Evaluates whether market has opened before fetching: attempted only if `listing_date < today (IST)` OR (`listing_date == today (IST)` AND IST time $\ge$ 16:00). Tested with synthetic clocks in `tests/test_actuals_job.py`.
     - **Zero Overwrite Rule**: Never modifies existing recorded outcomes.
5. **Workstream C: Missing Outcome Alerting & Dashboard Visibility (D-067, D-070)**:
   - Extended `scripts/watchdog.py` with Check (d): audits all `FORWARD` rows; any row with `listing_date` > 2 calendar days ago lacking an outcome fails the watchdog, and the alert names each company and its last logged operational error.
   - Added identical check at the end of `opi/run_daily.py` (Step 4) so daily runs alert immediately upon missing outcomes.
   - Updated `opi/report.py` to display `listed, outcome pending: K` with company names in the Completed Listings card and prospective evaluation statistics.
   - Authored unit tests in `tests/test_watchdog.py` and `tests/test_dashboard.py`.
6. **Workstream D: Maintainer Runbook (D-070 doc part)**:
   - Updated `docs/RUNBOOK.md` detailing the automated two-tier pipeline, the meaning of `PENDING_REVIEW`, manual resolution path with saved exchange pages, 2-day missing outcome alert, and explicit justification for why Zerodha Kite API is not used.
7. **Live Execution on Mainboard IPOs (Jio Platforms & Paras Healthcare)**:
   - Dispatched daily workflow on `main` (`run 41038093115`).
   - Recorded Jio Platforms Limited: Issue ₹1,119.00 -> Listing ₹1,358.00 (+21.36% gain; Model pred +22.14%, error 0.78 pp). Evidence: `data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.json` and `.txt`.
   - Recorded Paras Healthcare Limited: Issue ₹693.00 -> Listing ₹721.00 (+4.04% gain; Model pred -2.56%, error 6.60 pp). Evidence: `data/evidence/actuals/2026-10-28_paras-healthcare-limited_fe823e2ba992.json` and `.txt`.
   - Recorded evidenced market macro for listing date `2026-10-28` in `data/evidence/market/2026-10-28_nifty.json` (Nifty move -0.22%, VIX 16.25).
   - Regenerated dashboard (`dashboard/index.html`) and verification logs.

---

## 2. Scripts & Workflows Created / Modified

- `.github/workflows/probe_sources.yml`: Workflow for measuring source reachability from GitHub Actions runners.
- `scripts/probe_sources.py`: Probe script measuring HTTP latency and status codes for NSE, BSE, yfinance, and Chittorgarh.
- `phases/Phase 14/source_probe.md`: Empirical measurement report of cloud runner reachability.
- `opi/actuals.py`: Two-tier listing outcome recording engine (`record_actual_from_tier2`, `fetch_yfinance_first_session_open`, `fetch_second_source_open`, `execute_two_tier_outcome_chain`, `is_listing_ready_for_actuals`).
- `opi/log.py`: Updated `update_actual_outcome` supporting Tier 2 provenance notes, allowed secondary domains, and verification statuses.
- `opi/run_daily.py`: Integrated two-tier outcome chain into Step 2 and missing outcome check into Step 4.
- `scripts/update_actuals.py`: Added `--auto` flag to trigger two-tier chain from CLI.
- `scripts/watchdog.py`: Added Check (d) for missing listing outcomes older than 2 calendar days.
- `opi/report.py`: Added `listed_outcome_pending_count` and company names to dashboard cards and summary text.
- `docs/RUNBOOK.md`: Added `PENDING_REVIEW` protocol, manual resolution flow, 2-day alert description, and Kite API rationale.
- `DEFECTS.md`: Seeded D-066 through D-071; updated D-066..D-070 to FIXED, D-071 to PARTIAL. D-026 remains NOT FIXED.
- `tests/test_actuals_job.py`: 8 unit tests covering two-tier chain, cross-check tolerance, market hours timing, redirect rejection, and probe evidence.
- `tests/test_watchdog.py`: 3 unit tests covering 2-day threshold boundary, ignoring completed rows, and alert secret sanitization.
- `tests/test_dashboard.py`: 2 unit tests covering unresolved defect counting with NOT FIXED items and pending outcome counter.
- `tests/test_final_evaluation.py`, `tests/test_forward_log.py`, `tests/test_postmortem.py`: Updated assertions to support dynamic sample sizes as forward rows complete listings.
