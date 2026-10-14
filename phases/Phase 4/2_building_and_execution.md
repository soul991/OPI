# Phase 4: Building & Execution - Technical Implementation Log

> Standard sequential phase documentation per `RULES.md`.
> **Phase 4 Focus**: Strict Three-Way Chronological Split, Probability Calibration (Platt Sigmoid), Sector Taxonomy Decomposition, Fundamentals Audit, GMP Blending Optimization, and Append-Only Forward Prediction Logging.

---

## 1. Pipeline Architecture & Data Flow

The Phase 4 architecture enforces strict evaluation hygiene to eliminate data leakage and over-confidence:

```
[ Raw Scraped Sources ]
  ├── NSE/BSE Exchange Archives (2010–2020)
  ├── Moneycontrol Mainline Verified Prices (2020–2026)
  └── Bansal Academic IPO Dataset (2019–2026)
            │
            ▼
[ scripts/phase4_fix_sectors.py ]
  └── Decomposes 33% "Industrial & Manufacturing" catch-all into 8 specific industries
            │
            ▼
[ data/ipo_master.csv ] (749 Mainboard IPOs, 2010-01-04 to 2026-10-08)
            │
            ├──────────────────────────┬──────────────────────────┐
            ▼                          ▼                          ▼
   [ data/ipo_train.csv ]     [ data/ipo_val.csv ]     [ data/ipo_final_test.csv ]
      556 IPOs (74.2%)          118 IPOs (15.8%)             75 IPOs (10.0%)
   (< 2025-06-01 Listings)    (2025-06-01 to 2026-05-31)    (>= 2026-06-01 Listings)
            │                          │                          │
            ▼                          │                          │
   Model Retraining &                  ▼                          │
   Feature Engineering ────────► Hyperparameter Tuning            │
                               & Platt Calibration                │
                               & GMP Blend Optimization           │
                                       │                          │
                                       └──────────────────────────┼───────────────┐
                                                                  ▼               ▼
                                                        [ One-Time Test ]   [ Production Model ]
                                                        Evaluated EXACTLY   model/ipo_model_phase4.joblib
                                                        once on frozen 75   (PlattCalibrator + Regressor)
                                                        unseen IPOs                       │
                                                                                          ▼
                                                                                [ scripts/log_prediction.py ]
                                                                                Append-only forward logging
                                                                                into predictions/prediction_log.csv
```

---

## 2. Scripts Created / Modified

| File Path | Purpose | Key Parameters / Logic |
|---|---|---|
| [`scripts/phase4_split.py`](../../scripts/phase4_split.py) | Three-way chronological partitioning | Train (< 2025-06-01; 556 rows), Val (2025-06-01 to 2026-05-31; 118 rows), Final Test (>= 2026-06-01; 75 rows). Scores Phase 2 model on final test for reference baseline. |
| [`scripts/phase4_fix_sectors.py`](../../scripts/phase4_fix_sectors.py) | Sector taxonomy refinement & gap analysis | Reclassifies 109 companies out of 247 "Industrial & Manufacturing" catch-all into 8 granular sectors. Audits 2012-2014 exchange records. |
| [`scripts/phase4_fill_fundamentals.py`](../../scripts/phase4_fill_fundamentals.py) | Fundamentals coverage & spot-check | Audits 7 fundamental metrics across 479 IPOs (2021–2026). Excludes 4 metrics with 0% coverage. Conducts 30-IPO spot check (`random_state=42`) with 96.67% pass rate. |
| [`scripts/phase4_train_evaluate.py`](../../scripts/phase4_train_evaluate.py) | Full Phase 4 training, calibration, and evaluation pipeline | 81-combination grid search on validation; Platt scaling logistic calibrator; 4-way GMP comparison; one-time evaluation on frozen test set. |
| [`model/train.py`](../../model/train.py) | Shared feature engineering & model definitions | Added `PlattCalibrator` wrapper class enabling seamless serialization and forward calibrated probability inference. |
| [`scripts/log_prediction.py`](../../scripts/log_prediction.py) | Append-only forward prediction scoring | Scores upcoming unlisted IPOs using `model/ipo_model_phase4.joblib`, serializes feature snapshots in JSON, and appends to `predictions/prediction_log.csv` with `actual_gain_pct=""`. |
| [`scripts/update_actuals.py`](../../scripts/update_actuals.py) | Post-listing return reconciliation | Matches passed listing dates against `data/ipo_master.csv` and updates `actual_gain_pct` without mutating historical prediction records. |

---

## 3. Data Purification & Engineering Steps

### A. Sector Taxonomy Decomposition
Prior to Phase 4, `Industrial & Manufacturing` was a catch-all encompassing 247 out of 749 IPOs (33.0%). By running `scripts/phase4_fix_sectors.py`, 109 companies (44.1%) were remapped:
1. **Engineering & Capital Goods** (+46 companies): e.g., Waaree Energies, Premier Energies, Inox India, Sansera Engineering.
2. **Media & Entertainment** (+16 companies): e.g., Shemaroo, Nazara, D B Corp, UFO Moviez.
3. **Textiles & Apparel** (+13 companies): e.g., Campus Activewear, Metro Brands, Khadim, TCNS Clothing.
4. **Packaging** (+9 companies): e.g., Cello World, All Time Plastics, Astron Paper Board.
5. **Education & Training** (+8 companies): e.g., Physicswallah, Veranda Learning, CL Educate, S Chand.
6. **Defense & Aerospace** (+6 companies): e.g., Hindustan Aeronautics (HAL), Bharat Dynamics, Paras Defence, Midhani.
7. **Agriculture** (+6 companies): e.g., Aeroplane Basmati Rice, Sanstar, Mukka Proteins.
8. **Diversified / Conglomerate** (+5 companies): e.g., Adani Enterprises, Adani Wilmar, Future Ventures.
- **Resulting Industrial & Manufacturing Share**: Decreased from **33.0% down to 18.4%** (138 rows).

