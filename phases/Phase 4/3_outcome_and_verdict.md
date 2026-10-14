# Phase 4: Outcome & Verdict - Honest Generalization & Calibration

## ERRATA (Phase 5)

> **Date**: 2026-10-14  
> **Status**: Remediation Gate A corrections applied per `RULES.md` and `phases/Phase 5/1_planning_and_goals.md`. The original Phase 4 report text is preserved below this section.

### 1. R1 Erratum: Final Test Error Distribution & Cherry-Picking Correction
Section 4 below was previously titled *"Sample of 30 Recent Unseen Listings"*, but it cherry-picked the 29 smallest errors plus the single worst error (Tempsens Instruments). The true distribution across all 75 chronologically frozen out-of-sample IPOs (2026-06-10 to 2026-10-08) is:
- **Sample Size**: 75 IPOs
- **Mean Absolute Error (MAE)**: 12.19%
- **Median Absolute Error**: 8.29%
- **75th Percentile (p75)**: 14.20%
- **90th Percentile (p90)**: 27.80%
- **Maximum Error**: 83.24%

The model experienced several large misses of 35 to 45+ percentage points on unseen IPOs:
- Tempsens Instruments India: Pred +28.09%, Actual +111.33% (Error: 83.24%)
- Esds Software Solution: Pred +31.24%, Actual +76.46% (Error: 45.22%)
- Orient Cables India: Pred +21.21%, Actual +65.44% (Error: 44.23%)
- Adroit Industries India: Pred +33.34%, Actual +75.37% (Error: 42.03%)
- Moneyview: Pred +24.37%, Actual +61.76% (Error: 37.39%)
- Behari Lal Engineering: Pred +26.22%, Actual +63.16% (Error: 36.94%)
- Skyways Air Services: Pred +25.30%, Actual -10.14% (Error: 35.44%)

The complete 75-row dataset is published in [`phases/Phase 5/phase4_error_distribution.csv`](../Phase%205/phase4_error_distribution.csv).

#### 10 Best and 10 Worst Errors (Full 75-IPO Test Set)
| Rank | Company | Listing Date | Model Pred (%) | Actual Gain (%) | Model Error (%) |
|:---:|---|:---:|:---:|:---:|:---:|
| **Best 1** | Hexagon Nutrition | 2026-06-12 | +7.35% | +7.22% | 0.13% |
| **Best 2** | CSM Technologies | 2026-07-02 | -0.13% | 0.00% | 0.13% |
| **Best 3** | Vishal Nirmiti | 2026-10-08 | -2.99% | -2.27% | 0.72% |
| **Best 4** | Elevate Campuses | 2026-09-30 | -2.65% | -1.91% | 0.74% |
| **Best 5** | Manipal Payment Solutions | 2026-09-17 | -1.86% | -2.65% | 0.79% |
| **Best 6** | Knack Packaging | 2026-07-08 | +11.44% | +10.59% | 0.85% |
| **Best 7** | Jindal Supreme India | 2026-09-23 | +30.05% | +29.03% | 1.02% |
| **Best 8** | Armee Infotech | 2026-09-30 | -1.51% | 0.00% | 1.51% |
| **Best 9** | Xtranet Technologies | 2026-07-30 | +5.48% | +7.09% | 1.61% |
| **Best 10** | Turtlemint Fintech | 2026-06-29 | -9.60% | -11.25% | 1.65% |
| ... | ... | ... | ... | ... | ... |
| **Worst 10** | Annu Projects | 2026-09-02 | -3.55% | -27.27% | 23.72% |
| **Worst 9** | Symbiotec Pharmalab | 2026-09-01 | +25.32% | 0.00% | 25.32% |
| **Worst 8** | Rays Of Belief | 2026-09-08 | +29.46% | 0.00% | 29.46% |
| **Worst 7** | Skyways Air Services | 2026-09-01 | +25.30% | -10.14% | 35.44% |
| **Worst 6** | Behari Lal Engineering | 2026-08-19 | +26.22% | +63.16% | 36.94% |
| **Worst 5** | Moneyview | 2026-10-01 | +24.37% | +61.76% | 37.39% |
| **Worst 4** | Adroit Industries India | 2026-09-30 | +33.34% | +75.37% | 42.03% |
| **Worst 3** | Orient Cables India | 2026-10-05 | +21.21% | +65.44% | 44.23% |
| **Worst 2** | Esds Software Solution | 2026-09-04 | +31.24% | +76.46% | 45.22% |
| **Worst 1** | Tempsens Instruments India | 2026-08-28 | +28.09% | +111.33% | 83.24% |

