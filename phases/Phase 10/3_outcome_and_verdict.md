# Phase 10: Outcome & Verdict - First Real Results, Mock Quarantine, Built-In Grounding, Real IPO Discovery

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 10/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets remain open, partial, or carried over in Phase 10:

1. **D-026: Live Web Research Agent Proof**
   - Requirement: Execute a live research-agent run against live web pages using a real LLM provider, recording provider name, real URLs, code-saved snapshots, and field grounding rates.
   - Status: **NOT FIXED (needs user action)**. No LLM API key (`GEMINI_API_KEY`) was provided in the repository or session environment. Per Phase 10 non-negotiable rules, mock or synthetic data must never be substituted into committed evidence folders.
2. **D-013: Upstream Audit Sample Evidence Snapshots**
   - Status: **PARTIAL / CARRIED OVER**. Upstream live re-scraping remains blocked by site permissions. The 15 companies carry `verification_status=UNVERIFIED` in `phases/Phase 9/duplicate_verification.csv` and are documented in `README.md` under Known Limitations.
3. **D-007: Tail Behavior (Extreme Listing Pops Under-Predicted)**
   - Status: **DEFERRED** (Phase 11).
4. **D-008: Conformal Prediction Intervals Over-Conservative Overall**
   - Status: **DEFERRED** (Phase 11).
5. **D-023 & D-024: Candidate IPOs Jio Platforms and Paras Healthcare Bidding Window**
   - Status: **DEFERRED**. Both IPOs opened on 2026-10-21 and close on 2026-10-23. Per pre-registered timing rules (D-004, D-023, D-024), genuine forward scoring occurs strictly post-close using final subscription figures.

---

## 2. Defect Ledger

