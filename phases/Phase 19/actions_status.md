# Phase 19 GitHub Actions Health & Scheduled Runs Audit (G3, G4, G5, G6, G7, G8)

**Audit Timestamp**: 2026-11-07T02:00:00+05:30  
**Repository**: `soul991/OPI`  
**Auditor**: Antigravity (Phase 19 Gate A19)

---

## 1. Last 12 Scheduled Runs (G3)

Audited directly via `gh run list --event schedule --limit 12`:

| Run ID | Workflow | Event | Status | Conclusion | Started At (UTC) | Duration | Notes |
|---|---|---|---|---|---|---|---|
| **42286425753** | Daily Forward Test & Verification | schedule | completed | **failure** | 2026-11-06T20:12:58Z | 3m12s | Failed at step `Check overdue outcomes and coverage`; BLS Polymers overdue alert (Issue #18 comment) |
| **42259466958** | Watchdog Freshness & Provider Health | schedule | completed | **failure** | 2026-11-06T17:12:18Z | 40s | Failed at step `Execution`; BLS Polymers overdue alert (Issue #21 body) |
| **42227250129** | Daily Forward Test & Verification | schedule | completed | **failure** | 2026-11-06T13:39:23Z | 4m12s | Failed at step `Check overdue outcomes and coverage`; BLS Polymers overdue alert (Issue #18 comment) |
| **42107747479** | Daily Forward Test & Verification | schedule | completed | **failure** | 2026-11-05T20:54:46Z | 44s | Failed at step `Execute Daily Forward Test Runner`; BLS Polymers overdue alert (Issue #18 body) |
| **42078815778** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-11-05T17:52:19Z | 51s | Green scheduled run |
| **42039897604** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-05T13:54:09Z | 4m12s | Green scheduled run |
| **41908615355** | Daily Forward Test & Verification | schedule | completed | **failure** | 2026-11-04T20:39:05Z | 2m58s | Pre-Phase 18 failure |
| **41880421967** | Watchdog Freshness & Provider Health | schedule | completed | **failure** | 2026-11-04T17:46:49Z | 3m11s | Pre-Phase 18 failure: missing Nifty evidence |
| **41840431778** | Daily Forward Test & Verification | schedule | completed | **failure** | 2026-11-04T13:41:39Z | 1m54s | Pre-Phase 18 failure in daily job |
| **41711999763** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-03T20:22:41Z | 3m10s | Green scheduled run; recorded EAAA India Alternatives |
| **41685579043** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-11-03T17:34:34Z | 53s | Green scheduled run |
| **41644885663** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-03T13:30:12Z | 3m48s | Green scheduled run |

---

## 2. Issues & Failure Post-Mortems (G3)

### Open Issues Status
- `gh issue list --state open` returns exactly **2** open issues:
  1. **Issue #18**: `Daily run failed: 42107747479` (opened 2026-11-05T20:55:26Z, deduplicated with comments on runs 42207678334, 42218253536, 42227250129, 42286425753)
  2. **Issue #21**: `Watchdog run failed: 42259466958` (opened 2026-11-06T17:12:55Z)

### Quoted Failing Step Lines from Alert Issue Bodies
- **Issue #18 (Run 42286425753 comment)**:
  ```markdown
  - **Failed Step / Component**: `Check overdue outcomes and coverage`
  - **Reason / Diagnosis**: SUMMARY: Overdue & Coverage Audit FAILED with 1 alert(s):
    - Missing Listing Outcomes:
  Overdue listing outcome(s) missing (> 2 days since listing):
    - BLS Polymers (listed 2026-11-03, 4 days ago): MISSING_OUTCOME_ALERT: Listed 2026-11-03 (4d ago) missing outcome: PENDING_REVIEW: Tier 2 sources diverge beyond 1.0% tolerance: yfinance=248.0 vs second_source=244.1 (diff=1.57%)
  ```
- **Issue #18 (Run 42227250129 comment)**:
  ```markdown
  - **Failed Step / Component**: `Check overdue outcomes and coverage`
  - **Reason / Diagnosis**: SUMMARY: Overdue & Coverage Audit FAILED with 1 alert(s):
    - Missing Listing Outcomes:
  Overdue listing outcome(s) missing (> 2 days since listing):
    - BLS Polymers (listed 2026-11-03, 3 days ago): MISSING_OUTCOME_ALERT: Listed 2026-11-03 (3d ago) missing outcome: PENDING_REVIEW: Tier 2 sources diverge beyond 1.0% tolerance: yfinance=248.0 vs second_source=244.1 (diff=1.57%)
  ```
- **Issue #18 (Run 42107747479 body)**:
  ```markdown
  - **Failed Step / Component**: `Execute Daily Forward Test Runner`
  - **Failure Reason**: Overdue listing outcome(s) missing (> 2 days since listing):
    - BLS Polymers (listed 2026-11-03, 3 days ago): SKIPPED_NO_MATCH: Tier 2 primary source (BLSPOLY.NS) failed: LISTING_DAY_BAR_MISSING: first bar is 2026-11-05, listing date 2026-11-03
  ```
- **Issue #21 (Run 42259466958 body)**:
  ```markdown
  - **Failed Step / Component**: `Execution`
  - **Failure Reason**: SUMMARY: Watchdog FAILED with 1 issue(s):
    - Missing Listing Outcomes: Overdue listing outcome(s) missing (> 2 days since listing):
    - BLS Polymers (listed 2026-11-03, 3 days ago): MISSING_OUTCOME_ALERT: Listed 2026-11-03 (3d ago) missing outcome: PENDING_REVIEW: Tier 2 sources diverge beyond 1.0% tolerance: yfinance=248.0 vs second_source=244.1 (diff=1.57%)
  ```

### Red Runs Confirmation
Confirmed: all red daily and watchdog runs are caused by the overdue-outcome alert for BLS Polymers and nothing else. D-095 is verified effective: runs committed forward predictions and dashboard updates despite the alert.

---

## 3. Pending & Recent Forward Outcomes Table (G4)

Audited directly from `predictions/prediction_log.csv` and `predictions/run_log.csv`:

| Company | Listing Date | Days Since Listing (at 2026-11-07) | Last ACTUALS Run-Log Line | Saved Source Values in Repo |
|---|:---:|:---:|---|---|
| **BLS Polymers** | 2026-11-03 | 4d | `2026-11-07T01:43:32.780511+05:30 \| ACTUALS \| BLS Polymers \| PENDING_REVIEW \| Tier 2 sources diverge beyond 1.0% tolerance: yfinance=248.0 vs second_source=244.1 (diff=1.57%)` | Primary (yfinance, `BLSPOLY.NS`): `248.0`<br>Second source (Chittorgarh): `244.1`<br>Third source (Groww, from Phase 18 audit): `248.0`<br>*(No files in data/evidence/actuals/ due to PENDING_REVIEW return)* |
| **Bombay Coated & Special Steels** | 2026-11-05 | 2d | `2026-11-07T01:43:33.374225+05:30 \| ACTUALS \| Bombay Coated & Special Steels \| PENDING_REVIEW \| Tier 2 sources diverge beyond 1.0% tolerance: yfinance=91.0 vs second_source=92.02 (diff=1.12%)` | Primary (yfinance, `BCSSL.NS`): `91.0`<br>Second source (Chittorgarh): `92.02`<br>*(No files in data/evidence/actuals/ due to PENDING_REVIEW return)* |

---

## 4. Secret Sanitization Audit (G5)

- **GitHub Secret Presence**: `gh secret list` shows `OPENROUTER_API_KEY` (updated `2026-10-24T09:43:21Z`).
- **Repository Pattern Scan**: `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns strictly 0 matches across the repository.

---

## 5. Divergence Diagnosis (G6)

Audited from source fetching logic and logged values:

1. **BLS Polymers** (listed 2026-11-03, issue price ₹150.00):
   - **Primary Source (yfinance)**: Publisher = `Yahoo Finance`, Exchange = `NSE` (`BLSPOLY.NS`), Quantity = `open` (first session open), Bar Date = `2026-11-03`, Value = `248.0` (+65.33% gain).
   - **Second Source (Chittorgarh)**: Publisher = `Chittorgarh`, Exchange = `BSE`, Quantity = `listing_price` / `open`, Bar Date = `2026-11-03`, Value = `244.1` (+62.73% gain).
   - **Third Source (Groww)**: Publisher = `Groww`, Exchange = `NSE`, Quantity = `open`, Value = `248.0` (+65.33% gain).
   - **Diagnosis**: Divergence is between NSE (248.0) and BSE (244.1).
   - **Evidence Lines**:
     `2026-11-07T01:43:32.780511+05:30 | ACTUALS | BLS Polymers | PENDING_REVIEW | Tier 2 sources diverge beyond 1.0% tolerance: yfinance=248.0 vs second_source=244.1 (diff=1.57%)`

2. **Bombay Coated & Special Steels** (listed 2026-11-05, issue price ₹82.00):
   - **Primary Source (yfinance)**: Publisher = `Yahoo Finance`, Exchange = `NSE` (`BCSSL.NS`), Quantity = `open` (first session open), Bar Date = `2026-11-05`, Value = `91.0` (+10.98% gain).
   - **Second Source (Chittorgarh)**: Publisher = `Chittorgarh`, Exchange = `BSE`, Quantity = `listing_price` / `open`, Bar Date = `2026-11-05`, Value = `92.02` (+12.22% gain).
   - **Diagnosis**: Divergence is between NSE (91.0) and BSE (92.02).
   - **Evidence Lines**:
     `2026-11-07T01:43:33.374225+05:30 | ACTUALS | Bombay Coated & Special Steels | PENDING_REVIEW | Tier 2 sources diverge beyond 1.0% tolerance: yfinance=91.0 vs second_source=92.02 (diff=1.12%)`

3. **Manifest Inspection**:
   Existing manifests in `data/evidence/actuals/*.json` only label the primary source (`"exchange_used": "NSE"`), and do not label the exchange, quantity, or publisher of the second source. For divergent outcomes, no manifest is saved. This confirms **D-101**.

---

## 6. Pages Build & Deployment Failure Audit (G7)

- **Failed Run**: `42227803913` (`pages-build-deployment` run #79, 2026-11-06T13:43:30Z, duration 10m52s).
- **Log Failure Reason**:
  ```text
  2026-11-06T13:48:10.1903873Z Current status: syncing_files
  ...
  2026-11-06T13:54:20.1345397Z ##[error]Timeout reached, aborting!
  2026-11-06T13:54:20.1354641Z Canceling Pages deployment...
  2026-11-06T13:54:21.1579478Z Canceled deployment with ID 27e21836677b753b9c709be8cd6be6af18925b56
  ```
- **Analysis**: `actions/deploy-pages@v5` timed out after 600,000 ms (10 minutes) while in status `syncing_files`.
- **Subsequent Runs**: Run #80 (`42286881687`, 2026-11-06T20:16:05Z) succeeded in 49 seconds.
- **Verdict**: One-off platform timeout during file sync. D-102 confirmed and closed as `ACCEPTED`.

---

## 7. Discovery & Research Agent Audit (G8)

- **Discovery in Last 7 Days**: All discovered candidates in `predictions/run_log.csv` were classified as `SKIPPED_ALREADY_LISTED` (already in master or market). No new mainboard IPOs closed or opened for bidding in the last 7 days.
- **Research Agent Execution**: Since no newly closed IPO required feature grounding, the research agent was not invoked. D-026 remains `NOT FIXED` awaiting the next upcoming mainboard IPO.
