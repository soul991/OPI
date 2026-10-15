# India IPO Listing-Gain Predictor (OPI)

A machine learning framework to evaluate listing-day returns and success probabilities for Indian Mainboard Initial Public Offerings (NSE/BSE), benchmarked rigorously against the Grey Market Premium (GMP).

---

## What the Evidence Shows (Phase 7 Walk-Forward Re-evaluation)

The model was evaluated using a strict expanding walk-forward protocol across 20 quarters (2022Q1 to 2026Q4) on 398 matched, out-of-sample Mainboard IPOs. All statistical comparisons use paired bootstrap 95% confidence intervals (2,000 resamples, fixed seed = 42).

### 1. Where the Model Helps
- **Versus Historical Mean Baseline**: When evaluating purely pre-market public issue features (subscription, issue size, valuation, market momentum) without GMP, the Model achieves an MAE of 15.63%, beating the expanding mean baseline (19.88%) by **-4.25% MAE (95% CI: [-5.98%, -2.57%], excludes zero)**.
- **Classification / Directional Screening**: The calibrated classifier achieves a ROC-AUC of **0.9067** and Brier score loss of **0.1218** for predicting listing gains > 10%.
- **Fundamentals (ROE, PAT Margin, Debt/Equity)**: Incorporating pre-IPO accounting fundamentals showed **no demonstrated effect** over issue structure and subscription alone (MAE difference: +0.07%, 95% CI: [-0.19%, +0.33%], straddles zero).

### 2. Where Raw GMP is the Better Signal
- **Grey Market Dominance**: For all 398 evaluated IPOs with observed pre-listing grey market quotes, **Raw GMP is the superior point estimator**, achieving an MAE of **9.08%**.
- **Model vs. Raw GMP**: The standalone ML model incorporating GMP has higher error than Raw GMP alone (+1.83% MAE, 95% CI: [+0.22%, +3.11%]), showing **no demonstrated advantage over Raw GMP**.
- **Blend vs. Raw GMP**: An adaptive blend of Model + GMP achieves an MAE of 9.15%, demonstrating **no statistically significant difference over Raw GMP** (difference: +0.07% MAE, 95% CI: [-0.06%, +0.19%], straddles zero).
- **Practical Rule**: Whenever a dated pre-listing GMP quote is observed, **Raw GMP is the primary signal; the ML model provides contextual bounding only**.

### 3. Known Weaknesses & Failure Modes
- **Under-prediction of Tail Pops**: The model severely under-predicts extreme listing-day pops (> 50% gain). For the top 10% largest gains (actual gain >= 50.1%), empirical 80% conformal coverage collapses to **57.5% (FAIL)**.
- **Over-Conservative Conformal Intervals**: On pooled and observed issues, 80% conformal prediction intervals achieved **91.2% empirical coverage** with a mean width of 46.26 percentage points.
- **Probability Reliability Warning**: Do not treat predicted probabilities above approximately **0.85** or below approximately **0.10** as certainty. Empirical binomial Wilson intervals show wide dispersion in extreme bins.

### 4. Forward Test Status
- Genuine FORWARD predictions logged: **1** (`HD Fire Protect Limited`, listing scheduled for 2026-10-21).
- Genuine FORWARD listings completed: **0**.
- Status: **Provisional, no performance claims permitted below n = 30** (per pre-registered rules).

*Disclaimer: This system is a quantitative decision aid and research benchmark only. It does not constitute financial, investment, or trading advice.*

---

## Dataset & Structure

- **Cleaned Dataset**: 731 Mainboard IPO records (2010 to 2026) in `data/ipo_master.csv`, 100% compliant with audit rules (0 FPOs, 0 unverified duplicates, 0 date-order violations).
- **GMP Coverage**: 100% verified dated pre-listing GMP coverage for 2026Q3 (62/62) and 2026Q4 (10/10) with source URLs and last bidding day timestamps in `data/gmp_sourced.csv`.
- **Registry of Excluded Rows**: Full provenance in `data/excluded_rows.csv` and corrections log in `phases/Phase 7/data_corrections.csv`.

```
OPI/
├── RULES.md                        # Mandatory agent rules for phase reporting
├── README.md                       # Project overview and empirical evidence summary
├── requirements.txt                # Python dependencies
├── new_ipo.csv                     # Single-row template to score an upcoming IPO
│
├── data/
│   ├── ipo_master.csv              # Purified master dataset (731 records, 2010-2026)
│   ├── gmp_sourced.csv             # Dated historical GMP repository with source URLs
│   ├── excluded_rows.csv           # Registry of excluded issues (FPOs, withdrawn)
│   └── ipo_phase5_final_test.csv   # Frozen forward test log (unlisted issues post-Oct 15, 2026)
│
├── model/
│   ├── train.py                    # Training pipeline
│   ├── predict.py                  # Scores new upcoming IPOs with regime routing
│   └── ipo_model_phase4.joblib     # Production calibrated model artifact
│
├── predictions/
│   └── prediction_log.csv          # Append-only forward prediction audit trail
│
├── references/
│   ├── gmp_status_definitions.md   # Definitions of OBSERVED, NOT_RECORDED, CONFIRMED_UNAVAILABLE
│   └── inclusion_criteria.md       # Mainboard inclusion and exclusion rules
│
└── phases/
    ├── Phase 6/                    # Phase 6 purification & conformal baseline (with Phase 7 Errata)
    └── Phase 7/                    # Phase 7 GMP backfill, data verification & regime re-evaluation
        ├── 1_planning_and_goals.md
        ├── 2_building_and_execution.md
        ├── 3_outcome_and_verdict.md
        ├── preregistration.md
        ├── gmp_coverage.csv
        ├── gmp_second_source_check.csv
        ├── random_audit.csv
        ├── before_after_comparison.csv
        └── model_comparisons_bootstrap.csv
```

---

## Quickstart & Commands

### 1. Verification & Test Suite
```bash
python3 scripts/audit_dataset.py data/ipo_master.csv   # Must show 0 violations
python3 -m pytest -q                                   # Run unit test suite
python3 scripts/forward_report.py                      # Print genuine forward test status
```

### 2. Score an Upcoming IPO
```bash
python3 model/predict.py new_ipo.csv
```

Output applies the pre-registered regime routing rules:
- **GMP observed**: Uses Raw GMP as the primary expected return; model provides context and calibrated interval.
- **No GMP observed**: Uses model point estimate with regime-specific interval.