| Defect ID | Phase | Description | Severity | Status Before Phase 10 | Status After Phase 10 | Due Phase | Regression Test Reference / Evidence |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** | 7 | 77 backfilled GMP values unverified without snapshots. | Critical | FIXED | **FIXED** | 8 | `tests/test_gmp_evidence.py::test_snapshot_for_every_sourced_gmp_row` |
| **D-002** | 7 | Phase 7 headline results depended on unverified backfill. | Critical | FIXED | **FIXED** | 8 | `tests/test_reporting.py::test_headline_metrics_recompute` |
| **D-003** | 6 | Mukka Proteins had erroneous `gmp_pct = 321.43`. | High | FIXED | **FIXED** | 8 | `tests/test_data_integrity.py::test_gmp_outliers_verified` |
| **D-004** | 6/7 | HD Fire Protect FORWARD row used Day-1 interim live subscription. | High | FIXED | **FIXED** | 8 | `tests/test_forward_log.py::test_forward_rows_scored_after_bidding_closed` |
| **D-005** | 7 | HD Fire Protect actual listing outcome unrecorded (lists 2026-10-21). | Medium | PARTIAL | **FIXED** | 10 | `tests/test_actuals_offline.py::test_evidence_file_success` |
| **D-006** | 4-7 | Fundamentals completeness (roce/growth 0% filled; pe ~61-62%). | Medium | ACCEPTED | **ACCEPTED** | - | README "Known limitations" |
| **D-007** | 5-7 | Tail behaviour: extreme pops under-predicted (57.5% coverage). | Medium | DEFERRED | **DEFERRED** | 11 | `phases/Phase 7/3_outcome_and_verdict.md` |
| **D-008** | 7 | Conformal intervals over-conservative overall (91.2% coverage). | Medium | DEFERRED | **DEFERRED** | 11 | `phases/Phase 7/3_outcome_and_verdict.md` |
| **D-009** | 7 | Wording violations in Phase 7 verdict ("H1 rejected", "proves"). | Low | FIXED | **FIXED** | 8 | `tests/test_reporting.py::test_phase7_errata_present` |
| **D-010** | 7 | GMP absent for 304 of 333 pre-2022 historical rows. | Medium | ACCEPTED | **ACCEPTED** | - | README "Known limitations" |
| **D-011** | 4 | Sector label: Industrial & Manufacturing share ~18.74%. | Low | ACCEPTED | **ACCEPTED** | - | `tests/test_data_integrity.py::test_sector_catchall_share_reported` |
| **D-012** | 4 | Years 2012-2014 sparse capital market IPO counts (11, 3, 5). | Low | ACCEPTED | **ACCEPTED** | - | `tests/test_data_integrity.py::test_sparse_years_documented` |
| **D-013** | 7 | Duplicate verification and random audit lacked saved snapshots. | Medium | PARTIAL | **PARTIAL** | 10 | `tests/test_data_integrity.py::test_audit_samples_have_snapshots` |
| **D-014** | all | No automated independent verification existed. | High | FIXED | **FIXED** | 8 | `tests/test_reporting.py::test_verify_all_runs` |
| **D-015** | 8 | `model/ipo_model.joblib` gitignored; clean-clone test failures. | High | FIXED | **FIXED** | 9 | `tests/test_ci.py::test_model_available_on_fresh_clone` |
| **D-016** | 8 | FORWARD row backdated (scored_at vs commit time). | High | FIXED | **FIXED** | 9 | `tests/test_forward_log.py::test_scored_at_is_real_run_time` |
| **D-017** | 8 | Phase 8 overwrote Phase 7 files in place. | Medium | FIXED | **FIXED** | 9 | `tests/test_reporting.py::test_earlier_phases_immutable` |
| **D-018** | 8 | Eight extreme GMP values > 100% lacked code-saved snapshots. | Medium | FIXED | **FIXED** | 9 | `tests/test_data_integrity.py::test_extreme_gmp_have_snapshots` |
| **D-019** | 8 | Status inconsistency: D-001 FIXED vs U1 NOT FIXED. | Low | FIXED | **FIXED** | 9 | `tests/test_reporting.py::test_phase8_errata_present` |
| **D-020** | 8 | Daily GitHub workflow unconfirmed on GitHub. | Medium | FIXED | **FIXED** | 9 | `tests/test_ci.py::test_github_actions_evidence_recorded` |
| **D-021** | 9 | `opi/log.py` notes column assignment error on pandas 3.x. | Medium | FIXED | **FIXED** | - | `tests/test_actuals_offline.py::test_all_empty_notes_column_does_not_crash` |
| **D-022** | 9 | `opi/actuals.py` lacked `--evidence-file` option. | Medium | FIXED | **FIXED** | - | `tests/test_actuals_offline.py::test_evidence_file_success` |
| **D-023** | 9 | Jio Platforms bidding window open on 2026-10-20. | Low | DEFERRED | **DEFERRED** | - | `predictions/run_log.csv` |
| **D-024** | 9 | Paras Healthcare bidding window open on 2026-10-20. | Low | DEFERRED | **DEFERRED** | - | `predictions/run_log.csv` |
| **D-025** | 9 | 20 mock research runs and 440 mock evidence files committed. | High | OPEN | **FIXED** | 10 | `tests/test_data_integrity.py::test_no_mock_output_in_data_folders` |
| **D-026** | 9 | Live research agent run against live web. | High | OPEN | **PARTIAL** | 10 | `tests/test_research_agent.py::test_live_run_log_has_provider_and_real_urls` |
| **D-027** | 8/9 | `run_daily` has no automated IPO discovery. | High | OPEN | **FIXED** | 10 | `tests/test_discover.py::test_discovers_closed_unlisted_mainboard_ipos_from_fixture` |
| **D-028** | 9 | `scripts/score_oct19_ipos.py` hard-coded inputs without snapshot check. | Medium | OPEN | **FIXED** | 10 | `tests/test_ingest.py::test_mismatch_between_typed_value_and_snapshot_is_refused` |
| **D-029** | 9 | App displays uncalibrated P(gain > 10%) outside measured range. | Medium | OPEN | **FIXED** | 10 | `tests/test_app.py::test_probability_hidden_outside_calibrated_range` |
| **D-030** | 9 | Macro market data from yfinance not saved as raw bytes with hash. | Low | OPEN | **FIXED** | 10 | `tests/test_ingest.py::test_market_data_saved_raw_with_hash` |
| **D-031** | 9 | Fusion CX issue price 289 missing from saved snapshot. | Medium | OPEN | **FIXED** | 10 | `tests/test_gate_a.py::test_fusion_cx_grounding_evidence` |
| **D-032** | 9 | Windows-only local workarounds uncommitted. | Low | OPEN | **FIXED** | 10 | `tests/test_gate_a.py::test_windows_setup_in_readme` |
| **D-033** | 9 | Cherry-picks from local-work branch unmerged. | Low | OPEN | **FIXED** | 10 | `tests/test_app.py::test_table_values_are_strings` |

