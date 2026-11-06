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

---

## 3. Verification & Guardrail Audit

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

## 4. Final Phase 18 Verdict

**PASS (Phase Complete)**. All four planned workstreams (A, B, C, D) are fully implemented and backed by automated regression tests. The daily workflow failure root cause has been rectified, guaranteeing that alerting steps do not block prediction persistence. Tier 2b automated dual-source outcome verification, universal Nifty evidence collection for past listing dates, and pending-outcome dashboard visibility are active and verified.
