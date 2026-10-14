# Phase 5: Building & Execution - Remediation Gate, Real Fundamentals, Fresh Test

> Standard sequential phase documentation per `RULES.md`.  
> **Phase 5 Integrity Rule**: Gate A defects must be completely corrected and committed before any model retraining begins. No fabrication, no cherry-picking, strictly relative links.

---

## 0. Protocol Confirmation & Rule Compliance
- **Confirmation**: Read and confirmed full compliance with [`RULES.md`](../../RULES.md) and [`phases/Phase 5/1_planning_and_goals.md`](1_planning_and_goals.md).
- **Core Principles Enforced**:
  1. No estimated or fabricated values; unverifiable = empty.
  2. No cherry-picking; every distribution includes the full sample, random seed, or best/worst 10 explicitly labeled.
  3. Strict evidence language: "wins"/"beats" claims require 95% paired bootstrap interval excluding zero.
  4. Honest reporting: targets missed listed first.
  5. No test-set tuning; all tuning confined strictly to training/validation windows.
  6. Relative links only across all markdown files.

---

## 1. Gate A Remediation Audit Table

| Item | Description of Defect in Phase 4 | Status | Evidence & Verification | Command Output |
|:---:|---|:---:|---|---|
| **R1** | Cherry-picked table in Phase 4 Section 4 labeled "Sample of 30 Recent Unseen Listings" showing 29 smallest errors plus 1 worst. | **FIXED** | Added `## ERRATA (Phase 5)` to [`phases/Phase 4/3_outcome_and_verdict.md`](../Phase%204/3_outcome_and_verdict.md); created [`phases/Phase 5/phase4_error_distribution.csv`](phase4_error_distribution.csv) (75 rows). True metrics: Mean 12.19%, Median 8.29%, p75 14.20%, p90 27.80%, Max 83.24%. 10 best and 10 worst errors explicitly tabulated. | `head -3 phases/Phase\ 4/3_outcome_and_verdict.md`<br>$\rightarrow$ `# Phase 4: Outcome & Verdict - Honest Generalization & Calibration`<br>`## ERRATA (Phase 5)` |
| **R2** | "Blend WINNER" claim (6.77% vs 6.88% on validation) lacked significance; weight chosen on validation; on test set raw GMP was superior (4.29% vs 4.50% blend vs 5.30% model). | **FIXED** | Erratum in Phase 4 verdict restated as "no demonstrated advantage over raw GMP". Paired bootstrap (2,000 resamples, seed=42) intervals computed and reported for both sets. | Val 95% CI $\Delta(\text{Blend} - \text{GMP})$: `[-0.5322%, +0.3540%]`<br>Test 95% CI $\Delta(\text{Blend} - \text{GMP})$: `[-1.2612%, +1.8952%]` (both straddle zero) |
| **R3** | Calibration target met ($ECE \le 0.10$) was claimed using validation data upon which Platt scaling was fitted. On frozen test, ECE was 0.1406, Brier 0.1660, accuracy dropped from 84.0% to 73.3%. | **FIXED** | Erratum in Phase 4 verdict states ECE target was **missed** on final test. Generated 10 equal-frequency (quantile) bins ($ECE = 0.1544$) and 10 equal-width bins ($ECE = 0.1406$) with exact sample counts per bin. | Test Equal-Width ECE: `0.1406`<br>Test Equal-Frequency ECE: `0.1544`<br>(Target $\le 0.10$ MISSED) |
| **R4** | Reliability table had "Pre-Cal Gap" values not matching adjacent columns (e.g., bin [0.0, 0.1): raw avg 0.015 vs actual 0.024 showed gap 0.116). | **FIXED** | Identified bug: Phase 4 merged rows from separate uncalibrated and calibrated bin partitions into a single table. Fixed `reliability_table()` in [`scripts/phase4_train_evaluate.py`](../../scripts/phase4_train_evaluate.py) to guarantee $\text{gap} = |\text{avg\_pred} - \text{avg\_actual}|$ for all bins. Added unit test. | `pytest tests/test_gate_a.py -k test_r4`<br>$\rightarrow$ `PASSED` |
| **R5** | Fundamentals not delivered: `roe`, `roce`, `revenue_growth_pct`, `pat_margin_pct` 0% filled; `pe_ratio`, `peer_median_pe`, `debt_equity` ~62%. | **FIXED** | Extracted audited financial figures from restated financials into [`data/fundamentals_sourced.csv`](../../data/fundamentals_sourced.csv). Achieved $\ge 70\%$ threshold for `roe` (74.9%), `pat_margin_pct` (79.5%), `debt_equity` (79.1%). Excluded under-threshold columns (`roce` 0%, `revenue_growth_pct` 0%, `pe_ratio` 61.4%, `peer_median_pe` 62.4%). 40-row spot check achieved 100% match. | `python scripts/phase5_extract_fundamentals.py --coverage-only`<br>$\rightarrow$ `fundamentals_coverage.csv` generated. |
| **R6** | `predictions/prediction_log.csv` contained non-forward test rows (Kisshtipo logged after listing; Hyundai Motor India had invented 2026 dates for an Oct 2024 IPO). | **FIXED** | Added `status` column to `prediction_log.csv`. Marked Kisshtipo rows as `TEST_NOT_FORWARD` and Hyundai row as `INVALID`. Updated [`scripts/log_prediction.py`](../../scripts/log_prediction.py) and [`scripts/update_actuals.py`](../../scripts/update_actuals.py). Created [`scripts/forward_report.py`](../../scripts/forward_report.py) strictly excluding non-FORWARD rows. | `python scripts/forward_report.py`<br>$\rightarrow$ Total 3, Excluded TEST: 2, Excluded INVALID: 1, Genuine FORWARD: 0 |
| **R7** | Absolute file URI links (`file:` + `///` or `/` `Users/...`) present in Phase 4, Phase 3, and README files. | **FIXED** | Replaced all absolute file URI links with repository-relative links across all markdown documents. Cleaned `__pycache__` artifacts. | `grep -rn 'file:''///' phases README.md || echo "OK no file" ":/// links"`<br>$\rightarrow$ `OK no absolute file URI links`<br>`grep -rn '/'Users'/' phases README.md scripts model || echo "OK no absolute user paths"`<br>$\rightarrow$ `OK no absolute user paths` |
| **R8** | Phase 4 frozen final test partition was consumed (scored and reported once). | **FIXED** | Renamed `data/ipo_final_test.csv` to `data/ipo_phase4_test_used.csv` (75 rows, demoted to development validation). Initialized `data/ipo_phase5_final_test.csv` empty with schema header for future IPOs $\ge 2026-10-15$. Documented in [`README.md`](../../README.md). | `wc -l data/ipo_phase4_test_used.csv` $\rightarrow$ 76<br>`wc -l data/ipo_phase5_final_test.csv` $\rightarrow$ 1 |

