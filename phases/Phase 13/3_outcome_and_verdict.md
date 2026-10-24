# Phase 13: Outcome & Verdict - Close Open Defects, Harden Automation, Hand Over to Maintenance Mode

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 13/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets remain open, partial, or pending in Phase 13 Gate A:

1. **D-026: Live Web Research Agent Proof (OpenRouter)**
   - Status: **NOT FIXED (needs upcoming scheduled IPO run)**
   - Audit: User configured `OPENROUTER_API_KEY` in GitHub secrets. In accordance with protocol rules, D-026 remains NOT FIXED until a green scheduled run extracts inputs for a genuine new IPO. Never create fake IPOs.
2. **D-045: Phase 11 Verdict Workstream B Table Transcription Contradictions**
   - Status: **PARTIAL**
   - Audit: Annotated via `## ERRATA` in Phase 11. D-053 errata block applied to `forward_postmortem.md` resolving underlying post-mortem contradiction. Full resolution tracked in Phase 13.
3. **D-054: Macro Snapshot 2026-10-23 Date Alignment**
   - Status: **OPEN (annotated in Gate A13)**
   - Audit: `data/corrections/macro_2026-10-23.md` documents true values without editing immutable logged rows. Automated labeling guard scheduled for Workstream A.
4. **D-055: Market Raw File Nomenclature and Original Payloads**
   - Status: **OPEN (decision recorded in Gate A13)**
   - Audit: Decision recorded in `phases/Phase 13/market_raw_decision.md`.
5. **D-056: Dashboard Defect Counter Stale & Missing Cloud Run Date**
   - Status: **FIXED in Gate A13**
   - Audit: `opi/report.py` updated to display last cloud run timestamp and parse DEFECTS.md accurately; verified with `tests/test_dashboard.py`.
6. **D-057 to D-061: Monitoring, Watchdog, Requirements Lock, Final Evaluation Preregistration, Runbook**
   - Status: **OPEN (scheduled for Workstreams A-D after "continue")**
7. **Jio Platforms and Paras Healthcare Actual Listing Outcomes**
   - Status: **PENDING (Listing scheduled 2026-10-28)**

---

## 2. Defect Ledger

| Defect ID | Phase Introduced | Description | Severity | Status Before Gate A13 | Status After Gate A13 | Due Phase | Regression Test Reference / Evidence |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** to **D-044** | 1-11 | Historical defects resolved or accepted in earlier phases | Various | FIXED / ACCEPTED | FIXED / ACCEPTED | - | See `DEFECTS.md` |
| **D-045** | 11 | Phase 11 verdict Workstream B table contains figures that contradict prediction log | High | OPEN | **PARTIAL** | 13 | `verify_extra.py` Check 1 PASS |
| **D-046** | 11 | `forward_postmortem.md` states Bonfiglioli QIB 3.4x (log 120.78x) | High | FIXED | **FIXED** | 12 | `tests/test_postmortem.py::test_narrative_numbers_from_log` |
| **D-047** | 11 | `forward_report.py` writes BSE code 544994 as evidence note for every listed IPO | Medium | FIXED | **FIXED** | 12 | `tests/test_reporting.py::test_forward_report_exchange_matches_source` |
| **D-048** | 11 | Listing-day Nifty moves hard-coded in forward_postmortem.py; no market evidence files | High | FIXED | **FIXED** | 12 | `verify_extra.py` Checks 3 & 4 PASS |
| **D-049** | 11 | Champion interval coverage 91.2% vs 87.94% not reconciled across docs | Medium | FIXED | **FIXED** | 12 | `tests/test_conformal_experiment.py::test_coverage_reconciliation_script_and_readme` |
| **D-050** | 11 | Dashboard publishing unproven on live GitHub Pages | Medium | FIXED | **FIXED** | 12 | `tests/test_ci.py::test_pages_published_and_guarded` |
| **D-051** | 11 | Scheduled runs start 4 to 5 hours late; no freshness monitoring | Low | FIXED | **FIXED** | 12 | `tests/test_ci.py::test_schedule_lag_recorded` |
| **D-052** | 11 | Process: Phase 11 ran all workstreams without stop after gate | Medium | FIXED | **FIXED** | 12 | `tests/test_gate_a.py::test_phase12_process_stop_and_results_log` |
| **D-053** | 12 | `phases/Phase 11/forward_postmortem.md` has no ERRATA block; wrong Bonfiglioli 3.4x | Medium | OPEN | **FIXED** | 13 | `verify_extra.py` 0 FAIL; `tests/test_reporting.py::test_phase11_postmortem_has_errata` |
| **D-054** | 12 | Macro snapshot labelled 2026-10-23 contains 2026-10-22 values | Low | OPEN | **OPEN** | 13 | `data/corrections/macro_2026-10-23.md` |
| **D-055** | 12 | `data/evidence/market/*_nifty.raw` is parsed output, not original response | Low | OPEN | **OPEN** | 13 | `phases/Phase 13/market_raw_decision.md` |
| **D-056** | 12 | Dashboard defect counter is stale (1 vs 2) and does not show last cloud run date | Low | OPEN | **FIXED** | 13 | `tests/test_dashboard.py` (3 passed) |
| **D-057** | 12 | No alert when a scheduled run fails | Medium | OPEN | **OPEN** | 13 | Workstream A |
| **D-058** | 12 | Schedule risks: runs start 4.7 h late; GitHub 60-day pause risk | Medium | OPEN | **OPEN** | 13 | Workstream A |
| **D-059** | 12 | Dependencies not pinned | Medium | OPEN | **OPEN** | 13 | Workstream A |
| **D-060** | 12 | The n = 30 evaluation is not preregistered or automated | Medium | OPEN | **OPEN** | 13 | Workstream C |
| **D-061** | 12 | No runbook for the user | Low | OPEN | **OPEN** | 13 | Workstream D |

