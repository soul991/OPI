# Phase 5: Pre-Registration Protocol

> **Status**: Frozen Pre-Registration Document  
> **Committed**: Prior to Phase 5 model retraining per `RULES.md` and `phases/Phase 5/1_planning_and_goals.md`.  
> **Rule**: Any post-hoc changes require a dated "Amendment" section with justification; the original protocol remains unmodified.

---

## 1. Exact Evaluation Metrics

All model iterations and baselines will be evaluated using the following formal mathematical definitions:

1. **Continuous Regression Error**:
   - **Mean Absolute Error (MAE)**:
     $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N \left| y_i - \hat{y}_i \right|$$
   - **Median Absolute Error (MedAE)**:
     $$\text{MedAE} = \text{median}\left(\left| y_1 - \hat{y}_1 \right|, \dots, \left| y_N - \hat{y}_N \right|\right)$$
   where $y_i$ is actual listing day gain (`listing_gain_pct`) and $\hat{y}_i$ is predicted gain.

2. **Classification & Discrimination**:
   - **Binary Target**: `label_good` $= \mathbb{I}(y_i > 10.0\%)$.
   - **Area Under ROC Curve (ROC-AUC)**: Evaluated on continuous predicted probabilities $\hat{p}_i \in [0, 1]$.
   - **Threshold Accuracy**: Accuracy evaluated at standard decision threshold $\hat{p}_i \ge 0.50$.

3. **Probability Calibration**:
   - **Brier Score Loss**:
     $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N \left( \hat{p}_i - y_{i,\text{bin}} \right)^2$$
   - **Expected Calibration Error (ECE - Equal-Frequency Quantile Bins)**:
     $$\text{ECE}_{\text{quantile}} = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
     where $M=10$ quantile bins are formed using empirical percentiles of predicted probabilities, ensuring equal sample sizes across bins.
   - **Expected Calibration Error (ECE - Equal-Width Bins)**:
     $$\text{ECE}_{\text{uniform}} = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
     where $M=10$ uniform bins span $[0, 0.1), [0.1, 0.2), \dots, [0.9, 1.0]$.
   - **Target**: $\text{ECE} \le 0.10$ measured **strictly out-of-sample** (not on the calibration fitting set).

4. **Extreme Tail Behaviour**:
   - Evaluated on the top 10% largest actual listing day gains in the evaluation partition.
   - Mean absolute error and maximum error on this subset will be reported explicitly.

---

## 2. Paired Bootstrap Procedure

All performance comparisons between competing models or baselines (e.g., Model vs GMP, Blend vs GMP, Model vs Historical Mean, Model With Fundamentals vs Model Without Fundamentals) will use the following non-parametric paired bootstrap test:

1. **Resamples**: Exactly $B = 2,000$ bootstrap iterations.
2. **Random Seed**: Fixed pseudo-random seed `seed=42`.
3. **Paired Difference**: For resample $b \in \{1, \dots, B\}$, draw $N$ instances with replacement from the paired evaluation sample $\{(e_{1,i}, e_{2,i})\}_{i=1}^N$.
   $$\Delta^{(b)} = \frac{1}{N} \sum_{j \in \text{sample}_b} e_{1,j} - \frac{1}{N} \sum_{j \in \text{sample}_b} e_{2,j}$$
4. **Confidence Interval**: The two-sided $95\%$ bootstrap confidence interval is defined by the 2.5th and 97.5th percentiles of $\{\Delta^{(b)}\}_{b=1}^B$:
   $$\text{CI}_{95\%} = \left[ \Delta_{(0.025)}, \Delta_{(0.975)} \right]$$
5. **Strict Evidence Rule**:
   - Language such as *"wins"*, *"beats"*, *"improves"*, or *"statistically significant"* is strictly forbidden unless the $95\%$ confidence interval excludes zero.
   - If the interval spans zero (e.g., $[-0.5\%, +0.4\%]$), the report must plainly conclude **"no demonstrated difference"**.

---

## 3. Permissible Features & Anti-Leakage Constraints