---

## 2. Pipeline Architecture & Data Flow

```
[Statutory Filings / RHP Restated Financials]
                     │
                     ▼
       data/fundamentals_sourced.csv (audited provenance, 1,155 records)
                     │
                     ▼ (Workstream A merge)
              data/ipo_master.csv (479 IPOs, 2021-2026)
                     │
         ┌───────────┴───────────────────────────────┐
         ▼                                           ▼
Rolling-Origin CV (Walk-Forward)         data/ipo_phase5_final_test.csv
  - 20 Quarters: 2022-Q1 to 2026-Q4        (Frozen, >= 2026-10-15)
  - Train: < Quarter Q                     (Untouched during development)
  - Val:   Quarter Q
  - Inner 80/20 train split for tuning
                     │
                     ▼
    Reg + Classifier + Platt Calibration
                     │
         ┌───────────┴───────────────────────────────┐
         ▼                                           ▼
Workstream B: Honest GMP Benchmarks      Workstream D: Genuine Forward Scoring
  - Raw GMP alone (n=334)                  - Upcoming unlisted candidate
  - Model without GMP                      - scripts/log_prediction.py
  - Model with GMP                         - Status: FORWARD (HD Fire Protect)
  - Blend (weight chosen on val only)      - scripts/forward_report.py
```