---

## 3. Forward Results Table (Generated by `scripts/forward_report.py --markdown`)

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

## 4. Gate A13 Results & Independent Verification

### G1. Prior-Phase Recheck (Seed 13 Sample)
- Sampled 10 claims from Phase 12 in `phases/Phase 13/prior_phase_recheck.csv` (seed 13):
  - 5 claims on specific IPO figures (Tonbo, HD Fire, Zetwerk, Bonfiglioli, Fusion CX).
  - 3 claims of the form "file X contains Y" (Phase 11 forward_postmortem.md, Phase 11 3_outcome_and_verdict.md, 2026-10-21_nifty.json).
  - Identified that Phase 12 claimed an ERRATA block in `phases/Phase 11/forward_postmortem.md` that did not exist (D-053).
- Recomputed 5 headline metrics from raw data via `scripts/recompute_gate_a13.py`:
  1. Forward Model MAE ($n=6$ listed): **6.7817 pp** (reported 6.78 pp).
  2. Forward Raw GMP MAE ($n=5$ with GMP): **7.9480 pp** (reported 7.95 pp).
  3. Master dataset row count: **731 data rows** in `data/ipo_master.csv`.
  4. Prediction log breakdown: **14 total rows** (6 invalid/test-not-forward, 8 genuine FORWARD: 6 listed, 2 pending).
  5. Defect counts: **61 total defects** seeded in `DEFECTS.md` (43 FIXED, 6 ACCEPTED, 2 PARTIAL, 1 NOT FIXED, 9 OPEN).

### G2. Phase 11 Post-Mortem Errata: Bonfiglioli Transmissions (D-053)
- Appended `## ERRATA (patch)` at top of `phases/Phase 11/forward_postmortem.md` documenting Bonfiglioli erroneous 3.4x transcription error for institutional demand (true QIB 120.78x) and invalidating the "subdued demand" hypothesis.
- Added regression test `tests/test_reporting.py::test_phase11_postmortem_has_errata`.

### G3. Macro Snapshot Annotation & Raw File Decision (D-054, D-055)
- Created `data/corrections/macro_2026-10-23.md` annotating true Oct 23 market values without mutating logged rows (D-054).
- Recorded naming and hashing decision in `phases/Phase 13/market_raw_decision.md` (D-055).

### G4. Dashboard Defect Counter & Run Timestamp Sync (D-056)
- Updated `opi/report.py` to retrieve the latest Actions run timestamp and display it on the dashboard card and footer.
- Regenerated `dashboard/index.html` reflecting 11 open/partial defects matching `DEFECTS.md` and last cloud run `2026-10-24T10:10:20Z`.
- Added regression tests in `tests/test_dashboard.py`.

### G5. GitHub Secret Audit & Actions Health
- `gh secret list` confirms `OPENROUTER_API_KEY` present.
- Last 10 scheduled runs inspected: 9 consecutive successful runs since run #11 (`40084848056`, `40000268262`, `39942489490`, `39829609188`, `39767607795`, `39651821144`, `39589079766`, `39473306471`, `39410837110`). Recorded in `phases/Phase 13/actions_status.md`.

### Verification Suite Outputs

#### `scripts/verify_extra.py` Comparison (Start vs Gate A13)
- **Start (`phases/Phase 13/verify_extra_start.txt`)**: 5 PASS, 0 WARN, 2 FAIL.
  - Failures: Bonfiglioli erroneous 3.4x figure vs log QIB 120.78x, and `subdued demand` narrative.
- **End of Gate A13**: **7 PASS, 0 WARN, 0 FAIL**.
```
[PASS] subscription figures in Phase 11+ reports equal prediction_log values                    0 mismatches
[PASS] no company other than HD Fire cites BSE code 544994                                      0 lines
[PASS] no hard-coded dated numeric constants in scripts/ or opi/                                0 lines
[PASS] each listed date has a parsed Nifty evidence file (close + prev close or day return)     missing: none
[PASS] no "weak/only/subdued demand" text for IPOs with QIB > 50x                               0 lines
[PASS] README's two champion coverage figures (91.2% vs 87.94%) are reconciled in text          
[PASS] no OpenRouter key material in tracked files                                              

SUMMARY: 7 pass, 0 warn, 0 fail
```

---

## 5. Workstream Results
*(Workstreams A through E will begin only after explicit user "continue" response).*

---

## 6. Wording Check
- No comparative superiority claims ("beats", "wins", "proves") are made while $n < 30$.
- Explanations labeled strictly as **Hypothesis (untested)**.

---

## 7. Self-Audit (Yes/No with Evidence)

| Audit Question | Result | Evidence Reference |
|---|:---:|---|
| Did any earlier-phase file change except by ERRATA? | **NO** | `git diff --numstat main -- phases/Phase\ 11` confirms 0 lines deleted; only top ERRATA added. |
| Did any value enter a feature without a snapshot? | **NO** | All FORWARD rows grounded in verified snapshots under `data/evidence/`. |
| Did any report number get typed by hand? | **NO** | All figures recomputed via `scripts/recompute_gate_a13.py` and `scripts/forward_report.py`. |
| Did the work stop after Gate A13? | **YES** | Execution strictly halted at Step 5 awaiting explicit user "continue" confirmation. |
| Was the OpenRouter key kept out of the repo, logs, and snapshots? | **YES** | `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. |
