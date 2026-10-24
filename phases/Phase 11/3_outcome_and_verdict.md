# Phase 11: Outcome & Verdict - Re-verify Phase 10, Mega-Issue Safety, Tail and Interval Fixes, Live Research Proof

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 11/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets remain open, partial, or carried over in Phase 11 Gate A:

1. **D-040: Out-of-Range and Mega-Issue Guard**
   - Status: **OPEN** (scheduled for Workstream A).
   - Details: Out-of-range inputs (e.g. Jio Platforms issue size ₹30,213 cr exceeding master maximum ₹27,870 cr) scored without explicit warning flags.
2. **D-041: Post-Mortem of Forward Errors**
   - Status: **OPEN** (scheduled for Workstream B).
   - Details: Bonfiglioli Transmissions (and Zetwerk) misses require structured post-mortem.
3. **D-044: Jio Sector Label Doubtful and Unverified**
   - Status: **OPEN** (scheduled for Workstream A / E).
   - Details: Sector label "IT & Technology" unevidenced in snapshot `data/evidence/research/2026-10-28_jio-platforms-limited.html`.
4. **D-026: Live Web Research Agent Proof**
   - Status: **PARTIAL** (scheduled for Workstream D, cloud GitHub Actions execution with OpenRouter).
5. **D-013: Upstream Audit Sample Evidence Snapshots**
   - Status: **PARTIAL / CARRIED OVER** (documented in README under Known Limitations).
6. **D-007: Tail Behavior (Extreme Listing Pops Under-Predicted)**
   - Status: **DEFERRED** (scheduled for Workstream C).
7. **D-008: Conformal Prediction Intervals Over-Conservative Overall**
   - Status: **DEFERRED** (scheduled for Workstream C).

---

## 2. Defect Ledger

| Defect ID | Phase | Description | Severity | Status Before Phase 11 | Status After Gate A11 | Due Phase | Regression Test Reference / Evidence |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** to **D-039** | 1-10 | Historical defects resolved or accepted in earlier phases | Various | Various | FIXED / ACCEPTED | - | See `DEFECTS.md` |
| **D-040** | 11 | Out-of-range inputs scored without warning flag | High | - | **OPEN** | 11 | `tests/test_scoring_guard.py` (Workstream A) |
| **D-041** | 11 | Forward prediction misses lack structured post-mortem | Medium | - | **OPEN** | 11 | `phases/Phase 11/forward_postmortem.md` (Workstream B) |
| **D-042** | 11 | Actions runs #9 and #10 failed; cause unrecorded | Medium | - | **FIXED** | 11 | `tests/test_ci.py::test_actions_failures_recorded` |
| **D-043** | 11 | Dashboard publishing unverified (Pages not configured) | Medium | - | **FIXED** | 11 | `tests/test_ci.py::test_dashboard_publishing_status_documented` |
| **D-044** | 11 | Jio sector label "IT & Technology" unverified | Low | - | **OPEN** | 11 | `phases/Phase 11/actions_failures.md` |

---

## 3. Forward Results Table (Generated from `predictions/prediction_log.csv`)

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.00 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | LISTED | BSE official opening trade (544994) evidenced in snapshot `1ef0c35a650c` |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.25 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `0783e1c0985b` |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.15 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `d69406a6b7e8` |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1160.00 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `4c486eeb1b8d` |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | LISTED | BSE official opening trade (544994) evidenced in snapshot `6df55c3addef` |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | Pending | Pending | +22.14% | +22.34% | Pending | Pending | FORWARD | listing scheduled 2026-10-28 |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | Pending | Pending | -2.56% | +1.59% | Pending | Pending | FORWARD | listing scheduled 2026-10-28 |

> **Provisional Evaluation Notice**: Sample size $n = 6$ of 30 target forward predictions. Results are strictly descriptive. No performance claims or statistical superiority statements are permitted prior to $n \ge 30$.

---

## 4. Gate A11 Results

### G1. Prior-Phase Recheck (Seed 11 Sample)
- 10 randomly sampled claims from Phase 10 outcome and verdict verified against underlying codebase. All 10 claims marked `VERIFIED` in `phases/Phase 11/prior_phase_recheck.csv`.
- Recomputed 5 headline numbers:
  1. Forward Model MAE (n=6 listed): 6.7817 pp (reported 6.78 pp).
  2. Forward Raw GMP MAE (n=5 with GMP): 7.9480 pp (reported 7.95 pp).
  3. Master dataset row count: 731 data rows.
  4. Prediction log breakdown: 14 total rows (6 test/invalid, 8 genuine FORWARD: 6 listed, 2 scheduled).
  5. Defect counts: 44 total defects parsed.

### G2. Forward Log Timing & Grounding Audit
- All 8 FORWARD rows verified:
  - `scored_at` strictly after `close_date`.
  - `scored_at` strictly before `listing_date`.
  - Feature snapshots committed before or at scoring time.

### G3 & G4. GitHub Actions Failures Audit (D-042, D-043)
- Analyzed failure logs for scheduled runs #9 and #10: failed due to `Hyundai Motor India` temporarily carrying `status=FORWARD` instead of `INVALID`, triggering assertion failure in `test_r6_prediction_log_status_and_filtering`.
- Resolved in commit `7f7dc89`; runs #11 through #18 passed green.
- Dashboard verified via `gh api repos/soul991/OPI/pages` (HTTP 404): Pages not enabled; dashboard maintained in-repo as static asset.

### G5. Outcome Ingestion Schedule
- Jio Platforms and Paras Healthcare list on 2026-10-28; will be ingested post-listing via `scripts/update_actuals.py` using official exchange evidence.

### G6. Stray Local Branch Check (D-033)
- Checked branch `local-work-2026-10-20`: all useful changes were already merged and verified in `main`.

---

## 5. Workstream Results
*(To be populated following completion of Workstreams A through E)*

---

## 6. Wording Check
- No comparative superiority claims ("beats", "wins", "proves") are made while $n < 30$.
- Explanations are labeled strictly as **Hypothesis (untested)**.

---

## 7. Self-Audit (Yes/No with Evidence)

| Audit Question | Result | Evidence Reference |
|---|:---:|---|
| Did any earlier-phase file change except by ERRATA? | **NO** | `git status` shows no earlier phase file modified. |
| Did any value enter a feature without a snapshot? | **NO** | All FORWARD rows grounded in code-saved snapshots under `data/evidence/`. |
| Did any report number get typed by hand? | **NO** | Headline numbers recomputed directly from raw prediction log and CSV files; table generated via `forward_report.py`. |
| Did any test pass only because of untracked local files? | **NO** | Tested on clean clone via `verify_all.py`. |
| Was the OpenRouter key kept out of the repo, logs, and snapshots? | **YES** | `git grep sk-or-` returns 0 occurrences. |
