# Phase 10: Outcome & Verdict - First Real Results, Mock Quarantine, Built-In Grounding, Real IPO Discovery

> Living verdict document for Phase 10 per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets remain open, partial, or carried over in Phase 10:

1. **D-026: Live Web Research Agent Proof**
   - Issue: Research agent requires a live Gemini API key (`GEMINI_API_KEY`) and live outbound web access.
   - Status: **NOT FIXED (needs user action)**. No API key provided in the environment. Per Phase 10 binding instructions, mock results are never substituted.
2. **D-007: Tail Behavior (Large Pops Under-predicted)**
   - Status: **DEFERRED** (Phase 11).
3. **D-008: Conformal Prediction Intervals Over-conservative**
   - Status: **DEFERRED** (Phase 11).
4. **D-013: Upstream Audit Sample Evidence Snapshots**
   - Status: **PARTIAL** (Carried over from Phase 9).
5. **D-023 & D-024: Jio Platforms and Paras Healthcare Bidding Window**
   - Status: **DEFERRED**. Bidding closes 2026-10-23; genuine forward scoring occurs post-close.

---

## 2. Defect Ledger

| Defect ID | Phase | Description | Severity | Status | Due Phase | Regression Test Reference / Evidence |
|---|:---:|---|:---:|:---:|:---:|---|
| **D-005** | 7 | HD Fire Protect actual listing outcome unrecorded (lists 2026-10-21). | Medium | **FIXED** | 10 | `tests/test_actuals_offline.py::test_evidence_file_success` |
| **D-006** | 4-7 | Fundamentals completeness (roce/growth 0% filled; pe ~61-62%). | Medium | **ACCEPTED** | - | README "Known limitations" |
| **D-007** | 5-7 | Tail behaviour: extreme pops under-predicted (57.5% coverage). | Medium | **DEFERRED** | 11 | `phases/Phase 7/3_outcome_and_verdict.md` |
| **D-008** | 7 | Conformal intervals over-conservative overall (91.2% coverage). | Medium | **DEFERRED** | 11 | `phases/Phase 7/3_outcome_and_verdict.md` |
| **D-010** | 7 | GMP absent for 304 of 333 pre-2022 historical rows. | Medium | **ACCEPTED** | - | README "Known limitations" |
| **D-011** | 4 | Sector label: Industrial & Manufacturing share ~18.74%. | Low | **ACCEPTED** | - | `tests/test_data_integrity.py::test_sector_catchall_share_reported` |
| **D-012** | 4 | Years 2012-2014 sparse capital market IPO counts (11, 3, 5). | Low | **ACCEPTED** | - | `tests/test_data_integrity.py::test_sparse_years_documented` |
| **D-013** | 7 | Duplicate verification and random audit lacked saved snapshots. | Medium | **PARTIAL** | 10 | `tests/test_data_integrity.py::test_audit_samples_have_snapshots` |
| **D-023** | 9 | Candidate IPO Jio Platforms bidding open; score post-close on 10-23. | Low | **DEFERRED** | 10 | `predictions/run_log.csv` |
| **D-024** | 9 | Candidate IPO Paras Healthcare bidding open; score post-close on 10-23. | Low | **DEFERRED** | 10 | `predictions/run_log.csv` |
| **D-025** | 9 | 20 mock research runs and 440 mock evidence files quarantined. | High | **FIXED** | 10 | `tests/test_data_integrity.py::test_no_mock_output_in_data_folders` |
| **D-026** | 9 | Live research-agent run against live web. | High | **NOT FIXED** | 10 | `tests/test_research_agent.py::test_live_run_log_has_provider_and_real_urls` |
| **D-027** | 8/9 | `run_daily` has no IPO discovery: scores only new_ipo.csv. | High | **OPEN** | 10 | `tests/test_discover.py::test_discovers_closed_unlisted_mainboard_ipos_from_fixture` |
| **D-028** | 9 | `scripts/score_oct19_ipos.py` hard-coded inputs without snapshot verification. | Medium | **OPEN** | 10 | `tests/test_ingest.py::test_mismatch_between_typed_value_and_snapshot_is_refused` |
| **D-029** | 9 | App displays uncalibrated P(gain > 10%) outside measured range. | Medium | **FIXED** | 10 | `tests/test_app.py::test_probability_hidden_outside_calibrated_range` |
| **D-030** | 9 | Nifty 30d return and India VIX from yfinance not saved as raw with hash. | Low | **OPEN** | 10 | `tests/test_ingest.py::test_market_data_saved_raw_with_hash` |
| **D-031** | 9 | Fusion CX forward row issue price 289 not found in saved snapshot. | Medium | **FIXED** | 10 | `tests/test_gate_a.py::test_fusion_cx_grounding_evidence` |
| **D-032** | 9 | Windows-only local workarounds uncommitted. | Low | **FIXED** | 10 | `tests/test_gate_a.py::test_windows_setup_in_readme` |
| **D-033** | 9 | Cherry-pick useful improvements from local-work branch. | Low | **FIXED** | 10 | `tests/test_app.py::test_table_values_are_strings` |

---

## 3. First Real Results Table (Forward Prospective Test)

> **Provisional Evaluation Notice**: Sample size $n = 1$ of 30 target forward predictions. Results are strictly descriptive. No performance or superiority conclusions may be drawn prior to $n \ge 30$.

| Company | Listing Date | Issue Price (₹) | Listing Opening Price (₹) | Actual Listing Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | LISTED | BSE official quote (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | Pending | Pending | +4.33% | None (NOT_RECORDED) | Pending | N/A | FORWARD | Thin inputs; listing scheduled 2026-10-22 |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹412.00 | Pending | Pending | -0.77% | +4.85% | Pending | Pending | FORWARD | Listing scheduled 2026-10-23 |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹387.00 | Pending | Pending | +8.32% | +12.92% | Pending | Pending | FORWARD | Listing scheduled 2026-10-23 |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹540.00 | Pending | Pending | +74.70% | +64.81% | Pending | Pending | FORWARD | Listing scheduled 2026-10-23 |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹625.00 | Pending | Pending | +21.10% | +24.00% | Pending | Pending | FORWARD | Listing scheduled 2026-10-23 |

---

## 4. Gate A10 Remediations Summary

- **X1**: HD Fire Protect listing outcome recorded from BSE trade quotes. Actuals snapshot verified.
- **X2**: Quarantined 1,101 mock files with cryptographic manifest.
- **X3**: Enforced calibrated probability range `[0.091, 0.882]` across app and reports.
- **X4**: Evidenced Fusion CX issue price 289 in primary source snapshot.
- **X5**: Added Windows setup to README and cherry-picked tests.
- **X6**: DEFECTS.md register hygiene verified.
