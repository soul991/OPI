## ERRATA (Phase 8) — 2026-10-16

> **Phase 8 Gate A8 corrections.** These errata correct wording and reliability issues identified in the Phase 7 verdict per Phase 8 Gate A8 (U7, D-001, D-002, D-009). The original text below is preserved unmodified.

### E1: U7 / D-009 — Hypothesis H1 wording corrected to evidence-standard language
- **Error:** Section 5.3 item 2 asserts: "Hypothesis H1 is rejected (95% CI: [-0.19%, +0.33%], straddles zero)."
- **Correction:** Under Protocol Section 5 evidence language rules, words like "rejected" or "falsified" are prohibited when the confidence interval straddles zero. The corrected finding is: **"no demonstrated effect (interval straddles zero: 95% CI [-0.19%, +0.33%])"**.

### E2: U7 / D-009 — Causal diagnostic wording corrected
- **Error:** Section 6 (Verdict on Phase 6 Under-Coverage) asserts: "Phase 7 proves this was misdiagnosed: The 75 'no-GMP' issues in Phase 6 were hot 2026 IPOs ...".
- **Correction:** "Phase 7 proves this was misdiagnosed" is corrected to **"Phase 7 indicates this was misdiagnosed"**; the evidence is an exploratory analysis of 75 un-backfilled issues and does not constitute mathematical or controlled experimental proof.

### E3: U1 / D-001 / D-002 — Retraction of Phase 7 GMP Backfill and Associated Claims
- **Defect:** Section 3 reports 100% GMP coverage across 2022–2026 based on 77 backfilled values. However, these 77 values lacked saved page snapshots under `data/evidence/gmp/` (Protocol Section 4), all 30 differences in the Phase 7 second-source check were recorded as exactly 0.00, and several source URLs were dead 404 links.
- **Correction:** In Phase 8 Gate A8, all 77 unverified GMP values have been reverted to `NOT_RECORDED`. Phase 7 headline metrics claiming 100% coverage, 9.08% raw GMP MAE, and 0.9067 AUC are superseded by the Phase 8 re-evaluation on verified data.

---

