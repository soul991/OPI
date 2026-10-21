# Phase 10: Building & Execution - First Real Results, Mock Quarantine, Built-In Grounding, Real IPO Discovery

> Living record of execution for Phase 10 per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 0. User Requirements & Environment Confirmation

- **System Date & Time**: `2026-10-21T13:20:00+05:30` (IST).
- **Web Access**: Available for standard HTTP fetching and evidence gathering.
- **LLM API Key**: Not provided in repo or environment (`GEMINI_API_KEY` absent). As mandated by binding instructions in `1_planning_and_goals.md` Section 6, Workstream C defect **D-026** is designated **NOT FIXED (needs user action)**. No mock data will be substituted.
- **Listing Calendar Check**:
  - `HD Fire Protect Limited`: Listed today (2026-10-21) post-10:00 IST on BSE/NSE. Action: Recorded immediately in X1.
  - `Fusion CX Limited`: Lists 2026-10-22.
  - `Zetwerk`, `Sahajanand Medical`, `Tonbo Imaging`, `Bonfiglioli`: List 2026-10-23.
  - `Jio Platforms` and `Paras Healthcare`: Bidding closes 2026-10-23 after 18:00 IST. Cannot score before bidding concludes (D-023, D-024).

---

## 1. Gate A10 Execution Log

### Step 0: Verification Baseline & Defect Registration
- Upgraded `scripts/verify_all.py` to v3 with mock quarantine and forward grounding checks.
- Executed baseline verification and stored full output at `phases/Phase 10/verify_start.txt`.
- Baseline result confirmed expected failures: 20 mock research runs, 440 mock evidence files, Fusion CX issue price 289 missing in snapshot.
- Registered defects D-025 to D-033 in `DEFECTS.md`.

### X1: Record First Real Listing Result (HD Fire Protect Limited)
- BSE Scrip Code: `544994` (HD Fire Protect Limited).
- Official BSE Opening Price: `INR 334.40` on 2026-10-21.
- Issue Price: `INR 271.00`.
- Actual Listing Gain: `+23.39%` (`(334.40 - 271.00) / 271.00 * 100`).
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
- Hardened `opi/research_agent.py` to require `OPI_ENV=test` for mock provider and route test outputs strictly to `tests/fixtures/`.
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
