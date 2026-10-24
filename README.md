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
- **Over-Conservative Conformal Intervals (D-049 Protocol Reconciliation)**: On pooled and observed issues, 80% conformal prediction intervals achieved **91.2% empirical coverage** (mean width 46.26 pp) under Phase 7's static holdout evaluation (fixed calibration set on training split). When evaluated under Phase 11's expanding-window walk-forward re-calibration across 20 distinct calendar quarters (2022Q1–2026Q4, $n=398$), the same champion architecture achieved **87.94% empirical coverage** (mean width 48.96 pp, 95% Wilson CI: [84.4%, 90.8%]). Both evaluation protocols significantly exceed the 80% nominal target, confirming over-conservatism (D-008), with the difference (91.2% vs 87.94%) fully reconciled by the static versus expanding-window walk-forward calibration protocol (reproducible via `scripts/reconcile_coverage.py`).
- **Probability Reliability Warning**: Do not treat predicted probabilities above approximately **0.882** or below approximately **0.091** as certainty (the out-of-sample calibrated probability range measured across 398 rolling-origin evaluations is **[0.091, 0.882]**; values outside this range are suppressed in the app and report as uncalibrated). Empirical binomial Wilson intervals show wide dispersion in extreme bins.

### 4. Forward Test Status
- Genuine FORWARD predictions logged: **6** (`HD Fire Protect Limited`, `Fusion CX Limited`, `Zetwerk Manufacturing Business Limited`, `Sahajanand Medical Technologies Limited`, `Tonbo Imaging India Limited`, `Bonfiglioli Transmissions Limited`).
- Genuine FORWARD listings completed: **1** (`HD Fire Protect Limited`, listed 2026-10-21, Issue: INR 271.00, Listing: INR 334.40, Gain: +23.39%, Model: +26.12%, GMP: +30.26%).
- Status: **Provisional (n = 1 of 30), descriptive only, no performance claims permitted below n = 30** (per pre-registered rules).

### 4a. Champion Replay and Live Accuracy Dashboard
- The registered champion remains `v4.0.0-champion`, with a training window ending 2021-12-31; its artifact hash matches the registry. The master contains 333 IPOs through 2021 and 398 later rows. No training or model promotion was performed for this replay.
- `predictions/champion_replay_v4.0.0-champion.csv` records inference-only comparisons across the 396 eligible Mainboard rows in `data/ipo_master.csv` dated 2022 onward. The two InvIT/REIT rows are excluded by the model's Mainboard eligibility rule. Replay MAE is 7.98 percentage points and positive/non-positive direction matched 84.3% of the time.
- This is a retrospective replay using stored historical feature values; it is not a prospectively recorded prediction series, and not every historical feature has a verified pre-listing snapshot. The replay is shown separately from genuine FORWARD predictions and must not be presented as the live track record.
- Newly completed listings after the master data cutoff were checked; R.K. Fashion Accessories listed on NSE SME on 2026-10-12 and is outside this Mainboard model's scope, so it was not added or scored.
- `dashboard/index.html` compares replay predictions with actual listing gains and separately tracks the champion's genuine FORWARD predictions. `opi.run_daily` refreshes it during the daily run, and `scripts/update_actuals.py` refreshes it immediately after an official exchange outcome is recorded.
- Fusion CX's final bidding figures were available only after its 2026-10-16 close; the live champion prediction is **+4.33%**, with calibrated P(gain > 10%) of **30.1%**. No GMP input was recorded. It is due to be compared with the official listing outcome after 2026-10-22.

