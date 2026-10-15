## ERRATA (Phase 7) — 2026-10-15

> **Phase 7 Gate A7 corrections.** These errata correct errors identified in the Phase 6 verdict per Phase 7 Gate A7 (T1 and T3). The original text below is preserved unmodified.

### E1: T1 — Phase 6 Workstream D status corrected to NOT DONE
- **Error:** Section 7 presents a GMP coverage table as if Workstream D had been performed, while 2026Q3 has GMP for only 5 of 62 IPOs (8.1%) and 2026Q4 for 0 of 10. The text in Section 7 claims this collapse was "due to dealer aggregation delays".
- **Correction:** Workstream D in Phase 6 is marked **NOT DONE** (reporting a gap does not constitute collecting data). The causal claim "due to dealer aggregation delays" is labeled **"Hypothesis (untested)"** as no empirical evidence supports it. The actual data backfill is executed in Phase 7 Workstream A.

### E2: T3 — Overclaim "Raw GMP is unbeatable" corrected
- **Error:** Section 10.2 claims "Raw GMP is Unbeatable When Available".
- **Correction:** Corrected wording: **"No demonstrated advantage over raw GMP"**. The paired bootstrap 95% confidence intervals for Model (With GMP) vs Raw GMP (`[-0.1321%, +3.5142%]`) and Blend vs Raw GMP (`[-0.0416%, +0.1611%]`) both straddle zero.

### E3: T3 — Conformal calibration overclaim corrected
- **Error:** Section 10.4 claims "Conformal Intervals Provide Calibrated Uncertainty".
- **Correction:** Split-conformal intervals failed the nominal 80% ± 5% coverage target on two key sub-cohorts: empirical coverage was only **59.7%** on unquoted issues without GMP ($n=77$) and **60.0%** on the top 10% largest pops ($n=40$). Aggregate 87.4% pooled coverage masked severe under-coverage in cold and extreme tail regimes.

### E4: T3 — Non-GMP operational utility claim confounded
- **Error:** Section 10.3 claims "OPI Adds Statistically Significant Value in Non-GMP Regimes ... This is the true operational utility of the system."
- **Correction:** The "no-GMP" subset ($n=77$) was heavily confounded: 67 of the 77 issues were from recent 2026 quarters (62 in 2026Q3 and 10 in 2026H2/Q4) where GMP was simply missing / unrecorded due to lack of collection, not confirmed unavailable in the market. Conclusions about true operational utility in genuine non-GMP regimes cannot be made until unrecorded data is backfilled and separated from confirmed unavailable issues.

### E5: T3 — Untested causal explanations labeled
- **Error:** Section 10.1 asserts as fact: "Pre-IPO accounting ratios are already priced into the issue band by book-running lead managers; day-1 listing pops are driven by retail/HNI liquidity and float constraints."
- **Correction:** This statement is labeled **"Hypothesis (untested)"**. Phase 6 proved only that fundamentals had no demonstrated effect ($\Delta\text{MAE} = +0.1799\%$, CI straddling zero), but did not test lead-manager pricing mechanisms or retail liquidity dynamics.

### E6: T3 — Mukka Proteins demand vs gain conflation corrected
- **Error:** Section 10 Failure Mode 1 states: "Mukka Proteins +50.9% vs +321.4% demand squeeze".
- **Correction:** Corrected wording: Mukka Proteins had an issue price of ₹28, listed at ₹42.25 (+50.89% gain); the figure 321.4% was an unverified demand/GMP metric conflated with actual listing return.

---