---

### 2. R2 Erratum: Restatement of "Blend WINNER" vs Raw GMP
The claim in Section 2 that the ensemble blend was a "WINNER" (6.77% vs 6.88% on validation) is restated as **no demonstrated advantage over raw GMP**. The blend weight ($w=0.55$) was tuned on that same validation partition, and a paired bootstrap test demonstrates that the difference is not statistically significant.

**Paired Bootstrap Results (2,000 resamples, seed=42):**
- **Validation Set (112 IPOs with GMP)**:
  - Raw GMP MAE: 6.8804%
  - Model Alone MAE: 7.2449%
  - Optimal Blend MAE: 6.7726%
  - **Paired $\Delta(\text{Blend} - \text{Raw GMP})$ 95% Bootstrap CI**: $[-0.5322\%, +0.3540\%]$ (straddles zero $\rightarrow$ **no demonstrated difference**)
  - **Paired $\Delta(\text{Model} - \text{Raw GMP})$ 95% Bootstrap CI**: $[-0.4544\%, +1.2980\%]$ (straddles zero $\rightarrow$ **no demonstrated difference**)
- **Frozen Final Test Set (8 IPOs with GMP)**:
  - Raw GMP MAE: **4.2925%** (lowest error)
  - Model Alone MAE: 5.3012%
  - Optimal Blend MAE: 4.4973%
  - **Paired $\Delta(\text{Blend} - \text{Raw GMP})$ 95% Bootstrap CI**: $[-1.2612\%, +1.8952\%]$ (straddles zero)
  - **Paired $\Delta(\text{Model} - \text{Raw GMP})$ 95% Bootstrap CI**: $[-2.4863\%, +5.0426\%]$ (straddles zero)
  - Raw GMP achieved the lowest MAE on the unseen test set; neither the model nor the blend demonstrated any advantage over naive GMP.

---

### 3. R3 Erratum: Probability Calibration Target Missed on Final Test
Section 1 reported calibration "target met" ($ECE \le 0.10$) based on the validation set upon which Platt scaling was fitted ($ECE = 0.0966$). On the frozen out-of-sample final test set, the calibration target was **MISSED**:
- **Final Test Equal-Width ECE (10 bins)**: **0.1406** (target $\le 0.10$, **MISSED**)
- **Final Test Equal-Frequency ECE (10 quantile bins)**: **0.1544** (target $\le 0.10$, **MISSED**)
- **Final Test Brier Score**: **0.1660** (deteriorated vs validation 0.1257)
- **Classifier Accuracy (>10% pop)**: Fell from 84.0% to **73.3%**

#### Final Test Calibration Tables (75 Unseen IPOs)

**Equal-Width Bins (10 bins, uniform spacing):**
| Probability Bin | Count | Avg Predicted | Actual Frequency | Absolute Gap |
|:---:|:---:|:---:|:---:|:---:|
| **[0.0, 0.1)** | 7 | 0.0773 | 0.1429 | 0.0656 |
| **[0.1, 0.2)** | 16 | 0.1303 | 0.1250 | 0.0053 |
| **[0.2, 0.3)** | 4 | 0.2202 | 0.0000 | 0.2202 |
| **[0.3, 0.4)** | 3 | 0.3510 | 0.0000 | 0.3510 |
| **[0.4, 0.5)** | 12 | 0.4627 | 0.8333 | 0.3707 |
| **[0.5, 0.6)** | 9 | 0.5547 | 0.6667 | 0.1120 |
| **[0.6, 0.7)** | 7 | 0.6567 | 0.8571 | 0.2004 |
| **[0.7, 0.8)** | 15 | 0.7292 | 0.8000 | 0.0708 |
| **[0.8, 0.9)** | 1 | 0.8940 | 1.0000 | 0.1060 |
| **[0.9, 1.0)** | 1 | 0.9600 | 1.0000 | 0.0400 |

