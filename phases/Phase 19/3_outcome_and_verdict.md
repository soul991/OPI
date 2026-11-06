# Phase 19: Outcome & Verdict

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Mandatory Small-Sample Epistemic Guardrail**: Sample size is currently $n = 11$ listed of 30 target forward predictions (2 pending listing outcome verification). All metrics and error distributions are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## ERRATA

### H-02 Prior Cohort First-9 MAE Reconciliation
In Gate A19, the verification audit script calculated the MAE across the "first 9 listed forward IPOs" as **5.4578 percentage points**, disagreeing with Phase 17's reported figure of **5.8500 percentage points**.

**Root Cause Investigation**:
In `predictions/prediction_log.csv`, rows are appended chronologically as IPOs close bidding and are scored. M.K.Sons Fine Jewels (listed 2026-11-04, scored error 1.19 pp) was scored earlier and recorded at row 14, whereas EAAA India Alternatives (listed 2026-11-02, scored error 4.72 pp) was recorded at row 17. The Gate A19 audit script used `.iloc[:9]` in file-append order, selecting M.K.Sons instead of chronological EAAA India Alternatives:
- Append-order first 9 sum: $2.73 + 1.21 + 6.23 + 0.43 + 8.99 + 21.10 + 0.78 + 6.46 + 1.19 = 49.12 \implies 49.12 / 9 = 5.4578\text{ pp}$.

When forward rows are sorted chronologically by `(listing_date, scored_at)`, the first 9 listed IPOs are identical to the true Phase 17 forward cohort (ending at EAAA India Alternatives):
- Chronological first 9 sum: $2.73 + 1.21 + 6.23 + 0.43 + 8.99 + 21.10 + 0.78 + 6.46 + 4.72 = 52.65 \implies 52.65 / 9 = \mathbf{5.8500\text{ pp}}$ exactly.

**Resolution**:
1. Phase 17's reported figure of 5.8500 pp was correct.
2. `phases/Phase 19/prior_phase_recheck.csv` has been corrected by appending an `H-02-ERRATA` note preserving the original audit trail.
3. `scripts/forward_report.py` has been updated to sort forward rows chronologically before computing prior cohort metrics.
4. Regression test `tests/test_reporting.py::test_forward_report_chronological_first_9_mae` has been added.
5. Across the full current cohort of $n = 11$ listed forward IPOs, the provisional model MAE is **5.0909 percentage points** ($56.00 / 11$).

---

## 1. Targets Missed & Unfixed Items

The following items in `DEFECTS.md` remain open, partial, or not fixed at the conclusion of Phase 19:

1. **D-013 (Historical Phase 7 Audit Samples Lack Snapshots)**:
   - **Status**: `PARTIAL`.
   - **Reason**: 20 historical audit samples from Phase 7 have URLs routing to 404s or wrong SME entities on Chittorgarh; re-scraping is blocked by web permissions and project rules strictly prohibit inventing data. Maintained as a tracked historical defect per `PHASE_PROTOCOL.md`.
2. **D-026 (Live Web Research Agent Cloud Proof)**:
   - **Status**: `NOT FIXED`.
   - **Reason**: The research agent is integrated into `opi/run_daily.py` with grounding and schema validations. Marked NOT FIXED until a green scheduled cloud run discovers an unrecorded IPO requiring the agent and proves execution end-to-end in GitHub Actions.
3. **D-096 (Automate Tier 2b Dual-Source Outcome Verification)**:
   - **Status**: `PARTIAL`.
   - **Reason**: Automated Tier 2b resolution logic is implemented in `opi/actuals.py` and validated via tests `test_tier2b_dual_source_agreement_recorded` and `test_tier2b_divergence_beyond_tolerance_rejected`. In cloud runs, BLS Polymers remains `PENDING_REVIEW` because Yahoo Finance (248.0, NSE) and Chittorgarh (244.1, BSE) diverge by 1.57% (> 1.0% tolerance). A third independent source (Groww) quotes 248.0 (NSE), agreeing with Yahoo but differing in exchange from Chittorgarh (244.1, BSE). Under pre-registered arbitration rules (D-100), cross-exchange prices cannot arbitrate without intra-exchange agreement. Retained as PARTIAL until cloud execution encounters two agreeing non-Yahoo sources on the same exchange.

---

## 2. Defects Fixed & Accepted in Phase 19