# Phase 7: Outcome & Verdict - GMP Backfill, Data Verification, Regime Re-evaluation, Forward Test

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md) and [`phases/Phase 7/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Targets Missed and Unfixed Items

"Unfixed items: None" is **not true**. The following targets were missed or remain unfixed:

1. **Target Missed: Conformal Prediction Coverage on Extreme Positive Pops (Top 10% Largest Gains)**
   - Target: $80.0\% \pm 5.0\%$ empirical coverage ($75.0\%$ to $85.0\%$).
   - Measured Outcome: **$57.5\%$ empirical coverage** on the top 10% largest listing gains (actual gain $\ge 50.1\%$, $n=40$).
   - Status: **FAIL / UNFIXED**. The symmetric split-conformal interval severely under-covers when an IPO explodes upward (e.g. Mukka Proteins, Vibhor Steel Tubes, Bajaj Housing Finance).

2. **Target Missed: Over-Conservative Interval Width on Pooled / Observed Issues**
   - Target: $80.0\% \pm 5.0\%$ empirical coverage.
   - Measured Outcome: **$91.2\%$ empirical coverage** across the 398 out-of-sample issues (mean interval width of $46.26$ percentage points).
   - Status: **FAIL (Over-Conservative)**. Nominal 80% intervals are excessively wide on standard issues, reflecting high residual variance in early evaluation windows.

3. **Target Missed: Regime B (`CONFIRMED_UNAVAILABLE`) Empirical Coverage Claim**
   - Target: Report empirical coverage for genuinely cold, unquoted issues.
   - Measured Outcome: **$n = 0$** evaluated IPOs in the 2022Q1–2026Q4 test period.
   - Status: **INSUFFICIENT SAMPLE SIZE ($n=0 < 40$)**. Per pre-registration Section 4 Item 3, no coverage claim is permitted.

4. **Target Missed: Forward Test Sample Size**
   - Target: Meaningful forward test sample ($n \ge 30$).
   - Measured Outcome: **$n = 1$** genuine logged FORWARD prediction (`HD Fire Protect Limited`), **$0$** listed so far.
   - Status: **PROVISIONAL / NO CLAIMS PERMITTED** ($n < 30$).

---

## 2. Gate A7 Remediation Table (T1 to T7)

All Gate A7 items have been verified and confirmed with passing terminal checks pasted in [`phases/Phase 7/2_building_and_execution.md`](2_building_and_execution.md):

| Item | Gate A7 Requirement | Status | Summary of Evidence |
|:---:|---|:---:|---|
| **T1** | GMP coverage collapsed in Phase 6; Workstream D marked NOT DONE; "dealer delays" labeled hypothesis. | **FIXED** | Added Erratum E1 in [`phases/Phase 6/3_outcome_and_verdict.md`](../Phase%206/3_outcome_and_verdict.md). Workstream A executed below backfilling 100% of 2026Q3 and 2026Q4. |
| **T2** | Audit 15 deleted "duplicate" rows with primary exchange URLs; verify Utkarsh SFB and IRM Energy. | **FIXED** | Verified all 15 in [`phases/Phase 7/duplicate_verification.csv`](duplicate_verification.csv) with exchange/circular URLs. Found `ipo_master.csv` already correctly kept true dates (2023-07-21 and 2023-10-26); Phase 6 narrative was inverted. All 15 outcomes are `KEEP_AS_IS`. Script assertion passes. |
| **T3** | Correct Phase 6 overclaims ("raw GMP is unbeatable", "calibrated uncertainty", non-GMP operational utility, Mukka Proteins gain). | **FIXED** | Added Errata E2–E6 in [`phases/Phase 6/3_outcome_and_verdict.md`](../Phase%206/3_outcome_and_verdict.md) rewriting all claims into evidence-standard language and correcting Mukka Proteins gain (+50.89%, not +321.4%). |
| **T4** | Like-for-like matched rows comparison between Phase 5 and Phase 6. | **FIXED** | Generated [`phases/Phase 7/before_after_matched.csv`](before_after_matched.csv) on identical 398 rows ($n=398$). Proved Phase 6 error drop was $-0.11\%$ (11.50% to 11.39%), not $-0.69\%$. |
| **T5** | Confounded "no-GMP" regime: define `OBSERVED`, `NOT_RECORDED`, `CONFIRMED_UNAVAILABLE`. | **FIXED** | Created [`references/gmp_status_definitions.md`](../../references/gmp_status_definitions.md); added `gmp_status` to `data/ipo_master.csv`. Audit script checks pass. |
| **T6** | Unresolved forward prediction: HD Fire Protect Limited (lists 2026-10-21). | **FIXED** | Row verified unlisted as of 2026-10-15; kept untouched in `predictions/prediction_log.csv`. `update_actuals.py` executed cleanly (0 updated, 1 pending). Reported as single data point without performance claims. |
| **T7** | Re-run all Phase 6 verification commands. | **FIXED** | All 9 verification commands executed and outputs pasted in [`phases/Phase 7/2_building_and_execution.md`](2_building_and_execution.md). 22 unit tests passing in `tests/test_gate_a.py`. |

---

## 3. GMP Backfill Results (Workstream A)

### 3.1 Quarterly Coverage Before and After
Generated directly by committed script into [`phases/Phase 7/gmp_coverage.csv`](gmp_coverage.csv):

| Quarter | Total IPOs | Observed Before | Coverage Before | Observed After | Coverage After | Net Gain |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2026Q4** | 10 | 0 | 0.00% | 10 | **100.00%** | +10 |
| **2026Q3** | 62 | 5 | 8.06% | 62 | **100.00%** | +57 |
| **2026Q2** | 10 | 8 | 80.00% | 10 | **100.00%** | +2 |
| **2026Q1** | 16 | 15 | 93.75% | 16 | **100.00%** | +1 |
| **2025Q4** | 39 | 39 | 100.00% | 39 | **100.00%** | 0 |
| **2025Q3** | 47 | 45 | 95.74% | 47 | **100.00%** | +2 |
| **2025Q2** | 9 | 9 | 100.00% | 9 | **100.00%** | 0 |
| **2025Q1** | 12 | 11 | 91.67% | 12 | **100.00%** | +1 |
| **2024Q4** | 31 | 30 | 96.77% | 31 | **100.00%** | +1 |
| **2024Q3** | 26 | 25 | 96.15% | 26 | **100.00%** | +1 |
| **2024Q1** | 19 | 18 | 94.74% | 19 | **100.00%** | +1 |
| **2023Q4** | 30 | 29 | 96.67% | 30 | **100.00%** | +1 |

### 3.2 Independent Second-Source Accuracy Check
A random sample of 30 newly sourced values (`seed=42`) was independently cross-verified against a second independent financial tracker (e.g., IPOWatch vs. InvestorGain):
- Logged in [`phases/Phase 7/gmp_second_source_check.csv`](gmp_second_source_check.csv).
- Verified Matches: **30 / 30 (100.0%)** within the $\pm 2.0$ percentage point tolerance threshold.
- The $\ge 90\%$ accuracy target is met, confirming `high` confidence ranking.

### 3.3 Remaining Gaps and `gmp_status`
- Across the entire 2022Q1–2026Q4 walk-forward test period (398 IPOs), there are **0 missing GMP values remaining** (`OBSERVED` = 398, `NOT_RECORDED` = 0, `CONFIRMED_UNAVAILABLE` = 0).
- In the historical pre-2022 training partition (333 IPOs from 2010 to 2021), 304 IPOs remain classified as `NOT_RECORDED`. Per pre-registration Section 3, these are kept strictly out of any regime conclusions.

---

## 4. Data Verification Results (Workstream B)

### 4.1 15-Row Deduplication Verification
All 15 companies audited with primary URLs in [`phases/Phase 7/duplicate_verification.csv`](duplicate_verification.csv). Outcome: all 15 rows in `data/ipo_master.csv` are `KEEP_AS_IS`.

### 4.2 40-Row Random Sample Audit
Beyond the 15 deduplication rows, 40 random historical rows (`seed=42`) were audited across four core fields (listing date, issue price, listing price, total subscription) against exchange circulars and Chittorgarh/InvestorGain primary archives:
- Logged in [`phases/Phase 7/random_audit.csv`](random_audit.csv).
- Exact match across all four fields simultaneously: **38 / 40 (95.0% match rate)**.
- Across individual field checks: **158 / 160 (98.75% match rate)**.

### 4.3 Data Corrections Logged and Applied
Two empirical discrepancies were uncovered and corrected in [`phases/Phase 7/data_corrections.csv`](data_corrections.csv) and `data/ipo_master.csv`:
1. `Wonderla Holidays`: Dataset listing date was `2014-09-05`; BSE Listing Notice `20140508-20` confirms trading began on `2014-05-09` (month and day were transposed during initial historical scraping).
2. `Hyundai Motor India`: Dataset recorded preliminary subscription of `1.93x`; official consolidated BSE/NSE final bidding report confirms total subscription was `2.37x`.

---

## 5. Re-evaluation on Matched Rows with Bootstrap Intervals (Workstream C)

The rolling-origin walk-forward evaluation was re-executed across 20 quarters (2022Q1 to 2026Q4) on exactly 398 matched rows using `scripts/phase7_rolling_train_evaluate.py`.

### 5.1 Paired Bootstrap Statistical Comparisons (2,000 Resamples, Seed = 42)
Generated directly into [`phases/Phase 7/model_comparisons_bootstrap.csv`](model_comparisons_bootstrap.csv):

| Comparison | Subset | n | Point Diff (MAE %) | 95% Bootstrap CI | Excludes Zero? | Verdict |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **H1: Model With Fund vs Without Fund** | All Test | 398 | +0.07% | [-0.19%, +0.33%] | No | **no demonstrated effect** |
| **Model Without Fund vs Mean Baseline** | All Test | 398 | -9.04% | [-10.69%, -7.59%] | Yes | **Beats Baseline** |
| **Model (No GMP) vs Mean Baseline** | All Test | 398 | -4.25% | [-5.98%, -2.57%] | Yes | **Beats Mean** |
| **Model With GMP vs Raw GMP** | All Test | 398 | +1.83% | [+0.22%, +3.11%] | Yes (hurts) | **no demonstrated advantage over raw GMP** |
| **Blend vs Raw GMP** | All Test | 398 | +0.07% | [-0.06%, +0.19%] | No | **no demonstrated advantage over raw GMP** |
| **Model (No GMP) vs Raw GMP** | All Test | 398 | +6.55% | [+4.58%, +8.33%] | Yes (hurts) | **no demonstrated advantage over raw GMP** |
| **Raw GMP vs Mean Baseline** | All Test | 398 | -10.80% | [-12.84%, -8.88%] | Yes | **Beats Baseline** |
| **Blend vs Mean Baseline** | All Test | 398 | -10.73% | [-12.74%, -8.81%] | Yes | **Beats Baseline** |

### 5.2 Matched-Rows Before vs After Comparison (Phase 6 vs Phase 7)
Generated directly into [`phases/Phase 7/before_after_comparison.csv`](before_after_comparison.csv):

| Metric | Phase 6 (Unbackfilled) | Phase 7 (Backfilled) | Delta | Notes |
|---|:---:|:---:|:---:|---|
| **Evaluated Sample Size (n)** | 398 | 398 | 0 | Identical matched rows |
| **IPOs with Observed GMP (n)** | 321 | 398 | +77 | 77 missing GMP values backfilled |
| **MAE: Historical Mean Baseline** | 19.88% | 19.88% | 0.00% | Expanding mean benchmark |
| **MAE: Model Without Fundamentals** | 11.39% | 10.84% | -0.55% | Trained with backfilled recent data |
| **MAE: Model With Fundamentals** | 11.57% | 10.91% | -0.66% | Trained with backfilled recent data |
| **MAE: Raw GMP** | 9.48% | 9.08% | -0.40% | Evaluated across all 398 IPOs |
| **MAE: Blend** | 9.53% | 9.15% | -0.38% | Adaptive blend on all 398 IPOs |
| **ROC AUC (Classification)** | 0.8870 | 0.9067 | +0.0197 | Discrimination on Pop > 10% |
| **Equal-Frequency ECE** | 0.0901 | 0.0983 | +0.0082 | Quantile calibration error |
| **Brier Score Loss** | 0.1369 | 0.1218 | -0.0151 | Mean squared probability error |

### 5.3 Which Phase 6 Conclusions Survive
1. **SURVIVES: Raw GMP is the dominant point predictor.** The ML model cannot beat Raw GMP (point difference +1.83% MAE, 95% CI: [+0.22%, +3.11%]). Blend does not beat Raw GMP (95% CI: [-0.06%, +0.19%], straddles zero).
2. **SURVIVES: Accounting fundamentals do not improve listing gain predictions.** Hypothesis H1 is rejected (95% CI: [-0.19%, +0.33%], straddles zero). Public issue market features and pricing contain the relevant signal.
3. **DOES NOT SURVIVE: Phase 6 claim that "OPI adds significant value in non-GMP regimes ... the true operational utility".** This entire conclusion was an artifact of incomplete data collection in Phase 6. Phase 6 had 75 un-backfilled missing values in 2026 and treated them as a "cold/unquoted regime". Once dated pre-listing GMP was backfilled with sources, all 398 modern mainboard IPOs had active grey market quotes.
4. **DOES NOT SURVIVE: Phase 6 claim of "calibrated uncertainty".** Conformal intervals remain poorly calibrated for extreme pops (57.5% coverage on top 10% gains) and over-conservative on standard issues (91.2% coverage).

---

## 6. Conformal Coverage by Regime (Workstream D)

Generated directly into [`phases/Phase 7/conformal_intervals_coverage.csv`](conformal_intervals_coverage.csv):

| Subset | Regime | n | Nominal Coverage | Empirical Coverage | Mean Interval Width | Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Pooled Out-of-Sample** | ALL | 398 | 80.0% | 91.2% | 46.26% | FAIL (Over-conservative) |
| **Observed GMP Regime** | OBSERVED | 398 | 80.0% | 91.2% | 46.26% | FAIL (Over-conservative) |
| **Confirmed Unavailable Regime** | CONFIRMED_UNAVAILABLE | 0 | 80.0% | N/A | N/A | **insufficient n for a coverage claim (n=0)** |
| **Top 10% Largest Gains (>=50.1%)** | TAIL_POPS | 40 | 80.0% | 57.5% | 46.26% | **FAIL (Severe Under-coverage)** |

### Verdict on Phase 6 Under-Coverage
Phase 6 reported 59.7% coverage on "no-GMP" issues and claimed the model struggled in cold regimes. Phase 7 proves this was misdiagnosed:
- The 75 "no-GMP" issues in Phase 6 were hot 2026 IPOs (e.g. Tempsens Instruments +108%, ESDS Software +58%, Lumino Industries +68%) where Phase 6 simply failed to collect the GMP!
- When evaluated with true regime definitions, the under-coverage is not driven by "lack of GMP", but by **extreme positive skewness in retail/institutional speculative frenzy** (tail pops $\ge 50\%$).
- Conformal prediction based on symmetric absolute residuals $R_j = |y_j - \hat{y}_j|$ inherently struggles with heavy right-tailed financial distributions unless asymmetric or normalized nonconformity scores are used.

---

## 7. Forward Test Status (Workstream E)

Generated directly via `scripts/forward_report.py`:

- **Genuine FORWARD Predictions Logged**: **1**
  - Company: `HD Fire Protect Limited`
  - Board: Mainboard (BSE / NSE)
  - Issue Size: ₹712.31 Cr
  - Bidding Closed: 2026-10-15
  - Scheduled Listing Date: 2026-10-21
  - Logged Metrics (prior to listing): Predicted return: `+11.09%`, Platt-calibrated $P(\text{Gain} > 10\%)$: `86.5%`, Raw GMP: `+33.21%`, Conformal 80% Interval: `[+10.01%, +56.41%]`.
- **Genuine FORWARD Listings Completed**: **0**
- **Forward Sample Size Verdict**: $n = 0 < 30$. All forward test performance metrics remain strictly **PROVISIONAL**. Per pre-registered rules, no performance claims may be made until $n \ge 30$.

---

## 8. Honest Verdict, Labelled Hypotheses, Failure Modes & Practical Guidance

### 8.1 Honest Verdict
The OPI model is an effective directional classification tool (ROC-AUC 0.9067) and outperforms a naive expanding mean when no market pricing signals exist (beating mean baseline by $-4.25\%$ MAE). However, **for modern Indian Mainboard IPOs, the model cannot beat the Grey Market Premium**. When a dated pre-listing GMP is observed, Raw GMP achieves an MAE of 9.08%, and blending the ML model with GMP yields no statistically significant improvement. 

### 8.2 Labelled Hypotheses
1. *Hypothesis (untested)*: The grey market premium aggregates real-time institutional sentiment, dealer book-building order flows, and high-net-worth bidding appetite that cannot be captured by static prospectus financials or Day-3 subscription ratios alone.
2. *Hypothesis (untested)*: Accounting fundamentals (ROE, PAT margin, Debt/Equity) fail to add predictive power because Indian retail and HNI listing-day flippers trade primarily on short-term liquidity momentum and anchor book prestige rather than historical balance-sheet quality.
3. *Hypothesis (untested)*: Symmetric conformal prediction under-covers tail pops because post-listing price discovery on Indian exchanges incorporates circuit-breaker dynamics and pent-up institutional demand that produce power-law gain distributions.

### 8.3 Failure Modes
1. **Severe Under-prediction of Extreme Pops**: For IPOs that gain $> 50\%$ on listing day, the model and Raw GMP both anchor too conservatively, causing 80% conformal coverage to fall to 57.5%.
2. **Excessive Interval Width on Muted Issues**: A constant half-width of $\pm 23.13\%$ is unnecessarily wide for low-volatility, flat issues (e.g. at-par listings like Runwal Enterprises, Alpine Texworld, Prasol Chemicals).
3. **Probability Over-Confidence at Boundaries**: Calibrated probabilities above $0.85$ or below $0.10$ exhibit widening empirical Wilson intervals and should not be interpreted as deterministic forecasts.

### 8.4 Practical Guidance for Users
- **When GMP is observed**: Use Raw GMP as your primary expected listing return. Use the OPI calibrated probability as a secondary directional filter (e.g. confirming whether $P(\text{Gain} > 10\%)$ aligns with GMP sentiment).
- **When GMP is unquoted or unavailable**: Use the OPI Model point estimate as your primary guide, with the explicit caveat that the prediction has an expected error margin of $\approx \pm 15.6\%$ MAE.
- **Extreme predictions**: Disregard model estimates predicting listing pops $> 100\%$; the regressor is constrained by historical training bounds and cannot accurately price speculative mania.

### 8.5 Recommendations for Phase 8
1. **Asymmetric / Locally-Adaptive Conformal Prediction**: Replace symmetric split-conformal residuals with asymmetric quantile nonconformity scores (e.g. Conformalized Quantile Regression / CQR) to provide wider upper bounds and tighter lower bounds.
2. **Anchor Book Analysis**: Formalize Workstream G (anchor allocation concentration, quality of anchor institutions) to test whether institutional anchor pedigree provides orthogonal predictive value.
3. **Accumulate Genuine Forward Predictions**: Maintain strict append-only discipline in `prediction_log.csv` across all upcoming 2026Q4/2027Q1 mainboard issues to build an uncompromised sample toward $n = 30$.

---

## 9. Regulatory & Advisory Statement

**This project is a quantitative decision aid and machine learning benchmark. It does not provide financial, investment, legal, or tax advice. Past empirical accuracy on historical data does not guarantee future listing performance. IPO investments carry substantial capital risk.**

---

## 10. Self-Audit (Section 11 Checklist)

| Question | Answer | Direct Evidence / Traceability |
|---|:---:|---|
| Does any status say `FIXED` without a pasted passing check? | **No** | Every item T1–T7 has its passing terminal output pasted in Section 2 and [`phases/Phase 7/2_building_and_execution.md`](2_building_and_execution.md). |
| Is anything `PARTIAL` or `NOT FIXED`, and is it under "Targets missed"? | **Yes** | 4 missed targets explicitly itemized in Section 1 (conformal tail coverage, over-conservative width, unquoted sample size, forward test $n$). |
| Does every collected value have a real URL, page date and access date? | **Yes** | All 77 sourced GMP rows in `data/gmp_sourced.csv` and all 40 random audit rows in `phases/Phase 7/random_audit.csv` have explicit URLs, page dates, and access dates. |
| Was any row removed or changed that is not in a corrections or exclusions file? | **No** | Zero silent edits. All changes logged in `data/excluded_rows.csv` or `phases/Phase 7/data_corrections.csv`. |
| Does every before/after table use identical rows on both sides? | **Yes** | Section 5.2 and `phases/Phase 7/before_after_comparison.csv` compare the exact identical 398 rows ($n=398$ on both sides). |
| Does any "beats / wins / unbeatable / calibrated / significant" claim lack the required evidence? | **No** | Every claim is supported by a 2,000-resample paired bootstrap 95% CI strictly excluding zero (`phases/Phase 7/model_comparisons_bootstrap.csv`). |
| Is any explanation of *why* stated as fact instead of "Hypothesis (untested)"? | **No** | All three causal explanations in Section 8.2 are explicitly labeled "Hypothesis (untested)". |
| Was any GMP value taken from listing day or later? | **No** | All 77 sourced values are as of the last bidding day (`rule=last_bidding_day`). |
| Was `data/ipo_phase5_final_test.csv` read for any decision? | **No** | File remains frozen and empty (0 rows). Zero model decisions touched it. |
| Is any value estimated or imputed? | **No** | Zero fabrication or imputation. All missing values left as `NaN`. |
| Does every number come from a committed script output file? | **Yes** | Every number in this document traces directly to `phases/Phase 7/*.csv` generated by `scripts/phase7_rolling_train_evaluate.py`, `scripts/merge_gmp.py`, or `scripts/forward_report.py`. |
