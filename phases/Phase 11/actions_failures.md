# GitHub Actions Run Failures & Dashboard Publishing Audit (D-042, D-043)

> Recorded for Phase 11 Gate A11 (Items G3 & G4).

---

## 1. Actions Runs #9 and #10 Failure Root Cause (D-042)

### Summary
Across 18 recorded runs of the `.github/workflows/daily.yml` workflow, runs #9 and #10 failed. Inspection of the logs via `gh run view <id> --log-failed` reveals the exact failure mechanism:

### Run #9 Details
- **Run ID**: `39248257712`
- **Trigger**: Schedule (`cron: '0 6,14 * * *'`)
- **Execution Timestamp**: `2026-10-19T11:56:17Z`
- **Duration**: 56s
- **Runner**: Ubuntu 24.04 LTS (Hosted Agent)
- **Failing Step**: `Run Test Suite` (`python -m pytest -q`)
- **Error Output**:
  ```text
  tests/test_gate_a.py:136: in test_r6_prediction_log_status_and_filtering
      assert r["status"] == "INVALID", f"Hyundai row must be INVALID, got {r['status']}"
  E   AssertionError: Hyundai row must be INVALID, got FORWARD
  E   assert 'FORWARD' == 'INVALID'
  E     - INVALID
  E     + FORWARD
  FAILED tests/test_gate_a.py::test_r6_prediction_log_status_and_filtering - AssertionError: Hyundai row must be INVALID, got FORWARD
  1 failed, 63 passed in 10.33s
  Process completed with exit code 1.
  ```

### Run #10 Details
- **Run ID**: `39312521616`
- **Trigger**: Schedule
- **Execution Timestamp**: `2026-10-19T19:37:25Z`
- **Duration**: 48s
- **Runner**: Ubuntu 24.04 LTS (Hosted Agent)
- **Failing Step**: `Run Test Suite` (`python -m pytest -q`)
- **Error Output**:
  ```text
  tests/test_gate_a.py:136: in test_r6_prediction_log_status_and_filtering
      assert r["status"] == "INVALID", f"Hyundai row must be INVALID, got {r['status']}"
  E   AssertionError: Hyundai row must be INVALID, got FORWARD
  E   assert 'FORWARD' == 'INVALID'
  FAILED tests/test_gate_a.py::test_r6_prediction_log_status_and_filtering - AssertionError: Hyundai row must be INVALID, got FORWARD
  1 failed, 63 passed in 8.87s
  Process completed with exit code 1.
  ```

### Root Cause & Resolution
1. **Root Cause**: On 2026-10-19, `Hyundai Motor India` was logged in `predictions/prediction_log.csv` with `status = "FORWARD"`. However, Phase 6 regression test `tests/test_gate_a.py::test_r6_prediction_log_status_and_filtering` strictly enforces that Hyundai rows must carry status `INVALID` because the prediction occurred after listing / during an unverified session.
2. **Resolution**: The prediction log was subsequently updated in commit `7f7dc89` to set Hyundai's status to `INVALID`. All subsequent scheduled workflow runs from #11 (`39410837110`, 2026-10-20) through #18 (`40000268262`, 2026-10-23) passed completely green.

---

## 2. Dashboard Publishing Verification (D-043)

### Query and Evidence
- **GitHub Pages Remote Check**:
  ```bash
  gh api repos/soul991/OPI/pages
  ```
- **Response**:
  ```json
  {
    "message": "Not Found",
    "documentation_url": "https://docs.github.com/rest/pages/pages#get-a-apiname-pages-site",
    "status": "404"
  }
  ```
- **Finding**:
  GitHub Pages is currently **not enabled** on the repository `soul991/OPI`.
  The daily workflow step `Commit and Push Updated Predictions & Dashboard` writes and commits `dashboard/index.html` directly to the repository git tree, but does not deploy to GitHub Pages.
- **Classification**:
  The dashboard artifact is maintained strictly **in-repo (local/git artifact)** and is not publicly served at a GitHub Pages URL.

---

## 3. Jio Sector Ungrounded Verification (D-044)

- **Finding**: In `predictions/prediction_log.csv`, the feature snapshot for `Jio Platforms Limited` logs `"sector": "IT & Technology"`.
- **Audit**: Inspection of the underlying snapshot `data/evidence/research/2026-10-28_jio-platforms-limited.html` confirms that no sector or industry classification is stated in the Chittorgarh aggregator table.
- **Status**: The sector label `"IT & Technology"` is unevidenced in the snapshot and is flagged as **UNVERIFIED**.
