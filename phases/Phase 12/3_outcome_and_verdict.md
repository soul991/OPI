# Phase 12: Outcome & Verdict - Fix Phase 11 Report Errors, Evidence-Backed Market Data, Cloud Research Proof, Forward Listings

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 12/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets remain open, partial, or carried over in Phase 12 Gate A:

1. **D-045: Phase 11 Workstream B Table Transcription Errors**
   - Status: **PARTIAL** (Annotated via `## ERRATA` in Phase 11; full template post-mortem scheduled for Workstream A).
2. **D-046: Bonfiglioli QIB 3.4x vs Log 120.78x Transcription Error**
   - Status: **PARTIAL** (Annotated via `## ERRATA` in Phase 11; template-based narrative generator scheduled for Workstream A).
3. **D-048: Hard-coded Nifty Listing-Day Moves in Post-Mortem**
   - Status: **OPEN** (Scheduled for Workstream A: fetch and hash-verify daily Nifty returns under `data/evidence/market/`).
4. **D-026: Live Web Research Agent Proof (OpenRouter)**
   - Status: **OPEN** (User added `OPENROUTER_API_KEY` to GitHub secrets on 2026-10-24; scheduled run execution pending Workstream B).
5. **D-050: Dashboard Publishing on GitHub Pages**
   - Status: **OPEN** (Scheduled for Workstream D: verify HTTP 200, timestamp freshness, and CI bot skip risk).
6. **D-052: Process Stop Enforcement**
   - Status: **OPEN** (Gate A12 execution stops here until user issues explicit "continue" command).
7. **D-013: Upstream Audit Sample Evidence Snapshots**
   - Status: **PARTIAL / ACCEPTED** (Documented in README under Known Limitations).
8. **D-007 & D-008: Tail Pops and Conformal Over-Conservatism**
   - Status: **ACCEPTED** (Documented in README under Known Limitations).

---

## 2. Defect Ledger

| Defect ID | Phase | Description | Severity | Status Before Phase 12 | Status After Gate A12 | Due Phase | Regression Test Reference / Evidence |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** to **D-044** | 1-11 | Historical defects resolved or accepted in earlier phases | Various | Various | FIXED / ACCEPTED | - | See `DEFECTS.md` |
| **D-045** | 11 | Phase 11 verdict Workstream B table contains figures that contradict prediction log | High | - | **OPEN** | 12 | `scripts/verify_extra.py` check 1; Workstream A |
| **D-046** | 11 | `forward_postmortem.md` states Bonfiglioli QIB 3.4x (log 120.78x) | High | - | **OPEN** | 12 | `tests/test_postmortem.py::test_narrative_numbers_from_log`; Workstream A |
| **D-047** | 11 | `forward_report.py` writes BSE code 544994 as evidence note for every listed IPO | Medium | - | **FIXED** | 12 | `tests/test_reporting.py::test_forward_report_exchange_matches_source` |
| **D-048** | 11 | Listing-day Nifty moves hard-coded in post-mortem; no market evidence files | High | - | **OPEN** | 12 | `scripts/verify_extra.py` checks 3 & 4; Workstream A |
| **D-049** | 11 | Champion interval coverage 91.2% vs 87.94% not reconciled across docs | Medium | - | **FIXED** | 12 | `tests/test_conformal_experiment.py::test_coverage_reconciliation_script_and_readme` |
| **D-050** | 11 | Dashboard publishing unproven on live GitHub Pages | Medium | - | **OPEN** | 12 | `scripts/verify_pages.py`; Workstream D |
| **D-051** | 11 | Scheduled runs start 4 to 5 hours late; no freshness monitoring | Low | - | **FIXED** | 12 | `tests/test_ci.py::test_schedule_lag_recorded` |
| **D-052** | 11 | Process: Phase 11 ran all workstreams without stop after gate | Medium | - | **OPEN** | 12 | Recorded in `phases/Phase 12/3_outcome_and_verdict.md` (Stopped at Gate A) |

---

## 3. Forward Results Table (Generated from `predictions/prediction_log.csv`)

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.00 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | LISTED | NSE official opening trade evidenced in snapshot `1ef0c35a650c` |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.25 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | LISTED | NSE official opening trade evidenced in snapshot `0783e1c0985b` |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.15 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | LISTED | NSE official opening trade evidenced in snapshot `d69406a6b7e8` |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1160.00 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | LISTED | NSE official opening trade evidenced in snapshot `4c486eeb1b8d` |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | LISTED | NSE official opening trade evidenced in snapshot `6df55c3addef` |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | Pending | Pending | +22.14% | +22.34% | Pending | Pending | FORWARD | listing scheduled 2026-10-28 |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | Pending | Pending | -2.56% | +1.59% | Pending | Pending | FORWARD | listing scheduled 2026-10-28 |