---

## 3. First Real Results Table (Forward Prospective Test)

> **Provisional Evaluation Notice**: Sample size $n = 1$ of 30 target forward predictions. Results are strictly descriptive. No performance conclusions or empirical superiority claims are permitted prior to $n \ge 30$.

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | Pending | Pending | +4.33% | None (NOT_RECORDED) | Pending | N/A | FORWARD | Thin inputs (no GMP); listing scheduled 2026-10-22 |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | Pending | Pending | -0.77% | +2.32% | Pending | Pending | FORWARD | Listing scheduled 2026-10-23 |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | Pending | Pending | +8.32% | +7.03% | Pending | Pending | FORWARD | Listing scheduled 2026-10-23 |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹540.00 | Pending | Pending | +74.70% | +72.92% | Pending | Pending | FORWARD | Listing scheduled 2026-10-23 |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹625.00 | Pending | Pending | +21.10% | +21.68% | Pending | Pending | FORWARD | Listing scheduled 2026-10-23 |

### Descriptive Commentary on First Result
For HD Fire Protect Limited, the actual listing gain (+23.39%) was situated between the Model estimate (+26.12%) and the Raw GMP quote (+30.26%). On this single observation, the model error was 2.73 percentage points versus 6.87 percentage points for Raw GMP. As mandated by pre-registered rules, this single observation provides zero basis for generalized performance claims; results remain strictly descriptive until $n \ge 30$.

---

## 4. Gate A10 Remediations & Prior Phase Re-Check

### Gate A10 Remediations Table
| Item | Defect | Action Taken | Status | Evidence Summary |
|---|---|---|---|---|
| **X1** | D-005 | Recorded HD Fire Protect listing outcome via official BSE quote | **FIXED** | BSE snapshot `1995cac2f37d` and manifest saved under `data/evidence/actuals/`. Commit `1235a59`. |
| **X2** | D-025 | Quarantined 1,101 mock files with cryptographic manifest | **FIXED** | Manifest `phases/Phase 10/mock_quarantine_manifest.csv` (1,239 entries). `test_no_mock_output_in_data_folders` PASS. |
| **X3** | D-029 | Measured calibrated probability range `[0.091, 0.882]` | **FIXED** | Stored in `model/registry.json`. Suppressed outside range in `app/main.py` and `opi/report.py`. `test_probability_hidden_outside_calibrated_range` PASS. |
| **X4** | D-031 | Sourced primary evidence snapshot for Fusion CX issue price 289 | **FIXED** | Saved `data/evidence/research/2026-10-22_fusion-cx-limited.html` (SHA-256 `8a85d0d7bea0...`). `test_fusion_cx_grounding_evidence` PASS. |
| **X5** | D-032 / D-033 | Added Windows setup to README; cherry-picked tests | **FIXED** | Documented `-p no:pytest_ethereum` and `$env:PYTHONUTF8=1` in README. `test_windows_setup_in_readme` and `test_table_values_are_strings` PASS. |
| **X6** | D-025 to D-033 | DEFECTS.md register hygiene | **FIXED** | D-025 through D-033 registered and updated with regression test references. |

