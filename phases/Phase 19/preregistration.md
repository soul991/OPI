# Phase 19: Preregistration of Exchange-Labelled Outcomes, Divergence Arbitration, and Proven Defect Closure

> Committed prior to any Workstream implementation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 19/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Small-Sample Epistemic Guardrail**: Sample size is currently $n = 11$ listed of 30 target forward predictions (2 pending listing outcome verification). All forward error distributions and headline metrics are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## 1. Divergence Arbitration Rule Specification (D-100, Workstream B)

When Tier 2 outcome resolution discovers that the primary source (`yfinance`) and the second source disagree beyond the strict 1.0% relative tolerance ($> 1.0\%$):

1. **Reachable Independent Source Expansion**:
   - The pipeline fetches up to two additional independent publishers verified reachable from GitHub Actions runners via `probe_sources.yml` (e.g., Groww, Chittorgarh, or direct exchange pages).
   - Every raw page fetched is saved verbatim as production evidence under `data/evidence/actuals/` with an exchange and quantity manifest per Workstream A.

2. **Pre-Registered Arbitration Decision Rule**:
   - **Label Compatibility Gating**: Values are compared **strictly if and only if** their `exchange` (NSE vs BSE) and `quantity` (`open` vs `listing_price`) labels match. Values with `UNKNOWN` exchange or mismatched quantities are never arbitrated.
   - **Independent Publisher Requirement**: Yahoo Finance and any Yahoo-derived page count strictly as **one publisher**.
   - **Majority Agreement Standard**: An outcome is accepted **only if** at least two sources from different independent publishers agree within the strict 1.0% tolerance:
     $$\frac{|P_a - P_b|}{\min(P_a, P_b)} \le 0.01$$
     **AND** the agreeing group constitutes a **strict majority** of all valid, labelled sources for that specific exchange and quantity.
   - **Recorded Price**: The official recorded opening price is the **median** of the agreeing majority group.
   - **Gain Computation**:
     $$\text{actual\_gain\_pct} = \frac{\text{recorded\_open} - \text{issue\_price}}{\text{issue\_price}} \times 100$$
   - **Tier Label**: Outcomes recorded via this rule receive the distinct tier label `tier2_arbitrated`.
   - **Comprehensive Manifest**: The resulting JSON manifest records every source value queried (including rejected ones), its publisher, exchange, quantity, bar date, and the prospective listing gain each value would have yielded.

3. **Fallback & Rejection Handling**:
   - If no strict majority exists among agreeing sources, the pipeline records nothing, sets status `PENDING_REVIEW`, logs `SKIPPED_ARBITRATION_NO_MAJORITY`, and keeps the row pending.
   - If sources match across different exchanges without an intra-exchange majority, the pipeline logs `SKIPPED_ARBITRATION_EXCHANGE_MISMATCH` and records nothing.
   - If fewer than two independent sources can be fetched, the pipeline logs `SKIPPED_ARBITRATION_UNAVAILABLE` and records nothing.
   - Already recorded outcomes are never overwritten or altered.

---

## 2. Inviolable Guardrails & Tolerance Standards

1. **Strict 1.0% Relative Tolerance Maintained**:
   - The 1.0% relative tolerance constant (`TOLERANCE_PCT = 1.0`) is non-negotiable and **must not be loosened** under any circumstance.
   - Automated tests will assert this constant directly.

2. **Explicit Label Separation (Workstream A, D-101)**:
   - Every source value recorded in manifests must carry: `publisher`, `exchange` (`NSE`, `BSE`, or `UNKNOWN`), `quantity` (`open` or `listing_price`), `bar_date`, and `value`.
   - Parsers that cannot definitively verify the exchange must output `UNKNOWN`; guessing or assuming exchanges is strictly prohibited.

3. **Zero Hand-Authored Production Evidence**:
   - No human or local AI assistant may write to `predictions/prediction_log.csv` or `data/evidence/` by hand.
   - Only automated GitHub Actions workflows running on GitHub runners are permitted to commit production evidence, prediction logs, or outcome actuals.

4. **Post-Hoc Acknowledgment & Disaggregated Reporting**:
   - Because this arbitration rule was formalized after the specific divergences for **BLS Polymers** (1.57%) and **Bombay Coated & Special Steels** (1.12%) were observed in production, all metrics in `scripts/forward_report.py` and Phase 19 reports must present forward MAE **both with and without** `tier2_arbitrated` rows, clearly identifying the post-hoc nature of arbitrated outcomes.

---

## 3. Epistemic Guardrails & Model Immutability

1. **Small-Sample Boundary ($n = 11$ of 30)**:
   - Sample size stands at $n = 11$ evaluated forward predictions.
   - All performance evaluations remain strictly provisional and descriptive. No statistical claims of model superiority or winning against baselines are allowed.

2. **Champion Model Integrity**:
   - Production champion model `model/ipo_model.joblib` and Git release tag `v4.0.0-champion` remain strictly unchanged.
   - Scripts `scripts/verify_extra.py`, `scripts/verify_all.py`, and `scripts/verify_pages.py` must not be edited to make checks pass.
   - No bot pull requests may be merged without human verification.