| ID | Description | Severity | Status | Verification Test |
|---|---|---|---|---|
| D-085 | Missing Nifty market evidence for unrecorded listed dates causes verify_extra check 4 failure. | High | FIXED | `tests/test_market_evidence_job.py::test_job_records_nifty_evidence_for_unrecorded_past_listing` (Cloud proof: Actions run `42218253536`, `verify_extra.py` check 4 PASS) |
| D-091 | Daily and watchdog failure alerts name the step "Execution" with a generic reason (issue #11, watchdog run 42259466958). | Low | FIXED | `tests/test_alerts.py::test_watchdog_alert_names_failing_check_from_reason_file` (Cloud proof: Actions run `42297601919`, Issue #21 comment 1 named `check (d) missing outcomes`) |
| D-099 | Chittorgarh overview page format changes break symbol resolution for new listings. | Medium | FIXED | `tests/test_actuals_symbol_resolution.py::test_symbol_resolution_fallbacks` (Cloud proof: Actions run `42218253536` resolved `BCSSL.NS`) |
| D-100 | Divergence between Tier 2 primary and secondary sources leaves outcome in PENDING_REVIEW indefinitely without arbitration. | Medium | FIXED | `tests/test_actuals_divergence.py::test_arbitration_strict_majority_2_of_3_recorded` |
| D-101 | Evidence manifests store bare numbers without publisher or exchange labelling, making divergence diagnosis manual. | Low | FIXED | `tests/test_actuals_manifest.py::test_source_value_labelling_and_manifest_fields` |
| D-102 | GitHub Pages deployment timed out after 10 minutes in Actions run 42190760462. | Low | ACCEPTED | Transient GitHub Pages infrastructure deployment timeout; subsequent Actions runs `42290565047` and `42297531379` succeeded in under 3 minutes with no code changes. |

---

## 3. Forward Prediction Results Table

From `scripts/forward_report.py`:
- **Evaluated (Listed) Rows**: 11 of 30 target
- **Pending (Unlisted) Rows**: 2
- **Provisional Model MAE**: 5.09 percentage points (n=11)
- **Prior Cohort Model MAE**: 5.85 percentage points (n=9)
- **Provisional Raw GMP MAE**: 6.15 percentage points (n=7)

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Tier | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.39 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | unspecified | LISTED | Phase 9 Gate A9 V2: Scored post-bidding close with real write-time timestamp | Final subscription and final-day GMP backed by saved snapshots | Actual opening price verified via https://www.bseindia.com/stock-share-price/hd-fire-protect-ltd/hdfire/544994; snapshot=data/evidence/actuals/2026-10-21_hd-fire-protect-limited_1995cac2f37d.html |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.01 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | unspecified | LISTED | Closed 2026-10-16; final subscription reported 2026-10-16 17:57 IST; score after close and before scheduled 2026-10-22 listing. GMP and optional fundamentals omitted; stored feature values are sourced from NSE issue information and final exchange-sourced subscription summary. | Actual opening price verified via https://www.nseindia.com/get-quote/equity/FUSIONCX/Fusion-CX-Limited; snapshot=data/evidence/actuals/2026-10-22_fusion-cx-limited_1ef0c35a650c.html |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.24 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | unspecified | LISTED | Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23 | Actual opening price verified via https://www.nseindia.com/get-quote/equity/ZETWERK/Zetwerk-Manufacturing-Businesses-Limited; snapshot=data/evidence/actuals/2026-10-23_zetwerk-manufacturing-business-limited_0783e1c0985b.html |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.14 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | unspecified | LISTED | Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23 | Actual opening price verified via https://www.nseindia.com/get-quote/equity/SMT/Sahajanand-Medical-Technologies-Limited; snapshot=data/evidence/actuals/2026-10-23_sahajanand-medical-technologies-limited_d69406a6b7e8.html |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1159.97 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | unspecified | LISTED | Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23 | Actual opening price verified via https://www.nseindia.com/get-quote/equity/TONBO/Tonbo-Imaging-India-Limited; snapshot=data/evidence/actuals/2026-10-23_tonbo-imaging-india-limited_4c486eeb1b8d.html |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | unspecified | LISTED | Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23 | Actual opening price verified via https://www.nseindia.com/get-quote/equity/BONFIG/Bonfiglioli-Transmissions-Limited; snapshot=data/evidence/actuals/2026-10-23_bonfiglioli-transmissions-limited_6df55c3addef.html |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | ₹1358.02 | **+21.36%** | +22.14% | +22.34% | **0.78 pp** | **0.98 pp** | unspecified | LISTED | Closed 2026-10-23; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-10-28 | Actual opening price verified via https://finance.yahoo.com/quote/JPL.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.txt |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | ₹721.00 | **+4.04%** | -2.56% | +1.59% | **6.46 pp** | **2.31 pp** | unspecified | LISTED | Closed 2026-10-23; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-10-28 | Actual opening price verified via https://finance.yahoo.com/quote/PARASHLTH.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-10-28_paras-healthcare-limited_fe823e2ba992.txt |
| **M.K.Sons Fine Jewels** | 2026-11-04 | ₹162.00 | ₹171.01 | **+5.56%** | +4.37% | None (NOT_RECORDED) | **1.19 pp** | N/A | unspecified | LISTED | Closed 2026-10-30; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-04 | Actual opening price verified via https://finance.yahoo.com/quote/MKJEWELS.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-11-04_m-k-sons-fine-jewels_120ad4c51741.txt |
| **BLS Polymers** | 2026-11-03 | ₹150.00 | Pending | Pending | +53.28% | None (NOT_RECORDED) | Pending | N/A | unspecified | FORWARD | Closed 2026-10-29; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-03 | Status: PENDING_REVIEW (yfinance=248.0 [NSE] vs second_source=244.1 [BSE], diff=1.57% > 1.0% tolerance; arbitration skipped due to exchange mismatch) |
| **SFC Environmental Technologies** | 2026-11-03 | ₹330.00 | ₹355.11 | **+7.61%** | +5.49% | None (NOT_RECORDED) | **2.12 pp** | N/A | unspecified | LISTED | Closed 2026-10-29; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-03 | Actual opening price verified via https://finance.yahoo.com/quote/SFCTECH.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-11-03_sfc-environmental-technologies_c73079abd326.txt |
| **EAAA India Alternatives** | 2026-11-02 | ₹1665.00 | ₹1675.49 | **+0.63%** | +5.35% | None (NOT_RECORDED) | **4.72 pp** | N/A | unspecified | LISTED | Closed 2026-10-28; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-02 | Actual opening price verified via https://finance.yahoo.com/quote/EDELALTS.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-11-02_eaaa-india-alternatives_a8a32fe858d1.txt |
| **Bombay Coated & Special Steels** | 2026-11-05 | ₹82.00 | Pending | Pending | +10.14% | +11.28% | Pending | Pending | unspecified | FORWARD | Closed 2026-11-02; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-05 | Status: SKIPPED_NO_MATCH (Tier 2 primary source (BCSSL.NS) failed: LISTING_DAY_BAR_MISSING: first bar is 2026-11-06, listing date 2026-11-05) |

---

## 4. Verification & Guardrail Audit

1. **`scripts/verify_extra.py`**:
   - Result: `SUMMARY: 7 pass, 0 warn, 0 fail`
   - Checks pass cleanly: Nifty market evidence complete, no hardcoded constants, no key leakage, BSE symbol hygiene preserved, and champion coverage reconciled.

2. **`scripts/verify_all.py`**:
   - Result: `SUMMARY: 82 pass, 0 warn, 0 fail`
   - All 102 registered defects parsed; exactly 3 open/partial/not-fixed defects tracked in `DEFECTS.md` (D-013, D-026, D-096) and fully reconciled with this verdict.
   - Every `FIXED` defect has an existing, passing regression test.

3. **`pytest`**:
   - Complete local test suite: 255 passed, 1 skipped.

4. **Local CI Verification (`ci_local.py`)**:
   - Result: `CI_LOCAL: PASS` (all daily job, test suite, and verification steps pass in isolated environment).

---

## 5. Final Phase 19 Verdict

**PASS (Phase Complete)**. All Phase 19 workstreams (A, B, C, D) are fully implemented, verified, and audited against hard ground-truth rules. Source value metadata labelling (D-101) eliminates exchange ambiguity in evidence manifests. Pre-registered divergence arbitration (D-100) establishes an objective majority-based resolution protocol without loosening the strict 1.0% tolerance constant. Proven defects D-085, D-091, and D-099 are closed with live cloud execution proofs. The prior cohort MAE errata (H-02) is formally reconciled to 5.8500 percentage points, with the overall 11-IPO provisional model MAE at 5.0909 percentage points.