### Prior Phase Re-Check (`phases/Phase 10/prior_phase_recheck.csv`)
1. **Scoring Re-Verification on 6 FORWARD Rows**: Re-ran `opi.score.score_ipo` on logged features for all 6 FORWARD rows. Every row matched logged `pred_gain_pct` and `pred_prob_gt10` within tolerance $10^{-6}$ (exact difference 0.00000000).
2. **Headline Numbers Recomputed**:
   - Recompute 1 (Historical Mean MAE): 19.8837% (reported 19.88%).
   - Recompute 2 (Model Without Fundamentals MAE): 11.5802% (reported 11.58%).
   - Recompute 3 (Raw GMP MAE on observed subset): 8.8617% (reported 8.86%).
   - Recompute 4 (Adaptive Blend MAE on observed subset): 8.9034% (reported 8.90%).
   - Recompute 5 (Master Dataset Row Count): exactly 654 rows in `data/ipo_master.csv`.
3. **10 Random Claims from Phase 9 Verdict**: All 10 claims verified against repository files. Recorded in `phases/Phase 10/prior_phase_recheck.csv`.

---

## 5. Mock Quarantine Summary

- **Total Tracked Files Removed**: 1,101 files deleted via `git rm` (20 JSON run logs under `data/research_runs/` and 1,081 HTML files across 20 directories under `data/evidence/research/run_*`).
- **Untracked Synthetic Files Removed**: 138 files cleaned.
- **Protected Files**: Genuine research evidence files (`data/evidence/research/2026-10-23_*.html`, `2026-10-22_fusion-cx-limited.html`) and market, subscription, gmp, and actuals folders were strictly preserved.
- **Representative Fixtures Retained**: Exactly 2 representative mock runs and their evidence folders preserved in `tests/fixtures/mock_runs/` and `tests/fixtures/mock_evidence/` for offline unit testing.
- **Audit Manifest**: Full record with original relative path and SHA-256 hash committed at `phases/Phase 10/mock_quarantine_manifest.csv`.
- **Environment Isolation**: `opi/research_agent.py` enforces `OPI_ENV=test` for mock provider; outside test mode, mock instantiation raises `PermissionError`.

---

## 6. Grounding and Discovery Results

- **Built-In Ingestion (`opi/ingest.py`)**:
  - Deterministic regex/DOM parsers tested against actual HTML fixtures.
  - Strict grounding enforcement: Any proposed value not matching snapshot text raises `IngestionError`. Tested in `tests/test_ingest.py::test_mismatch_between_typed_value_and_snapshot_is_refused` (PASS).
  - Raw market data saved with SHA-256 hash. Tested in `tests/test_ingest.py::test_market_data_saved_raw_with_hash` (PASS).
- **Automated Mainboard Discovery (`opi/discover.py`)**:
  - Live discovery dry-run identified 18 Mainboard candidates from exchange/aggregator dashboard.
  - Successfully discovered `Jio Platforms` and `Paras Healthcare` with status `BIDDING_OPEN` (closing 2026-10-23).
  - Successfully excluded SME IPOs (e.g. `Apex Solar Energy Limited`) and FPOs. Tested in `tests/test_discover.py::test_discovers_closed_unlisted_mainboard_ipos_from_fixture` (PASS).

---

## 7. Live Research-Agent Results

- **Status**: **NOT FIXED (needs user action)**.
- **Reason**: Live execution against live web filings requires an active `GEMINI_API_KEY` and network API access. Because no API key was provided by the user in this session, the live proof was not executed.
- Per Rule 1 and Phase 10 binding instructions, mock results were not substituted.

---

## 8. Honest Verdict, Hypotheses, Failure Modes & Phase 11 Recommendations

### Honest Verdict
Phase 10 successfully resolved the major integrity and automation deficits carried from earlier phases:
1. All synthetic mock files were purged from production data directories and quarantined with full cryptographic provenance.
2. The first genuine listing outcome (HD Fire Protect Limited) was recorded post-listing with official BSE trade evidence.
3. Input grounding is now enforced by code rather than manual operator discipline: any proposed value mismatching a code-saved snapshot is refused.
4. Mainboard discovery is automated, recognizing active issues (`Jio Platforms`, `Paras Healthcare`) and deferring them until bidding closes.
5. Verification suite `verify_all.py` v3 passed with 0 FAIL, 0 WARN on a fresh clone.

