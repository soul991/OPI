# Phase 16: Outcome & Verdict (Gate A16 State)

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 16/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Epistemic Guardrail**: Sample size is currently $n = 8$ of 30 target forward predictions ($n = 7$ with GMP, 4 pending unlisted). All metrics and error distributions are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets remain open, partial, or pending at Gate A16:

1. **D-026: Live Web Research Agent Proof (OpenRouter)**
   - Status: **NOT FIXED (awaiting real new IPO in scheduled run)**
   - Reason: In accordance with project rules ("Never create fake IPOs to prove the research agent; leave D-026 NOT FIXED until a scheduled run handles a real new IPO"), D-026 remains NOT FIXED until an upcoming Mainboard IPO bidding cycle appears in scheduled runs.
2. **D-071: Dashboard Card & verify_all NOT FIXED count**
   - Status: **PARTIAL (needs user action)**
   - Reason: Dashboard generation was fixed in Phase 14 (`opi/report.py`), but `scripts/verify_all.py` line 202 continues to count only `OPEN` and `PARTIAL`. Updating `verify_all.py` status tuple is pending user action; agents are strictly forbidden from modifying control verification scripts.
3. **D-079: Pre-Listing Predictions List**
   - Status: **OPEN (seeded in Gate A16)**
   - Reason: Pending forward predictions are visible only as "Pending" rows in the audit trail; IPOs with bidding open are invisible. Scheduled for Workstream A.
4. **D-080: Unscored IPO Watchdog & Coverage Alerts**
   - Status: **OPEN (seeded in Gate A16)**
   - Reason: Four IPOs sat unscored for days while their listing dates approached, with green runs and no alert. Scheduled for Workstream D.
5. **D-081: Automatic GMP Page Discovery**
   - Status: **OPEN (seeded in Gate A16)**
   - Reason: `gmp_url` is never found automatically, so new IPOs are scored without GMP. Scheduled for Workstream B.
6. **D-082: Research Agent in Daily Scoring Pipeline**
   - Status: **OPEN (seeded in Gate A16)**
   - Reason: The research agent is not part of the daily job; D-026 is unprovable. Scheduled for Workstream C.
7. **D-083: Monthly Retraining Pull Request Reporting**
   - Status: **OPEN (seeded in Gate A16)**
   - Reason: Monthly retraining runs dry-run without promotion, opens no pull request, and Phase 13 verdict claim overstates. Scheduled for Workstream D.
8. **D-084: Audit of Four 2026-11-01 Forward Scored Rows**
   - Status: **OPEN (seeded in Gate A16)**
   - Reason: Four automatically scored rows had not been audited for provenance, final subscription, and snapshots. Audited in Gate A16 check G6.

---

## 2. Defect Ledger

All 84 defects tracked in [`DEFECTS.md`](../../DEFECTS.md):