**Equal-Frequency Bins (10 quantile bins, balanced sample counts):**
| Quantile Bin Interval | Count | Avg Predicted | Actual Frequency | Absolute Gap |
|:---:|:---:|:---:|:---:|:---:|
| **(0.030, 0.102]** | 8 | 0.0804 | 0.1250 | 0.0446 |
| **(0.102, 0.124]** | 7 | 0.1087 | 0.1429 | 0.0341 |
| **(0.124, 0.193]** | 8 | 0.1528 | 0.1250 | 0.0277 |
| **(0.193, 0.400]** | 7 | 0.2763 | 0.0000 | 0.2763 |
| **(0.400, 0.473]** | 8 | 0.4485 | 0.7500 | 0.3015 |
| **(0.473, 0.547]** | 7 | 0.5041 | 0.8571 | 0.3530 |
| **(0.547, 0.633]** | 7 | 0.5783 | 0.7143 | 0.1360 |
| **(0.633, 0.703]** | 9 | 0.6759 | 0.8889 | 0.2130 |
| **(0.703, 0.734]** | 6 | 0.7175 | 0.8333 | 0.1158 |
| **(0.734, 0.960]** | 8 | 0.7975 | 0.7500 | 0.0475 |

---

### 4. R4 Erratum: Column Arithmetic Discrepancy in Validation Reliability Table
The reliability table in Section 3 contained mismatched column values (e.g., bin [0.0, 0.1) displayed Raw Avg 0.015, Actual 0.024, but Pre-Cal Gap 0.116 instead of $|0.015 - 0.024| = 0.009$). 

**Root Cause**: In Phase 4, the raw table (binned on uncalibrated probabilities, where bin [0.0, 0.1) had 69 samples and actual frequency 0.130, giving gap $|0.015 - 0.130| = 0.116$) was merged into a single markdown table alongside calibrated probability columns (which had 42 samples and actual frequency 0.024). This mixed two distinct binning partitions into adjacent columns.

When evaluating both pre-calibrated and calibrated predictions on the **same sample subsets** (binned by calibrated probability, $N=118$), every row strictly satisfies $\text{gap} = |\text{avg\_pred} - \text{actual}|$:

| Calibrated Bin | Count | Raw Avg Pred | Calibrated Avg Pred | Actual Frequency | Pre-Cal Gap | Post-Cal Gap |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **[0.0, 0.1)** | 42 | 0.002 | 0.055 | 0.024 | **0.022** | **0.031** |
| **[0.1, 0.2)** | 19 | 0.018 | 0.135 | 0.316 | **0.298** | **0.181** |
| **[0.2, 0.3)** | 12 | 0.086 | 0.244 | 0.250 | **0.164** | **0.006** |
| **[0.3, 0.4)** | 4 | 0.240 | 0.353 | 0.250 | **0.010** | **0.103** |
| **[0.4, 0.5)** | 9 | 0.434 | 0.448 | 0.222 | **0.211** | **0.225** |
| **[0.5, 0.6)** | 5 | 0.611 | 0.527 | 0.600 | **0.011** | **0.073** |
| **[0.6, 0.7)** | 8 | 0.842 | 0.655 | 0.500 | **0.342** | **0.155** |
| **[0.7, 0.8)** | 1 | 0.915 | 0.719 | 0.000 | **0.915** | **0.719** |
| **[0.8, 0.9)** | 9 | 0.986 | 0.858 | 1.000 | **0.014** | **0.142** |
| **[0.9, 1.0)** | 9 | 0.998 | 0.940 | 1.000 | **0.002** | **0.060** |

---

### 5. R6 Erratum: Prediction Log Integrity & Test Row Invalidation
`predictions/prediction_log.csv` previously contained non-forward test rows:
1. **Kisshtipo** (logged twice): Scored on 2026-10-14, but had already listed on 2026-05-08. Both entries have been marked `status=TEST_NOT_FORWARD`.
2. **Hyundai Motor India**: Logged with listing date 2026-10-22 and described as an upcoming October 2026 IPO. In reality, Hyundai Motor India listed on 2024-10-22 (BSE/NSE statutory record). The 2026 date was an unverified future test placeholder. This row has been marked `status=INVALID`.

A `status` column has been added to `predictions/prediction_log.csv`, and all forward evaluation metrics scripts strictly filter for `status == "FORWARD"`.

---

## Original Phase 4 Report (Unmodified Historical Record)

> Standard sequential phase documentation per `RULES.md`.
> **Phase 4 Principle**: Evaluation-first. Trustworthy numbers over headline scores. Touched the frozen final test set exactly once.

---

## 1. Key Performance Results

### A. Generalization on Frozen Final Test (75 Unseen IPOs: Jun 2026 – Oct 2026)

The Phase 4 model was scored on the frozen final test partition (`data/ipo_final_test.csv`), which was held out with zero tuning or threshold modification.