### 5. Known Limitations
- **D-006 (Accounting Fundamentals Completeness)**: Fundamentals columns `roce` and `revenue_growth_pct` are 0% filled; `pe_ratio`/`peer_median_pe` are ~61-62% filled. All fundamental ratios are aggregator-sourced (medium confidence). Pre-IPO accounting fundamentals showed no demonstrated effect in Phase 6/7 evaluations ($\Delta\text{MAE} = +0.08\%$, 95% CI: [-0.16%, +0.33%]); line closed as `ACCEPTED`.
- **D-007 (Tail Pop Under-prediction)**: Large pops are under-predicted; empirical 80% conformal coverage for the top 10% largest listing gains is 55.0% for the Champion. Tested in Phase 11 walk-forward experiment against Candidate 1 (Mondrian Conformal, 57.5% tail coverage) and Candidate 2 (Quantile CQR, 67.5% tail coverage). Neither candidate met the pre-registered adoption criteria (Target 2 >= 70% and width reduction >= 5 pp); line closed as ACCEPTED limitation.
- **D-008 (Conformal Prediction Over-conservatism & D-049 Reconciliation)**: Pooled conformal prediction intervals yield 87.94% empirical coverage across the 20-quarter expanding walk-forward sample (vs 80% nominal target) and 91.2% under static holdout calibration (difference reconciled by calibration protocol via `scripts/reconcile_coverage.py`). Evaluated in Phase 11; Candidate 1 achieved 85.68% and Candidate 2 achieved 83.92% with wider bounds (+3.76 pp), failing simultaneous multi-objective criteria; line closed as ACCEPTED limitation.
- **D-010 (Historical GMP Availability)**: GMP quotes are unrecorded for 304 of 333 pre-2022 issues (2010–2021). The model is historically trained largely without GMP and evaluated with verified GMP quotes primarily from 2022 onward; line closed as `ACCEPTED`.
- **D-011 (Sector Distribution)**: The broad classification "Industrial & Manufacturing" represents 137 of 731 issues (18.74%). While the largest category, it does not dominate the dataset; line closed as `ACCEPTED`.
- **D-012 (Capital Markets Dry Spell 2012–2014)**: Years 2012–2014 contain very few mainboard IPOs (2012: 11, 2013: 3, 2014: 5). Verified against NSE/BSE official listing notices and Chittorgarh archives as reflecting historical market stagnation; line closed as `ACCEPTED`.
- **D-013 (Upstream Audit Sample URLs & Snapshots)**: The 15-row duplicate verification and 40-row random audit from Phase 7 contained corrupted upstream URLs (wrong Chittorgarh SME IDs and generic 404s). In Phase 8, 20 audit snapshots were saved under `data/evidence/audit/` documenting this mismatch. Live bulk re-scraping remains blocked by site permissions; those 15 entities carry status `UNVERIFIED` in `phases/Phase 9/duplicate_verification.csv`; line maintained as `PARTIAL`.

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
    └── Phase 9/                    # Phase 9 OPI Console, Grounded Agent & Governed Learning Loop
        ├── 1_planning_and_goals.md
        ├── 2_building_and_execution.md
        ├── 3_outcome_and_verdict.md
        ├── preregistration.md
        ├── actions_run_evidence.md
        ├── verify_start.txt
        └── verify_end.txt
├── opi/                            # Core Phase 9 application package
│   ├── schema.py                   # Pydantic typed schemas for verified IPO data
│   ├── collect.py                  # Snapshot-backed deterministic field verification
│   ├── research_agent.py           # Grounded agent with prompt injection defense
│   ├── validate.py                 # Input validation & gating rules (mainboard, close date)
│   ├── score.py                    # Production model scoring & conformal prediction
│   └── log.py                      # Immutable forward prediction logger
└── app/
    └── main.py                     # Streamlit analysis console
