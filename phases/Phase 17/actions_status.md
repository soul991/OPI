# Phase 17 GitHub Actions Health & Scheduled Runs Audit (G3, G4, G5, G6)

**Audit Timestamp**: 2026-11-04T03:33:00+05:30  
**Repository**: `soul991/OPI`  
**Auditor**: Antigravity (Phase 17 Gate A17)

---

## 1. Last 10 Scheduled Runs (G3)

Audited directly via `gh run list --event schedule -L 12`:

| Run ID | Workflow | Event | Status | Conclusion | Started At (UTC) | Duration | Notes |
|---|---|---|---|---|---|---|---|
| **41711999763** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-03T20:22:41Z | 3m10s | Green scheduled run; recorded EAAA India Alternatives (+0.63%) |
| **41685579043** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-11-03T17:34:34Z | 53s | Green scheduled run |
| **41644885663** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-03T13:30:12Z | 3m48s | Green scheduled run |
| **41514942571** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-11-02T19:58:55Z | 46s | Green scheduled run |
| **41463708776** | Daily Forward Test & Verification | schedule | completed | **failure** | 2026-11-02T14:37:25Z | 1m3s | Failed at step "Run Test Suite" (7-space IndentationError in verify_all.py); opened Issue #11 |
| **41338045829** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-01T18:43:13Z | 1m34s | Green scheduled run; scored M.K.Sons, BLS Polymers, SFC Environmental, EAAA India Alternatives |
| **41327176620** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-11-01T16:36:11Z | 41s | Green scheduled run |
| **41307153260** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-01T12:34:40Z | 2m9s | Green scheduled run |
| **41296833925** | Weekly Canary Dependency Build | schedule | completed | **success** | 2026-11-01T10:17:32Z | 1m6s | Green scheduled run |
| **41275742845** | Monthly Challenger Model Evaluation | schedule | completed | **success** | 2026-11-01T05:08:20Z | 48s | Green scheduled run (dry run) |

---

## 2. Issues & Failure Post-Mortems (G3)

### Alert Issue #11 Audit
- **Issue Title**: `Daily run failed: 41463708776`
- **Triggering Run**: `41463708776` (`daily.yml`, scheduled run on `main`, 2026-11-02 14:37:25 UTC).
- **Failing Step**: "Run Test Suite" (exited code 1 due to IndentationError: unexpected indent in `scripts/verify_all.py` introduced in commit on `main`).
- **Alert Quality Defect (D-091)**: The issue body reported generic text: `Failed Step / Component: Execution`, `Failure Reason: Workflow step returned non-zero exit code or validation failure`, requiring maintainers to open full raw logs to identify the indentation error.
- **Resolution**: Indentation fixed on `main` in PR #10; closed automatically by subsequent green dispatch run `41466028853` on 2026-11-02 14:57:35 UTC.

### Retraining Run Failures & PR Proof (D-083, D-087)
- **Failed Run**: `41453047131` (`monthly_retrain.yml`, workflow_dispatch on branch `feat/phase16-workstreams`, 2026-11-02 13:26:48 UTC).
  - Failing Step: `Open Pull Request with Challenger Comparison` (`gh pr create` failed due to missing repository workflow permission toggle).
- **Subsequent Green Run on `main`**: `41724471260` (`monthly_retrain.yml`, workflow_dispatch on `main`, 2026-11-03 21:44:12 UTC).
  - All steps completed successfully: Set up job, Check out repo, Set up Python 3.11, Install dependencies, Run Row Promotion Audit, Execute Challenger Evaluation, Verify Zero Automatic Model Promotion, Open Pull Request with Challenger Comparison.
  - **Pull Request Created**: Successfully opened **PR #12** (`Monthly Challenger Evaluation - 2026-11`) against `main` from branch `retrain/challenger-20261103-214459`.
  - **Permission Status**: Repository permission `Settings -> Actions -> General -> Workflow permissions -> Allow GitHub Actions to create and approve pull requests` is verified active.

---

## 3. Pending & Recent Forward Outcomes Audit (G4)

Computed directly from `predictions/prediction_log.csv` and `predictions/run_log.csv` as of 2026-11-04 03:33 IST:

| Company | Listing Date | Days Since Listing | Outcome in Log | Last ACTUALS Run-Log Status | Last Message / Error Detail |
|---|:---:|:---:|:---:|:---:|---|
| **BLS Polymers** | 2026-11-03 | 1d | Pending | `SKIPPED_FETCH_FAILED` | Tier 2 primary source (BLSPOLY.NS) failed: yfinance returned empty price history for BLSPOLY.NS |
| **SFC Environmental Technologies** | 2026-11-03 | 1d | Pending | `SKIPPED_FETCH_FAILED` | Tier 2 primary source (545009.BO) failed: yfinance returned empty price history for 545009.BO |
| **M.K.Sons Fine Jewels** | 2026-11-04 | 0d | Pending | `IN_PROGRESS` | Scheduled listing date is today; market session in progress (current IST: 03:33, required >= 16:00) |
| **Bombay Coated & Special Steels** | 2026-11-05 | -1d | Pending | `SCHEDULED` | Scheduled listing date 2026-11-05 is in the future; scored before listing |
| **EAAA India Alternatives** | 2026-11-02 | 2d | **+0.63%** | `RECORDED` | Recorded opening price ₹1675.5 via tier2 (EDELALTS.NS); cross-checked with Chittorgarh |

---

## 4. Secret Sanitization Audit (G5)

- **GitHub Secret Presence**: `gh secret list` confirms `OPENROUTER_API_KEY` is registered in GitHub Secrets.
- **Repository Pattern Scan**: Secret key pattern search returns strictly 0 matches across all branches and working trees.
- **Clean Hygiene**: Zero secret key material committed to disk, logs, issues, or snapshots.

---

## 5. PR #12 Audit & Status (G6)

- **PR State**: `OPEN` (URL: https://github.com/soul991/OPI/pull/12, branch: `retrain/challenger-20261103-214459`)
- **Appended Rows (9 total)**:
  1. HD Fire Protect Limited (listed 2026-10-21, gain 23.39%)
  2. Fusion CX Limited (listed 2026-10-22, gain 5.54%)
  3. Zetwerk Manufacturing Business Limited (listed 2026-10-23, gain 5.46%)
  4. Sahajanand Medical Technologies Limited (listed 2026-10-23, gain 7.89%)
  5. Tonbo Imaging India Limited (listed 2026-10-23, gain 65.71%)
  6. Bonfiglioli Transmissions Limited (listed 2026-10-23, gain 0.0%)
  7. Jio Platforms Limited (listed 2026-10-28, gain 21.36%)
  8. Paras Healthcare Limited (listed 2026-10-28, gain 3.90%)
  9. EAAA India Alternatives (listed 2026-11-02, gain 0.63%)
- **Existing Master Rows Changed**: Exactly **731 of 731** existing rows had values changed in `data/ipo_master.csv` (all existing integer years float-cast to `2010.0` due to NaN columns in appended rows, plus an unapproved `updated_at` column was introduced).
- **Failing Test on PR Head**: Running `pytest` on PR head `e084603` failed:
  `tests/test_discover.py::test_discovers_closed_unlisted_mainboard_ipos_from_fixture`
  `AssertionError: assert 'LISTED' == 'CLOSED_UNLISTED'` (Zetwerk, SMT, Jio, Paras presence in master breaks discovery test classification).
- **Disposition**: Per protocol, PR #12 is NOT merged and not pushed to. The user closes PR #12 on GitHub. Workstream B addresses the promotion format (D-092) and fixture isolation (D-093).