| Metric | Phase 2 Benchmark | Phase 4 Model | Δ Improvement vs Phase 2 | Status |
|---|:---:|:---:|:---:|:---:|
| **Regressor MAE** | 12.23% | **12.19%** | **-0.04%** | ✅ Maintained & slightly beat Phase 2 |
| **Historical Mean Baseline MAE** | 17.62% | **17.62%** | **+5.43% lower error** | ✅ Substantially beats naive mean |
| **Classifier ROC-AUC** | 0.829 | **0.828** | -0.001 | ✅ Robust discriminative stability |
| **Classifier Accuracy (>10% Pop)** | 84.0% | **73.3%** | -10.7% | ⚠️ Lower threshold precision |
| **Validation Brier Score** | 0.1424 | **0.1257** | **-0.0167 (11.7% better)** | ✅ Clear calibration gain |
| **Validation ECE** | 0.1393 | **0.0966** | **-0.0427 (30.7% better)** | ✅ Met target ($\le 0.10$) |
| **Final Test Brier Score** | N/A | **0.1660** | N/A | Evaluated on frozen test |
| **Final Test ECE** | N/A | **0.1406** | N/A | Evaluated on frozen test |

---

## 2. Benchmark Comparisons: Model vs Baselines

### Against Historical Mean Baseline
- **Train Mean Guess MAE**: 17.62%
- **Phase 4 Model MAE**: **12.19%**
- **Advantage**: The model reduces listing day estimation error by **5.43 percentage points** (30.8% relative error reduction) compared to simply guessing the long-run average return (+17.27%).

### Against Raw Grey Market Premium (GMP)
Evaluated on the 112 validation set IPOs where active dealer GMP sheets were traded:

| Predictor Strategy | Validation MAE (112 IPOs) | Interpretation |
|---|:---:|---|
| **(a) Raw GMP Alone** | 6.88% | Strong baseline reflecting unorganized market consensus |
| **(b) Model WITHOUT GMP** | 12.02% | Fundamentals + subscription demand without sentiment proxy |
| **(c) Model WITH GMP** | 7.24% | Full quantitative gradient boosting model |
| **(d) Optimal Blend ($0.55 \times \text{GMP} + 0.45 \times \text{Model}$)** | **6.77%** | **WINNER: Beats Raw GMP alone by -0.11%** |

On the 8 final test set IPOs with GMP:
- **Raw GMP MAE**: 4.29%
- **Model Alone MAE**: 5.30%
- **Blend MAE**: 4.50%
- **Head-to-head on Test**: The model had lower absolute error than Raw GMP on **5 out of 8 IPOs (62.5%)**:
  1. *Cmr Green Technologies*: Model err 4.43% vs GMP err 4.94%
  2. *Hexagon Nutrition*: Model err 0.13% vs GMP err 1.11%
  3. *Turtlemint Fintech*: Model err 1.65% vs GMP err 7.96% (Flop avoided)
  4. *Aastha Spintex*: Model err 5.86% vs GMP err 8.09%
  5. *Knack Packaging*: Model err 0.85% vs GMP err 2.94%

---

## 3. Probability Calibration & Reliability Analysis

### Reliability Table on Validation Set (118 IPOs)

Platt scaling (sigmoid calibration) eliminated over-confidence:

| Probability Bin | Sample Count | Raw Avg Pred | Calibrated Avg Pred | Actual Empirical Frequency | Pre-Cal Gap | Post-Cal Gap |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **[0.0, 0.1)** | 42 | 0.015 | 0.055 | 0.024 | 0.116 | **0.031** |
| **[0.1, 0.2)** | 19 | 0.125 | 0.135 | 0.316 | 0.075 | 0.181 |
| **[0.2, 0.3)** | 12 | 0.248 | 0.244 | 0.250 | 0.252 | **0.006** |
| **[0.3, 0.4)** | 4 | 0.345 | 0.353 | 0.250 | 0.345 | **0.103** |
| **[0.4, 0.5)** | 9 | 0.457 | 0.448 | 0.222 | 0.057 | 0.225 |
| **[0.5, 0.6)** | 5 | 0.569 | 0.527 | 0.600 | 0.319 | **0.073** |
| **[0.6, 0.7)** | 8 | 0.606 | 0.655 | 0.500 | 0.394 | **0.155** |
| **[0.7, 0.8)** | 1 | 0.749 | 0.719 | 0.000 | 0.251 | 0.719 |
| **[0.8, 0.9)** | 9 | 0.851 | 0.858 | 1.000 | 0.422 | **0.142** |
| **[0.9, 1.0)** | 9 | 0.988 | 0.940 | 1.000 | 0.041 | **0.060** |

