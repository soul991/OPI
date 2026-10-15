# Phase 8: Pre-Registration Document

> Committed under `phase8-preregistration` prior to any Workstream implementation.  
> Governs Workstreams A (Pipeline Refactor), B (Automated Daily Forward Test), C (Dashboard), and D (Retraining Governance).

---

## 1. Timing & Bidding Rules for Forward Scoring

1. **Eligible Issues**: Indian Mainboard IPOs listed on BSE / NSE only. SME IPOs, Follow-on Public Offers (FPOs), rights issues, and debt offerings are strictly excluded.
2. **Scoring Window**: An upcoming IPO may **only be scored after bidding closes** (strictly after 18:00 IST on the official issue closing date). Scoring prior to bidding close or using Day-1/Day-2/live interim subscription data is invalid.
3. **Mandatory Final Inputs**:
   - Final official subscription ratios (Total, QIB, NII, Retail) sourced from BSE/NSE consolidated bidding data or verified aggregators (Chittorgarh).
   - Final-day pre-listing Grey Market Premium (GMP) if available, dated on or before the last bidding day.
   - Issue structure parameters: Issue size (Rs Cr), lot size, fresh issue %, OFS %, sector, exchange.
   - Market regime parameters: Nifty 30-day return, India VIX, trailing recent IPO average gain.
4. **Evidence Standard**: Every feature snapshot must record the source URL, page date, access date, and have a saved local HTML/evidence snapshot under `data/evidence/`. If inputs cannot be fetched or verified, the issue must be logged as `SKIPPED_<reason>` in `predictions/run_log.csv`. Missing values must never be fabricated, estimated, or imputed.
5. **Pre-Listing Lock**: All predictions must be committed to the append-only log `predictions/prediction_log.csv` strictly before the listing date. No retroactive logging or backfilling is permitted.
6. **Outcome Logging**: Actual listing price may only be recorded after official trading commences on the listing date (or later), supported by an official exchange price snapshot.

---

## 2. Evaluation Metrics & Statistical Decision Rules

1. **Point Prediction Accuracy**:
   - Metric: Mean Absolute Error (MAE) in percentage points of listing-day gain.
   - Benchmark 1: Expanding historical mean baseline.
   - Benchmark 2: Raw Grey Market Premium (GMP) when available.
   - Benchmark 3: Adaptive Blend ($0.55 \times \text{GMP} + 0.45 \times \text{Model}$).
2. **Directional Probability Calibration**:
   - Classification target: Listing gain $> 10.0\%$.
   - Metrics: ROC-AUC, Brier score loss, Equal-Frequency Expected Calibration Error (ECE) across 10 quantile bins.
   - Calibration algorithm: Platt scaling (logistic calibration) on out-of-fold validation residuals.
3. **Uncertainty Quantification**:
   - Method: Split-conformal prediction at nominal 80.0% confidence level ($1 - \alpha = 0.80$).
   - Monitored cohorts: Pooled out-of-sample issues, observed GMP regime, and extreme tail pops (top 10% largest gains $\ge 50\%$).
4. **Evidence-Standard Language Rules**:
   - Superiority claims ("beats", "improves", "advantage") require a 2,000-iteration paired bootstrap 95% confidence interval strictly excluding zero.
   - If the 95% bootstrap confidence interval straddles zero, the outcome must strictly be reported as "no demonstrated difference / effect".
   - Explanations of underlying market drivers must be labeled "Hypothesis (untested)".

---

## 3. Automated Daily Forward Runner Specification (Workstream B)

1. **Workflow**: Automated GitHub Actions scheduled workflow (`.github/workflows/daily.yml`) running twice daily (06:00 UTC and 14:00 UTC / 11:30 IST and 19:30 IST) with `workflow_dispatch` manual trigger.
2. **Command Entrypoint**: `python -m opi.run_daily [--dry-run]`
3. **Execution Steps**:
   - Query upcoming/closing mainboard IPOs from official exchange feeds / tracking aggregators.
   - Filter to issues where bidding closed today and listing date is in the future.
   - Collect final subscription and GMP data, download and store evidence snapshots in `data/evidence/`.
   - Validate features against schema and timing rules.
   - Compute point estimate, conformal interval, and Platt-calibrated probability using the registered champion model.
   - Append prediction row to `predictions/prediction_log.csv`.
   - For already-logged IPOs whose listing date has passed, fetch official listing price, verify against exchange circular, and update actuals via `opi.log`.
   - Run test suite and `scripts/verify_all.py` to ensure repository integrity.

---

## 4. Dashboard Specification (Workstream C)

1. **Generation**: Static HTML/CSS dashboard generated in `dashboard/` directly from CSV data files by `opi.report` (no manual number entry).
2. **Required Dashboard Views**:
   - **Forward Predictions Table**: All FORWARD rows with timestamp, company, issue size, subscription, GMP, model prediction, calibrated probability, and status (PENDING, LISTED, SKIPPED, INVALID).
   - **Predicted vs Actual Scatter Plot**: Scatter of predicted gain vs actual listing gain for all listed forward issues.
   - **Cumulative MAE Comparison**: Model vs Historical Mean Baseline vs Raw GMP.
   - **Conformal Interval Coverage**: Empirical coverage percentage vs nominal 80% target.
   - **Calibration Reliability Table**: Shown only when listed issues $n \ge 30$; below $n = 30$, displays "Calibration table deferred until n >= 30".
   - **System & Model Health**: Registered model version, date of artifact, and latest `verify_all.py` execution status (PASS/FAIL counts, open defects count).
   - **Provisional Disclaimer Banner**: Prominently displayed: `"PROVISIONAL (n = ...): Decision aid only, not financial advice. No empirical performance claims permitted until n >= 30."`

---

## 5. Model Registry & Retraining Governance (Workstream D)

1. **Model Registry**: `model/registry.json` tracks model versions. Each entry includes:
   - `model_version`: Deterministic identifier based on training data hash, feature code hash, and hyperparameter configuration.
   - `training_window`: Start and end dates / quarters of training data.
   - `created_at`: Creation ISO timestamp.
   - `champion`: Boolean flag indicating active production model.
2. **Promotion Governance**:
   - Automatic model retraining or auto-promotion in CI is strictly prohibited.
   - Challenger models may be trained and evaluated only quarterly or after at least 30 new verified forward test rows have accumulated.
   - Evaluation protocol: Paired bootstrap comparison against the champion on the identical expanding walk-forward test split.
   - Promotion criteria: Challenger must achieve statistically non-inferior MAE (bootstrap interval for $\Delta(\text{Challenger} - \text{Champion})$ does not exclude zero in the wrong direction) AND equal or better calibration/conformal coverage.
   - Every promotion requires updating `model/registry.json`, logging the change in the dashboard, and committing the new artifact with evidence.
