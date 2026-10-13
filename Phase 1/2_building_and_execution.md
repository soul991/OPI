# Phase 1: Building and Execution Process

## 1. Pipeline Overview & Data Flow
Phase 1 constructed an automated, end-to-end data ingestion, purification, training, and holdout evaluation pipeline:

```
[Raw Sources: 2006-2026] 
   │
   ▼
skills/ipo-data-collector/scripts/collect_and_enrich.py
   ├── Filters Mainboard (NSE/BSE) & excludes SME/FPO
   ├── Harmonizes column types & fixes historical typos
   ├── Downloads ^NSEI (Nifty 50) & ^INDIAVIX from Yahoo Finance
   └── Computes rolling 5-IPO sentiment: recent_ipo_avg_gain
   │
   ▼
data/ipo_master.csv (828 Purified Rows)
   │
   ▼
skills/ipo-data-collector/scripts/validate_dataset.py (Integrity Checks Passed)
   │
   ▼
model/train.py
   ├── Chronological Split: 80% Train (662) / 20% Holdout (166)
   ├── Saves: data/ipo_train.csv & data/ipo_holdout_test.csv
   ├── Engineers Domain Ratios: pe_vs_peer, sub_retail_vs_qib, sub_hni_vs_retail
   ├── Fits HistGradientBoosting Regressor & Classifier ONLY on Train Set
   └── Saves: model/ipo_model.joblib
   │
   ▼
model/evaluate_holdout.py
   ├── Loads model & evaluates against 166 unseen holdout IPOs
   ├── Compares prediction vs actual listing gain and GMP
   └── Saves: data/holdout_comparison_report.csv
```

---

## 2. Ingestion & Data Purification Details

### A. Aggregation of Multiple Historical Sources
- **2006 – 2020**: Ingested 474 mainboard records from the `samip9898/Data-Analysis-of-Indian-stock-market-IPOs` archive.
- **2021**: Ingested 52 records from `shubhankar-rai/indian-stock-ipo-data-analysis` plus 11 late-2021 records from `saqibsafdar11/Predicting-Listing-Gains-in-the-Indian-IPO-Market`.
- **2022 – 2026**: Ingested 312 modern mainboard records from `abhnxvj/ipo-listing-gain-predictor`.
- **Deduplication**: Companies deduplicated on `(company, listing_date)` prioritizing rows with the lowest missing-value counts, resulting in **828 distinct mainboard IPOs**.

### B. Cleaning Heuristics & Specific Corrections
1. **SME vs Mainboard Separation**: Screened out all SME board listings where `NSE_SME_Listing_day_open` or `BSE_SME_Listing_day_open` was populated.
2. **Outlier Correction on Bids vs Multiples**: Fixed row 857 (`HDFC Asset Management Company Limited`) where raw bid share count ($18,804,290$) was recorded instead of subscription multiple ($83.05\times$).
3. **Date Discrepancy Correction**: Corrected `20 Microns Limited` listing date typo (`2008-09-06` to `2008-10-06`) where listing day had been mistyped prior to issue close.
4. **Issue Size Normalization**: Applied regex parsing to extract clean INR Crore amounts from string descriptions (`aggregating up to ₹3,018.00 Cr`).
5. **Sector Categorization**: Implemented a keyword rule classifier mapping companies into 11 canonical industry sectors (*IT & Technology*, *Healthcare & Pharma*, *Financial Services*, *Consumer & Retail*, *Energy & Power*, etc.).

---

## 3. Market Context Integration (Yahoo Finance)
Using `yfinance`, 4,678 days of daily trading history from 2007 to 2026 were indexed:
- **`nifty_30d_return`**: Looked up Nifty 50 close at `open_date` vs `open_date - 30 days`:
  $$\text{Nifty 30d Return} = \frac{\text{Close}_{\text{open}} - \text{Close}_{-30d}}{\text{Close}_{-30d}} \times 100$$
- **`india_vix`**: Looked up closing volatility index on `close_date`.
- **`recent_ipo_avg_gain`**: Computed rolling mean listing gain of the 5 prior listed mainboard IPOs before each issue open date.

---

## 4. Model Architecture & Training Protocol

In [`model/train.py`](file:///Users/istakahamed06/Documents/OPI/model/train.py):
- **Algorithm**: `HistGradientBoostingRegressor` and `HistGradientBoostingClassifier` with `max_depth=4`, `learning_rate=0.03`, `max_iter=300`.
- **Categorical Handling**: Native histogram categorical splitting on `sector` and `exchange`.
- **Domain Ratios Engineered**:
  - $\text{pe\_vs\_peer} = \frac{\text{pe\_ratio}}{\text{peer\_median\_pe}}$
  - $\text{sub\_retail\_vs\_qib} = \frac{\text{sub\_retail}}{\text{sub\_qib}}$
  - $\text{sub\_hni\_vs\_retail} = \frac{\text{sub\_nii}}{\text{sub\_retail}}$
  - $\text{log\_issue\_size} = \ln(1 + \text{issue\_size\_cr})$
  - $\text{gmp\_vs\_recent\_avg} = \text{gmp\_pct} - \text{recent\_ipo\_avg\_gain}$
- **Train vs Holdout Split**: 
  - Train: 662 IPOs (2006 to Sept 3, 2024).
  - Holdout: 166 IPOs (Sept 4, 2024 to May 8, 2026).
  - **No refit on full data**: Model is saved strictly on the training partition.

---

## 5. Execution Steps & Reproducibility Commands

To completely reproduce the Phase 1 pipeline from scratch:

```bash
# Step 1: Install required dependencies
pip install -r requirements.txt

# Step 2: Run data collection and enrichment
python3 skills/ipo-data-collector/scripts/collect_and_enrich.py

# Step 3: Verify dataset schema integrity
python3 skills/ipo-data-collector/scripts/validate_dataset.py data/ipo_master.csv

# Step 4: Train the model and establish the holdout split
python3 model/train.py data/ipo_master.csv

# Step 5: Evaluate predictions against actual outcomes on the unseen holdout set
python3 model/evaluate_holdout.py data/ipo_holdout_test.csv

# Step 6: Test scoring a new upcoming IPO
python3 model/predict.py new_ipo.csv
```