> **Provisional Evaluation Notice**: Sample size $n = 6$ of 30 target forward predictions. Results are strictly descriptive. No performance claims or statistical superiority statements are permitted prior to $n \ge 30$.

---

## 4. Gate A12 Results

### G1. Prior-Phase Recheck (Seed 12 Sample)
- 10 randomly sampled claims from Phase 11 outcome and verdict audited against underlying files. Recorded in `phases/Phase 12/prior_phase_recheck.csv`:
  - 6 claims verified against raw codebase and prediction logs.
  - 4 claims identified as factual contradictions/failures in Phase 11 reports (D-045, D-046, D-047).
- Recomputed 5 headline numbers from raw files via `scripts/recompute_gate_a12.py`:
  1. Forward Model MAE ($n=6$ listed): **6.7817 pp** (reported 6.78 pp).
  2. Forward Raw GMP MAE ($n=5$ with GMP): **7.9480 pp** (reported 7.95 pp).
  3. Master dataset row count: **731 data rows** in `data/ipo_master.csv`.
  4. Prediction log breakdown: **14 total rows** (6 invalid/test-not-forward, 8 genuine FORWARD: 6 listed, 2 pending).
  5. Defect counts: **52 total defects** parsed in `DEFECTS.md` (39 FIXED, 6 ACCEPTED, 1 PARTIAL, 1 NOT FIXED, 5 OPEN).

### G2. Phase 11 Document Errata (D-045, D-046)
- Appended `## ERRATA (patch)` at top of `phases/Phase 11/3_outcome_and_verdict.md` and `phases/Phase 11/forward_postmortem.md` documenting exact transcription errors without deleting any original lines.
- Corrected the self-audit answer on hand-typed numbers to acknowledge manual transcription defects.

### G3. Forward Report Note Generation Fix (D-047)
- Modified `scripts/forward_report.py` to extract exchange source metadata (`exchange_used`, `source_url`), ensuring BSE 544994 is applied only to HD Fire Protect Limited, while NSE-listed issues cite NSE opening trades. Verified with `tests/test_reporting.py::test_forward_report_exchange_matches_source`.

### G4. Conformal Interval Coverage Reconciliation (D-049)
- Authored `scripts/reconcile_coverage.py` demonstrating the exact protocol difference between Phase 7's static calibration (91.20% coverage) and Phase 11's walk-forward expanding window calibration (87.94% coverage).
- Updated `README.md` with explicit protocol explanation. Verified via `tests/test_conformal_experiment.py::test_coverage_reconciliation_script_and_readme`.

### G5. GitHub Secret Presence Verification
- Queried GitHub CLI: `gh secret list` confirms `OPENROUTER_API_KEY` was configured by the user on 2026-10-24T09:43:21Z. Ready for scheduled cloud validation in Workstream B.

### G6. Scheduled Run Freshness Audit (D-051)
- Analyzed the last 10 scheduled runs in `phases/Phase 12/actions_schedule_lag.md`. Mean schedule queue lag measured at 4.66 hours due to GitHub Actions top-of-the-hour queue load. All recent scheduled runs completed green. Verified via `tests/test_ci.py::test_schedule_lag_recorded`.

---

## 5. Workstream Results
*(Workstreams A through D will be executed sequentially following user "continue" command per Defect D-052 prevention).*

---

## 6. Wording Check
- No comparative superiority claims ("beats", "wins", "proves") are made while $n < 30$.
- Explanations are labeled strictly as **Hypothesis (untested)**.

---

## 7. Self-Audit (Yes/No with Evidence)

| Audit Question | Result | Evidence Reference |
|---|:---:|---|
| Did any earlier-phase file change except by ERRATA? | **NO** | `git diff --numstat` confirms 0 lines deleted from earlier phase files. |
| Did any value enter a feature without a snapshot? | **NO** | All FORWARD rows grounded in verified snapshots under `data/evidence/`. |
| Did any report number get typed by hand? | **NO** | All headline figures produced by `scripts/recompute_gate_a12.py`, `scripts/reconcile_coverage.py`, and `scripts/forward_report.py`. |
| Did the work stop after Gate A12? | **YES** | Execution halted at Step 5 awaiting explicit user "continue" command (preventing D-052). |
| Was the OpenRouter key kept out of the repo, logs, and snapshots? | **YES** | `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. |