### A. Pre-Listing Timing Rule
Every feature value must be strictly knowable and published **before 9:00 AM IST on the listing date**:
- **GMP**: Captured on the final bidding day (`close_date`) or pre-listing evening from active dealer sheets.
- **Subscription Demand**: Category-wise final subscription figures as confirmed by the registrar post-allotment.
- **Macro / Market**: Closing Nifty 50 30-day return as of issue open date; closing India VIX on `close_date`.

### B. Feature List
- **Categoricals**: `sector` (refined 18-class taxonomy), `exchange` (`NSE`, `BSE`, `BOTH`).
- **Issue Sizing & Structure**: `issue_price`, `issue_size_cr`, `fresh_issue_pct`, `ofs_pct`, `lot_size`, `log_issue_size`.
- **Demand Multiples**: `sub_qib`, `sub_nii`, `sub_retail`, `sub_total`, `log_sub_total`, `log_sub_qib`, `log_sub_nii`, `log_sub_retail`, `sub_retail_vs_qib`, `sub_hni_vs_retail`, `qib_demand_share`.
- **Market Sentiment & Context**: `gmp_pct`, `gmp_vs_recent_avg`, `gmp_x_sub`, `nifty_30d_return`, `india_vix`, `is_high_vix`, `recent_ipo_avg_gain`.
- **Fundamental Features**: `roe`, `roce`, `revenue_growth_pct`, `pat_margin_pct`, `debt_equity`, `pe_ratio`, `peer_median_pe`, `pe_vs_peer`.

### C. Fundamentals Admission Threshold
A fundamental metric column is permitted into the modeling matrix **if and only if**:
1. Coverage over the 2021–2026 era is $\ge 70\%$.
2. Verified spot-check accuracy against secondary statutory sources is $\ge 95\%$ (within a $2\%$ relative tolerance).
Any column failing either threshold is **strictly excluded** from feature matrices, and hypothesis H1 for that metric will be marked "not tested". Imputation or fabrication of missing fundamentals is forbidden.

---

## 4. Probability Calibration Specification

- **Algorithm**: Platt Scaling (Sigmoid Calibration via Logistic Regression on raw logits $\text{logit}(\hat{p}) = \ln(\hat{p}/(1-\hat{p}))$).
- **Fitting Partition**: Fitted exclusively on out-of-fold training windows in walk-forward evaluation.
- **Evaluation Partition**: Calibration metrics ($ECE_{\text{quantile}}$, $ECE_{\text{uniform}}$, Brier score) are measured exclusively on out-of-sample evaluation folds.

---

## 5. Blend Weight Selection Rule

For issues with active dealer GMP quotes:
- $\hat{y}_{\text{blend}} = w \cdot \text{GMP} + (1 - w) \cdot \hat{y}_{\text{model}}$.
- The optimal weight $w \in [0.0, 1.0]$ (searched in increments of $0.05$) is determined exclusively on training/validation partitions by minimizing MAE.
- The weight is never optimized or selected using final test partition data.

---

## 6. Pre-Registered Decision Rules (Success Criteria)

| Research Question | Metric | Success / Rejection Criterion |
|---|---|---|
| **Gate A Remediation** | Audit Checklist (R1–R8) | All defects resolved or documented as NOT FIXED. |
| **Fundamentals Coverage** | % populated (2021–2026) | Target $\ge 70\%$ per column to enter model; else excluded. |
| **Fundamentals Accuracy** | 40-row spot check | Target $\ge 95\%$ match within 2% relative tolerance. |
| **H1: Fundamentals Help** | Rolling-Origin MAE & AUC | Conclude "helps" only if paired bootstrap interval $\Delta(\text{with} - \text{without})$ excludes zero. |
| **Model vs Historical Mean** | Rolling-Origin MAE | Conclude model adds value only if bootstrap interval excludes zero. |
| **Model / Blend vs Raw GMP** | MAE on GMP subset | Conclude "beats GMP" only if bootstrap interval excludes zero; else recommend raw GMP. |
| **Probability Calibration** | Out-of-sample ECE | Target $ECE_{\text{quantile}} \le 0.10$ and $ECE_{\text{uniform}} \le 0.10$ on unseen data. |
| **Tail Behaviour** | MAE on top 10% gains | Reported transparently; no arbitrary threshold. |
| **Forward Test Integrity** | Forward log ($n$) | No performance claims permissible below $n = 30$ ("n too small"). |
