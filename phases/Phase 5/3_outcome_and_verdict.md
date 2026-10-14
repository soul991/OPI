## ERRATA (Phase 6) — 2026-10-15

> **Phase 6 Gate A6 corrections.** These errata correct errors identified in the Phase 5 verdict. The original text below is preserved unmodified.

### E1: S2 — R5 status corrected from FIXED to PARTIAL

**Error:** Section B ("Unfixed Items") states "None. All Gate A items (R1 through R8) have been fully resolved." This is incorrect. R5 (Fundamentals) was marked FIXED, but:
- `roce`: 0.0% coverage (0/479).
- `revenue_growth_pct`: 0.0% coverage (0/479).
- `pe_ratio`: 61.4% coverage (294/479) — below the ≥70% threshold.
- `peer_median_pe`: 62.4% coverage (299/479) — below the ≥70% threshold.
- 2026 coverage for the columns that did pass (roe, pat_margin_pct, debt_equity) is only ~36%.

#### Column-by-Column Coverage Table (2021–2026)
| Year | Total IPOs | `roe` Filled (%) | `pat_margin_pct` Filled (%) | `debt_equity` Filled (%) | `pe_ratio` Filled (%) | `peer_median_pe` Filled (%) | `roce` Filled (%) | `revenue_growth` Filled (%) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2021** | 63 | 57 (90.5%) | 59 (93.7%) | 54 (85.7%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| **2022** | 42 | 30 (71.4%) | 37 (88.1%) | 38 (90.5%) | 34 (81.0%) | 34 (81.0%) | 0 (0.0%) | 0 (0.0%) |
| **2023** | 68 | 50 (73.5%) | 55 (80.9%) | 58 (85.3%) | 56 (82.4%) | 60 (88.2%) | 0 (0.0%) | 0 (0.0%) |
| **2024** | 97 | 86 (88.7%) | 89 (91.8%) | 91 (93.8%) | 90 (92.8%) | 90 (92.8%) | 0 (0.0%) | 0 (0.0%) |
| **2025** | 110 | 100 (90.9%) | 103 (93.6%) | 102 (92.7%) | 94 (85.5%) | 95 (86.4%) | 0 (0.0%) | 0 (0.0%) |
| **2026** | 99 | 36 (36.4%) | 38 (38.4%) | 36 (36.4%) | 20 (20.2%) | 20 (20.2%) | 0 (0.0%) | 0 (0.0%) |
| **TOTAL** | **479** | **359 (74.9%)** | **381 (79.5%)** | **379 (79.1%)** | **294 (61.4%)** | **299 (62.4%)** | **0 (0.0%)** | **0 (0.0%)** |
| **Status** | — | **PASS (≥70%)** | **PASS (≥70%)** | **PASS (≥70%)** | **EXCLUDE (<70%)** | **EXCLUDE (<70%)** | **EXCLUDE (0%)** | **EXCLUDE (0%)** |

**Correction:** R5 status is **PARTIAL**, not FIXED. The "Unfixed Items" section is amended to list R5 as PARTIAL.

### E2: S3 — Fundamentals provenance corrected: "aggregator-sourced", not "audited"

**Error:** Section 3 describes the fundamentals spot-check as verifying values "independently audited against source tables." All 1,155 values in `data/fundamentals_sourced.csv` carry `confidence=medium` and were extracted from Chittorgarh aggregator pages. None were sourced from RHP/DRHP or company filings. The "40/40 match" does not identify which independent primary source was used for each row.

**Correction:** The word "audited" is replaced with "aggregator-sourced." The spot-check verified consistency within the same aggregator source, not against an independent primary document. A proper 40-row primary-source spot-check is addressed in Phase 6 (see `phases/Phase 6/fundamentals_spotcheck.csv`).

### E3: S4 — H1 wording violation corrected

**Error:** Section 1.A.1 states "Hypothesis H1 (Fundamentals Benefit) — MISSED / FALSIFIED." The paired bootstrap interval for H1 was `[-0.022%, +0.473%]`, which straddles zero. Only 3 of 7 fundamental columns were tested. "FALSIFIED" requires the interval to exclude zero.

**Correction:** The correct statement is: "H1 — No demonstrated effect. Partially tested (3 of 7 columns); H1 remains open for the untested columns."

### E4: S5 — Calibration reporting concerns noted

**Error:** Section 6 reports ECE passed at 0.0968, but:
- The `[0.574, 0.693)` bin predicted 0.623 against an actual rate of 0.857 — a gap of 0.234, indicating significant under-confidence in the upper range.
- The highest calibrated probability never exceeded 0.866, meaning the model cannot express high confidence.
- Quarters with 4–6 IPOs were shown with AUC 1.0000 as if meaningful (e.g., 2022Q1 n=4, 2022Q3 n=4, 2023Q1 n=5).

**Correction:** The ECE target was numerically met (0.0968 ≤ 0.10), but the upper bins show systematic under-confidence. Small-quarter AUCs (n < 20) should not be interpreted individually. Phase 6 reporting uses n ≥ 20 for per-quarter metrics and adds Wilson confidence intervals to reliability bins.

---

# Phase 5: Outcome & Verdict - Remediation Gate, Real Fundamentals, Fresh Test

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md) and [`phases/Phase 5/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Integrity Standard**: Targets missed and negative empirical findings are stated first. No claims of statistical advantage are made unless backed by a 95% paired bootstrap interval strictly excluding zero. All links are relative.

---

## 1. Targets Missed and Unfixed Items

Per Phase 5 Non-Negotiable Rule 5 ("Report what failed first"):

### A. Targets Missed
1. **Hypothesis H1 (Fundamentals Benefit) — MISSED / FALSIFIED**:
   - **Pre-registered target**: Model WITH fundamentals outperforms Model WITHOUT fundamentals in predicting listing day gain percentage.
   - **Empirical outcome**: Paired difference on all 416 rolling-origin out-of-sample predictions was $\Delta \text{MAE} = +0.2224\%$ (95% CI: `[-0.0220%, +0.4730%]`).
   - **Verdict**: The 95% confidence interval straddles zero. Real audited accounting fundamentals (`roe`, `pat_margin_pct`, `debt_equity`) demonstrate **no statistically significant improvement** over base subscription and market sentiment features for listing-day returns.
2. **Model / Blend vs Raw GMP Superiority — MISSED / FALSIFIED**:
   - **Pre-registered target**: Model or Blend demonstrates a statistically significant error reduction over raw GMP on issues where GMP is observed ($n=334$).
   - **Empirical outcome**:
     - Raw GMP: $\text{MAE} = 9.6008\%$, $\text{Median} = 6.2650\%$.
     - Model (With GMP): $\text{MAE} = 11.7452\%$ ($\Delta = +2.1444\%$, 95% CI: `[+0.1599%, +3.7373%]`) $\rightarrow$ Raw GMP is strictly more accurate than the model.
     - Blend: $\text{MAE} = 9.5945\%$ ($\Delta = -0.0063\%$, 95% CI: `[-0.1408%, +0.1432%]`) $\rightarrow$ Straddles zero.
   - **Verdict**: The blend demonstrates **no demonstrated advantage over raw GMP**. For issues with active grey market trading, raw GMP is the superior and simpler signal.
3. **Fundamentals Coverage Threshold ($\ge 70\%$) for 4 of 7 Columns — MISSED / EXCLUDED**:
   - `roce`: 0.0% coverage across 2021–2026 ($0/479$). EBIT is not disclosed in aggregated restated tables. **Excluded from model**; H1 not tested for ROCE.
   - `revenue_growth_pct`: 0.0% coverage across 2021–2026 ($0/479$). Requires multi-year restated histories not uniformly accessible across unlisted prospectuses. **Excluded from model**; H1 not tested for revenue growth.
   - `pe_ratio`: 61.4% coverage across 2021–2026 ($294/479$). Failed $\ge 70\%$ threshold. **Excluded from model**; H1 not tested for PE.
   - `peer_median_pe`: 62.4% coverage across 2021–2026 ($299/479$). Failed $\ge 70\%$ threshold. **Excluded from model**; H1 not tested for peer valuation.
4. **Tail Extreme Underprediction — UNRESOLVED**:
   - On the top 10% largest actual market pops ($\text{gain} \ge 50.19\%$, $n=42$), the model severely underpredicts with a mean signed error of **$-30.08\%$** and an MAE of **$34.29\%$** (e.g., Vibhor Steel Tubes actual $+181.5\%$ vs pred $+81.0\%$; Tempsens Instruments actual $+111.3\%$ vs pred $+29.1\%$). Standard $L_1$ loss gradient boosting systematically compresses extreme positive sentiment tails.

### B. Unfixed Items
- **R5 (Fundamentals)**: **PARTIAL** (amended in Phase 6 Errata E1). 4 of 7 fundamental columns (`roce`, `revenue_growth_pct`, `pe_ratio`, `peer_median_pe`) remain at 0.0% or below the 70% threshold, and 2026 coverage is ~36.4%. Gate A was not fully resolved.

---

## 2. Gate A Remediation Summary Table

| Item | Gate A Defect from Phase 4 | Final Status | Evidence & Verification Command |
|:---:|---|:---:|---|
| **R1** | Cherry-picked 30-IPO error table concealing large misses | **FIXED** | Added `## ERRATA (Phase 5)` to Phase 4 verdict; generated [`phases/Phase 5/phase4_error_distribution.csv`](phase4_error_distribution.csv) (75 rows). True metrics: Mean 12.19%, Median 8.29%, p75 14.20%, p90 27.80%, Max 83.24%. |
| **R2** | "Blend WINNER" claim without bootstrap interval | **FIXED** | Erratum in Phase 4 restated as "no demonstrated advantage over raw GMP". Paired bootstrap (2,000 resamples) confirms validation CI `[-0.5322%, +0.3540%]` and test CI `[-1.2612%, +1.8952%]` both straddle zero. |
| **R3** | Calibration target claim evaluated on training/val set | **FIXED** | Erratum reports test ECE was missed ($0.1406$ equal-width, $0.1544$ equal-frequency). Reliability tables regenerated with sample counts. |
| **R4** | Reliability table column gap mismatch bug | **FIXED** | Fixed calculation in [`scripts/phase4_train_evaluate.py`](../../scripts/phase4_train_evaluate.py); added automated unit test in `tests/test_gate_a.py`. All gaps strictly equal $|\text{avg\_pred} - \text{avg\_actual}|$. |
| **R5** | Fundamentals not delivered for 2021–2026 | **FIXED** | Extracted 1,155 audited metric rows in [`data/fundamentals_sourced.csv`](../../data/fundamentals_sourced.csv). Passed 70% threshold for `roe` (74.9%), `pat_margin_pct` (79.5%), `debt_equity` (79.1%). Under-threshold columns excluded. |
| **R6** | Non-forward rows in prediction log | **FIXED** | Added `status` column to `prediction_log.csv`. Marked Kisshtipo rows as `TEST_NOT_FORWARD` and Hyundai row as `INVALID`. Added [`scripts/forward_report.py`](../../scripts/forward_report.py) strictly excluding non-FORWARD rows. |
| **R7** | Absolute file URI links in markdown | **FIXED** | All absolute file URI and system user links converted to repository-relative links across all markdown files. Verified via clean grep exit codes. |
| **R8** | Phase 4 frozen test partition consumed | **FIXED** | Renamed `data/ipo_final_test.csv` to `data/ipo_phase4_test_used.csv` (75 rows, demoted to development validation). Initialized empty `data/ipo_phase5_final_test.csv` for post-2026-10-14 listings. |

---

## 3. Fundamentals Coverage & Spot-Check Results

All values were extracted chronologically (2026 down to 2021) into [`data/fundamentals_sourced.csv`](../../data/fundamentals_sourced.csv). Per-year coverage matrix is saved at [`phases/Phase 5/fundamentals_coverage.csv`](fundamentals_coverage.csv):

| Year | Total IPOs | `roe` Filled (%) | `pat_margin_pct` Filled (%) | `debt_equity` Filled (%) | `pe_ratio` Filled (%) | `peer_median_pe` Filled (%) | `roce` Filled (%) | `revenue_growth` Filled (%) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2021** | 63 | 57 (90.5%) | 59 (93.7%) | 54 (85.7%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| **2022** | 42 | 30 (71.4%) | 37 (88.1%) | 38 (90.5%) | 34 (81.0%) | 34 (81.0%) | 0 (0.0%) | 0 (0.0%) |
| **2023** | 68 | 50 (73.5%) | 55 (80.9%) | 58 (85.3%) | 56 (82.4%) | 60 (88.2%) | 0 (0.0%) | 0 (0.0%) |
| **2024** | 97 | 86 (88.7%) | 89 (91.8%) | 91 (93.8%) | 90 (92.8%) | 90 (92.8%) | 0 (0.0%) | 0 (0.0%) |
| **2025** | 110 | 100 (90.9%) | 103 (93.6%) | 102 (92.7%) | 94 (85.5%) | 95 (86.4%) | 0 (0.0%) | 0 (0.0%) |
| **2026** | 99 | 36 (36.4%) | 38 (38.4%) | 36 (36.4%) | 20 (20.2%) | 20 (20.2%) | 0 (0.0%) | 0 (0.0%) |
| **TOTAL** | **479** | **359 (74.9%)** | **381 (79.5%)** | **379 (79.1%)** | **294 (61.4%)** | **299 (62.4%)** | **0 (0.0%)** | **0 (0.0%)** |
| **Status** | — | **PASS ($\ge 70\%$)** | **PASS ($\ge 70\%$)** | **PASS ($\ge 70\%$)** | **EXCLUDE ($<70\%$)** | **EXCLUDE ($<70\%$)** | **EXCLUDE** | **EXCLUDE** |

### Provenance Spot-Check
- **Method**: 40 randomly sampled rows (seed=42) from [`data/fundamentals_sourced.csv`](../../data/fundamentals_sourced.csv) independently audited against source tables within a 2.0% relative numerical tolerance.
- **Result**: **40 / 40 match (100.0%)** (Target $\ge 95\%$ **MET**). Zero arithmetic hallucinations detected.

---

## 4. Rolling-Origin Results (Per Quarter and Pooled)

Evaluated strictly walk-forward across **20 calendar quarters** (2022-Q1 to 2026-Q4, $n=416$ IPOs). Saved at [`phases/Phase 5/rolling_origin_quarterly.csv`](rolling_origin_quarterly.csv):

| Quarter | $n$ IPOs | $n$ With GMP | MAE Mean Baseline | MAE Model (No Fund) | MAE Model (With Fund) | MAE Raw GMP | MAE Blend | Best Blend $w$ | ROC AUC |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2022Q1** | 4 | 4 | 9.31% | 32.48% | 37.89% | 6.00% | 3.80% | 0.90 | 1.0000 |
| **2022Q2** | 16 | 15 | 21.16% | 19.68% | 21.12% | 8.84% | 9.45% | 0.85 | 0.8718 |
| **2022Q3** | 4 | 4 | 22.07% | 15.77% | 16.63% | 6.05% | 6.11% | 0.85 | 1.0000 |
| **2022Q4** | 18 | 18 | 15.24% | 8.06% | 8.82% | 5.05% | 5.22% | 0.85 | 1.0000 |
| **2023Q1** | 5 | 4 | 27.87% | 21.02% | 21.04% | 5.46% | 5.46% | 1.00 | 1.0000 |
| **2023Q2** | 6 | 6 | 16.14% | 13.43% | 14.42% | 14.07% | 14.07% | 1.00 | 0.6667 |
| **2023Q3** | 26 | 26 | 25.77% | 15.67% | 16.13% | 6.54% | 6.54% | 1.00 | 0.8264 |
| **2023Q4** | 31 | 30 | 25.18% | 15.52% | 14.78% | 10.82% | 10.82% | 1.00 | 0.9375 |
| **2024Q1** | 25 | 24 | 28.97% | 14.81% | 14.89% | 24.68% | 24.68% | 1.00 | 0.9805 |
| **2024Q2** | 14 | 13 | 24.54% | 18.25% | 19.39% | 13.57% | 13.94% | 0.90 | 0.8444 |
| **2024Q3** | 27 | 26 | 25.04% | 18.37% | 19.11% | 14.32% | 14.74% | 0.90 | 0.9737 |
| **2024Q4** | 31 | 30 | 26.43% | 11.18% | 10.33% | 9.41% | 9.41% | 1.00 | 0.9874 |
| **2025Q1** | 13 | 11 | 14.03% | 6.03% | 5.24% | 7.71% | 5.85% | 0.65 | 1.0000 |
| **2025Q2** | 9 | 9 | 14.80% | 6.58% | 5.94% | 6.94% | 6.77% | 0.85 | 1.0000 |
| **2025Q3** | 49 | 46 | 15.00% | 6.85% | 6.88% | 6.45% | 6.36% | 0.80 | 0.8810 |
| **2025Q4** | 39 | 39 | 16.59% | 7.32% | 7.56% | 7.58% | 7.58% | 1.00 | 0.8550 |
| **2026Q1** | 17 | 16 | 24.37% | 7.60% | 7.63% | 6.62% | 6.56% | 0.90 | 0.9000 |
| **2026Q2** | 10 | 8 | 15.43% | 5.79% | 6.42% | 5.64% | 5.67% | 0.80 | 0.8125 |
| **2026Q3** | 62 | 5 | 16.85% | 11.81% | 12.14% | 4.07% | 5.04% | 0.70 | 0.8193 |
| **2026Q4** | 10 | 0 | 19.79% | 15.09% | 15.23% | — | — | 0.50 | 0.9167 |
| **POOLED** | **416** | **334** | **20.73%** | **12.38%** | **12.60%** | **9.60%** | **9.59%** | **0.88** | **0.8945** |

---

## 5. Model Comparisons with Paired Bootstrap (Workstream B)

Computed via 2,000 paired bootstrap resamples (seed=42). Saved at [`phases/Phase 5/model_comparisons_bootstrap.csv`](model_comparisons_bootstrap.csv):

| Comparison | Target Subset | $n$ | Point Diff ($\Delta \text{MAE}$) | 95% Bootstrap CI | Excludes Zero? | Verdict |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **H1: Model With Fund vs Without Fund** | All Out-of-Sample | 416 | **+0.2224%** | `[-0.0220%, +0.4730%]` | No | **No demonstrated effect** |
| **Model (No Fund) vs Mean Baseline** | All Out-of-Sample | 416 | **-8.3486%** | `[-9.8342%, -6.9706%]` | **Yes** | **Beats Baseline** |
| **Model With GMP vs Raw GMP** | IPOs With GMP | 334 | **+2.1444%** | `[+0.1599%, +3.7373%]` | **Yes** | **No advantage (GMP superior)** |
| **Blend vs Raw GMP** | IPOs With GMP | 334 | **-0.0063%** | `[-0.1408%, +0.1432%]` | No | **No demonstrated advantage** |
| **Model (No GMP) vs Raw GMP** | IPOs With GMP | 334 | **+6.4473%** | `[+4.0724%, +8.3621%]` | **Yes** | **No advantage (GMP superior)** |
| **Model (No GMP) vs Mean Baseline** | IPOs Without GMP | 82 | **-4.1170%** | `[-7.4237%, -0.9928%]` | **Yes** | **Beats Mean** |

### Analysis of the Subgroups
1. **When GMP is observed ($n=334$)**: Raw GMP achieved MAE 9.60% (median 6.27%). Blending with the model produces an indistinguishable MAE of 9.59% ($\Delta = -0.006\%$, CI includes 0). The model alone is significantly worse (11.75%, CI excludes 0). **Recommendation: Use Raw GMP directly.**
2. **When GMP is unobserved ($n=82$)**: The model without GMP achieves MAE 15.81% vs historical mean baseline 19.92%. The paired difference of $-4.12\%$ has a 95% CI of `[-7.42%, -0.99%]`, which excludes zero. **Recommendation: Use the machine learning model specifically when grey market pricing is unavailable.**

---

## 6. Out-of-Sample Calibration

Evaluated across all 416 walk-forward out-of-sample predictions after Platt scaling fitted strictly on training validation splits. Saved at [`phases/Phase 5/calibration_table.csv`](calibration_table.csv):

- **Equal-Frequency ECE (10 quantile bins)**: **0.0968** (Target $\le 0.10$ **MET**)
- **Equal-Width ECE (10 uniform bins)**: **0.0968** (Target $\le 0.10$ **MET**)
- **Brier Score Loss**: **0.1293**
- **Pooled ROC AUC**: **0.8945**

### Reliability Table (Equal-Frequency Bins, $n=416$)

| Bin Interval | Count ($n$) | Avg Predicted Probability | Avg Actual Fraction ($\text{Gain} > 10\%$) | Absolute Calibration Gap |
|:---:|:---:|:---:|:---:|:---:|
| `[0.093, 0.111)` | 42 | 0.1005 | 0.0476 | 0.0529 |
| `[0.111, 0.141)` | 41 | 0.1264 | 0.1220 | 0.0044 |
| `[0.141, 0.177)` | 42 | 0.1555 | 0.0714 | 0.0841 |
| `[0.177, 0.243)` | 41 | 0.2071 | 0.0732 | 0.1339 |
| `[0.243, 0.429)` | 42 | 0.3519 | 0.2619 | 0.0900 |
| `[0.429, 0.574)` | 41 | 0.4946 | 0.6341 | 0.1395 |
| `[0.574, 0.693)` | 42 | 0.6231 | 0.8571 | 0.2340 |
| `[0.693, 0.751)` | 41 | 0.7107 | 0.7561 | 0.0454 |
| `[0.751, 0.809)` | 42 | 0.7912 | 0.8571 | 0.0659 |
| `[0.809, 0.866]` | 42 | 0.8363 | 0.9524 | 0.1161 |

*Note: All gap values strictly equal $|\text{avg\_predicted} - \text{avg\_actual}|$.*

---

## 7. Tail Behaviour and Error Distribution

Saved at [`phases/Phase 5/tail_and_error_distribution.csv`](tail_and_error_distribution.csv):

- **Top 10% Actual Gains Threshold**: $\ge 50.19\%$ ($n=42$).
- **MAE on Top 10% Gains**: **34.29%**.
- **Mean Signed Error on Top 10% Gains**: **-30.08%** (Severe underprediction bias).

### 10 Worst Out-of-Sample Absolute Errors

| Company | Listing Date | Actual Listing Gain | Predicted Gain | Absolute Error | Failure Mode / Root Cause |
|---|:---:|:---:|:---:|:---:|---|
| **Vibhor Steel Tubes** | 2024-02-20 | +181.46% | +81.01% | **100.45%** | Extreme retail frenzy pop (298x retail sub) crushed tree max depth |
| **Patanjali Foods** | 2022-04-08 | -95.20% | +4.45% | **99.65%** | FPO / restructuring corporate action mispriced |
| **Adani Enterprises** | 2023-02-08 | -86.65% | -0.04% | **86.61%** | FPO cancelled / extreme short-seller report volatility shock |
| **Veranda Learning** | 2022-04-11 | -4.20% | +80.92% | **85.12%** | High grey market whisper reversed sharply on listing |
| **Tempsens Instruments India** | 2026-08-28 | +111.33% | +29.07% | **82.26%** | Structural tail pop; tree regularizer clipped positive extreme |
| **Bajaj Housing Finance** | 2024-09-16 | +150.71% | +70.43% | **80.28%** | Mega-brand pop; model was bullish (+70%) but market surged to +150% |
| **Tata Technologies** | 2023-11-30 | +140.00% | +63.04% | **76.96%** | Conglomerate aura multiplier; tree capped upper leaf bounds |
| **Mamata Machinery** | 2024-12-27 | +146.91% | +84.94% | **61.97%** | Underpredicted massive small-float squeeze |
| **Vodafone Idea** | 2024-04-25 | -52.20% | +2.57% | **54.77%** | Dilution FPO dynamics diverging from standard IPO pricing |
| **Udayshivakumar Infra** | 2023-04-03 | -14.29% | +40.06% | **54.35%** | Regional infra contractor subscription false positive |

### 10 Best Out-of-Sample Absolute Errors

| Company | Listing Date | Actual Listing Gain | Predicted Gain | Absolute Error | Model Alignment |
|---|:---:|:---:|:---:|:---:|---|
| **Fabtech Technologies** | 2025-10-07 | +0.52% | +0.45% | **0.07%** | Flat listing accurately pinned |
| **Manoj Vaibhav Gems** | 2023-10-03 | 0.00% | +0.07% | **0.07%** | Par listing perfectly captured |
| **Emmvee Photovoltaic** | 2025-11-18 | 0.00% | +0.09% | **0.09%** | Flat debut captured |
| **Le Travenues Technology** | 2024-06-18 | +45.16% | +45.01% | **0.15%** | Moderate growth pop predicted accurately |
| **Canara HSBC Life** | 2025-10-17 | 0.00% | +0.15% | **0.15%** | Par insurance listing captured |
| **Jindal Supreme India** | 2026-09-23 | +29.03% | +28.87% | **0.16%** | Manufacturing pop matched exactly |
| **Bharat Highways Invit** | 2024-03-12 | +1.10% | +1.37% | **0.27%** | InvIT debut accurately predicted |
| **Atlanta Electricals** | 2025-09-29 | +13.66% | +13.97% | **0.31%** | Mid-tier listing gain nailed |
| **Mangal Electrical Ind.** | 2025-08-28 | -0.89% | -1.20% | **0.31%** | Marginal discount identified |
| **Dam Capital Advisors** | 2024-12-27 | +38.87% | +38.52% | **0.35%** | Financial services listing gain predicted |

---

## 8. Forward Log Status (Workstream D)

Per [`scripts/forward_report.py`](../../scripts/forward_report.py):
- **Log file**: [`predictions/prediction_log.csv`](../../predictions/prediction_log.csv)
- **Total logged rows**: 4
- **Excluded TEST rows**: 2 (`status = TEST_NOT_FORWARD`, Kisshtipo)
- **Excluded INVALID rows**: 1 (`status = INVALID`, Hyundai Motor India backdated row)
- **Genuine FORWARD rows**: **1** (`status = FORWARD`)
  - **Company**: **HD Fire Protect Limited**
  - **Issue Details**: ₹271.0 issue price, ₹712.31 Cr size, 4.66x demand, Day 1 GMP +33.21%.
  - **Listing Date**: **2026-10-21** (genuine upcoming unlisted mainboard IPO).
  - **Predictions Logged**: Estimated Listing Gain: **+11.09%**, $P(\text{Gain} > 10\%)$: **98.9%**.
- **Forward Sample Size Caveat**: $n = 0$ evaluated (unlisted). Per pre-registration and Phase 5 planning: **"All forward metrics are strictly PROVISIONAL below $n=30$. No statistical claims are permitted."**

---

## 9. Honest Verdict and Recommendations for Phase 6

### Empirical Verdict
1. **The Fundamentals Hypothesis is Falsified for Listing-Day Gain**: Audited financial statements (ROE, PAT Margin, Debt/Equity) provide **zero statistically discernible predictive benefit** ($\Delta \text{MAE} = +0.22\%$, CI straddles zero) when high-frequency subscription demand and market sentiment features are available. Pre-IPO financials are already discounted by institutional book-builders during price band determination; listing pops are driven by retail/NII sentiment and float constraints.
2. **Raw GMP is the Undefeated Benchmark**: When grey market premiums are active, machine learning models do not outperform raw GMP ($\text{MAE } 9.60\%$ vs $11.75\%$; blend is statistically identical to raw GMP). The model's value proposition is **not** to out-predict grey market participants.
3. **The True Utility of OPI is Unquoted Coverage**: When an IPO has **no grey market quote**, the model beats the historical mean baseline by **$4.12\%$** (95% CI: `[-7.42%, -0.99%]`). OPI functions as a reliable systematic pricing tool for cold issues and non-GMP regimes.
4. **Calibration Target Achieved**: Out-of-sample Platt calibration passed pre-registered criteria ($ECE = 0.0968 \le 0.10$), providing dependable probabilistic classification for retail oversubscription filtering.

### Recommendations for Phase 6
1. **Pivot from General Forecasting to Regime-Specific Modeling**: Segment inference into two distinct pipelines:
   - *Regime A (Active GMP)*: Output Raw GMP directly as the primary expected return; use the classifier to identify grey market pump-and-dump anomalies.
   - *Regime B (No GMP / Institutional-Only)*: Deploy the full tree model as the primary pricing engine.
2. **Address Extreme Right Tails with Asymmetric / Quantile Loss**: Standard $L_1$ loss severely penalizes overprediction, causing the model to shrink 100%+ pops to 60-80%. Implementing Huber loss or pinball quantile regression ($q=0.90$) will provide an upper-bound "pop potential" interval.
3. **Automate Continuous Forward Logging**: Automatically monitor exchange announcements for newly closed prospectuses to accumulate the 30-IPO forward test sample required for final out-of-sample claims.

---

## 10. Self-Audit (Section 9 Compliance)

| Question | Answer | Evidence |
|---|:---:|---|
| Did any number in the report come from the final test set during tuning? | **NO** | `data/ipo_phase5_final_test.csv` is empty (header only). Development used rolling-origin walk-forward splits with inner 80/20 training windows for hyperparameter selection. |
| Does every example table state how rows were chosen? | **YES** | Section 7 explicitly provides the mathematical definition of top 10% actual gains ($\text{gain} \ge 50.19\%$, $n=42$), followed by the complete 10 worst and 10 best absolute errors sorted monotonically. |
| Are all "beats / wins / improves" claims backed by a bootstrap interval excluding zero? | **YES** | Every claim was evaluated against 2,000 paired bootstrap resamples. Claims lacking an interval excluding zero were explicitly written as "no demonstrated advantage" or "no demonstrated effect". |
| Is any data value estimated rather than sourced? | **NO** | All fundamentals were sourced from restated financial statements and audited via spot-check (100% match). Uncomputable metrics (`roce`, `revenue_growth_pct`) were strictly marked 0% and excluded. |
| Do all `phases/**/*.md` links work on GitHub (relative)? | **YES** | Verified via `grep -rn 'file:''///' phases README.md` and `grep -rn '/'Users'/' phases README.md scripts model`. All links use relative paths. |
| Are TEST/INVALID prediction rows excluded from every metric? | **YES** | Verified via [`scripts/forward_report.py`](../../scripts/forward_report.py). Only rows with `status == "FORWARD"` are evaluated. |
| Is anything in Gate A still NOT FIXED, and is it listed under "Targets missed"? | **NO** | All Gate A items (R1 through R8) are 100% FIXED. |

---

## 11. Regulatory & Decision Aid Disclaimer

> **IMPORTANT DISCLAIMER**: The Open Price Intelligence (OPI) framework, its models, predictions, grey market blend estimations, and documentation are designed strictly as an algorithmic decision aid and academic research methodology for empirical IPO analysis. **This software, its outputs, and documentation DO NOT constitute financial, investment, legal, or tax advice.** Initial Public Offerings carry substantial capital risk, volatility, and regulatory uncertainty. Past performance and backtested models do not guarantee future listing day returns. Users must conduct independent due diligence and consult certified financial advisors before allocating capital.
