# India IPO Listing-Gain Predictor (OPI)

A machine learning framework to estimate listing-day returns and success probabilities for Indian Mainboard Initial Public Offerings (NSE/BSE), benchmarked against the Grey Market Premium (GMP).

---

## Key Features
- **Extensive Historical Dataset**: 828 purified Indian Mainboard IPO records from 2006 to 2026.
- **Strict Out-of-Sample Holdout Protocol**: Chronological 80/20 train-test partition (662 train IPOs, 166 unseen holdout IPOs).
- **Baseline Beating**: Outperforms naive Mean baseline (MAE $15.05\%$ vs $19.62\%$) and naive GMP baseline ($15.05\%$ vs $17.29\%$).
- **Dual Inference Engine**:
  - Continuous Listing Day Gain (%) Prediction (`HistGradientBoostingRegressor`).
  - Probability of Listing Pop $> 10\%$ (`HistGradientBoostingClassifier`, ROC-AUC $0.856$, Accuracy $80.7\%$).
- **Anti-Leakage Design**: Every feature is knowable prior to listing morning (final bidding day GMP, 30-day prior Nifty return, close-date India VIX).
- **Mandatory Phase Reporting**: Standardized sequential AI phase reporting protocol (`Phase 1`, `Phase 2`, ...).

---

## Project Structure
```
OPI/
├── RULES.md                        # Mandatory agent rules for phase reporting
├── README.md                       # Project overview and quickstart guide
├── requirements.txt                # Python dependencies
├── new_ipo.csv                     # Single-row template to score an upcoming IPO
│
├── data/
│   ├── ipo_master.csv              # Full purified dataset (828 records, 2006-2026)
│   ├── ipo_train.csv               # Training partition (662 records, 2006 to Sep 2024)
│   ├── ipo_holdout_test.csv        # Out-of-sample holdout test set (166 records, Sep 2024 to May 2026)
│   └── holdout_comparison_report.csv# Detailed model vs actual vs GMP comparison
│
├── model/
│   ├── train.py                    # Trains model strictly on ipo_train.csv
│   ├── evaluate_holdout.py         # Evaluates model against ipo_holdout_test.csv
│   ├── predict.py                  # Scores new upcoming IPOs
│   └── ipo_model.joblib            # Trained production model artifact
│
├── phases/
│   └── Phase 1/                    # Phase 1 Documentation (Base Model)
│       ├── 1_planning_and_goals.md # Phase 1 Objectives & Hypotheses
│       ├── 2_building_and_execution.md # Data pipeline, scripts & executed commands
│       └── 3_outcome_and_verdict.md# Holdout performance, GMP comparison & review
│
├── Phase 1/                        # Root mirror of Phase 1
│   ├── 1_planning_and_goals.md
│   ├── 2_building_and_execution.md
│   └── 3_outcome_and_verdict.md
│
└── skills/                         # Antigravity agent skills
    ├── ipo-data-collector/         # Ingestion, enrichment & schema validation
    └── ipo-research-analyst/       # Multi-LLM consensus research on new IPOs
```

---

## Quickstart & Commands

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Data Collection & Enrichment
```bash
python3 skills/ipo-data-collector/scripts/collect_and_enrich.py
python3 skills/ipo-data-collector/scripts/validate_dataset.py data/ipo_master.csv
```

### 3. Model Training (80/20 Chronological Split)
```bash
python3 model/train.py data/ipo_master.csv
```

### 4. Holdout Evaluation vs Actual Outcomes
```bash
python3 model/evaluate_holdout.py data/ipo_holdout_test.csv
```

### 5. Predict Listing Gain for an Upcoming IPO
```bash
python3 model/predict.py new_ipo.csv
```

### 6. Phase 4: Honest Testing, Calibration & Forward Prediction Pipeline
```bash
# 1. Chronological 3-way split (Train < Jun 2025, Val Jun 2025 - May 2026, Frozen Test >= Jun 2026)
python3 scripts/phase4_split.py

# 2. Sector taxonomy refinement (splits Industrial & Manufacturing catch-all into 8 specific categories)
python3 scripts/phase4_fix_sectors.py

# 3. Fundamentals coverage audit and 30-row spot-check
python3 scripts/phase4_fill_fundamentals.py

# 4. Phase 4 full training, Platt calibration, GMP comparison & frozen test evaluation
python3 scripts/phase4_train_evaluate.py

# 5. Log forward predictions for upcoming IPOs (append-only)
python3 scripts/log_prediction.py new_ipo.csv

# 6. Reconcile actual listing day returns post-listing
python3 scripts/update_actuals.py
```

---

## Data Sources and Licensing

This project utilizes historical IPO data, grey market premium (GMP) records, and index data sourced from:
- **National Stock Exchange of India (NSE) & Bombay Stock Exchange (BSE)**: Historical listing open prices, issue prices, and category-wise subscription bids.
- **Moneycontrol & Chittorgarh**: Mainline IPO prospectus details, anchor book details, and daily dealer GMP tracking.
- **Samip BSE/NSE Archive**: Historical 2010–2020 Mainboard public issue dataset.
- **Yahoo Finance (`yfinance`)**: Historical Nifty 50 and India VIX daily closing series.

**Licensing & Redistribution Note**:
Due to third-party website terms of use (Moneycontrol, Chittorgarh), raw scraped files residing in `data/raw/` are excluded from version control (`.gitignore`). Anyone cloning this repository can reconstitute the full master dataset deterministically by running:
```bash
python3 scripts/download_all_raw_data.py
python3 scripts/build_clean_master.py
```
Purified and standardized feature matrices (`data/ipo_master.csv`, `data/ipo_train.csv`, `data/ipo_val.csv`, `data/ipo_final_test.csv`) are provided under the project's educational and non-commercial research license.

---

## AI Agent Rules & Phase Reporting
Any AI agent modifying or retraining models in this repository must comply with [`RULES.md`](RULES.md). All major training iterations must create sequential phase directories (`phases/Phase 1/`, `phases/Phase 2/`, ...) with:
1. `1_planning_and_goals.md`
2. `2_building_and_execution.md`
3. `3_outcome_and_verdict.md`
