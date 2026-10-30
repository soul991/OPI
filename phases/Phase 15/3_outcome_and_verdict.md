# Phase 15: Outcome & Verdict

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Mandatory Small-Sample Epistemic Guardrail**: Sample size is currently $n = 8$ of 30 target forward predictions ($n = 7$ with GMP). All metrics and error distributions are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## 1. Targets Missed & Unfixed Items

1. **Unfixed Defect D-026 (Research Agent Scheduled Proof)**:
   - **Status**: Kept `NOT FIXED` awaiting a real upcoming IPO during an active bidding cycle in a scheduled run.
   - **Reason**: Per explicit project rules, no synthetic or fake IPOs may ever be created to artificially force a fix. Bidding for new upcoming Mainboard IPOs has not opened during this maintenance cycle.
2. **Defect D-071 (Dashboard Card & verify_all NOT FIXED count)**:
   - **Status**: `PARTIAL (needs user action)`.
   - **Reason**: The dashboard generator (`opi/report.py`) and renderer were updated to correctly count `OPEN + PARTIAL + NOT FIXED` (verified by `tests/test_dashboard.py::test_dashboard_defect_counter_matches_register`). Modifying `scripts/verify_all.py` to count NOT FIXED items is strictly prohibited by project rules ("Do not edit scripts/verify_all.py, scripts/verify_extra.py or scripts/verify_pages.py to make a check pass"). The user will update the status tuple in `scripts/verify_all.py`.
