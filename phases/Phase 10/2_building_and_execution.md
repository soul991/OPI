# Phase 10: Building & Execution - First Real Results, Mock Quarantine, Built-In Grounding, Real IPO Discovery

> Living record of execution for Phase 10 per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 0. User Requirements & Environment Confirmation

- **Execution Date & Time**: `2026-10-21T13:40:00+05:30` (IST).
- **Web Access**: Available for live web requests and official exchange evidence gathering.
- **LLM API Key**: Not provided in repo or environment (`GEMINI_API_KEY` absent). As mandated by binding instructions in `1_planning_and_goals.md` Section 6, Workstream C defect **D-026** is marked **NOT FIXED (needs user action)**. No synthetic or mock results were substituted.
- **Listing Schedule Tracking**:
  - `HD Fire Protect Limited`: Listed today (2026-10-21) on BSE/NSE. Action: Recorded immediately in X1.
  - `Fusion CX Limited`: Scheduled listing 2026-10-22.
  - `Zetwerk`, `Sahajanand Medical`, `Tonbo Imaging`, `Bonfiglioli`: Scheduled listing 2026-10-23.
  - `Jio Platforms` and `Paras Healthcare`: Bidding opened 2026-10-21 and closes 2026-10-23 after 18:00 IST. Bidding window is currently open; cannot score forward prediction until bidding concludes (D-023, D-024).

---

## 1. Gate A10 Execution Log

### Step 0: Baseline Verification & Registration
- Upgraded `scripts/verify_all.py` to v3 with mock quarantine and forward grounding checks.
- Executed baseline verification and saved full output at `phases/Phase 10/verify_start.txt`.
- Baseline confirmed expected failures: 20 mock research runs, 440 mock evidence files, Fusion CX issue price 289 missing in snapshot.
- Registered defects D-025 to D-033 in `DEFECTS.md`.

### X1: Record First Real Listing Result (HD Fire Protect Limited)
- BSE Scrip Code: `544994` (HD Fire Protect Limited).
- Official BSE Opening/Listing Price: `INR 334.40` on 2026-10-21.
- Issue Price: `INR 271.00`.
- Actual Listing Gain: `+23.39%` (`(334.40 - 271.00) / 271.00 * 100`).
- Model Point Estimate: `+26.12%` (Absolute Error: `2.73 pp`).
- Pre-listing Last Bidding Day GMP: `+30.26%` (Absolute Error: `6.87 pp`).
- Sourced and verified via official BSE trading quotes with browser snapshot saved to:
  `data/evidence/actuals/2026-10-21_hd-fire-protect-limited_1995cac2f37d.html`
  SHA-256: `1995cac2f37d89481ecff60ea1eb7024f92328ba6b90875c7553535914fa7670`.
- Manifest created at:
  `data/evidence/actuals/2026-10-21_hd-fire-protect-limited_manifest.json`.
- Updated `predictions/prediction_log.csv` and refreshed `dashboard/index.html`.
- Logged in `phases/Phase 10/results_log.md`.
- Committed in git as `1235a59`: `record: HD Fire Protect official listing outcome`.

### X2: Quarantine Mock Data (D-025)
- Removed all 20 mock research runs (`data/research_runs/*.json`) and 440 mock evidence files (`data/evidence/research/run_*`) using `git rm`. Total tracked files removed: 1,101. Untracked synthetic files cleaned: 138.
- Preserved only 4 genuine research evidence files (`data/evidence/research/2026-10-23_*.html`).
- Preserved 2 representative mock runs in `tests/fixtures/mock_runs/`.
- Exported complete cryptographic audit trail to `phases/Phase 10/mock_quarantine_manifest.csv` (1,239 entries).
- Hardened `opi/research_agent.py` to require `OPI_ENV=test` for mock provider and route test outputs strictly to temporary test directories.
- Added regression test `tests/test_data_integrity.py::test_no_mock_output_in_data_folders` (PASS).
- `check_mock_quarantine()` in `scripts/verify_all.py` reports `[PASS]`.

### X3: Measured Probability Rule (D-029)
- Analyzed rolling-origin out-of-sample calibrated probabilities ($n=398$). Measured empirical minimum: `0.0910`, empirical maximum: `0.8820`.
- Saved `"calibrated_probability_range": [0.091, 0.882]` in `model/registry.json`.
- Updated `app/main.py` and `opi/report.py` to suppress probabilities outside this range with `"not shown: outside measured range"`.
- Labelled unused fundamentals as `(not used by model)` in `app/main.py`.
- Added tests `tests/test_app.py::test_probability_hidden_outside_calibrated_range` and `tests/test_app.py::test_table_values_are_strings` (PASS).

### X4: Fusion CX Primary Evidence Grounding (D-031)
- Fetched and saved primary news detail snapshot containing issue price ₹289 for Fusion CX Limited:
  `data/evidence/research/2026-10-22_fusion-cx-limited.html`
  SHA-256: `8a85d0d7bea0f13cdce72454432a317d7df1f2d2761acdc6380dc1e71b4dc7fe`.
- Added regression test `tests/test_gate_a.py::test_fusion_cx_grounding_evidence` (PASS).
- `verify_all.py` forward grounding check for Fusion CX reports `[PASS]`.

### X5: Windows Setup & Cherry-Picks (D-032, D-033)
- Documented Windows environment configuration (`-p no:pytest_ethereum`, `$env:PYTHONUTF8 = "1"`, `$env:PYTHONIOENCODING = "utf-8"`) in `README.md`.
- Cherry-picked string-casting for table rendering and flexible date format grounding (`verify_value_in_html`).
- Added regression tests `tests/test_gate_a.py::test_windows_setup_in_readme` and `tests/test_ingest.py::test_grounding_accepts_date_format_variants` (PASS).