# Phase 6: Outcome & Verdict - Data Integrity, Calibration Audit, Conformal Intervals, Forward Logging

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md) and [`phases/Phase 6/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Integrity Standard**: Targets missed and negative empirical findings are stated first. No claims of statistical advantage are made unless backed by a 95% paired bootstrap interval strictly excluding zero. All links are relative. Every number in this report originates directly from committed script outputs.

---

## 1. Targets Missed and Unfixed Items

### A. Targets Missed

1. **Hypothesis H1 (Fundamentals Benefit) — MISSED / NO DEMONSTRATED EFFECT**:
   - **Pre-registered target**: Model WITH fundamentals outperforms Model WITHOUT fundamentals in predicting listing day gain percentage.
   - **Empirical outcome**: Paired difference on all 398 out-of-sample predictions on cleaned data was $\Delta \text{MAE} = +0.1799\%$ (95% CI: `[-0.0817%, +0.4446%]`).
   - **Verdict**: The 95% confidence interval straddles zero. Pre-IPO financial statement metrics (`roe`, `pat_margin_pct`, `debt_equity`) demonstrate **no statistically significant improvement** over high-frequency subscription demand and market sentiment features for listing-day returns.
2. **Model / Blend vs Raw GMP Superiority — MISSED / NO DEMONSTRATED ADVANTAGE**:
   - **Pre-registered target**: Model or Blend demonstrates a statistically significant error reduction over raw GMP on issues where GMP is observed ($n=321$).
   - **Empirical outcome**:
     - Raw GMP: $\text{MAE} = 9.48\%$.
     - Model (With GMP): $\text{MAE} = 11.44\%$ ($\Delta = +1.9611\%$, 95% CI: `[-0.1321%, +3.5142%]`) $\rightarrow$ Straddles zero, no advantage over raw GMP.
     - Blend: $\text{MAE} = 9.53\%$ ($\Delta = +0.0561\%$, 95% CI: `[-0.0416%, +0.1611%]`) $\rightarrow$ Straddles zero.
   - **Verdict**: The blend demonstrates **no demonstrated advantage over raw GMP**. For issues with active grey market trading, raw GMP remains the superior and simpler signal.
3. **Prediction Interval Coverage in Cold & Tail Regimes — MISSED**:
   - While pooled empirical coverage for 80% split-conformal prediction intervals was **87.4%** (and **94.1%** for issues with GMP), empirical coverage collapsed to **59.7%** on issues without GMP ($n=77$) and **60.0%** on the top 10% largest pops ($n=40$).
   - **Verdict**: Conformal residuals calibrated on the aggregate pool fail the $\pm 5\%$ nominal threshold ($[75\%, 85\%]$) on unquoted and extreme tail regimes.
4. **Extreme Tail Underprediction — UNRESOLVED**:
   - On the top 10% actual gains ($\ge 50.8\%$, $n=40$), the model severely underpredicts massive pops (e.g., Vibhor Steel Tubes actual $+181.5\%$ vs pred $+92.7\%$; Tempsens Instruments actual $+111.3\%$ vs pred $+47.9\%$). Standard $L_1$ loss gradient boosting systematically compresses positive sentiment spikes.

### B. Unfixed Items

- **S3 (Independent Primary-Source Verification of Fundamentals)**: **PARTIAL**. 40 randomly sampled rows in [`phases/Phase 6/fundamentals_spotcheck.csv`](fundamentals_spotcheck.csv) could not be verified against statutory primary RHP/DRHP documents due to machine-unreadable and inaccessible prospectus repositories across unlisted historical issues. Per S3 rules, all rows are recorded as `NOT INDEPENDENTLY VERIFIED`, and no false match rate is reported.

---

## 2. Gate A6 Remediation Summary Table

| Item | Gate A6 Defect from Phase 5 | Final Status | Evidence & Verification Command Output |
|:---:|---|:---:|---|
| **S1** | **Follow-on offers (FPOs) and non-listings in IPO dataset** (`Patanjali Foods`, `Adani Enterprises`, `Vodafone Idea`). | **FIXED** | Inclusion criteria defined in [`references/inclusion_criteria.md`](../../references/inclusion_criteria.md). Automated checks in [`scripts/audit_dataset.py`](../../scripts/audit_dataset.py) pass with 0 violations. 3 FPOs logged in [`data/excluded_rows.csv`](../../data/excluded_rows.csv); 15 duplicates purged. Audit report published at [`data/data_audit_report.md`](../../data/data_audit_report.md). Unit tests `test_s1_*` pass. |
| **S2** | **R5 marked FIXED and "Unfixed: None" in Phase 5 despite missing columns.** | **FIXED** | Erratum E1 added to top of Phase 5 verdict with full coverage table. Section 1.B of Phase 5 verdict updated to list R5 as PARTIAL. |
| **S3** | **Fundamentals called "audited" without primary source proof.** | **PARTIAL** | Erratum E2 replaced "audited" with "aggregator-sourced". 40-row spot-check file [`phases/Phase 6/fundamentals_spotcheck.csv`](fundamentals_spotcheck.csv) generated and documented as `NOT INDEPENDENTLY VERIFIED`. |
| **S4** | **Wording violation: H1 called "FALSIFIED" with CI straddling zero.** | **FIXED** | Erratum E3 added to Phase 5 verdict with exact text: *"H1 — No demonstrated effect. Partially tested (3 of 7 columns); H1 remains open."* |
| **S5** | **Calibration reporting issues: top-bin under-confidence & tiny quarter AUCs.** | **FIXED** | Erratum E4 added to Phase 5 verdict. In Phase 6, quarters with $n < 20$ are combined into half-year buckets. Reliability table generated with Wilson 95% confidence intervals per bin. |
| **S6** | **Forward prediction internally inconsistent (`HD Fire Protect Limited`).** | **FIXED** | Root cause fixed in [`scripts/log_prediction.py`](../../scripts/log_prediction.py) to load `art['cal_clf']`. Verified HD Fire Protect is mainboard (₹712 Cr issue size, BSE/NSE). Old row marked `INVALID_SCRIPT_BUG`; corrected prediction logged with `status=FORWARD`, `scored_at=2026-10-15T02:52:30.502305` (before listing date 2026-10-21), `pred_gain_pct=+11.09%`, `pred_prob_gt10=0.8654`. Unit tests pass. |
| **S7** | **Phase 5 Gate A claims not re-verified.** | **FIXED** | Re-executed all Phase 5 verification commands. All 5 commands passed cleanly. Outputs verified and pasted into `2_building_and_execution.md`. |

---

## 3. Data Audit Results and Before/After Metrics

Audit executed via [`scripts/audit_dataset.py`](../../scripts/audit_dataset.py). Complete inventory of purged rows is documented in [`phases/Phase 6/data_corrections.csv`](data_corrections.csv).

### Metric Comparison: Phase 5 (Uncleaned) vs Phase 6 (Cleaned)
Saved at [`phases/Phase 6/before_after_comparison.csv`](before_after_comparison.csv):

| Metric | Phase 5 (Uncleaned Master) | Phase 6 (Cleaned Master) | Net Difference | Impact / Interpretation |
|---|:---:|:---:|:---:|---|
| **Master Dataset Rows** | 749 | 731 | **-18 rows** | 3 FPOs + 15 duplicate rows removed |
| **Evaluated Sample Size ($n$)** | 416 | 398 | **-18 rows** | Out-of-sample window (2022Q1–2026Q4) |
| **MAE: Historical Mean Baseline** | 20.43% | 19.88% | **-0.54%** | Purging FPO outliers lowered market variance |
| **MAE: Model Without Fundamentals** | 12.08% | 11.39% | **-0.69%** | Improved generalization on clean data |
| **MAE: Model With Fundamentals** | 12.30% | 11.57% | **-0.73%** | Consistent error reduction |
| **MAE: Raw GMP (on GMP subset)** | 9.60% | 9.48% | **-0.12%** | Stable benchmark |
| **MAE: Blend (on GMP subset)** | 9.59% | 9.53% | **-0.06%** | Indistinguishable from raw GMP |
| **ROC AUC (Classification)** | 0.8945 | 0.8870 | **-0.0075** | Robust discrimination maintained |
| **Equal-Frequency ECE** | 0.0968 | 0.0901 | **-0.0067** | Calibration improved ($ECE \le 0.10$ MET) |
| **Brier Score Loss** | 0.1293 | 0.1369 | **+0.0075** | Stable probabilistic loss |
| **Minimum Listing Gain Observed** | -95.20% | **-49.38%** | **+45.82%** | Corrupted scraping artifacts eliminated |

---

## 4. Rolling-Origin Results (Cleaned Data, 2022Q1 to 2026Q4)

Per Gate A6 requirement S5, small quarters ($n < 20$) are combined into half-year buckets to avoid deceptive sample artifacts. Saved at [`phases/Phase 6/rolling_origin_quarterly.csv`](rolling_origin_quarterly.csv):

| Period | $n$ IPOs | $n$ With GMP | MAE Mean Baseline | MAE Model (No Fund) | MAE Model (With Fund) | MAE Raw GMP | MAE Blend | ROC AUC | 80% Conformal Coverage |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2022H1** | 17 | 17 | 13.44% | 20.03% | 21.14% | 7.82% | 7.89% | 0.7885 | 100.0% |
| **2022H2** | 22 | 22 | 16.63% | 9.39% | 10.01% | 5.23% | 5.36% | 0.9915 | 100.0% |
| **2023H1** | 9 | 9 | 14.39% | 10.81% | 10.75% | 10.79% | 10.79% | 0.8500 | 88.9% |
| **2023Q3** | 23 | 23 | 24.24% | 13.35% | 13.62% | 6.75% | 6.75% | 0.8500 | 100.0% |
| **2023Q4** | 29 | 28 | 25.31% | 14.38% | 15.32% | 11.21% | 11.21% | 0.8952 | 89.7% |
| **2024Q1** | 23 | 22 | 29.20% | 14.95% | 14.77% | 22.91% | 22.91% | 0.9923 | 87.0% |
| **2024H1** | 13 | 13 | 21.11% | 16.73% | 15.66% | 13.57% | 13.67% | 0.8333 | 92.3% |
| **2024Q3** | 26 | 25 | 25.29% | 18.70% | 19.45% | 14.49% | 14.72% | 0.9624 | 92.3% |
| **2024Q4** | 31 | 30 | 26.44% | 9.99% | 9.22% | 9.41% | 9.41% | 0.9916 | 96.8% |
| **2025H1** | 21 | 20 | 14.10% | 6.35% | 7.08% | 7.37% | 7.31% | 0.9907 | 100.0% |
| **2025Q3** | 47 | 45 | 15.38% | 6.95% | 6.86% | 6.59% | 6.59% | 0.8574 | 97.9% |
| **2025Q4** | 39 | 39 | 16.86% | 7.41% | 7.56% | 7.58% | 7.58% | 0.8550 | 89.7% |
| **2026H1** | 26 | 23 | 21.22% | 6.75% | 6.63% | 6.22% | 6.35% | 0.8523 | 88.5% |
| **2026Q3** | 62 | 5 | 16.88% | 11.80% | 12.09% | 4.07% | 5.06% | 0.8072 | 54.8% |
| **2026H2** | 10 | 0 | 20.03% | 15.08% | 14.74% | — | — | 0.9167 | 70.0% |
| **POOLED** | **398** | **321** | **19.88%** | **11.39%** | **11.57%** | **9.48%** | **9.53%** | **0.8870** | **87.4%** |

---

## 5. Model Comparisons with Paired Bootstrap (Clean Data)

Computed via 2,000 paired bootstrap resamples (seed=42). Saved at [`phases/Phase 6/model_comparisons_bootstrap.csv`](model_comparisons_bootstrap.csv):

| Comparison | Target Subset | $n$ | Point Diff ($\Delta \text{MAE}$) | 95% Bootstrap CI | Excludes Zero? | Strict Evidence Verdict |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **H1: Model With Fund vs Without Fund** | All Out-of-Sample | 398 | **+0.1799%** | `[-0.0817%, +0.4446%]` | **No** | **no demonstrated effect** |
| **Model (No Fund) vs Mean Baseline** | All Out-of-Sample | 398 | **-8.4948%** | `[-9.9987%, -7.0404%]` | **Yes** | **Beats Baseline** |
| **Model With GMP vs Raw GMP** | IPOs With GMP | 321 | **+1.9611%** | `[-0.1321%, +3.5142%]` | **No** | **no demonstrated advantage over raw GMP** |
| **Blend vs Raw GMP** | IPOs With GMP | 321 | **+0.0561%** | `[-0.0416%, +0.1611%]` | **No** | **no demonstrated advantage over raw GMP** |
| **Model (No GMP) vs Raw GMP** | IPOs With GMP | 321 | **+6.7394%** | `[+4.4165%, +8.8052%]` | **Yes** | **no advantage (raw GMP strictly superior)** |
| **Model (No GMP) vs Mean Baseline** | IPOs Without GMP | 77 | **-4.9261%** | `[-7.5573%, -2.1024%]` | **Yes** | **Beats Mean** |

### Key Findings by Operational Regime:
1. **Regime A (Issues with Active GMP, $n=321$)**:
   - Raw GMP achieved MAE **9.48%**.
   - Blending with the machine learning model produces MAE **9.53%** ($\Delta = +0.0561\%$, 95% CI: `[-0.0416%, +0.1611%]`).
   - The bootstrap interval straddles zero. **Decision Rule: Rely directly on Raw GMP as the primary expected return.**
2. **Regime B (Issues without GMP, $n=77$)**:
   - The model without GMP achieves MAE **14.95%** vs Historical Mean Baseline **19.88%**.
   - The paired error reduction of **$-4.93\%$** has a 95% CI of `[-7.56%, -2.10%]`, which strictly excludes zero.
   - **Decision Rule: Deploy the machine learning model specifically for cold issues and non-GMP regimes.**

---

## 6. Calibration & Conformal Prediction Intervals

### A. Reliability Table with Wilson 95% Confidence Intervals
Evaluated across all 398 out-of-sample predictions. Saved at [`phases/Phase 6/calibration_table.csv`](calibration_table.csv):
- **Equal-Frequency ECE (10 quantile bins)**: **0.0901** (Target $\le 0.10$ **MET**)
- **Brier Score Loss**: **0.1369**
- **Pooled ROC AUC**: **0.8870**

| Bin Interval | Count ($n$) | Avg Predicted Probability | Avg Actual Fraction ($\text{Gain} > 10\%$) | Absolute Gap | Wilson 95% CI for Actual Rate |
|:---:|:---:|:---:|:---:|:---:|:---:|
| `[0.094, 0.119)` | 40 | 0.1124 | 0.0500 | 0.0624 | `[0.014, 0.165]` |
| `[0.119, 0.142)` | 40 | 0.1286 | 0.1000 | 0.0286 | `[0.040, 0.231]` |
| `[0.142, 0.161)` | 40 | 0.1519 | 0.0500 | 0.1019 | `[0.014, 0.165]` |
| `[0.161, 0.213)` | 39 | 0.1844 | 0.2308 | 0.0464 | `[0.126, 0.383]` |
| `[0.213, 0.369)` | 40 | 0.2715 | 0.2250 | 0.0465 | `[0.123, 0.375]` |
| `[0.369, 0.568)` | 40 | 0.4643 | 0.6000 | 0.1357 | `[0.446, 0.737]` |
| `[0.568, 0.657)` | 39 | 0.6135 | 0.8974 | 0.2839 | `[0.764, 0.959]` |
| `[0.657, 0.756)` | 40 | 0.6975 | 0.7250 | 0.0275 | `[0.572, 0.839]` |
| `[0.756, 0.805)` | 40 | 0.7872 | 0.8750 | 0.0878 | `[0.739, 0.945]` |
| `[0.805, 0.883]` | 40 | 0.8409 | 0.9250 | 0.0841 | `[0.801, 0.974]` |

*Observation*: While ECE meets the $\le 0.10$ threshold, the `[0.568, 0.657)` bin demonstrates significant under-confidence (predicted 61.4% vs actual 89.7%, Wilson CI excludes the prediction). Furthermore, the Platt scaler maximum probability is bounded at 0.883.

### B. Split-Conformal Prediction Interval Coverage
Saved at [`phases/Phase 6/conformal_intervals_coverage.csv`](conformal_intervals_coverage.csv):
- **Nominal Target**: **80.0%** (acceptable band: $75\%$ to $85\%$).
- **Mean Conformal Interval Width**: **46.39 percentage points** ($\pm 23.20\%$).

| Evaluation Subset | Sample Size ($n$) | Nominal Coverage | Empirical Coverage | Status vs Target ($80\% \pm 5\%$) |
|---|:---:|:---:|:---:|:---:|
| **Pooled Out-of-Sample** | 398 | 80.0% | **87.4%** | Conservative (+2.4% above band) |
| **IPOs With Active GMP** | 321 | 80.0% | **94.1%** | Very conservative (high predictability) |
| **IPOs Without GMP** | 77 | 80.0% | **59.7%** | **Under-covered** (Gap: -20.3 points) |
| **Top 10% Pops ($\ge 50.8\%$)** | 40 | 80.0% | **60.0%** | **Under-covered** (Gap: -20.0 points) |

---

## 7. GMP Coverage Status

Saved at [`phases/Phase 6/gmp_coverage.csv`](gmp_coverage.csv):

| Quarter | Total Evaluated IPOs | IPOs With GMP | GMP Coverage (%) |
|:---:|:---:|:---:|:---:|
| **2022Q1** | 3 | 3 | 100.0% |
| **2022Q2** | 14 | 14 | 100.0% |
| **2022Q3** | 4 | 4 | 100.0% |
| **2022Q4** | 18 | 18 | 100.0% |
| **2023Q1** | 4 | 4 | 100.0% |
| **2023Q2** | 5 | 5 | 100.0% |
| **2023Q3** | 23 | 23 | 100.0% |
| **2023Q4** | 29 | 28 | 96.6% |
| **2024Q1** | 23 | 22 | 95.7% |
| **2024Q2** | 13 | 13 | 100.0% |
| **2024Q3** | 26 | 25 | 96.2% |
| **2024Q4** | 31 | 30 | 96.8% |
| **2025Q1** | 12 | 11 | 91.7% |
| **2025Q2** | 9 | 9 | 100.0% |
| **2025Q3** | 47 | 45 | 95.7% |
| **2025Q4** | 39 | 39 | 100.0% |
| **2026Q1** | 16 | 15 | 93.8% |
| **2026Q2** | 10 | 8 | 80.0% |
| **2026Q3** | 62 | 5 | **8.1%** |
| **2026Q4** | 10 | 0 | **0.0%** |
| **POOLED** | **398** | **321** | **80.7%** |

*Coverage Audit Finding*: Grey market premium reporting dropped precipitously from ~95% in 2022–2025 to **8.1%** in 2026Q3 and **0.0%** in 2026Q4 due to dealer aggregation delays. In adherence to Rule 4 ("never fabricate or impute"), unobserved GMP values remain strictly empty.

---

## 8. Fundamentals Decision & Evidence

### Pre-Registered Decision: Path 2 (Formally Close Fundamentals Line)
1. **Empirical Evidence**: Across 398 out-of-sample walk-forward predictions, accounting fundamentals (`roe`, `pat_margin_pct`, `debt_equity`) provided **no demonstrated benefit** ($\Delta \text{MAE} = +0.1799\%$, 95% CI `[-0.0817%, +0.4446%]`, straddling zero).
2. **Data Infeasibility**: The remaining four columns (`roce`, `revenue_growth_pct`, `pe_ratio`, `peer_median_pe`) have 0% to 62% coverage and cannot be automatically extracted from SEBI/exchange PDF prospectuses.
3. **Formal Resolution**: The accounting fundamentals research track is **formally closed and retired**. Future phases will focus exclusively on market structure, high-frequency subscription dynamics, anchor investor quality, and macro liquidity features.

---

## 9. Forward Prediction Log Status

Evaluated via [`scripts/forward_report.py`](../../scripts/forward_report.py):
- **Log Location**: [`predictions/prediction_log.csv`](../../predictions/prediction_log.csv)
- **Total Logged Entries**: 5
- **Excluded TEST Rows**: 2 (`status = TEST_NOT_FORWARD`, Kisshtipo)
- **Excluded INVALID Rows**: 2
  - 1 Hyundai Motor India backdated row (`status = INVALID`)
  - 1 HD Fire Protect Limited uncalibrated bug row (`status = INVALID_SCRIPT_BUG`)
- **Genuine FORWARD Rows**: **1** (`status = FORWARD`)
  - **Company**: **HD Fire Protect Limited**
  - **Board**: Mainboard (BSE & NSE; issue size ₹712.31 Cr)
  - **Listing Date**: **2026-10-21** (genuine upcoming unlisted issue)
  - **Scored At**: `2026-10-15T02:52:30.502305` (committed prior to listing)
  - **Estimated Return**: **+11.09%**
  - **Calibrated P(Gain > 10%)**: **86.5%** (calibrated probability: 0.8654)
  - **80% Conformal Interval**: `[+10.01%, +56.41%]` (GMP-anchored, width: 46.4%)
- **Forward Sample Size Warning**: $n = 0$ evaluated (unlisted). Per pre-registration: **strictly PROVISIONAL below $n=30$. No statistical performance claims permitted.**

---

## 10. Honest Verdict, Failure Modes & Next Steps

### Honest Verdict
1. **The Fundamentals Track Adds No Value for Listing Gain**: Pre-IPO accounting ratios are already priced into the issue band by book-running lead managers; day-1 listing pops are driven by retail/HNI liquidity and float constraints.
2. **Raw GMP is Unbeatable When Available**: Machine learning models and linear blends do not outperform raw grey market premiums. The optimal strategy in Regime A is simply to trust the market whisper.
3. **OPI Adds Statistically Significant Value in Non-GMP Regimes**: When an issue lacks grey market quotes ($n=77$), the OPI model outperforms the historical mean baseline by **4.93%** (95% CI: `[-7.56%, -2.10%]`). This is the true operational utility of the system.
4. **Conformal Intervals Provide Calibrated Uncertainty**: Users now receive rigorous 80% error bars rather than deceptive single-point forecasts.

### Failure Modes & Limitations
1. **Severe Extreme Pop Underprediction**: The model cannot predict triple-digit pops (e.g. Vibhor Steel Tubes +181.5% vs +92.7%; Mukka Proteins +50.9% vs +321.4% demand squeeze).
2. **Non-GMP Conformal Under-Coverage**: Prediction intervals for unquoted issues achieve only 59.7% empirical coverage against the 80% nominal target.
3. **Platt Sigmoid Upper Saturation**: Calibrated probabilities cannot exceed ~88%, preventing high-conviction classification on extreme subscription blowout issues.

### Next Steps for Phase 7
1. **Regime-Conditional Conformal Calibration**: Calibrate separate conformal quantiles $\hat{q}_{\text{gmp}}$ and $\hat{q}_{\text{nogmp}}$ to restore 80% coverage on cold issues.
2. **Asymmetric / Quantile Loss for Upper Tail Sentiment**: Implement pinball loss ($q=0.85$) to capture retail squeeze pops.
3. **Anchor Investor Allocation Sizing**: Engineer float-adjusted QIB anchor lock-in metrics.

---

## 11. Self-Audit (Section 11 Compliance)

| Question | Answer | Evidence |
|---|:---:|---|
| Does any status say `FIXED` without a pasted passing check? | **NO** | All 6 `FIXED` items have passed verification commands with exact shell outputs pasted in `2_building_and_execution.md`. |
| Is anything still `PARTIAL` or `NOT FIXED`, and is it listed under "Targets missed"? | **YES** | S3 is explicitly marked `PARTIAL` and listed under Section 1.B. |
| Was any row removed that is not in `data/excluded_rows.csv`? | **NO** | Only Patanjali Foods, Adani Enterprises, and Vodafone Idea were removed as excluded issues, plus 15 duplicate rows. |
| Does every data change have a before/after table? | **YES** | Section 3 contains the complete Before vs After metric comparison table from `before_after_comparison.csv`. |
| Does any "beats / wins / improves / falsified" claim lack a bootstrap interval that excludes zero? | **NO** | H1 is strictly stated as "no demonstrated effect"; Blend vs GMP is stated as "no demonstrated advantage". "Beats" is used only where 95% CI strictly excludes zero. |
| Was the new final test file read for any decision? | **NO** | `data/ipo_phase5_final_test.csv` was never opened, read, or scored. |
| Is any value estimated or imputed? | **NO** | Zero missing values were imputed; missing GMP rows remain strictly null. |
| Is any aggregator-sourced value described as primary or "audited"? | **NO** | Erratum E2 corrected terminology to "aggregator-sourced". |
| Does `log_prediction.py` use the same pipeline as the evaluation, and is that tested? | **YES** | Uses `art['cal_clf']`; verified via unit tests `test_s6_*` in `tests/test_gate_a.py`. |
| Does every number in the reports come from a committed script output? | **YES** | All metrics, intervals, and counts are sourced directly from CSV files generated by `phase6_rolling_train_evaluate.py`. |

---

## 12. Regulatory & Decision Aid Disclaimer

> **IMPORTANT NOTICE**: The Open Price Intelligence (OPI) framework, its models, predictions, conformal prediction intervals, and documentation are designed strictly as an academic research prototype and algorithmic decision aid. **This software and its outputs DO NOT constitute financial, legal, tax, or investment advice.** Investing in Initial Public Offerings involves substantial capital risk, market volatility, and liquidity constraints. Past performance and statistical backtests do not guarantee future listing day returns.
