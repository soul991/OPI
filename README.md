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

---

## AI Agent Rules & Phase Reporting
Any AI agent modifying or retraining models in this repository must comply with [`RULES.md`](file:///Users/istakahamed06/Documents/OPI/RULES.md). All major training iterations must create sequential phase directories (`phases/Phase 1/`, `phases/Phase 2/`, ...) with:
1. `1_planning_and_goals.md`
2. `2_building_and_execution.md`
3. `3_outcome_and_verdict.md`