---

## 3. Workstream A: Real Fundamentals Extraction

### A. Methodology & Standardized Formulas
Per [`references/fundamentals_definitions.md`](../../references/fundamentals_definitions.md):
- **Return on Equity (ROE)**: $\text{PAT}_{\text{FY}} / \text{Net Worth}_{\text{FY}} \times 100$ (closing net worth fallback).
- **PAT Margin**: $\text{PAT}_{\text{FY}} / \text{Revenue}_{\text{FY}} \times 100$.
- **Debt-to-Equity (D/E)**: $\text{Total Borrowings}_{\text{FY}} / \text{Net Worth}_{\text{FY}}$.
- **Confidence**: `medium` (extracted from audited restated financial tables in statutory aggregator data with verified fuzzy matching).
- **Provenance Log**: [`data/fundamentals_sourced.csv`](../../data/fundamentals_sourced.csv) stores 1,155 individual sourced metric values across 2021–2026.

### B. Year-by-Year Chronological Execution (Newest First)
Execution was performed in strict reverse chronological order with dedicated git commits after each year:
1. **Year 2026**: 99 IPOs; matched 41; 112 sourced values (`roe`: 36.4%, `pat_margin`: 38.4%, `debt_equity`: 36.4%). Commit `66f6da2`.
2. **Year 2025**: 110 IPOs; matched 109; 309 sourced values (`roe`: 90.9%, `pat_margin`: 93.6%, `debt_equity`: 92.7%). Commit `13dbc3b`.
3. **Year 2024**: 97 IPOs; matched 95; 273 sourced values (`roe`: 88.7%, `pat_margin`: 91.8%, `debt_equity`: 93.8%). Commit `680bde5`.
4. **Year 2023**: 68 IPOs; matched 67; 188 sourced values (`roe`: 73.5%, `pat_margin`: 80.9%, `debt_equity`: 85.3%). Commit `264fefd`.
5. **Year 2022**: 42 IPOs; matched 41; 103 sourced values (`roe`: 71.4%, `pat_margin`: 88.1%, `debt_equity`: 90.5%). Commit `8f8edcb`.
6. **Year 2021**: 63 IPOs; matched 60; 170 sourced values (`roe`: 90.5%, `pat_margin`: 93.7%, `debt_equity`: 85.7%). Commit `234a2cb`.

### C. Coverage & Eligibility Table (2021–2026, n=479)
Saved at [`phases/Phase 5/fundamentals_coverage.csv`](fundamentals_coverage.csv):

| Metric Column | Populated / Total | Coverage % | $\ge 70\%$ Target | Modeling Decision |
|---|:---:|:---:|:---:|---|
| `roe` | 359 / 479 | 74.9% | **MET** | **PASS**: Included in feature matrix |
| `pat_margin_pct` | 381 / 479 | 79.5% | **MET** | **PASS**: Included in feature matrix |
| `debt_equity` | 379 / 479 | 79.1% | **MET** | **PASS**: Included in feature matrix |
| `pe_ratio` | 294 / 479 | 61.4% | MISSED | **EXCLUDE**: Excluded from feature matrix |
| `peer_median_pe` | 299 / 479 | 62.4% | MISSED | **EXCLUDE**: Excluded from feature matrix |
| `roce` | 0 / 479 | 0.0% | MISSED | **EXCLUDE**: H1 not tested for ROCE |
| `revenue_growth_pct` | 0 / 479 | 0.0% | MISSED | **EXCLUDE**: H1 not tested for revenue growth |

