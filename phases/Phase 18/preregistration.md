# Phase 18: Preregistration of Tier 2b Automation, Non-Blocking Overdue Alerts, Universal Market Evidence, and Pending Outcomes Visibility

> Committed prior to any Workstream implementation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 18/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Epistemic Statement**: This project is a quantitative research decision aid, not financial, trading, or investment advice. Sample size is $n = 9$ listed of 30 target forward predictions (4 unlisted pending). All forward error distributions and headline metrics remain provisional and descriptive. No statistical superiority claims ("beats GMP", "unbeatable", "proven edge") are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## 1. Tier 2b Acceptance & Automation Specification (D-096)

1. **Dual Independent Non-Yahoo Source Standard**:
   - When Tier 2 returns `LISTING_DAY_BAR_MISSING` or `yfinance returned empty` and the listing date is at least 1 day in the past (`listing_date < today_ist`), the automated pipeline executes Tier 2b.
   - The pipeline fetches opening trade prices from two independent non-Yahoo sources verified reachable from GitHub Actions runners (via `probe_sources.yml`).
   - Both pages must be dated on or after the listing date and must explicitly name the company.
   - Opening prices from both sources must agree within **1.0% tolerance**:
     $$\frac{|P_{\text{source1}} - P_{\text{source2}}|}{\min(P_{\text{source1}}, P_{\text{source2}})} \le 0.01$$
   - The agreed opening price is the unweighted average of the two agreeing sources (or the primary non-Yahoo source if within tolerance).
   - `actual_gain_pct` is computed using the standard formula:
     $$\text{actual\_gain\_pct} = \frac{\text{agreed\_open} - \text{issue\_price}}{\text{issue\_price}} \times 100$$
   - The outcome is recorded with tier label `tier2b`.
2. **Disagreement & Missing Source Guardrails**:
   - If sources disagree by more than 1.0%, the pipeline logs `SKIPPED_TIER2B_DISAGREE` and records no outcome.
   - If fewer than two reachable sources are available or parsable, the pipeline logs `SKIPPED_TIER2B_UNAVAILABLE` and records no outcome.
   - The Yahoo listing-day bar guard (D-072) remains inviolate: the pipeline never accepts a first bar that does not match the exact listing date.
3. **Evidence Persistence**:
   - Raw pages from both independent sources are saved verbatim as production evidence under:
     `data/evidence/actuals/<listing_date>_<company-slug>_<source>_tier2b.{json,txt}`.

---

## 2. Prohibition on Manual Evidence and Hand-Written Data

1. **Zero Hand-Authored Production Data**:
   - Never write to `predictions/prediction_log.csv` or `data/evidence/` by hand or from a local developer machine.
   - All production forward predictions, outcomes, actuals snapshots, and market evidence files are written solely by GitHub Actions automated workflows.
   - No mock, fake, or synthetic data files may ever be placed under `data/evidence/` or `data/research_runs/`.

---

## 3. Non-Blocking Overdue Alerts Specification (D-095)

1. **Alerts Never Block Automated Commits**:
   - An overdue unrecorded outcome (`check_missing_outcomes` > 2 days) or a coverage gap (`check_unlogged_closing_ipos`) must **NEVER** raise an unhandled exception in `opi.run_daily`.
   - `opi.run_daily` logs `MISSING_OUTCOME_ALERT` or `COVERAGE_ALERT` to `predictions/run_log.csv`, prints the alert details to console, and exits `0` (success) so that upstream and downstream data (new IPO discoveries, dashboard updates, predictions) are committed.
2. **Post-Commit Workflow Failure & Alerting**:
   - In `daily.yml`, a dedicated step named `Check overdue outcomes and coverage` executes **after** the `Commit and Push` step.
   - This step re-checks overdue outcomes and coverage, and exits non-zero if an alert condition exists.
   - The job fails at this dedicated step, triggering the automated notification issue naming the exact failing step per D-091 format, while preserving committed data.

---