3. **Targets Missed**: None. All scheduled deliverables (Gate A15, preregistration, Workstreams A, B, and C, runner reachability probe on Linux, append-only corrections engine, Tier 2b multi-source protocol, Paras correction, workflow entrypoints smoke test, process protocol update, PR #7 merge, and cloud post-merge runs) were successfully executed and verified.

---

## 2. Defect Ledger

| Defect ID | Phase Seeded | Summary Description | Severity | Final Status | Closed Phase | Verification Proof / Test Name |
|---|:---:|---|:---:|:---:|:---:|---|
| **D-026** | 7 | Real scheduled cloud research run with live OpenRouter model not proven on a new IPO. | Medium | **NOT FIXED** | — | Awaiting next real upcoming IPO bidding cycle; no mock IPOs permitted. |
| **D-071** | 14 | Dashboard card and verify_all.py count only OPEN and PARTIAL, omitting NOT FIXED (D-026). | Low | **PARTIAL** | 14 | `tests/test_dashboard.py::test_dashboard_defect_counter_matches_register` (verify_all part needs user action) |
| **D-072** | 14 | Tier 2 silently falls back to the first bar in history when listing-date bar is missing; Paras recorded from 2026-10-29 bar (721, +4.04%) instead of 2026-10-28 (720, +3.90%). | Medium | **FIXED** | 15 | `tests/test_actuals_job.py::test_yfinance_rejects_missing_listing_day_bar_paras_data` |
| **D-073** | 14 | A recorded outcome can be wrong and rules forbid editing the log; no audited way to correct it. | Medium | **FIXED** | 15 | `tests/test_outcomes_corrections.py::test_reports_agree_with_effective_value` |
| **D-074** | 14 | D-068 was marked FIXED from a probe on win32, not on a runner; runner reachability has no committed evidence. | Medium | **FIXED** | 15 | `tests/test_actuals_job.py::test_runner_probe_committed_and_verified` |
| **D-075** | 14 | Watchdog failed on runner (run 41090951686, issue #6) because `watchdog.py` imported `scripts.manage_alerts`; standalone execution not tested. | Medium | **FIXED** | 15 | `tests/test_workflow_entrypoints.py::test_workflow_entrypoints_smoke` |
| **D-076** | 15 | Process: fixes were pushed to main without a defect id, a branch or a PR. | Low | **FIXED** | 15 | `tests/test_ci.py::test_phase15_process_rule_defect_registration_and_branch_pr` |

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

---

## 4. Gate A15 Results & Audit Findings

### G1: Prior Phase Recheck & Trading-Day Analysis
- **Audit File**: `phases/Phase 15/prior_phase_recheck.csv` (seed 15).
- Evaluated 10 sampled claims from `phases/Phase 14/3_outcome_and_verdict.md`, including at least 5 regarding specific IPO numbers and 3 verifying file contents. All 10 claims matched raw data exactly.
- Recomputed 5 headline metrics:
  - Model MAE ($n=8$): 6.0088 pp -> 6.01 pp.
  - GMP MAE ($n=7$): 6.1671 pp -> 6.17 pp.
  - Model MAE on GMP subset ($n=7$): 6.6914 pp -> 6.69 pp.
  - Model MAE excluding Bonfiglioli ($n=7$): 3.8529 pp -> 3.85 pp.
  - Master dataset row count: 731 rows.
- Evaluated trading sessions for the two Phase 14 listings:
  - **Jio Platforms Limited**: Earliest bar in saved response `data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.txt` is `2026-10-27T18:30:00.000Z`, which in `Asia/Kolkata` is `2026-10-28 00:00:00 IST`. This corresponds to the true listing-day session.
  - **Paras Healthcare Limited**: Earliest bar in saved response `data/evidence/actuals/2026-10-28_paras-healthcare-limited_fe823e2ba992.txt` is `2026-10-28T18:30:00.000Z`, which in `Asia/Kolkata` is `2026-10-29 00:00:00 IST` (open ₹721.00). This corresponds to the trading day *after* listing.

### G2: Regression Test Audit
- Audited defects D-053 through D-070. All FIXED defects had named passing tests.
- Identified that D-068 was marked FIXED based on `phases/Phase 14/source_probe.md`, which reported execution on `win32` rather than a Linux runner. Seeded D-074 to track empirical runner proof.

### G3: Cloud Runs & Defect Mapping
- Audited last 10 scheduled runs via `gh run list --event schedule` in `phases/Phase 15/actions_status.md`.
- Documented closed Issue #6 (Watchdog failure on runner in run `41090951686`).
- Audited 15 commits since `phase14-gate-a`: mapped commits `06ff884` and `9dd1b7d` as process defects (pushed straight to `main` without PR or defect registration; D-076).

### G4: Paras Price Comparison
Side-by-side comparison of saved evidence:
- Yahoo Finance Bar 1: `2026-10-28T18:30:00.000Z` (IST: 2026-10-29), Open: ₹721.00.
- Yahoo Finance Bar 2: `2026-10-29T18:30:00.000Z` (IST: 2026-10-30), Open: ₹708.20.
- Chittorgarh Quote Page: Listing Date `2026-10-28`, Open: ₹720.00.
- This proved conclusively that the logged price ₹721.00 came from the 2026-10-29 session.

### G5: Secret Sanitization
- `gh secret list` confirms `OPENROUTER_API_KEY` present.
- `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returned 0 matches across the repository.

---

## 5. The Paras Healthcare Story

1. **The Flaw in `opi/actuals.py`**:
   The original implementation in `fetch_yfinance_first_session_open` attempted to locate a bar matching `listing_date`. If no bar matched, it fell back to:
   ```python
   # Defect D-072: silent fallback to earliest bar
   row = df.iloc[0]
   return float(row["Open"]), None, raw_response
   ```
   For Paras Healthcare (listed on 2026-10-28), Yahoo Finance only returned two bars starting from 2026-10-29. Because the issue price was ₹693.00, the 2026-10-29 open of ₹721.00 (+4.04%) was within 0.14% of the Chittorgarh price of ₹720.00 (+3.90%), well within the 1.0% cross-check tolerance. The fallback silently accepted the wrong session.

2. **The Fix (D-072)**:
   In `opi/actuals.py`, the fallback was completely removed. Timestamps are converted to `Asia/Kolkata`, and exact date equality is enforced:
   ```python
   if len(matching) == 0:
       earliest = df.index[0].strftime("%Y-%m-%d")
       return None, f"LISTING_DAY_BAR_MISSING: first bar is {earliest}, listing date {listing_date}", raw_bytes
   ```
   If the bar is missing, the caller logs `SKIPPED_NO_MATCH` and records nothing.

3. **Audited Correction via Tier 2b (D-073)**:
   Because `predictions/prediction_log.csv` is immutable and must never be edited, an audited append-only corrections engine was established.
   Under the preregistered Tier 2b protocol, two independent web sources were fetched by code (`scripts/apply_paras_correction.py`):
   - **Source 1**: Chittorgarh Stock Price Quote (`https://www.chittorgarh.com/stockpricequote/paras-healthcare-limited/8103/`), Open: ₹720.00. Saved to `data/evidence/actuals/2026-10-28_paras-healthcare-limited_chittorgarh_tier2b.*`.
   - **Source 2**: Groww Research Listing Article (`https://groww.in/blog/paras-healthcare-ipo-listing`), Listing Open: ₹720.00. Saved to `data/evidence/actuals/2026-10-28_paras-healthcare-limited_groww_tier2b.*`.
   - **Agreement**: $0.00\%$ divergence, satisfying the $\le 1.0\%$ rule.
   - **Correction Record**: Appended to `predictions/outcome_corrections.csv`:
     ```csv
     company,listing_date,field,old_value,new_value,reason,evidence_path,tier,corrected_at
     Paras Healthcare Limited,2026-10-28,actual_gain_pct,4.04,3.90,D-073: Tier 2b dual independent source verification (Chittorgarh 720.00 and Groww 720.00 vs issue price 693.00; diff 0.00%),data/evidence/actuals/2026-10-28_paras-healthcare-limited_chittorgarh_tier2b.json,tier2b,2026-10-31T01:54:13.203603+00:00
     ```
   - **Impact on Metrics**:
     - Raw Gain: `+4.04%` (Open ₹721.00) -> Effective Gain: `+3.90%` (Open ₹720.00).
     - Model Error: `6.60 pp` -> `6.46 pp` (-0.14 pp).
     - GMP Error: `2.45 pp` -> `2.31 pp` (-0.14 pp).
     - Forward Model MAE ($n=8$): `6.01 pp` -> `5.99 pp` (`5.9913 pp`).
     - Forward GMP MAE ($n=7$): `6.17 pp` -> `6.15 pp` (`6.1471 pp`).
     - `predictions/prediction_log.csv` remained 100% byte-identical.

---

## 6. Runner Probe Result (D-074 & D-068 Proof)

The probe workflow was executed on GitHub Actions (`ubuntu-24.04` runner, run `41128632410`).
Output committed directly by the runner to `phases/Phase 15/source_probe_runner.md`:
- **Environment**: `Python 3.12.15 on linux (GitHub Actions run ID: 41128632410)`
- **Target Candidates**: Jio Platforms Limited, Paras Healthcare Limited (Listed 2026-10-28)

Empirical Reachability Matrix from Cloud Runner:
1. **NSE Official API (`nseindia.com`)**: HTTP 403 (Akamai WAF/CDN block).
2. **BSE Official API (`api.bseindia.com`)**: HTTP 403 (WAF block).
3. **BSE Announcements**: HTTP 403.
4. **yfinance NSE (`query1.finance.yahoo.com`)**: HTTP 200 (PARASHLTH.NS, JPL.NS).
5. **Chittorgarh Listing / Quote (`chittorgarh.com`)**: HTTP 200 (Paras ₹720.00, Jio ₹1358.00).

Verdict:
- D-068 and D-074 are fully verified with cloud runner empirical evidence. The cloud runner cannot reach official Indian exchanges directly (Akamai/WAF block), proving that Tier 2 with independent cross-validation is mandatory for cloud automation.

---

## 7. Smoke Test Proof on Old vs New Code (D-075)

### Problem
In run `41090951686` (Issue #6), the watchdog workflow crashed on the cloud runner with:
```text
ModuleNotFoundError: No module named 'scripts'
```
Because `python scripts/watchdog.py` sets `sys.path[0]` to `scripts/`, internal imports like `from scripts.manage_alerts import sanitize_text` fail unless `ROOT_DIR` is explicitly added or `PYTHONPATH` is configured. Local tests and previous CI suites failed to catch this because pytest adds the project root to `sys.path`.

### Smoke Test Design (`tests/test_workflow_entrypoints.py`)
1. Parses all `.github/workflows/*.yml` files.
2. Extracts every Python invocation (`python scripts/...`, `python -m ...`).
3. Executes each command with `--help` from `ROOT_DIR` with `PYTHONPATH` unset.
4. Integrated into `scripts/ci_local.py` as Step 1.

### Efficacy Proof on Pre-Fix Code
In `test_smoke_test_fails_on_prefix_watchdog`, the watchdog code from commit `06ff884` (prior to fix `9dd1b7d`) was extracted and executed without `PYTHONPATH`:
```text
Output:
ModuleNotFoundError: No module named 'scripts'
Exit code: 1 (Test PASSES assertion that pre-fix code fails)
```
In contrast, current code in `scripts/watchdog.py` passes standalone execution with exit code 0.

---

## 8. Self-Audit (Yes/No with Pasted Evidence)

| Audit Question | Answer | Pasted Evidence / Verification Command |
|---|:---:|---|
| Did any report number come from anywhere but a script over the log, corrections or evidence? | **YES (strictly followed)** | All figures verified via `scripts/recompute_phase15.py` and `scripts/forward_report.py`. |
| Did any summary line claim a file changed when `git diff --stat` shows otherwise? | **NO** | `git diff --stat` verified before every commit. |
| Was the log edited at all (`git diff` on `predictions/prediction_log.csv`)? | **NO** | `git diff predictions/prediction_log.csv` returned 0 changes. File is byte-identical. |
| Did any earlier-phase file change except by ERRATA? | **NO** | Zero modifications to earlier-phase files. Verified by `verify_all.py` check `earlier-phase artifacts unchanged since phase15-gate-a`. |
| Was any outcome recorded without a saved real response? | **NO** | Raw HTML and response JSON manifests committed in `data/evidence/actuals/` for both Chittorgarh and Groww. |
| Does any FIXED row rely on a file produced off the runner? | **NO** | D-074 and D-068 proven by `phases/Phase 15/source_probe_runner.md` produced by runner run `41128632410`. |
| Did the work stop after the gate? | **YES** | Work paused after Gate A15 commit `phase15-gate-a` and resumed only upon user instruction. |
| Was the key kept out of the repo, logs, issues, and snapshots? | **YES** | `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches across the repository. |

---

## 9. Handover State

1. **Repository Health**:
   - `scripts/verify_all.py`: `SUMMARY: 70 pass, 0 warn, 0 fail`.
   - `scripts/verify_extra.py`: `SUMMARY: 7 pass, 0 warn, 0 fail`.
   - `scripts/ci_local.py`: `CI_LOCAL: PASS` across all 4 steps (entrypoint smoke tests, daily job, pytest 199 passed, verify_all).
2. **Defect Counts**:
   - Total Defects: 76
   - Fixed: 67
   - Accepted: 6
   - Deferred: 0
   - Unresolved (Open / Partial / Not Fixed): 3 (D-026 NOT FIXED awaiting real new IPO; D-071 PARTIAL awaiting user edit to `verify_all.py` status tuple; 0 OPEN).
3. **Cloud Infrastructure**:
   - Daily workflow run `41129785639` on `main`: Success (1m56s).
   - Watchdog workflow run `41129797926` on `main`: Success (33s).
   - Open alert issues on GitHub: 0.
4. **Prospective Forward Record**:
   - Total listed: 8 IPOs ($n = 8$ of 30 target forward predictions; 7 with GMP).
   - Provisional Model MAE ($n=8$): **5.99 pp** (5.9913 pp).
   - Provisional GMP MAE ($n=7$): **6.15 pp** (6.1471 pp).
   - Provisional Model MAE on GMP subset ($n=7$): **6.67 pp** (6.6743 pp).
   - Provisional Model MAE excluding Bonfiglioli ($n=7$): **3.83 pp** (3.8329 pp).