### X6: Prior Phase Re-Check & Register Hygiene
- Re-scored all 6 genuine FORWARD rows using `opi.score.score_ipo`: all 6 match logged values within tolerance $10^{-6}$ (exact diff 0.00000000).
- Recomputed 5 headline metrics and verified 10 Phase 9 claims. Stored in `phases/Phase 10/prior_phase_recheck.csv`.
- Confirmed `DEFECTS.md` reflects updated statuses for D-005, D-025, D-029, D-031, D-032, D-033.
- Committed Gate A as `phase10-gate-a` (`d42f88b`).
- Committed Preregistration as `phase10-preregistration` (`9a68056`).

---

## 2. Workstream A: Built-In Grounding (`opi/ingest.py`, `scripts/score_ipo.py`)

- **Implementation**: Built `opi/ingest.py` containing deterministic regex/DOM parsers:
  - `parse_chittorgarh_overview`: extracts issue price, price band, lot size, issue size.
  - `parse_chittorgarh_subscription`: extracts category breakdown (QIB, NII, Retail, Total).
  - `parse_investorgain_gmp`: extracts the GMP row corresponding strictly to the evening of the last bidding day (never blindly taking the latest row).
  - `save_raw_market_data`: saves raw macroeconomic response bytes with SHA-256 hash manifest.
  - `ingest_ipo_data`: compares any supplied/proposed values against parsed snapshot content and raises `IngestionError` on mismatch.
- **CLI Replacement**: Built `scripts/score_ipo.py` replacing hard-coded `scripts/score_oct19_ipos.py` (which is retained marked `[DEPRECATED]`).
- **Defect Resolution**:
  - `D-028`: FIXED. Tested via `tests/test_ingest.py::test_mismatch_between_typed_value_and_snapshot_is_refused` (PASS).
  - `D-030`: FIXED. Tested via `tests/test_ingest.py::test_market_data_saved_raw_with_hash` (PASS).
- Committed as `phase10-workstream-a` (`5c093bd`).

---

## 3. Workstream B: Real IPO Discovery and Daily Automation (`opi/discover.py`)

- **Implementation**: Built `opi/discover.py` to identify Mainboard IPO candidates across three lifecycle stages:
  - `UPCOMING`: bidding window opens in the future.
  - `BIDDING_OPEN`: bidding currently active (scores deferred post-close).
  - `CLOSED_UNLISTED`: bidding concluded, awaiting listing date.
- **Inclusion Rules**: Strictly enforces Mainboard eligibility; automatically excludes SME board IPOs (BSE SME, NSE Emerge), FPOs, and Rights issues.
- **Automated Discovery Execution**:
  - Live discovery test found 18 Mainboard candidates from live exchange/aggregator tables, including `Jio Platforms` (`BIDDING_OPEN`, close 2026-10-23) and `Paras Healthcare` (`BIDDING_OPEN`, close 2026-10-23).
- **Daily Runner Integration**: Updated `opi/run_daily.py` to execute discovery, defer open issues with `SKIPPED_BIDDING_OPEN`, score unlisted issues, and audit pending listings for actuals.
- **Defect Resolution**:
  - `D-027`: FIXED. Tested via `tests/test_discover.py::test_discovers_closed_unlisted_mainboard_ipos_from_fixture` (PASS).
- Committed as `phase10-workstream-b` (`1b7af02`).

---

## 4. Workstream C: Live Research-Agent Proof

- **Environment Evaluation**: Outbound web scraping tools are active; however, no live LLM API credentials (`GEMINI_API_KEY`) were provided by the user in this session.
- **Protocol Adherence**:
  - Per Rule 1 and Phase 10 binding instructions, mock results are strictly forbidden from being substituted into live evidence folders or claims.
  - Defect `D-026` is formally designated **NOT FIXED (needs user action)**.
- Committed as `phase10-workstream-c` (`9cb0359`).

---

## 5. Workstream D: Results Dashboard & Forward Reporting

- **Forward Reporter**: Enhanced `scripts/forward_report.py` to display:
  - Provisional Status Banner: `⚠️ PROVISIONAL: n listed = 1 of 30`.
  - Side-by-side descriptive errors for Model and Raw GMP.
  - Clear label that comparisons are descriptive only below $n = 30$.
- **Dashboard Upgrade**: Updated `opi/report.py` and `dashboard/index.html`:
  - Added full forward evaluation table: Company, Listing Date, Model Version, Model Estimate, 80% Interval, GMP at Close, Actual Gain, Error Model, Error GMP, Status, Thin Inputs flag.
  - Added prominent provisional banner.
- Committed as `phase10-workstream-d` (`2e57675`).

---

## 6. Verification Commands & Outputs

```bash
$env:PYTHONUTF8 = "1"
python scripts/verify_all.py > "phases/Phase 10/verify_end.txt"
# Result: 58 pass, 0 warn, 0 fail (verified on a completely fresh temporary clone)

python -m pytest -q
# Result: 94 passed, 1 skipped in 21.72s

python -m opi.discover --dry-run
# Result: Discovered 18 eligible Mainboard candidates (including Jio Platforms, Paras Healthcare)

python -m opi.run_daily --dry-run
# Result: Steps 1-3 executed cleanly; deferred bidding-open candidates, audited pending listings

python scripts/forward_report.py
# Result: Evaluated 1 of 30, Model MAE 2.73 pp, GMP MAE 6.87 pp, 5 pending forward candidates
```