### B. Historical 2012–2014 Volume Reconciliation
An audit of BSE/NSE exchange archives confirmed that the low volumes in 2012 (11 IPOs), 2013 (3 IPOs), and 2014 (5 IPOs) reflect an authentic macroeconomic "IPO drought" post-Eurozone sovereign debt crisis and pre-2014 general election, rather than missing data. (100% concordance with SEBI annual reports).

### C. Fundamentals Audit & Dropped Columns
Evaluation across 479 IPOs listed between 2021 and 2026:
- `roe`: 0 / 479 (0.0% coverage) ➔ **Formally Excluded** (Failed >= 70% threshold).
- `roce`: 0 / 479 (0.0% coverage) ➔ **Formally Excluded** (Failed >= 70% threshold).
- `revenue_growth_pct`: 0 / 479 (0.0% coverage) ➔ **Formally Excluded** (Failed >= 70% threshold).
- `pat_margin_pct`: 0 / 479 (0.0% coverage) ➔ **Formally Excluded** (Failed >= 70% threshold).
- `pe_ratio`: 294 / 479 (61.38% coverage) ➔ **Retained** with native NaN gradient boosting.
- `peer_median_pe`: 299 / 479 (62.42% coverage) ➔ **Retained** with native NaN gradient boosting.
- `debt_equity`: 298 / 479 (62.21% coverage) ➔ **Retained** with native NaN gradient boosting.

### D. Spot-Check Verification
A 30-IPO random sample (`random_state=42`) verified values against plausible domain bounds:
- **Pass Rate**: **29 / 30 (96.67%)** (Exceeds >= 95% threshold).
- **Flagged Outlier**: `Amagi Media Labs` (`pe_ratio` = 603.43, `debt_equity` = 200.0) logged to `phases/Phase 4/data_corrections.csv`.

---

## 4. Hyperparameter Tuning & Optimal Parameters

A grid search over 81 configurations was executed on `data/ipo_train.csv` (556 IPOs) and scored strictly on `data/ipo_val.csv` (118 IPOs):

### Regressor (`HistGradientBoostingRegressor`)
- `loss`: `"absolute_error"` (L1 median regression)
- `max_depth`: `3` (Constrained to prevent overfitting to listing pops)
- `learning_rate`: `0.05`
- `max_iter`: `400`
- `min_samples_leaf`: `10`
- `l2_regularization`: `0.1`
- **Validation MAE**: **7.16%** (vs Train Mean Baseline of **17.35%**)

### Classifier (`HistGradientBoostingClassifier` + `PlattCalibrator`)
- `max_depth`: `4`
- `learning_rate`: `0.03`
- `max_iter`: `500`
- `min_samples_leaf`: `20`
- `l2_regularization`: `0.5`
- **Validation ROC-AUC**: **0.873**

---

## 5. Exact Terminal Commands Executed

To completely reproduce Phase 4 from scratch:

```bash
# 1. Generate 3-way chronological split
python3 scripts/phase4_split.py

# 2. Refine sector taxonomy and log 2012-2014 audit
python3 scripts/phase4_fix_sectors.py

# 3. Execute fundamentals coverage analysis and 30-IPO spot check
python3 scripts/phase4_fill_fundamentals.py

# 4. Train tuned model, perform Platt calibration, optimize GMP blend, and evaluate final test
python3 scripts/phase4_train_evaluate.py

# 5. Score upcoming unlisted IPO (Hyundai Motor India) and append to forward prediction log
python3 scripts/log_prediction.py new_ipo.csv

# 6. Verify forward log reconciliation script
python3 scripts/update_actuals.py
```

---

## 6. Artifacts & Generated Data Files

| Artifact File | Description | Location |
|---|---|---|
| `model/ipo_model_phase4.joblib` | Production model bundle containing regressor, classifier, Platt calibrator, categories, and blend weights | [`model/ipo_model_phase4.joblib`](../../model/ipo_model_phase4.joblib) |
| `data/ipo_train.csv` | Train split (< 2025-06-01, 556 rows) | [`data/ipo_train.csv`](../../data/ipo_train.csv) |
| `data/ipo_val.csv` | Validation split (2025-06-01 to 2026-05-31, 118 rows) | [`data/ipo_val.csv`](../../data/ipo_val.csv) |
| `data/ipo_final_test.csv` | Frozen final test split (>= 2026-06-01, 75 rows) | [`data/ipo_phase4_test_used.csv`](../../data/ipo_phase4_test_used.csv) |
| `phases/Phase 4/final_test_results.csv` | Complete company-by-company test set predictions, actuals, and errors | [`phases/Phase 4/final_test_results.csv`](final_test_results.csv) |
| `phases/Phase 4/fundamentals_coverage.csv` | Column-by-column coverage report for 2021–2026 listings | [`phases/Phase 4/fundamentals_coverage.csv`](fundamentals_coverage.csv) |
| `phases/Phase 4/data_corrections.csv` | Log of data corrections and outlier flags | [`phases/Phase 4/data_corrections.csv`](data_corrections.csv) |
| `phases/Phase 4/gap_analysis_2012_2014.md` | Verification report for 2012–2014 low-volume era | [`phases/Phase 4/gap_analysis_2012_2014.md`](gap_analysis_2012_2014.md) |
| `phases/Phase 4/phase4_summary.json` | Machine-readable metrics summary | [`phases/Phase 4/phase4_summary.json`](phase4_summary.json) |
| `predictions/prediction_log.csv` | Append-only forward prediction log | [`predictions/prediction_log.csv`](../../predictions/prediction_log.csv) |