## 4. Universal Market Evidence Ingestion Rule (D-097, D-085)

1. **Evidence for Every Past Listing Date**:
   - `opi.market.ensure_market_evidence_for_listed_dates` must collect and persist Nifty 50 and India VIX evidence for **every** `FORWARD` row with `listing_date <= today_ist`, regardless of whether `actual_gain_pct` is recorded or pending.
   - The job fetches Nifty close, previous close, and 1-day return, saving raw and parsed artifacts:
     `data/evidence/market/<listing_date>_nifty.raw`
     `data/evidence/market/<listing_date>_nifty.json`
2. **Immutability & Integrity**:
   - Existing market evidence files are never overwritten.
   - If market data is temporarily unavailable from the provider, the job logs `MARKET_EVIDENCE SKIPPED_<reason>` and retries on subsequent runs.
   - Values are never guessed, interpolated, or typed by hand.

---

## 5. Pending Outcomes Visibility Specification (D-098)

1. **Transparent Operational Status**:
   - Both `dashboard/index.html` and `predictions/pre_listing_predictions.md` must display a dedicated table: **"Listed, outcome pending"**.
   - Table fields: `Company`, `Listing Date`, `Days Since Listing`, `Last Logged Status`, and `Reason / Detail`.
   - Populated dynamically from `predictions/prediction_log.csv` and `predictions/run_log.csv` with sanitized error text.

---

## 6. Closure Criteria for Phase 18 Defects

1. **D-095 (Alerts never block commits)**:
   - `FIXED` requires: unit test with fixture log demonstrating `run_daily` exits 0 with alert logged; workflow-order test asserting alert step runs after commit without `continue-on-error`; and cloud proof where an overdue row commits data while the alert step fails with issue naming `Check overdue outcomes and coverage`. (If no overdue row exists in cloud, left `PARTIAL`).
2. **D-096 (Tier 2b in the cloud)**:
   - `FIXED` requires: unit tests verifying agreement, disagreement (>1.0%), and source failure; cloud proof where BLS Polymers, SFC Environmental, or M.K.Sons is recorded by a cloud run with two saved evidence files under `data/evidence/actuals/`.
3. **D-097 (Universal market evidence) & D-085 (Historical Nifty evidence)**:
   - `FIXED` requires: unit tests asserting past unrecorded listing dates receive evidence and future dates do not; cloud proof of `2026-11-03_nifty.*` and `2026-11-04_nifty.*` committed by `github-actions[bot]`; and `scripts/verify_extra.py` passing 7 of 7 checks in CI.
4. **D-098 (Pending-outcome visibility)**:
   - `FIXED` requires: fixture unit tests verifying table rendering in dashboard and markdown; no manual edits to `verify_all.py`, `verify_extra.py`, or `verify_pages.py`.
5. **D-091 (Daily alert failed step name)**:
   - Reopened in Gate A18 (`OPEN`). `FIXED` requires cloud proof where a failing workflow run produces an issue body naming the exact failed step rather than `Execution`.
6. **D-026 (Live research agent)**:
   - Stays `NOT FIXED` awaiting a real upcoming IPO in a scheduled cloud run.
7. **D-013 (Historical Phase 7 audit snapshots)**:
   - Stays `PARTIAL` as a documented historical constraint.

---

## 7. Model Stability & Epistemic Boundaries

1. **Champion Model Immutability**:
   - The production champion model `model/ipo_model.joblib` and its release tag `v4.0.0-champion` remain strictly unchanged.
   - Scripts `scripts/verify_extra.py`, `scripts/verify_all.py`, and `scripts/verify_pages.py` must not be edited to make failing tests pass.
2. **Sample Size & Reporting Limits**:
   - Target remains $n = 30$. Current sample is $n = 9$ listed ($n = 8$ prior cohort, $n = 7$ with GMP, 4 pending).
   - No claims of model superiority, outperforming GMP, or statistical significance may be made in any report or documentation. All metrics are descriptive and provisional.
