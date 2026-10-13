# Phase 2: Building & Execution Log

## 1. Pipeline Architecture & Data Flow

```
[Raw Sources Download]
 ├── Moneycontrol API (406 Mainline, 2020-2026)
 ├── Samip BSE/NSE Archives (1,025 listings, 2006-2020)
 ├── Bansal Thesis & GMP Data (416 listings + 418 GMP rows)
 └── Yahoo Finance (^NSEI, ^INDIAVIX historical daily data)
             │
             ▼
[Purification & Consolidation: scripts/build_clean_master.py]
 ├── Precedence: Verified Exchange Open > Day Close
 ├── Sector Standardisation: URL/Name classification into 11 sectors
 ├── Deduplication: (listing_date, issue_price) with completeness scoring
 ├── Date Alignment: open_date <= close_date <= listing_date
 └── Rolling Features: Trailing 30d Nifty return & 5-IPO rolling listing gain
             │
             ▼
[Validated Dataset: data/ipo_master.csv (749 rows)]
             │
             ├─── 80% Train Partition (599 IPOs) ───► model/train.py
             │                                              │
             │                                        model/ipo_model.joblib
             │                                              │
             └─── 20% Holdout Partition (150 IPOs) ──► model/evaluate_holdout.py
                                                            │
                                              data/holdout_comparison_report.csv
```

---

## 2. Scripts Created & Modified

### `scripts/download_all_raw_data.py` [NEW]
- Programmatically downloads raw primary datasets:
  - `data/raw/moneycontrol_all.csv`: Full JSON query pagination from `api.moneycontrol.com/mcapi/v1/ipo/get-listed-ipo`.
  - `data/raw/samip_indian_ipo_data.csv`: Historical BSE/NSE archives.
  - `data/raw/bansal_*.csv`: Detailed fundamentals, QIB/NII/Retail breakdown, and grey market premiums.

### `scripts/fetch_market_data.py` [NEW]
- Downloads full historical time series for `^NSEI` and `^INDIAVIX` from 2009 to current date.
- Computes daily 30-calendar-day trailing returns for instant O(1) alignment during data processing.

### `scripts/build_clean_master.py` [NEW]
- Merges, standardizes, and validates all listings.
- Strictly resolves the "Opening Price vs Day Close" conflict by enforcing verified open prices from Moneycontrol (`dt_open`) and BSE/NSE records (`NSE_Listing_day_open`).
- Standardizes company names (removes informal "ipo" and corporate legal suffixes).
- Calculates `nifty_30d_return`, `india_vix`, `recent_ipo_avg_gain`, `listing_gain_pct`, and `label_good`.

### `model/train.py` [OPTIMIZED]
- Updated with:
  - Robust L1 loss (`loss="absolute_error"`) for `HistGradientBoostingRegressor`.
  - Log-transformed subscription multiples: `log_sub_total`, `log_sub_qib`, `log_sub_nii`, `log_sub_retail`.
  - Interactive demand features: `qib_demand_share`, `gmp_x_sub`.
  - Regularized `HistGradientBoostingClassifier` (`l2_regularization=0.5`, `min_samples_leaf=15`).

---

## 3. Reproduction Commands

To replicate this entire pipeline from scratch:

```bash
# 1. Download raw market index data (Nifty 50 and India VIX)
python3 scripts/fetch_market_data.py

# 2. Download all raw IPO datasets from authoritative sources
python3 scripts/download_all_raw_data.py

# 3. Consolidate, deduplicate, and purify master dataset
python3 scripts/build_clean_master.py

# 4. Verify dataset passes schema rules
python3 skills/ipo-data-collector/scripts/validate_dataset.py data/ipo_master.csv

# 5. Train model on strictly partitioned chronological training set
python3 model/train.py data/ipo_master.csv

# 6. Evaluate strictly on unseen holdout partition
python3 model/evaluate_holdout.py
```
