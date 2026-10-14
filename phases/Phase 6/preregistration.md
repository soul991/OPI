# Phase 6: Pre-Registration Protocol

> **Status**: Frozen Pre-Registration Document  
> **Committed**: Prior to Phase 6 model retraining and evaluation per `RULES.md` and `phases/Phase 6/1_planning_and_goals.md`.  
> **Rule**: Any post-hoc changes require a dated "Amendment" section; the original protocol text remains unmodified.

---

## 1. Objectives & Pre-Registered Hypotheses

1. **Re-Evaluation on Purified Dataset (Workstream B)**:
   - Cleaned dataset removes 3 FPOs/non-listings and 15 duplicate rows.
   - Hypothesis: Conclusions from Phase 5 (H1 fundamentals lack of effect, raw GMP superiority on quoted issues, model utility on non-GMP issues) will be tested with paired bootstrap on clean data.
2. **Prediction Intervals (Workstream C)**:
   - Method: Split-conformal prediction intervals computed using historical absolute residuals from rolling-origin out-of-sample folds prior to each evaluation quarter.
   - Target nominal coverage: **80%** (acceptable empirical range: **75% to 85%**).
3. **Fundamentals Decision (Workstream F)**:
   - **Path 2 (Close)** is formally selected: Formally close the fundamentals research line (*"no demonstrated effect with 3 of 7 columns; remaining columns not feasible from machine-readable primary sources without non-reproducible manual extraction"*). No aggregator values will be treated as primary-sourced.
4. **Real Forward Test (Workstream E)**:
   - Genuine unlisted IPOs scored prior to listing date using calibrated pipeline; strictly provisional below $n=30$.
5. **Tail Handling (Workstream G - Optional)**:
   - Asymmetric/quantile Huber loss compared to $L_1$ loss on rolling-origin data; accepted if and only if top-decile MAE improves with 95% bootstrap interval excluding zero and pooled MAE does not worsen.

---

## 2. Exact Mathematical Evaluation Metrics

1. **Continuous Regression Error**:
   - **Mean Absolute Error (MAE)**:
     $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N \left| y_i - \hat{y}_i \right|$$
   - **Median Absolute Error (MedAE)**:
     $$\text{MedAE} = \text{median}\left(\left| y_1 - \hat{y}_1 \right|, \dots, \left| y_N - \hat{y}_N \right|\right)$$
   where $y_i$ is actual listing day percentage gain and $\hat{y}_i$ is point prediction.

2. **Classification & Calibration Metrics**:
   - **Binary Target**: $\text{label\_good} = \mathbb{I}(y_i > 10.0\%)$.
   - **Discrimination**: Area Under ROC Curve (ROC-AUC) evaluated on continuous calibrated probabilities $\hat{p}_i \in [0, 1]$.
   - **Brier Score Loss**:
     $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N (\hat{p}_i - y_{i,\text{bin}})^2$$
   - **Expected Calibration Error (ECE - Equal-Frequency Quantile Bins)**:
     $$\text{ECE}_{\text{quantile}} = \sum_{m=1}^M \frac{|B_m|}{N} |\text{acc}(B_m) - \text{conf}(B_m)|$$
     with $M=10$ quantile bins.
   - **Wilson 95% Confidence Intervals for Bin Reliability**:
     For each calibration bin with count $n$ and observed positive rate $\hat{p}$:
     $$CI_{\text{Wilson}} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}} \quad (z = 1.96)$$

3. **Prediction Interval Metrics (Conformal Prediction)**:
   - **Nominal Coverage**: $1 - \alpha = 0.80$ (80%).
   - **Empirical Coverage**: Fraction of actual listing gains falling within predicted bounds:
     $$\text{Coverage} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\hat{y}_{i,\text{lower}} \le y_i \le \hat{y}_{i,\text{upper}})$$
   - **Mean Interval Width**:
     $$\text{Width} = \frac{1}{N} \sum_{i=1}^N (\hat{y}_{i,\text{upper}} - \hat{y}_{i,\text{lower}})$$
   - Evaluated pooled, by half-year buckets, for issues with vs without GMP, and for top 10% gains.

---

## 3. Paired Bootstrap Inference Protocol

All model comparisons use paired non-parametric bootstrapping:
- **Resamples**: Exactly $B = 2,000$ iterations.
- **Fixed Random Seed**: `seed = 42`.
- **Confidence Interval**: Two-sided 95% bootstrap percentile interval:
  $$CI_{95\%} = [\Delta_{(0.025)}, \Delta_{(0.975)}]$$
- **Evidence Language Mandate**:
  - *"Beats"*, *"wins"*, *"improves"*, or *"falsified"* are permitted **if and only if** the 95% interval strictly excludes zero.
  - If the interval straddles zero, the wording **must** be *"no demonstrated difference"* or *"no demonstrated advantage"*.

---

## 4. Conformal Prediction Interval Protocol

For each rolling-origin test quarter $Q_t$:
1. Let $\mathcal{D}_{\text{train}, t} = \{(x_i, y_i) : \text{listing\_date}_i < \text{start}(Q_t)\}$.
2. Train model $\hat{f}_t$ on inner 80% split of $\mathcal{D}_{\text{train}, t}$.
3. Compute non-conformity scores (absolute residuals) on calibration split (remaining 20% of $\mathcal{D}_{\text{train}, t}$):
   $$R_j = |y_j - \hat{f}_t(x_j)|, \quad j \in \mathcal{D}_{\text{cal}, t}$$
4. For nominal $80\%$ coverage ($\alpha = 0.20$), calculate the $(1-\alpha)(1 + 1/n_{\text{cal}})$-th empirical quantile $\hat{q}_{\alpha}$ of residuals.
5. For test instance $x_{\text{test}} \in Q_t$, output prediction interval:
   $$[\hat{y} - \hat{q}_{\alpha}, \; \hat{y} + \hat{q}_{\alpha}]$$
6. Strictly out-of-sample: $\hat{q}_{\alpha}$ is determined strictly before quarter $Q_t$ begins.

---

## 5. Blend Weight Selection & Inference Rules

1. **Active GMP Regime**:
   $$\hat{y}_{\text{blend}} = w \cdot \text{GMP} + (1-w) \cdot \hat{y}_{\text{model}}$$
   Weight $w \in [0.0, 1.0]$ optimized on inner training validation by minimizing MAE.
   Inference output rule: *"GMP available: rely on GMP as primary expected listing gain; model provides contextual confidence interval."*
2. **No-GMP Regime**:
   Inference output rule: *"GMP not available: model estimate with conformal prediction interval."*

---

## 6. Pre-Registered Decision Thresholds

| Decision Area | Metric | Success / Action Threshold |
|---|---|---|
| **Conformal Interval Coverage** | Empirical Coverage | Target $80\% \pm 5\%$ ($[75\%, 85\%]$); report gap otherwise |
| **Model vs Mean Baseline** | Paired Bootstrap $\Delta\text{MAE}$ | Accept if 95% CI excludes zero in favorable direction |
| **Model / Blend vs Raw GMP** | Paired Bootstrap $\Delta\text{MAE}$ | Declare superiority only if 95% CI excludes zero |
| **Probability Calibration** | Out-of-sample Equal-Freq ECE | Target $\le 0.10$; Wilson intervals reported per bin |
| **Forward Test Validity** | Sample size $n$ | Strictly PROVISIONAL below $n=30$; no statistical claims |
| **Frozen Test Partition** | `data/ipo_phase5_final_test.csv` | ZERO reads during development or tuning |
