# Phase 18 GitHub Actions Health & Scheduled Runs Audit (G3, G4, G5, G6)

**Audit Timestamp**: 2026-11-05T19:25:00+05:30  
**Repository**: `soul991/OPI`  
**Auditor**: Antigravity (Phase 18 Gate A18)

---

## 1. Last 10 Scheduled Runs (G3)

Audited directly via `gh run list --event schedule --limit 10`:

| Run ID | Workflow | Event | Status | Conclusion | Started At (UTC) | Duration | Notes |
|---|---|---|---|---|---|---|---|
| **41908615355** | Daily Forward Test & Verification | schedule | completed | **failure** | 2026-11-04T20:39:05Z | 2m58s | Failure prior to Phase 17 hotfix; failed at step |
| **41880421967** | Watchdog Freshness & Provider Health | schedule | completed | **failure** | 2026-11-04T17:46:49Z | 3m11s | Failed at step `verify_extra.py` (missing 2026-11-02 Nifty evidence); opened Issue #15 |
| **41840431778** | Daily Forward Test & Verification | schedule | completed | **failure** | 2026-11-04T13:41:39Z | 1m54s | Failed in daily workflow execution; opened Issue #14 |
| **41711999763** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-03T20:22:41Z | 3m10s | Green scheduled run; recorded EAAA India Alternatives (+0.63%) |
| **41685579043** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-11-03T17:34:34Z | 53s | Green scheduled run |
| **41644885663** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-03T13:30:12Z | 3m48s | Green scheduled run |
| **41514942571** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-11-02T19:58:55Z | 46s | Green scheduled run |
| **41463708776** | Daily Forward Test & Verification | schedule | completed | **failure** | 2026-11-02T14:37:25Z | 1m3s | Failed at step "Run Test Suite" (indentation error in verify_all.py); opened Issue #11 |
| **41338045829** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-01T18:43:13Z | 1m34s | Green scheduled run; scored M.K.Sons, BLS Polymers, SFC Environmental, EAAA India Alternatives |
| **41327176620** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-11-01T16:36:11Z | 41s | Green scheduled run |

---

## 2. Issues & Failure Post-Mortems (G3)

### Failures Since 2026-11-04
- Run `41840431778` (Daily Forward Test & Verification, 2026-11-04T13:41:39Z, opened Issue #14)
- Run `41880421967` (Watchdog Freshness & Provider Health, 2026-11-04T17:46:49Z, opened Issue #15)
- Run `41908615355` (Daily Forward Test & Verification, 2026-11-04T20:39:05Z)

### Alert Issue #14 Audit
- **Issue Title**: `Daily run failed: 41840431778`
- **Quoted Step Line**:
  ```markdown
  - **Failed Step / Component**: `Execution`
  ```

### Alert Issue #15 Audit
- **Issue Title**: `Watchdog run failed: 41880421967`
- **Quoted Step Line**:
  ```markdown
  - **Failed Step / Component**: `Execution`
  ```

### D-091 Verification & Defect Status
Because both Issue #14 and Issue #15 bodies report `- **Failed Step / Component**: \`Execution\`` rather than the granular failed step name, D-091 is not proven in cloud runs and has been **REOPENED** in `DEFECTS.md` as `OPEN`.

### PR #17 Status
- **PR State**: `MERGED`
- **Title**: `Monthly Challenger Evaluation - 2026-11`
- **Merge Commit**: `a2407261893452ad347870cf51bc816aa3d4b29d`
- **Merged By**: `soul991` on `2026-11-05T17:48:24+05:30`
- **Master Dataset Effect**: Appended 9 forward rows to `data/ipo_master.csv` (total count now 740 rows).

### Open Issues Status
- `gh issue list --state open` returns 0 open issues.

---

## 3. Pending & Recent Forward Outcomes Table (G4)

Computed directly from `predictions/prediction_log.csv`, `predictions/run_log.csv`, and `data/evidence/market/` as of 2026-11-05:

| Company | Listing Date | Days Since Listing | Last ACTUALS Run-Log Status | Last ACTUALS Message / Reason | Nifty Market Evidence Exists? |
|---|:---:|:---:|:---:|---|:---:|
| **BLS Polymers** | 2026-11-03 | 2d | `SKIPPED_NO_MATCH` | Tier 2 primary source (BLSPOLY.NS) failed: LISTING_DAY_BAR_MISSING: first bar is 2026-11-04, listing date 2026-11-03 | **NO** (missing `2026-11-03_nifty.*`) |
| **SFC Environmental Technologies** | 2026-11-03 | 2d | `SKIPPED_NO_MATCH` | Tier 2 primary source (SFCTECH.NS) failed: LISTING_DAY_BAR_MISSING: first bar is 2026-11-04, listing date 2026-11-03 | **NO** (missing `2026-11-03_nifty.*`) |
| **M.K.Sons Fine Jewels** | 2026-11-04 | 1d | `SKIPPED_FETCH_FAILED` | Tier 2 primary source (MKJEWELS.NS) failed: yfinance returned empty price history for MKJEWELS.NS | **NO** (missing `2026-11-04_nifty.*`) |
| **Bombay Coated & Special Steels** | 2026-11-05 | 0d | None logged yet | Listing date is 2026-11-05 (today); market session in progress / unclosed during last run | **NO** (missing `2026-11-05_nifty.*`) |

---

## 4. Secret Sanitization Audit (G5)

- **GitHub Secret Presence**: `gh secret list` confirms `OPENROUTER_API_KEY` exists (updated 2026-10-24T09:43:21Z).
- **Repository Pattern Scan**: Secret key pattern search returns strictly 0 matches across all branches and working trees.
- **Clean Hygiene**: Zero secret key material committed to disk, logs, issues, or snapshots.

---

## 5. D-095 Reproduction Before Fix (G6)

Reproduced in an isolated temporary clone with a fixture prediction log containing an unrecorded FORWARD row listed 4 days ago (`2026-11-01`).
When `python -m opi.run_daily` was executed with `dry_run=False`, it raised `RuntimeError` at Step 4:
```text
RuntimeError: Overdue listing outcomes missing: Overdue listing outcome(s) missing (> 2 days since listing):
  - Overdue IPO Limited (listed 2026-11-01, 4 days ago): SKIPPED_FETCH_FAILED: Non-positive issue price in prediction row
```
Exit code: `1`.
This demonstrates that under the current implementation, an overdue outcome halts `run_daily`, preventing the workflow from proceeding to the commit step and blocking all downstream updates until the outcome is recorded.