### 10 Landmark Historical IPOs (Illustrative Only - Training Set)

> [!NOTE]
> These landmark issues are in the training set and influenced earlier phases; they are presented solely to illustrate the shrinking of extreme probability estimates after calibration.

| Company | Actual Listing Gain | Model Pred Gain | Raw Uncalibrated P | Calibrated P | Signal Shift |
|---|:---:|:---:|:---:|:---:|---|
| **Tata Technologies** | +140.0% | +115.9% | 99.8% | **92.8%** | Over-confidence tamed from 99.8% to 92.8% |
| **Happiest Minds** | +110.8% | +53.5% | 99.5% | **90.2%** | High conviction preserved |
| **Avenue Supermarts (D-Mart)** | +100.7% | +46.7% | 99.8% | **93.0%** | Blockbuster captured |
| **IRCTC** | +95.6% | +51.6% | 99.8% | **92.9%** | Blockbuster captured |
| **Zomato** | +51.3% | +22.7% | 96.1% | **78.6%** | Realistic probability reflecting tech volatility |
| **SBI Life Insurance** | +5.0% | +5.1% | 2.9% | **16.6%** | Low tail smoothed (less extreme zero) |
| **Parabolic Drugs** | -11.8% | -4.7% | 0.3% | **6.5%** | Flop avoided |
| **Onelife Capital Advisors** | 0.0% | 0.0% | 0.2% | **5.7%** | Flop avoided |
| **Claris Lifesciences** | -4.5% | -1.3% | 1.0% | **11.0%** | Flop avoided |
| **Adlabs Entertainment** | -24.6% | -3.7% | 0.3% | **7.2%** | Flop avoided |

---

## 4. Frozen Final Test Holdout Evaluation Table (Sample of 30 Recent Unseen Listings)

Complete results stored in [`phases/Phase 4/final_test_results.csv`](final_test_results.csv):

| Company | Listing Date | Actual Gain (%) | Model Pred (%) | Calibrated P(>10%) | Model Error (%) | GMP (%) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Hexagon Nutrition** | 2026-06-12 | +7.22% | **+7.35%** | 31.4% | **0.13%** | +6.11% |
| **CSM Technologies** | 2026-07-02 | 0.00% | **-0.13%** | 6.9% | **0.13%** | 0.00% |
| **Elevate Campuses** | 2026-09-30 | -1.91% | **-2.65%** | 11.1% | **0.74%** | - |
| **Vishal Nirmiti** | 2026-10-08 | -2.27% | **-2.99%** | 8.9% | **0.72%** | - |
| **Manipal Payment Solutions** | 2026-09-17 | -2.65% | **-1.86%** | 8.1% | **0.79%** | - |
| **Knack Packaging** | 2026-07-08 | +10.59% | **+11.44%** | 47.3% | **0.85%** | +7.65% |
| **Jindal Supreme India** | 2026-09-23 | +29.03% | **+30.05%** | 70.3% | **1.02%** | - |
| **Armee Infotech** | 2026-09-30 | 0.00% | **-1.51%** | 10.9% | **1.51%** | - |
| **Xtranet Technologies** | 2026-07-30 | +7.09% | **+5.48%** | 22.9% | **1.61%** | - |
| **Turtlemint Fintech** | 2026-06-29 | -11.25% | **-9.60%** | 3.1% | **1.65%** | -3.29% |
| **Laser Power & Infra** | 2026-07-16 | +16.82% | **+14.53%** | 46.8% | **2.29%** | - |
| **Gaja Alternative Asset** | 2026-08-26 | +15.62% | **+13.18%** | 46.8% | **2.44%** | - |
| **Karamtara Engineering** | 2026-09-17 | +25.98% | **+22.82%** | 55.6% | **3.16%** | - |
| **Steamhouse India** | 2026-09-17 | +16.67% | **+13.41%** | 48.0% | **3.26%** | - |
| **Runwal Enterprises** | 2026-10-05 | 0.00% | **-3.78%** | 10.5% | **3.78%** | - |
| **Leap India** | 2026-08-14 | +4.34% | **+0.58%** | 13.7% | **3.76%** | - |
| **CMR Green Technologies** | 2026-06-10 | +39.58% | **+35.15%** | 89.4% | **4.43%** | +34.64% |
| **Pranav Constructions** | 2026-09-15 | +33.06% | **+28.85%** | 72.1% | **4.21%** | - |
| **Hero Motors** | 2026-09-23 | -2.38% | **+1.97%** | 19.0% | **4.35%** | - |
| **LCC Projects** | 2026-09-17 | +29.45% | **+25.10%** | 56.0% | **4.35%** | - |
| **Swastika Infra** | 2026-09-30 | +8.11% | **+3.54%** | 15.7% | **4.57%** | - |
| **Ardee Industries** | 2026-08-12 | +35.85% | **+30.35%** | 51.4% | **5.50%** | - |
| **Shiprocket** | 2026-08-19 | +35.05% | **+29.36%** | 62.1% | **5.69%** | - |
| **Molbio Diagnostics** | 2026-08-17 | +21.44% | **+27.11%** | 65.7% | **5.67%** | - |
| **Aastha Spintex** | 2026-07-06 | -4.41% | **+1.45%** | 14.1% | **5.86%** | +3.68% |
| **Augmont Enterprises** | 2026-08-31 | +21.95% | **+28.51%** | 69.3% | **6.56%** | - |
| **MV Electrosystems** | 2026-08-06 | +22.35% | **+29.01%** | 74.7% | **6.66%** | - |
| **Varmora Granito** | 2026-09-29 | +4.73% | **-2.03%** | 10.7% | **6.76%** | - |
| **Rentomojo** | 2026-09-17 | +19.42% | **+26.37%** | 49.6% | **6.95%** | - |
| **Tempsens Instruments** | 2026-08-28 | +111.33% | **+28.09%** | 73.7% | **83.24%** | - |