```

---

## System Architecture

```
                      [ Public Sources / Exchanges / Aggregators ]
                                           │
                                           ▼
                 ┌──────────────────────────────────────────────────┐
                 │             Code Fetch & Snapshotting            │
                 │           (data/evidence/research/...)           │
                 └─────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                 ┌──────────────────────────────────────────────────┐
                 │        Research Agent & Grounding Verifier       │
                 │   (Untrusted HTML -> Typed Schema / Null Check)  │
                 └─────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                 ┌──────────────────────────────────────────────────┐
                 │          Input Validation & Gating Engine        │
                 │  (Mainboard Check, Bidding Close, As-Of Date)    │
                 └─────────────────────────┬────────────────────────┘
                                           │
                          ┌────────────────┴────────────────┐
                          ▼                                 ▼
                [ PREVIEW Gating ]                 [ FORWARD Gating ]
                (Pre-close / Unlogged)             (Post-close Final Log)
                          │                                 │
                          └────────────────┬────────────────┘
                                           ▼
                 ┌──────────────────────────────────────────────────┐
                 │          Calibrated Scoring & Conformal          │
                 │         (Raw GMP vs Model Regime Routing)        │
                 └─────────────────────────┬────────────────────────┘
                                           │
                          ┌────────────────┴────────────────┐
                          ▼                                 ▼
                 ┌──────────────────┐             ┌──────────────────┐
                 │ Streamlit Console│             │ Governed Loop    │
                 │ (app/main.py)    │             │ (Monthly PR,     │
                 │                  │             │ Zero Auto-Promote│
                 └──────────────────┘             └──────────────────┘
```

---

## Quickstart & Commands

### 0. Windows Setup & Environment Notes
When running pytest on Windows environments where global or external site-packages plugins (such as `pytest-ethereum`) might be loaded by pytest, pass `-p no:pytest_ethereum` or configure `addopts = -p no:pytest_ethereum` in your local pytest flags to prevent unneeded dependency conflicts. In PowerShell, ensure UTF-8 output encoding is active (`$env:PYTHONIOENCODING = "utf-8"`).


### 1. Environment Configuration
Copy `.env.example` to `.env` (gitignored) and configure your LLM provider:
```bash
OPI_LLM_PROVIDER=gemini       # Options: gemini, mock (for offline hermetic runs)
GEMINI_API_KEY=your_key_here
```

### 2. Run the Streamlit Analysis Console
Launch the interactive decision-aid console:
```bash
streamlit run app/main.py
```

### 3. Run the Grounded IPO Research Agent
Propose and verify fields for an upcoming or recent IPO:
```bash
# Live grounded run (saves HTML snapshots and verifies every field)
python -m opi.research_agent --company "HD Fire Protect Limited"

# Hermetic mock run (offline, 0 tokens)
python -m opi.research_agent --company "HD Fire Protect Limited" --mock
```

### 4. Governed Learning Loop & Promotion Audit
Audit unlisted vs listed candidate rows for promotion into master:
```bash
python scripts/promote_forward_rows.py --audit
```

### 5. Record an Actual Listing Outcome
The updater lists pending forward predictions without changing data:
```bash
python scripts/update_actuals.py
```

After an IPO lists, record its **opening/listing price** from an official NSE or BSE page. The command fetches that page itself, checks that the company identifier, listing date, and opening-price quote appear in the fetched content, saves an immutable snapshot and metadata manifest under `data/evidence/actuals/`, computes the gain from the issue price saved with the original prediction, and only then updates the forward log. It refuses non-exchange URLs, redirects away from NSE/BSE, future listing dates, missing quotes, and repeat updates.

```bash
python scripts/update_actuals.py \
  --company "Exact company name from prediction_log.csv" \
  --source-url "<official NSE/BSE page URL>" \
  --actual-listing-price "<opening price shown on the page>" \
  --page-date "<listing date YYYY-MM-DD>" \
  --company-quote "<exact company identifier visible on the page>" \
  --price-quote "<exact opening/listing price excerpt from the page>"
```

This is a command template; replace each quoted placeholder with values visible on the official exchange page. The quote must identify an opening/listing price and include the exact supplied price; the page must show the prediction's listing date. If the exchange page cannot be fetched or the supplied text is not present in its snapshot, the outcome stays pending. The legacy historical master CSV is not used to fill forward outcomes.

### 6. Full Test Suite & Independent Verification
```bash
python -m pytest -q            # Runs 64 unit, schema, app, and governance tests
python scripts/verify_all.py   # Independent repository verification (48 checks, 0 fail)
```

Output applies the pre-registered regime routing rules:
- **GMP observed**: Uses Raw GMP as the primary expected return; model provides context and calibrated interval.
- **No GMP observed**: Uses model point estimate with regime-specific interval.

---

## Regulatory & Non-Advisory Notice
**Decision aid, not financial advice.** Initial Public Offerings carry significant capital risk. Model estimates and grey market quotes are probabilistic quantitative research aids and do not guarantee future listing performance. No output from this software constitutes a recommendation to apply, buy, sell, or avoid any security.