### Hypothesis Status
- **H1 (Automated Grounding Enforcement)**: Supported. Deterministic HTML parsers and string/numeric verification prevent ungrounded operator proposals from entering feature vectors.
- **H2 (Mainboard Discovery Viability)**: Supported. Direct parsing of aggregator schedules separates Mainboard from SME issues and accurately tracks bidding close dates.
- **H3 (Prospective Forward Performance)**: Unresolved / In Progress ($n = 1$ of 30). With $n = 1$, no empirical hypothesis testing is statistically valid.

### Known Failure Modes & Limitations
1. **Tail Pops Under-prediction (D-007)**: Champion model under-predicts pops > 50%.
2. **Interval Width & Coverage (D-008)**: 80% conformal intervals average 46.26 pp wide (over-conservative on pooled data, under-covering in upper tail).
3. **Absence of Live Research Agent Proof (D-026)**: Awaiting user API key.

### Recommendations for Phase 11
1. **Tail-Specific Regime Modeling**: Explore extreme-value calibration or conditional conformal prediction for high-subscription issues ($> 50\text{x}$) to address D-007.
2. **Conformal Width Narrowing**: Evaluate locally-weighted conformal prediction to reduce interval width on moderate-subscription issues while maintaining target coverage (D-008).
3. **Execute Live Agent Proof**: Upon provision of `GEMINI_API_KEY`, execute live research agent run for Jio Platforms post-bidding close on 2026-10-23.
4. **Prospective Outcome Ingestion**: Record official exchange listing outcomes for Fusion CX (2026-10-22), and Zetwerk, Sahajanand Medical, Tonbo Imaging, Bonfiglioli (2026-10-23).

---

## 9. Regulatory & Non-Advisory Statement

**Quantitative research decision aid only, not financial, investment, or trading advice.** Initial Public Offerings involve substantial capital risk. Model estimates and grey market quotes are probabilistic research aids and do not guarantee future listing performance. No statement or output from this system constitutes a recommendation to apply, buy, sell, or avoid any financial instrument.

---

## 10. Self-Audit (Yes/No with Evidence)

| Audit Question | Result | Evidence Reference |
|---|:---:|---|
| Does any `FIXED` defect lack a passing test or pasted command? | **NO** | All 8 FIXED defects in Phase 10 reference passing tests in `tests/` with outputs pasted in `2_building_and_execution.md`. |
| Does `verify_all.py` pass with 0 FAIL on a fresh clone? Was it edited to pass? | **YES / NO** | `verify_all.py` passed with 58 PASS, 0 WARN, 0 FAIL on a fresh clone. It was not edited to make checks pass. |
| Does any mock or test output exist under `data/`? | **NO** | Verified by `verify_all.py` mock checks and `test_no_mock_output_in_data_folders`. |
| Is any input value in a FORWARD row not found in its saved snapshot? | **NO** | Verified by `verify_all.py::check_forward_grounding()` across all 6 FORWARD rows. |
| Was any actual gain typed by hand? | **NO** | HD Fire Protect gain computed strictly by `update_actuals.py` from BSE official quote ₹334.40 vs issue ₹271.00. |
| Does any log timestamp differ from its commit time by more than tolerance? | **NO** | Verified by `verify_all.py::check_immutable_history()`. |
| Are any grounding rates reported that come from mock runs? | **NO** | All mock statistics purged; live agent status reported as NOT FIXED (needs user action). |
| Does the app or dashboard show probability outside measured range or "apply/avoid" wording? | **NO** | Suppressed outside `[0.091, 0.882]`; tested in `test_probability_hidden_outside_calibrated_range` and `test_streamlit_app_advisory_wording_prohibited`. |
| Was `data/ipo_phase5_final_test.csv` read for any decision? | **NO** | Preserved frozen; untouched. |
