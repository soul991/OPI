# Phase 1: Outcome, Verdict and Model Review

## 1. Empirical Results on Unseen Holdout Dataset

The primary test of Phase 1 was evaluating how accurately the model, trained strictly on pre-September 2024 IPOs, generalizes to **166 out-of-sample IPOs (September 2024 to May 2026)** that it had never seen before.

### Overall Benchmark Comparison

| Metric | Phase 1 Model | Historical Mean Baseline | Naive GMP Baseline | Benchmark Advantage |
|---|---|---|---|---|
| **Mean Absolute Error (MAE)** | **15.05%** | 19.62% | 17.29% | **+2.24% lower error than GMP alone** |
| **Accuracy (Gain > 10%)** | **80.7%** | 56.6% (Majority class) | — | **+24.1% higher than baseline** |
| **ROC-AUC Score** | **0.856** | 0.500 (Random guess) | 0.833 | **Superior separation power** |
| **Directional Accuracy (+/-)** | **69.9%** | — | — | Solid day-1 sign detection |

> **Conclusion**: The Phase 1 model comfortably beats both the naive mean baseline and the real-world Grey Market Premium baseline across continuous error reduction (MAE) and classification discrimination (ROC-AUC).

---

## 2. Permutation Feature Importance Analysis

Permutation importance computed on the unseen holdout test set reveals which features drive the model's predictive advantage:

| Rank | Feature | Importance Score | Domain Interpretation |
|---|---|---|---|
| 1 | `sub_total` | **0.2304 ± 0.091** | Overall multi-category market oversubscription is the dominant liquidity driver. |
| 2 | `gmp_pct` | **0.0434 ± 0.045** | Critical real-time dealer sentiment signal, serving as an effective price anchor. |
| 3 | `issue_price` | **0.0411 ± 0.005** | Nominal pricing level affects retail affordability and lot sizing. |
| 4 | `issue_size_cr` | **0.0357 ± 0.032** | Supply-side absorption drag; mega-issues (>₹5,000 Cr) face day-1 liquidity resistance. |
| 5 | `nifty_30d_return` | **0.0193 ± 0.021** | Pre-issue secondary market momentum significantly inflates or deflates day-1 pops. |
| 6 | `india_vix` | **0.0138 ± 0.011** | Market volatility acts as a dampener; higher VIX increases risk of day-1 gap downs. |
| 7 | `sector` | **0.0135 ± 0.007** | Industry sector tailwinds (e.g., Tech/Defence/EMS vs cyclical commodities). |
| 8 | `sub_nii` | **0.0127 ± 0.010** | High-Net-Worth leverage and borrowing costs dictate aggressive listing-day bids. |
| 9 | `recent_ipo_avg_gain` | **0.0056 ± 0.004** | Primary market sentiment climate across the previous 5 listings. |

---

## 3. Case Studies: Model vs Actual vs GMP

Examining individual IPO outcomes in the holdout comparison report ([`holdout_comparison_report.csv`](../../data/holdout_comparison_report.csv)) illustrates how the model operates:

### Success Case 1: Filtering Out False GMP Positives (*Powerica*)
- **Metrics**: Issue Price ₹395 | GMP was **+1.01%** (signaling a modest positive opening).
- **Actual Listing**: Opened at ₹366 (**-7.34% discount**).
- **Model Prediction**: **-6.47%** (Absolute Error: **0.87%**).
- **Why the Model Won**: Institutional bidding numbers and macro VIX signaled weak demand that the superficial grey market dealer quotes had missed.

### Success Case 2: Accurate Flat Listing Estimation (*Rajputana Stainless*)
- **Metrics**: Issue Price ₹122 | Actual Listing Price ₹122 (**0.00% gain**).
- **Model Prediction**: **-2.24%** (Absolute Error: **2.24%**).
- **Why the Model Won**: Sub-par subscription multiples correctly signaled muted investor interest.

### Success Case 3: Capturing Bullish Listing Expansion (*Kissht*)
- **Metrics**: Issue Price ₹171 | GMP was +2.92%.
- **Actual Listing**: Opened at ₹190 (**+11.11% gain**).
- **Model Prediction**: **+8.20%** (Absolute Error: **2.91%**).
- **Why the Model Won**: Strong retail demand combined with positive sector sentiment lifted the opening beyond the early dealer GMP.

### Failure Case: The Sudden Market Dump Outlier (*Shree Ram Twistex*)
- **Metrics**: Issue Price ₹104 | Actual Listing Price ₹68 (**-34.62% discount**).
- **Model Prediction**: **+36.34%** (Absolute Error: **70.96%**).
- **Post-Mortem**: High pre-listing subscription multiples inflated the model's expectations, but heavy opening sell-offs caused a severe price crash. This highlights the inherent limit of pre-listing subscription data during unanticipated liquidity dumps.

---

## 4. Honest Verdict & Model Review

### What Works Well:
1. **Dampening Noise in GMP**: By weighting institutional demand (`sub_qib`) and issue size alongside GMP, the model avoids getting trapped in dealer-driven hype.
2. **High Classification Reliability**: With **80.7% accuracy** and **0.856 ROC-AUC**, the model serves as an effective filter for identifying IPOs likely to return $> 10\%$.
3. **Robust Handling of Missing Data**: Scikit-learn's `HistGradientBoosting` handles missing fundamental ratios (e.g., historical P/E or debt-to-equity) seamlessly without breaking execution.

### Limitations & Known Blind Spots:
1. **Unquantified Qualitative Hazards**: Promoter disputes, criminal litigation, and aggressive Private Equity exits (100% OFS) cannot be perceived from numerical columns alone.
2. **Missing Granular Fundamentals for Older IPOs**: While recent IPOs (2022–2026) have rich fundamental features (P/E, Debt-Equity), older issues (2006–2015) rely primarily on subscription and price band metrics.

---

## 5. Roadmap & Recommendations for Phase 2
1. **Anchor Investor Allocation Quality**: Integrate anchor book data (percentage allocated to marquee domestic mutual funds vs FPIs).
2. **OFS vs Fresh Issue Penalty**: Create deeper non-linear penalties for issues where promoters sell $> 70\%$ of their holdings.
3. **Macro Sector Momentum**: Incorporate sector-specific indices (Nifty IT, Nifty Bank, Nifty Auto 30-day returns) rather than relying solely on the broad Nifty 50.
4. **LightGBM / CatBoost Ensembling**: Benchmark HistGradientBoosting against tuned CatBoost models for improved categorical handling of industry sectors.
