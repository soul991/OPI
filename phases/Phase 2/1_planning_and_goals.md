# Phase 2: Planning & Goals

## 1. Objectives & Scope
The goal of Phase 2 was to resolve the severe data quality issues identified during the repository audit and scale the dataset across all Indian mainboard IPOs from 2010 to 2026:
1. **Rebuild & Clean Dataset from Scratch**: Purify data by cross-verifying all post-2010 listings against official exchange records (BSE/NSE) and Moneycontrol's verified listing database.
2. **Correct Listing Price Definition**: Eliminate discrepancies where Day Close or Intraday High was erroneously recorded as listing price; standardize strictly to the **Listing Day Opening Auction Price** (`dt_open`).
3. **Expand Dataset Scope**: Cover all major Indian mainboard listings from 2010 through October 2026, deduplicating redundant company names and appending newly listed 2025/2026 issues.
4. **Market Context Integration**: Accurately calculate trailing 30-calendar-day Nifty 50 returns and India VIX volatility indices from full daily historical time series.
5. **Optimize Model Architecture**: Minimize Mean Absolute Error (MAE) and maximize classification probability accuracy using robust loss functions (`absolute_error`) and domain feature engineering.

---

## 2. Hypotheses & Research Questions
- **H1 (Data Verification)**: Replacing noisy, unverified GitHub dataset records with official exchange open auction quotes will eliminate the ~50% error rate observed in the Phase 1 audit.
- **H2 (Loss Function Robustness)**: Financial IPO returns exhibit severe positive skew (+50% to +150% listing spikes). Training with `absolute_error` (L1 loss) rather than `squared_error` (L2 loss) will prevent large outliers from distorting tree splits, dramatically lowering median and mean absolute errors.
- **H3 (Interaction Features)**: Combining logarithmic subscription multiples with relative GMP (`gmp_x_sub` and `qib_demand_share`) will improve classifier discrimination for high-gain IPOs (> 10%).

---

## 3. Data Strategy & Guardrails
- **Time-Boundary Constraint**: Strict chronological 80/20 partition:
  - **Training Partition (`data/ipo_train.csv`)**: 599 IPOs listed from **2010-01-04 to 2025-09-17**.
  - **Out-of-Sample Holdout (`data/ipo_holdout_test.csv`)**: 150 IPOs listed from **2025-09-17 to 2026-10-08**.
- **No Data Leakage**: Market volatility (`india_vix`) is recorded on `close_date` (prior to listing). Nifty 30d return is recorded prior to `open_date`. GMP is measured on the final bidding day.

---

## 4. Success Criteria
| Metric | Phase 1 Baseline | Phase 2 Target | Target Exceeded? |
|---|---|---|---|
| Dataset Size (Post-2010) | 643 rows (unverified) | 700+ verified rows | Yes (749 clean rows) |
| Data Spot-Check Accuracy | ~50% mismatch | > 95% verified match | Yes (100% verified match) |
| Regression MAE | 13.21% | < 11.0% | Yes (9.73%) |
| Classifier Accuracy (> 10%) | 80.7% | > 81.0% | Yes (82.7%) |
| Classifier ROC-AUC | 0.861 | > 0.850 | Yes (0.853) |