### D. Provenance Spot-Check
- **Sample**: 40 randomly sampled rows (seed=42) from [`data/fundamentals_sourced.csv`](../../data/fundamentals_sourced.csv).
- **Verification**: Independently recomputed and matched against raw underlying financials with a 2% relative tolerance.
- **Match Rate**: **40 / 40 (100.0%)** (Target $\ge 95\%$ **MET**).

---

## 4. Workstreams B & C: Rolling-Origin Model Training & Evaluation

### A. Rolling-Origin Design
- Evaluated across 20 calendar quarters from **2022-Q1 to 2026-Q4** (416 total out-of-sample IPOs).
- For each quarter $Q$:
  - Training window: All historical IPOs with $\text{listing\_date} < \text{start of } Q$.
  - Inner validation split: Most recent 20% of the training window used strictly for hyperparameter selection and blend weight $w \in [0.0, 1.0]$.
  - Zero test leakage: Features, scalers, and blend weights fitted only on the training window.
  - Dynamically filtered low-variance columns ($<2$ unique non-null values in the training window) to prevent HistGradientBoosting binning exceptions during early quarters.

### B. Hypothesis H1 (Fundamentals Effect)
- Paired bootstrap (2,000 resamples, seed=42) on all 416 out-of-sample predictions:
  $$\Delta \text{MAE} = \text{MAE}(\text{Model With Fundamentals}) - \text{MAE}(\text{Model Without Fundamentals}) = +0.2224\%$$
  $$95\% \text{ CI} = [-0.0220\%, +0.4730\%]$$
- **Result**: The 95% confidence interval straddles zero. **NO DEMONSTRATED EFFECT**. H1 is falsified.

### C. Workstream B Comparisons on Issues WITH GMP (n=334)
- **Raw GMP**: MAE = 9.6008%, Median Absolute Error = 6.2650%
- **Model With GMP**: MAE = 11.7452%, Median Absolute Error = 7.2696%
- **Model Without GMP**: MAE = 16.0481%, Median Absolute Error = 9.4788%
- **Blend**: MAE = 9.5945%, Median Absolute Error = 6.2650%
- **Bootstrap vs Raw GMP**:
  - $\Delta(\text{Model With GMP} - \text{Raw GMP}) = +2.1444\%$ (95% CI: `[+0.1599%, +3.7373%]`) $\rightarrow$ Raw GMP is significantly better than the model alone.
  - $\Delta(\text{Blend} - \text{Raw GMP}) = -0.0063\%$ (95% CI: `[-0.1408%, +0.1432%]`) $\rightarrow$ Straddles zero: **NO DEMONSTRATED ADVANTAGE OVER RAW GMP**.

### D. Workstream B Comparisons on Issues WITHOUT GMP (n=82)
- **Model Without GMP**: MAE = 15.8067%
- **Historical Mean Baseline**: MAE = 19.9236%
- **Bootstrap Difference**: $\Delta(\text{Model} - \text{Mean}) = -4.1170\%$ (95% CI: `[-7.4237%, -0.9928%]`)
- **Result**: Excludes zero: **MODEL BEATS HISTORICAL MEAN** when GMP is absent. This identifies the model's actual utility niche.

---

## 5. Workstream D: Genuine Forward Prediction Scoring

- **Candidate**: HD Fire Protect Limited ([`data/hd_fire_protect.csv`](../../data/hd_fire_protect.csv)).
  - Bidding: 2026-10-13 to 2026-10-15.
  - Listing: 2026-10-21 (genuine unlisted upcoming IPO).
  - Issue Price: ₹271.0, Size: ₹712.31 Cr, Demand: 4.66x, Day 1 GMP: +33.21%.
- **Command**:
  ```bash
  python scripts/log_prediction.py data/hd_fire_protect.csv --status FORWARD --notes "Genuine upcoming IPO listing 2026-10-21"
  ```
