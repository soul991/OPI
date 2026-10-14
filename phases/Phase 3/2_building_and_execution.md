# Phase 3: Building & Execution Log

## 1. Multi-Dataset Pipeline Architecture

To prevent data leakage across distinct experimental partitions, the pipeline isolates historical data chronologically:

```
                      Master Dataset: data/ipo_master.csv (749 Rows)
                                            │
       ┌────────────────────────────────────┼────────────────────────────────────┐
       ▼                                    ▼                                    ▼
[Part A: Landmark Backtests]       [Part B: Paytm Scenarios]           [Part C: Regime Partitions]
 10 Distinct Retrained Models       Dedicated Pre-2021 Model            4 Distinct Historical Models
 Train: listing_date < target       Train: listing_date < 2021-11-18    Era 1 (2010-2019): N=254
 Dynamic column variance filter     3 Scenarios (GMP / Raw / Hype)      Era 2 (2020-2021): N=79
 Regressor & Classifier Fit         Out-of-sample evaluation            Era 3 (2022-2023): N=110
       │                                    │                           Era 4 (2024-2026): N=306
       ▼                                    ▼                                    │
historical_10_backtest.csv          paytm_scenario_eval.csv                      ▼
                                                                       regime_partition_metrics.csv
                                            │
                                            ▼
                           [Part D: Interactive Generative UI]
                           historical_10_backtest_chart.html
```

---

## 2. Engineering Challenges & Technical Solutions

### Handling Low Feature Variance on Historical Subsets
- **Problem**: When slicing the dataset prior to earlier years (e.g., 2015 for Adlabs or 2017 for D-Mart), financial metrics like `debt_equity`, `peer_median_pe`, or `pe_ratio` had fewer than 2 distinct non-NaN values in the training subset.
- This triggered an internal Scikit-Learn binning exception:
  `ValueError: window shape cannot be larger than input array shape`.
- **Solution**: Implemented dynamic feature column validation prior to model fitting:
  ```python
  valid_cols = [c for c in Xtr.columns if len(Xtr[c].dropna().unique()) >= 2]
  Xtr = Xtr[valid_cols]
  ```
  This allowed models trained on smaller historical partitions (e.g. 126 rows for Adlabs in 2015) to train cleanly without dropping rows.

### Dynamic Category Index Mapping
- Categorical features (`sector`, `exchange`) were dynamically re-indexed against `valid_cols` so `categorical_features` arguments to `HistGradientBoosting` remained aligned regardless of which numerical features were pruned.

---

## 3. Scripts Created & Outputs Saved

### 1. `phases/Phase 3/run_phase_3.py` [NEW]
Main orchestrator script executing Parts A, B, and C, and copying the interactive chart into the phase outputs directory.

### 2. `scripts/backtest_10_historical_ipos.py` [NEW]
Automated script running the 10 landmark out-of-sample evaluations, calculating directional accuracy, and exporting console metrics.

### 3. `scripts/backtest_paytm.py` [NEW]
Dedicated standalone backtester for Paytm's November 2021 listing, isolating pre-listing data and testing multiple pre-IPO feature hypotheses.

### 4. Output Artifacts in `phases/Phase 3/outputs/`:
- [`historical_10_backtest.csv`](outputs/historical_10_backtest.csv): Full table of predicted gains, probabilities, actual gains, errors, and signals for the 10 landmark IPOs.
- [`paytm_scenario_eval.csv`](outputs/paytm_scenario_eval.csv): Comparison of Paytm predictions across pre-listing data states.
- [`regime_partition_metrics.csv`](outputs/regime_partition_metrics.csv): Cross-era benchmark statistics and within-regime model validation metrics.
- [`historical_10_backtest_chart.html`](outputs/historical_10_backtest_chart.html): Standalone Generative UI comparative visualization widget.

---

## 4. Reproduction Commands

To reproduce the entire Phase 3 multi-dataset training experiment:

```bash
# Run complete Phase 3 pipeline
python3 "phases/Phase 3/run_phase_3.py"

# Or run individual backtests:
python3 scripts/backtest_10_historical_ipos.py
python3 scripts/backtest_paytm.py
```
