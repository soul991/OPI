# Preregistration: Prospective $n = 30$ Final Evaluation Protocol

> **Status**: Registered & Immutable Protocol (Phase 13 / Defect D-060)  
> **Preregistration Date**: 2026-10-24  
> **Execution Condition**: Strictly automated execution via `scripts/final_evaluation.py` upon reaching $n = 30$ listed forward IPOs with verified exchange actuals.  
> **Mandatory Disclaimer**: Research decision aid only, not financial or investment advice.

---

## 1. Objective and Evaluation Scope

This protocol establishes the immutable prospective evaluation plan for assessing the production forecasting accuracy and statistical validity of the OPI quantitative IPO listing-gain model (`v4.0.0-champion`).

The primary research question is:
> Does the multi-modal conformal gradient boosted model achieve statistically superior accuracy compared to the grey-market premium (GMP) heuristic and naive historical baselines on prospective, un-leaked Indian Mainboard IPOs?

To eliminate p-hacking, selective reporting, or retroactive metric definitions, all evaluation rules, sampling cohorts, statistical tests, random seeds, and phrasing guardrails are preregistered herein prior to reaching the target sample size.

---

## 2. Cohort Definition and Population Rules

1. **Target Sample Size**: Exactly the first $n = 30$ prospectively scored Mainboard IPOs that list on NSE/BSE with official opening price evidence.
2. **Strict Inclusion Criteria**:
   - Status must be `FORWARD` in `predictions/prediction_log.csv`.
   - Prediction must have been committed and timestamped prior to official listing time (`scored_at < listing_date`).
   - Official opening price and `actual_gain_pct` must be established from verified NSE/BSE exchange snapshots under `data/evidence/actuals/` with SHA-256 hash provenance.
   - Mainboard IPOs only; SME exchange IPOs are excluded.
3. **Exclusion / Separation Policy**:
   - No row may be selectively dropped or re-classified post-listing.
   - Predictions tagged as `confidence: LOW` (e.g., extreme mega-issues like Jio Platforms exceeding training support, or missing financial metrics) remain in the comprehensive population, but must be evaluated in two explicit cohorts:
     - **Full Cohort ($n = 30$)**: All 30 genuine forward listings.
     - **Core Cohort ($n_{\text{core}} \le 30$)**: Forward listings excluding `confidence: LOW` rows.

---

## 3. Primary Evaluation Metrics

All metrics are computed deterministically from `predictions/prediction_log.csv`:

1. **Model Mean Absolute Error (MAE)**:
   $$\text{MAE}_{\text{model}} = \frac{1}{n} \sum_{i=1}^{n} | \hat{y}_{i}^{\text{model}} - y_{i} |$$

2. **GMP Mean Absolute Error (MAE)**:
   Computed across rows with observed GMP ($n_{\text{gmp}}$):
   $$\text{MAE}_{\text{gmp}} = \frac{1}{n_{\text{gmp}}} \sum_{i=1}^{n_{\text{gmp}}} | \hat{y}_{i}^{\text{gmp}} - y_{i} |$$

3. **Historical-Mean Baseline MAE**:
   Calculated using the constant historical training set mean listing gain (24.77 pp):
   $$\text{MAE}_{\text{baseline}} = \frac{1}{n} \sum_{i=1}^{n} | 24.77 - y_{i} |$$

4. **Conformal Interval Empirical Coverage**:
   Fraction of actual outcomes falling within the nominal 90% conformal prediction interval $[q_{0.05}, q_{0.95}]$:
   $$\text{Coverage Rate} = \frac{1}{n} \sum_{i=1}^{n} \mathbb{I}(y_{i} \in [\hat{y}_{i}^{\text{low}}, \hat{y}_{i}^{\text{high}}])$$
   Accompanied by a 95% Wilson Score Confidence Interval.

5. **Directional Accuracy**:
   Accuracy in predicting whether listing gain is positive ($> 0\%$) vs non-positive ($\le 0\%$):
   $$\text{Accuracy}_{\text{dir}} = \frac{1}{n} \sum_{i=1}^{n} \mathbb{I}(\text{sgn}(\hat{y}_{i}) == \text{sgn}(y_{i}))$$

6. **Probabilistic Calibration (Brier Score)**:
   Mean squared error between calibrated probability $P(\text{gain} > 0)$ and binary indicator $\mathbb{I}(y_i > 0)$.

---

## 4. Statistical Hypothesis Testing Methodology

1. **Paired Difference Analysis**:
   For each IPO $i$ where GMP was observed, compute the paired absolute error difference:
   $$d_{i} = | \hat{y}_{i}^{\text{gmp}} - y_{i} | - | \hat{y}_{i}^{\text{model}} - y_{i} |$$
   A positive $d_i$ indicates superior model accuracy on instance $i$.

2. **Bootstrap Resampling**:
   - **Method**: Non-parametric paired bootstrap resampling of the vector of paired differences $(d_1, \dots, d_{n_{\text{gmp}}})$.
   - **Resamples**: Exactly $B = 2,000$ bootstrap iterations.
   - **Random Seed**: Fixed pseudo-random seed `42` (`numpy.random.default_rng(42)`).
   - **Confidence Level**: Two-sided 95% percentile confidence interval: $[\theta^*_{0.025}, \theta^*_{0.975}]$.

---

## 5. Claim Governance & Wording Constraints

To prevent overclaiming and ensure scientific integrity:
1. **The "Strict Superiority" Rule**:
   - The model may be described as having **"statistically outperformed"** or **"statistically beaten"** GMP **IF AND ONLY IF** the 95% bootstrap confidence interval of the mean paired error difference $[\theta^*_{0.025}, \theta^*_{0.975}]$ is strictly greater than zero ($\theta^*_{0.025} > 0.00$).
2. **Indistinguishable Performance Rule**:
   - If the 95% bootstrap interval includes zero (e.g., $[-1.50, +3.20]$), the narrative report MUST state that the model's accuracy is **"statistically indistinguishable from the GMP heuristic"** or **"within expected sampling variance"**.
3. **Inferior Performance Rule**:
   - If the 95% bootstrap interval is strictly below zero ($\theta^*_{0.975} < 0.00$), the narrative report MUST explicitly conclude that GMP outperformed the model.
4. **Sample Size Gate ($n < 30$)**:
   - While $n < 30$, all dashboards and documentation must display the **"PROVISIONAL"** banner. No formal victory or definitive empirical claims are permitted until $n = 30$ is reached.

---

## 6. Automation & Execution Mechanism

1. The script `scripts/final_evaluation.py` is invoked during daily automated runs.
2. For $n < 30$, the script outputs `NOT_READY (n=<k> of 30)` and exits cleanly.
3. Upon detecting $n \ge 30$, the script automatically generates:
   - `phases/Final Evaluation/report.md` with complete tabular breakdown and KaTeX statistics.
   - Transitions the dashboard data status from `provisional: True` to `provisional: False`.
4. This preregistration file itself remains strictly read-only and immutable.
