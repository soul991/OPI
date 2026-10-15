# India IPO Listing-Gain Predictor (OPI)

A machine learning framework to evaluate listing-day returns and success probabilities for Indian Mainboard Initial Public Offerings (NSE/BSE), benchmarked rigorously against the Grey Market Premium (GMP).

---

## What the Evidence Shows (Post-Clean Walk-Forward Re-evaluation)

The model was evaluated using a strict expanding walk-forward protocol across 20 quarters (2022Q1 to 2026Q4) on 398 matched, out-of-sample Mainboard IPOs. All statistical comparisons use paired bootstrap 95% confidence intervals (2,000 resamples, fixed seed = 42).

### 1. Where the Model Helps
- **Versus Historical Mean Baseline**: When evaluating purely pre-market public issue features (subscription, issue size, valuation, market momentum) without GMP, the Model achieves an MAE of 15.41%, beating the expanding mean baseline (19.88%) by **-4.47% MAE (95% CI: [-6.16%, -2.78%], excludes zero)**. Incorporating all features without fundamentals, the model achieves an MAE of 11.58% across all 398 out-of-sample issues, beating baseline by **-8.30% MAE (95% CI: [-9.78%, -6.85%])**.
- **Classification / Directional Screening**: The calibrated classifier achieves a ROC-AUC of **0.8884**, Brier score loss of **0.1357**, and Equal-Frequency ECE of **0.0789** for predicting listing gains > 10%.
- **Fundamentals (ROE, PAT Margin, Debt/Equity)**: Incorporating pre-IPO accounting fundamentals showed **no demonstrated effect** over issue structure and subscription alone (MAE difference: +0.08%, 95% CI: [-0.16%, +0.33%], straddles zero).

### 2. Where Raw GMP is the Better Signal
- **Grey Market Dominance**: Across the 321 evaluated IPOs with verified observed pre-listing grey market quotes, **Raw GMP is the superior point estimator**, achieving an MAE of **8.86%**.
- **Model vs. Raw GMP**: The standalone ML model incorporating GMP has higher error than Raw GMP alone (+2.62% MAE, 95% CI: [+1.47%, +3.76%]), showing **no demonstrated advantage over Raw GMP** (in fact, hurting point accuracy).
- **Blend vs. Raw GMP**: An adaptive blend of Model + GMP achieves an MAE of 8.90%, demonstrating **no statistically significant difference over Raw GMP** (difference: +0.04% MAE, 95% CI: [-0.06%, +0.15%], straddles zero).
- **Practical Rule**: Whenever a dated pre-listing GMP quote is observed, **Raw GMP is the primary signal; the ML model provides contextual bounding only**.

### 3. Known Weaknesses & Failure Modes
- **Under-prediction of Tail Pops**: The model severely under-predicts extreme listing-day pops (> 50% gain). For the top 10% largest gains (actual gain >= 50.1%), empirical 80% conformal coverage collapses to **57.5% (FAIL)**.
- **Over-Conservative Conformal Intervals**: On pooled and observed issues, 80% conformal prediction intervals achieved **91.2% empirical coverage** with a mean width of 46.26 percentage points.
- **Probability Reliability Warning**: Do not treat predicted probabilities above approximately **0.85** or below approximately **0.10** as certainty. Empirical binomial Wilson intervals show wide dispersion in extreme bins.

### 4. Forward Test Status
- Genuine FORWARD predictions logged: **1** (`HD Fire Protect Limited`, scored post-close with final features, listing scheduled for 2026-10-21).
- Genuine FORWARD listings completed: **0**.
- Status: **Provisional, no performance claims permitted below n = 30** (per pre-registered rules).

### 5. Known Limitations
- **D-006 (Accounting Fundamentals Completeness)**: Fundamentals columns `roce` and `revenue_growth_pct` are 0% filled; `pe_ratio`/`peer_median_pe` are ~61-62% filled. All fundamental ratios are aggregator-sourced (medium confidence). Pre-IPO accounting fundamentals showed no demonstrated effect in Phase 6/7 evaluations ($\Delta\text{MAE} = +0.08\%$, 95% CI: [-0.16%, +0.33%]); line closed as `ACCEPTED`.
- **D-010 (Historical GMP Availability)**: GMP quotes are unrecorded for 304 of 333 pre-2022 issues (2010–2021). The model is historically trained largely without GMP and evaluated with verified GMP quotes primarily from 2022 onward; line closed as `ACCEPTED`.
- **D-011 (Sector Distribution)**: The broad classification "Industrial & Manufacturing" represents 137 of 731 issues (18.74%). While the largest category, it does not dominate the dataset; line closed as `ACCEPTED`.
- **D-012 (Capital Markets Dry Spell 2012–2014)**: Years 2012–2014 contain very few mainboard IPOs (2012: 11, 2013: 3, 2014: 5). Verified against NSE/BSE official listing notices and Chittorgarh archives as reflecting historical market stagnation; line closed as `ACCEPTED`.

*Disclaimer: This system is a quantitative decision aid and research benchmark only. It does not constitute financial, investment, or trading advice.*

---

## Dataset & Structure

- **Cleaned Dataset**: 731 Mainboard IPO records (2010 to 2026) in `data/ipo_master.csv`, 100% compliant with audit rules (0 FPOs, 0 unverified duplicates, 0 date-order violations).
- **GMP Evidence Standard**: 321 verified historical GMP quotes in `data/ipo_master.csv`. All 77 unverified Phase 7 backfill rows lacking evidence snapshots were reverted to `NOT_RECORDED` per Protocol Section 4 and D-001/D-002.
- **Registry of Excluded Rows**: Full provenance in `data/excluded_rows.csv` and corrections log in `phases/Phase 8/data_corrections.csv`.

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