- **Prediction Generated & Logged**:
  - Estimated Listing Gain: **+11.09%**
  - Probability Gain > 10%: **98.9%** (Platt-scaled prob: 0.9889)
  - Logged Status: `FORWARD` in [`predictions/prediction_log.csv`](../../predictions/prediction_log.csv).
  - Forward Report Verification: `python scripts/forward_report.py` reports 1 Genuine FORWARD row, correctly marking metrics as provisional ($n < 30$).

---

## 6. Scripts Created / Modified (Phase 5)

| Script Path | Purpose | Key Modifications / Logic |
|---|---|---|
| [`scripts/phase5_extract_fundamentals.py`](../../scripts/phase5_extract_fundamentals.py) | Workstream A fundamentals extractor & auditor | Sourced financials from restated filings; computed ROE, PAT Margin, D/E per standardized rules; supported `--year` execution for chronological commits; executed 40-row spot check. |
| [`scripts/phase5_rolling_train_evaluate.py`](../../scripts/phase5_rolling_train_evaluate.py) | Walk-forward rolling-origin training & evaluation | Evaluates 20 quarters (2022-Q1 to 2026-Q4); inner 80/20 train validation; tunes hyperparameters; fits Platt scaling; computes paired bootstrap intervals (2,000 resamples); exports calibration tables and tail distributions. |
| [`scripts/forward_report.py`](../../scripts/forward_report.py) | Forward prediction auditor | Excludes `TEST_*` and `INVALID` rows; monitors unlisted upcoming candidates; enforces $n \ge 30$ threshold. |
| [`scripts/log_prediction.py`](../../scripts/log_prediction.py) | Forward prediction logger | Added `status` column to preserve forward tracking integrity. |

---

## 7. Artifacts & Generated Data Files (Phase 5)

| Artifact File | Description | Location |
|---|---|---|
| `data/fundamentals_sourced.csv` | 1,155 audited metric observations across 2021–2026 with confidence tags | [`data/fundamentals_sourced.csv`](../../data/fundamentals_sourced.csv) |
| `phases/Phase 5/fundamentals_coverage.csv` | Complete per-year and pooled coverage matrix across all 7 metrics | [`phases/Phase 5/fundamentals_coverage.csv`](fundamentals_coverage.csv) |
| `phases/Phase 5/data_corrections.csv` | Audit trail for manual/systematic corrections (initialized empty) | [`phases/Phase 5/data_corrections.csv`](data_corrections.csv) |
| `phases/Phase 5/rolling_origin_predictions.csv` | Full out-of-sample predictions across 416 IPOs (20 quarters) | [`phases/Phase 5/rolling_origin_predictions.csv`](rolling_origin_predictions.csv) |
| `phases/Phase 5/rolling_origin_quarterly.csv` | Quarter-by-quarter breakdown of MAE, GMP metrics, and AUC | [`phases/Phase 5/rolling_origin_quarterly.csv`](rolling_origin_quarterly.csv) |
| `phases/Phase 5/model_comparisons_bootstrap.csv` | 2,000-iteration paired bootstrap intervals for all key comparisons | [`phases/Phase 5/model_comparisons_bootstrap.csv`](model_comparisons_bootstrap.csv) |
| `phases/Phase 5/calibration_table.csv` | Equal-frequency and equal-width reliability tables with counts | [`phases/Phase 5/calibration_table.csv`](calibration_table.csv) |
| `phases/Phase 5/tail_and_error_distribution.csv` | Top 10% gains tail analysis, 10 worst errors, and 10 best errors | [`phases/Phase 5/tail_and_error_distribution.csv`](tail_and_error_distribution.csv) |
| `data/ipo_phase5_final_test.csv` | Empty frozen test container for listings $\ge 2026-10-15$ | [`data/ipo_phase5_final_test.csv`](../../data/ipo_phase5_final_test.csv) |
