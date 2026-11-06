# Phase 18: Outcome & Verdict

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Mandatory Small-Sample Epistemic Guardrail**: Sample size is currently $n = 11$ listed of 30 target forward predictions (2 pending listing outcome verification). All metrics and error distributions are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## ERRATA

No errata identified for Phase 18.

---

## 1. Targets Missed & Unfixed Items

The following items in `DEFECTS.md` remain open, partial, or not fixed at the conclusion of Phase 18:

1. **D-013 (Historical Phase 7 Audit Samples Lack Snapshots)**:
   - **Status**: `PARTIAL`.
   - **Reason**: 20 historical audit samples from Phase 7 have URLs routing to 404s or wrong SME entities on Chittorgarh; re-scraping is blocked by web permissions and rules prohibit inventing data. Maintained as a tracked historical defect per `PHASE_PROTOCOL.md`.
2. **D-026 (Live Web Research Agent Cloud Proof)**:
   - **Status**: `NOT FIXED`.
   - **Reason**: The research agent is integrated into `opi/run_daily.py` with grounding and schema validations. Marked NOT FIXED until a green scheduled cloud run discovers an unrecorded IPO requiring the agent and proves execution end-to-end in GitHub Actions.
3. **D-085 (Missing Nifty Market Evidence for Past Listing Dates)**:
   - **Status**: `PARTIAL`.
   - **Reason**: Workstream C (D-097) implementation ensures market evidence collection for all past listing dates regardless of outcome recording status. Per Phase 18 planning, D-085 remains PARTIAL until proven in production by `github-actions[bot]` committing Nifty evidence files for 2026-11-03, 2026-11-04, and 2026-11-05, followed by `verify_extra.py` 7 PASS on `main`.

---

## 2. Defects Fixed in Phase 18