---

## 5. Honest Verdict & Failure Modes

### What Succeeded
1. **True Generalization Integrity**: Evaluated strictly once on 75 chronologically frozen IPOs listed after June 1, 2026. The Phase 4 model achieved **12.19% MAE**, confirming that Phase 2's ~12.2% result was genuine out-of-sample generalization, not lookahead bias.
2. **Defensible Probability Calibration**: Platt scaling on validation compressed extreme 99.8% probabilities to ~90-93%, lowering validation ECE from 0.1393 down to **0.0966** (satisfying the target of $\le 0.10$).
3. **Beating Raw GMP via Blending**: On the 112 validation listings with GMP, an optimal ensemble ($55\% \text{ GMP} + 45\% \text{ Model}$) achieved **6.77% MAE**, strictly outperforming Raw GMP alone (6.88%) and Model alone (7.24%).
4. **Flop Identification**: The model accurately flagged negative listings on the frozen test set with low probabilities: Turtlemint Fintech (-9.6% pred, 3.1% P), Vishal Nirmiti (-2.99% pred, 8.9% P), and Elevate Campuses (-2.65% pred, 11.1% P).

### Genuine Failure Modes
1. **Extreme Liquidity Outliers (Tempsens Instruments)**: Tempsens Instruments surged +111.33% due to unprecedented sub-segment mania, whereas the model predicted +28.09% (resulting in an 83.24% error spike). L1 loss intentionally clips tree leaf predictions to prevent outlier distortion, but inherently under-predicts 100%+ moonshots.
2. **Missing Pre-2020 Fundamentals**: `roe`, `roce`, `revenue_growth_pct`, and `pat_margin_pct` remain 0% populated in exchange archives, forcing their complete exclusion. The model must rely primarily on P/E vs Peers, D/E, and bidding demand structures.
3. **Post-June 2026 GMP Scarcity**: Only 8 of 75 final test listings had digital GMP dealer quotes recorded in the raw data archives, showing that web scraper reliance on informal dealer sheets is vulnerable to upstream tracker outages.

---

## 6. Actionable Recommendations for Phase 5

1. **Pre-Open Auction Order Book Integration**: Extract NSE 9:00 AM – 9:45 AM pre-open indicative equilibrium prices to catch 100%+ liquidity explosions (e.g., Tempsens Instruments).
2. **Automated Prospectus (RHP) PDF Parser**: Build a dedicated PyPDF/OCR pipeline targeting SEBI RHP filing tables to extract audited EPS, ROE, and revenue growth directly from statutory filings, bypassing website scraping gaps.
3. **Anchor Investor Quality Scoring**: Parse anchor investor allotment sheets to quantify the ratio of domestic mutual funds vs foreign hedge funds.
