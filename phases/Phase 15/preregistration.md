# Phase 15: Preregistration of Listing-Day Price Enforcement, Outcome Corrections, and CI Runner Parity

> Committed prior to any Workstream implementation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 15/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Epistemic Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice. Sample size is $n = 8 < 30$. All forward metrics are descriptive.

---

## 1. The Listing-Day-Only Rule (D-072)

1. **Strict Session Matching**:
   - In `fetch_yfinance_first_session_open`, every retrieved price bar's timestamp index must be converted to `Asia/Kolkata` (+05:30).
   - The bar's calendar date in IST must strictly equal the IPO's `listing_date`.
   - The former fallback to the first chronological bar in the series (`iloc[0]` without date equality) is completely removed.
2. **Missing-Bar Protocol**:
   - If no bar in the retrieved price history matches `listing_date`, the function must return `(None, "LISTING_DAY_BAR_MISSING: first bar is <date>, listing date <date>", raw_bytes)`.
   - The automated recording engine must never record another trading day's price as the listing outcome.
   - The execution logs `SKIPPED_NO_MATCH` or `PENDING_REVIEW` with the specific reason.
   - A missing bar older than 2 calendar days triggers a GitHub Actions alert issue under defect rule D-067.
   - The raw response payload is always persisted to disk under `data/evidence/actuals/` with SHA256 checksum for auditability.

---

## 2. Multi-Source Tier 2b Protocol (D-073)

1. **Definition of Tier 2b**:
   - When Tier 1 (Official Exchange Direct Scrape) is blocked or unreachable (e.g. WAF 403), and Tier 2 (Yahoo Finance) lacks the listing-day bar (`LISTING_DAY_BAR_MISSING`), the pipeline may invoke **Tier 2b**.
2. **The 1.0% Two-Independent-Page Rule**:
   - Tier 2b requires **two independent, code-fetched web pages** (neither Yahoo Finance), each explicitly citing the company's `listing_date` and official opening/listing price.
   - Candidates include Chittorgarh stock price quote page and an independent listing tracker (e.g., `gmpipowatch.in`).
   - The two independent sources must agree within 1.0% relative tolerance:
     $$\frac{|\text{Price}_{\text{SourceA}} - \text{Price}_{\text{SourceB}}|}{\text{Price}_{\text{SourceA}}} \le 0.01$$
   - Both complete HTTP responses must be saved as raw evidence in `data/evidence/actuals/` with manifest metadata.
   - If two independent pages agreeing within 1.0% cannot be retrieved by code, **nothing is recorded**, status remains `PENDING_REVIEW`, and an alert issue is raised.
   - Rows recorded or corrected under this protocol receive `outcome_source=tier2b`.

---

## 3. Audited Append-Only Corrections Engine (D-073)

1. **Byte-Identical Log Immutability**:
   - The file `predictions/prediction_log.csv` is strictly append-only for prospective logging and must never be edited in-place to correct an outcome.
   - Every file diff on `predictions/prediction_log.csv` during correction workflows must show zero modifications to existing rows.
2. **The Corrections Ledger (`predictions/outcome_corrections.csv`)**:
   - All corrections are stored in `predictions/outcome_corrections.csv`.
   - Required schema:
     `company, listing_date, field, old_value, new_value, reason, evidence_path, tier, corrected_at`
3. **Effective Outcome Resolver (`opi.outcomes::effective_outcome`)**:
   - All reporting modules (`forward_report.py`, `final_evaluation.py`, `recompute_gate_a*.py`, and dashboard generator `opi.report`) must query row outcomes exclusively through `effective_outcome(row)`.
   - `effective_outcome` returns the latest registered correction from `outcome_corrections.csv` for a given company and listing date, falling back to `prediction_log.csv` if no correction exists.
4. **Dual Visibility Requirement**:
   - Every report, post-mortem, and dashboard view must show both the original recorded value and the corrected effective value, alongside the audit reason and evidence manifest link.

---

## 4. Cloud Runner Parity & Smoke Testing (D-074, D-075, D-076)

1. **Runner Reachability Evidence Standard (D-074 / D-068)**:
   - D-068 may be marked `FIXED` only upon committing `phases/Phase 15/source_probe_runner.md` produced directly inside a GitHub Actions Linux runner (with environment line verifying Linux and runner run ID).
   - If exchanges remain unreachable (HTTP 403) from cloud runners, this limitation must be recorded transparently.
2. **Entry-Point Smoke Testing (D-075)**:
   - `tests/test_workflow_entrypoints.py` must dynamically inspect all GitHub Actions workflow files (`.github/workflows/*.yml`), extract every CLI invocation (`python scripts/...` or `python -m ...`), and execute each with standalone entry-point arguments without inherited local environment variables.
   - The smoke test must be added to `scripts/ci_local.py` to ensure local tests execute in the exact environment order as CI.
   - Verification standard: The smoke test must be proven by demonstrating failure against the pre-fix watchdog code (prior to `9dd1b7d`) and passing on current code. D-075 cannot be marked FIXED on the strength of `9dd1b7d` alone.
3. **Branch and PR Process Rule (D-076)**:
   - Every bug fix and workstream change must have a registered defect ID in `DEFECTS.md` before commit, must be committed on a dedicated branch, must pass `ci_local.py`, and must be merged via pull request. Direct pushes to `main` for fixes are strictly prohibited.

---

## 5. Statistical Epistemic Governance

1. **Provisional Forward Sample ($n = 8 < 30$)**:
   - All prospective results are strictly observational and descriptive.
   - No statements claiming the model "beats", "outperforms", or "falsifies" GMP baselines are permitted before $n \ge 30$ verified listings with paired bootstrap confidence intervals.