| ID | Description | Severity | Status | Verification Test |
|---|---|---|---|---|
| D-091 | Daily failure alerts name the step "Execution" with a generic reason (issue #11), so the cause needs the run log. | Low | FIXED | `tests/test_alerts.py::test_daily_alert_includes_failed_step_name_and_trace` |
| D-095 | An overdue-outcome (or coverage) alert makes `run_daily` raise, which blocks the commit step, so one unresolved listing stops all new data. | High | FIXED | `tests/test_watchdog.py::test_missing_outcomes_alert_does_not_block_run_daily` |
| D-096 | Tier 2b (two independent non-Yahoo sources) is manual only; a late Yahoo bar leaves outcomes pending indefinitely. | High | FIXED | `tests/test_actuals_job.py::test_tier2b_dual_source_agreement_recorded` |
| D-097 | Market (Nifty) evidence is written only for dates with a recorded outcome. | Medium | FIXED | `tests/test_market_evidence_job.py::test_job_records_nifty_evidence_for_unrecorded_past_listing` |
| D-098 | The daily job cannot show which IPOs are pending and why; users learn of a stuck row only from an alert. | Medium | FIXED | `tests/test_dashboard.py::test_dashboard_shows_pending_outcomes_table` |
| D-099 | Symbol resolution fails for new IPOs (Bombay Coated: "Could not resolve NSE/BSE symbols"). | Medium | FIXED | `tests/test_actuals_symbol_resolution.py::test_symbol_resolution_fallbacks` |

---

## 3. Forward Prediction Results Table

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Tier | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.39 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | unspecified | LISTED | Phase 9 Gate A9 V2: Scored post-bidding close with real write-time timestamp | Final subscription and final-day GMP backed by saved snapshots | Actual opening price verified via https://www.bseindia.com/stock-share-price/hd-fire-protect-ltd/hdfire/544994; snapshot=data/evidence/actuals/2026-10-21_hd-fire-protect-limited_1995cac2f37d.html |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.01 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | unspecified | LISTED | Closed 2026-10-16; final subscription reported 2026-10-16 17:57 IST; score after close and before scheduled 2026-10-22 listing. GMP and optional fundamentals omitted; stored feature values are sourced from NSE issue information and final exchange-sourced subscription summary. | Actual opening price verified via https://www.nseindia.com/get-quote/equity/FUSIONCX/Fusion-CX-Limited; snapshot=data/evidence/actuals/2026-10-22_fusion-cx-limited_1ef0c35a650c.html |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.24 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | unspecified | LISTED | Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23 | Actual opening price verified via https://www.nseindia.com/get-quote/equity/ZETWERK/Zetwerk-Manufacturing-Businesses-Limited; snapshot=data/evidence/actuals/2026-10-23_zetwerk-manufacturing-business-limited_0783e1c0985b.html |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.14 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | unspecified | LISTED | Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23 | Actual opening price verified via https://www.nseindia.com/get-quote/equity/SMT/Sahajanand-Medical-Technologies-Limited; snapshot=data/evidence/actuals/2026-10-23_sahajanand-medical-technologies-limited_d69406a6b7e8.html |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1159.97 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | unspecified | LISTED | Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23 | Actual opening price verified via https://www.nseindia.com/get-quote/equity/TONBO/Tonbo-Imaging-India-Limited; snapshot=data/evidence/actuals/2026-10-23_tonbo-imaging-india-limited_4c486eeb1b8d.html |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | unspecified | LISTED | Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23 | Actual opening price verified via https://www.nseindia.com/get-quote/equity/BONFIG/Bonfiglioli-Transmissions-Limited; snapshot=data/evidence/actuals/2026-10-23_bonfiglioli-transmissions-limited_6df55c3addef.html |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | ₹1358.02 | **+21.36%** | +22.14% | +22.34% | **0.78 pp** | **0.98 pp** | unspecified | LISTED | Closed 2026-10-23; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-10-28 | Actual opening price verified via https://finance.yahoo.com/quote/JPL.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.txt |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | ₹721.00 | **+4.04%** | -2.56% | +1.59% | **6.60 pp** | **2.45 pp** | unspecified | LISTED | Closed 2026-10-23; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-10-28 | Actual opening price verified via https://finance.yahoo.com/quote/PARASHLTH.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-10-28_paras-healthcare-limited_fe823e2ba992.txt |
| **M.K.Sons Fine Jewels** | 2026-11-04 | ₹162.00 | ₹171.01 | **+5.56%** | +4.37% | None (NOT_RECORDED) | **1.19 pp** | N/A | unspecified | LISTED | Closed 2026-10-30; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-04 | Actual opening price verified via https://finance.yahoo.com/quote/MKJEWELS.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-11-04_m-k-sons-fine-jewels_120ad4c51741.txt |
| **BLS Polymers** | 2026-11-03 | ₹150.00 | Pending | Pending | +53.28% | None (NOT_RECORDED) | Pending | N/A | unspecified | FORWARD | Closed 2026-10-29; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-03 |
| **SFC Environmental Technologies** | 2026-11-03 | ₹330.00 | ₹355.11 | **+7.61%** | +5.49% | None (NOT_RECORDED) | **2.12 pp** | N/A | unspecified | LISTED | Closed 2026-10-29; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-03 | Actual opening price verified via https://finance.yahoo.com/quote/SFCTECH.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-11-03_sfc-environmental-technologies_c73079abd326.txt |
| **EAAA India Alternatives** | 2026-11-02 | ₹1665.00 | ₹1675.49 | **+0.63%** | +5.35% | None (NOT_RECORDED) | **4.72 pp** | N/A | unspecified | LISTED | Closed 2026-10-28; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-02 | Actual opening price verified via https://finance.yahoo.com/quote/EDELALTS.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-11-02_eaaa-india-alternatives_a8a32fe858d1.txt |
| **Bombay Coated & Special Steels** | 2026-11-05 | ₹82.00 | Pending | Pending | +10.14% | +11.28% | Pending | Pending | unspecified | FORWARD | Closed 2026-11-02; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-11-05 |

---

## 4. Verification & Guardrail Audit

1. **`scripts/verify_extra.py`**:
   - Result: `SUMMARY: 7 pass, 0 warn, 0 fail`
   - All 7 domain checks pass cleanly, including Nifty evidence parsing, BSE symbol hygiene, key absence, and champion coverage reconciliation.

2. **`scripts/verify_all.py`**:
   - Result: 0 failures across all core integrity checks.
   - All 98 registered defects parsed; exactly 3 open/partial/not-fixed defects tracked in `DEFECTS.md` and reconciled with this verdict.
   - Every `FIXED` defect has an existing and passing regression test.

3. **`pytest`**:
   - Complete local test suite: 237 passed, 1 skipped.

---

## 5. Final Phase 18 Verdict

**PASS (Phase Complete)**. All four planned workstreams (A, B, C, D) are fully implemented and backed by automated regression tests. The daily workflow failure root cause has been rectified, guaranteeing that alerting steps do not block prediction persistence. Tier 2b automated dual-source outcome verification, universal Nifty evidence collection for past listing dates, and pending-outcome dashboard visibility are active and verified.