| Defect ID | Phase Introduced | Description | Severity | Status Before Gate A16 | Status After Gate A16 | Due Phase | Verification Proof |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **D-001** to **D-065** | 1-13 | Historical defects resolved or accepted in earlier phases | Various | FIXED / ACCEPTED | **FIXED / ACCEPTED** | - | See `DEFECTS.md` |
| **D-066** | 14 | `opi/run_daily.py` logs SKIPPED_BLOCKED_SOURCE for listed IPOs without attempt | Medium | FIXED | **FIXED** | 14 | `tests/test_actuals_job.py::test_tier2_success_with_agreeing_second_source` |
| **D-067** | 14 | No alert when a listed row has empty outcome > 2 days | Medium | FIXED | **FIXED** | 14 | `tests/test_watchdog.py::test_missing_outcomes_threshold_boundary` |
| **D-068** | 14 | Outcome source cloud reachability unproven; WAF blocks exchanges | Medium | FIXED | **FIXED** | 14 | `tests/test_actuals_job.py::test_two_tier_probe_committed` |
| **D-069** | 14 | Job cannot tell market hours on listing day | Low | FIXED | **FIXED** | 14 | `tests/test_actuals_job.py::test_is_listing_ready_for_actuals_market_hours_rule` |
| **D-070** | 14 | Dashboard lacked count/names of listed IPOs pending outcome | Low | FIXED | **FIXED** | 14 | `tests/test_dashboard.py::test_dashboard_shows_listed_outcome_pending_count_and_names` |
| **D-071** | 14 | Dashboard and verify_all count only OPEN/PARTIAL, omitting NOT FIXED | Low | PARTIAL | **PARTIAL** | 14 | `tests/test_dashboard.py::test_dashboard_defect_counter_matches_register` |
| **D-072** | 14 | Tier 2 silently falls back to earliest bar when listing-date bar is missing | Medium | FIXED | **FIXED** | 15 | `tests/test_actuals_job.py::test_yfinance_rejects_missing_listing_day_bar_paras_data` |
| **D-073** | 14 | No audited append-only way to correct recorded outcomes | Medium | FIXED | **FIXED** | 15 | `tests/test_outcomes_corrections.py::test_reports_agree_with_effective_value` |
| **D-074** | 14 | D-068 marked FIXED from win32 probe rather than cloud runner | Medium | FIXED | **FIXED** | 15 | `tests/test_actuals_job.py::test_runner_probe_committed_and_verified` |
| **D-075** | 14 | Watchdog failed on runner (run 41090951686, issue #6) due to missing path | Medium | FIXED | **FIXED** | 15 | `tests/test_workflow_entrypoints.py::test_workflow_entrypoints_smoke` |
| **D-076** | 15 | Process: fixes pushed straight to main without defect id, branch or PR | Low | FIXED | **FIXED** | 15 | `tests/test_ci.py::test_phase15_process_rule_defect_registration_and_branch_pr` |
| **D-077** | 10 | `opi/discover.py` never sets sub_url, skipping CLOSED_UNLISTED IPOs | High | FIXED | **FIXED** | 15 | `tests/test_discover.py::test_derive_subscription_url_from_overview_url` |
| **D-078** | 15 | `derive_subscription_url` corrupts protocol-relative and edge-case URLs | Low | FIXED | **FIXED** | 15 | `tests/test_discover.py::test_derive_subscription_url_edge_cases` |
| **D-079** | 16 | No pre-listing predictions list | High | OPEN | **OPEN** | 16 | Scheduled for Workstream A |
| **D-080** | 16 | Four IPOs sat unscored for days without alert | High | OPEN | **OPEN** | 16 | Scheduled for Workstream D |
| **D-081** | 16 | `gmp_url` is never found automatically | High | OPEN | **OPEN** | 16 | Scheduled for Workstream B |
| **D-082** | 16 | Research agent is not part of daily job | Medium | OPEN | **OPEN** | 16 | Scheduled for Workstream C |
| **D-083** | 16 | Monthly retraining never promotes listed rows and opens no PR | Medium | OPEN | **OPEN** | 16 | Scheduled for Workstream D |
| **D-084** | 16 | Four automatically scored rows (2026-11-01) not audited | Medium | OPEN | **OPEN** | 16 | Gate check G6 |

---

## 3. Forward Table from `forward_report.py --markdown`

Generated directly via `python scripts/forward_report.py --markdown`:

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Tier | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | unspecified | LISTED | BSE official opening trade (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.00 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | unspecified | LISTED | NSE official opening trade evidenced in snapshot `1ef0c35a650c` |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.25 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `0783e1c0985b` |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.15 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `d69406a6b7e8` |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1160.00 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `4c486eeb1b8d` |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `6df55c3addef` |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | ₹1358.02 | **+21.36%** | +22.14% | +22.34% | **0.78 pp** | **0.98 pp** | Tier 2 | LISTED | Closed 2026-10-23; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-10-28 | Actual opening price verified via https://finance.yahoo.com/quote/JPL.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.txt |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | ₹720.00 | **+3.90%** | -2.56% | +1.59% | **6.46 pp** | **2.31 pp** | Tier 2b | LISTED | Corrected (D-073) via Tier 2b from raw 4.04% |
| **M.K.Sons Fine Jewels** | 2026-11-04 | ₹162.00 | Pending | Pending | +4.37% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-04 |
| **BLS Polymers** | 2026-11-03 | ₹150.00 | Pending | Pending | +53.28% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-03 |
| **SFC Environmental Technologies** | 2026-11-03 | ₹330.00 | Pending | Pending | +5.49% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-03 |
| **EAAA India Alternatives** | 2026-11-02 | ₹1665.00 | Pending | Pending | +5.35% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-02 |

---

## 4. Gate A16 Results & Audit Findings

### G1: Prior-Phase Recheck & Headline Recomputations (Seed 16)
- Evaluated 10 sampled claims from `phases/Phase 15/3_outcome_and_verdict.md` (6 IPO claims, 4 file content claims) with `random.Random(16)` into `phases/Phase 16/prior_phase_recheck.csv`. All 10 claims matched underlying files exactly (VERIFIED).
- Recomputed 5 headline metrics directly from raw files:
  1. Overall Forward Model MAE ($n=8$ listed): **5.99 pp** (5.9913 pp).
  2. Raw GMP MAE ($n=7$ with GMP): **6.15 pp** (6.1471 pp).
  3. Model MAE on GMP subset ($n=7$): **6.67 pp** (6.6743 pp).
  4. Model MAE excluding Bonfiglioli ($n=7$): **3.83 pp** (3.8329 pp).
  5. Master Dataset row count: **731 rows** in `data/ipo_master.csv`.

### G2: Regression Test Audit (D-066 to D-078)
- Audited all 12 FIXED defects from D-066 through D-078.
- Every defect has a registered regression test; all 12 passed in 12.77s.

### G3: Cloud Runs & Defect Mapping
- Last 10 scheduled runs audited from `gh run list --event schedule -L 12` in `phases/Phase 16/actions_status.md`.
- 0 open alert issues in the repository.
- Audited 18 commits since `phase15-gate-a`: all 18 mapped to defects, PR merges (#7, #8, #9), or scheduled bot automated runs.

### G4: Effective Outcomes Audit
- Evaluated all 8 listed forward rows using `opi/outcomes.py`.
- `predictions/prediction_log.csv` is 100% byte-identical and unedited (`git diff` clean).
- Paras Healthcare Limited displays effective gain of +3.90% (vs raw 4.04%) layered via `predictions/outcome_corrections.csv`.

### G5: Secret Scanning & Credentials Check
- `gh secret list` confirms `OPENROUTER_API_KEY` present.
- `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns strictly 0 matches across the repository.

### G6: Audit of Four 2026-11-01 Forward IPOs (D-084)

#### M.K.Sons Fine Jewels
- Bidding closed 2026-10-30; scored 2026-11-01T22:31:30 IST; scheduled listing 2026-11-04 (scored BEFORE listing). Issue price ₹162, issue size ₹275 Cr, subscription Total 5.09x (QIB 1.84x, NII 14.12x, Retail 3.08x). HTML snapshots saved and grounded in `data/evidence/subscription/` and `data/evidence/research/`. GMP is missing (`None`) due to D-081. Status: **OK (missing GMP noted under D-081)**.

#### BLS Polymers
- Bidding closed 2026-10-29; scored 2026-11-01T22:31:31 IST; scheduled listing 2026-11-03 (scored BEFORE listing). Issue price ₹150, issue size ₹255 Cr, subscription Total 241.22x (QIB 200.25x, NII 559.2x, Retail 128.36x). High demand leads to predicted gain of +53.28% and P(>10%)=0.8887. HTML snapshots saved and grounded. GMP missing due to D-081. Status: **OK (missing GMP noted under D-081)**.

#### SFC Environmental Technologies
- Bidding closed 2026-10-29; scored 2026-11-01T22:31:32 IST; scheduled listing 2026-11-03 (scored BEFORE listing). Issue price ₹330, issue size ₹668 Cr, subscription Total 9.47x (QIB 18.81x, NII 12.81x, Retail 2.71x). HTML snapshots saved and grounded. GMP missing due to D-081. Status: **OK (missing GMP noted under D-081)**.

#### EAAA India Alternatives
- Bidding closed 2026-10-28; scored 2026-11-01T22:31:33 IST; scheduled listing 2026-11-02 (scored BEFORE listing). Issue price ₹1665, issue size ₹1200 Cr, subscription Total 5.51x (QIB 13.8x, NII 4.81x, Retail 1.08x). HTML snapshots saved and grounded. GMP missing due to D-081. Status: **OK (missing GMP noted under D-081)**.

### G7: Bombay Coated & Special Steels Limited Status
- Dates read directly from Chittorgarh overview page (`https://www.chittorgarh.com/ipo/bombay-coated-and-special-steels-ipo/2671/`) using project discovery code:
  - Bidding Open: **2026-10-29**
  - Bidding Close: **2026-11-02**
  - Listing Date: **2026-11-05**
  - Registrar: KFin Technologies
  - Issue Price: ₹82
  - Issue Size: ₹183 Cr
- Status in Prediction Log: **NOT in prediction_log.csv** (unscored).
- Operational Timing: Bidding closes today (2026-11-02) at 17:00 IST. Per project rules, it must only be scored after bidding closes (with final subscription) and before it lists (2026-11-05). It must never be scored after listing or backfilled.

---

## 5. Workstream Results & Execution Plans
*(Work strictly halted at Gate A16 awaiting user "continue" instruction.)*

---

## 6. Self-Audit (Pasted Command Output)

| Audit Question | Verdict | Verifying Evidence |
|---|:---:|---|
| Did any report number come from anywhere but a script over the log/evidence? | **NO** | Recomputed via `scripts/recompute_gate_a16.py` and `scripts/forward_report.py --markdown`. |
| Did any claim say a file changed when `git diff --stat` shows otherwise? | **NO** | Verified with `git diff --stat` before staging. |
| Did the log get edited at all? | **NO** | `git diff predictions/prediction_log.csv` shows 0 changes. |
| Did any earlier-phase file change except by ERRATA? | **NO** | Zero modifications to historical phase files. |
| Was any outcome recorded without a saved real response? | **NO** | All outcomes backed by saved manifests in `data/evidence/actuals/`. |
| Does any FIXED row rely on a file produced off the runner? | **NO** | Runner probe committed in `phases/Phase 15/source_probe_runner.md`. |
| Did the work stop after Gate A16? | **YES** | Execution strictly halted awaiting user "continue". |
| Was the key kept out of the repo, logs, issues, and snapshots? | **YES** | `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. |

---

## 7. Handover State
Gate A16 complete and verified. Ready for preregistration commit and user pause.
