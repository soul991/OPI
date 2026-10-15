# Phase 7: Pre-Registration Protocol

> **Status**: Frozen Pre-Registration Document  
> **Committed**: Prior to Phase 7 model training, evaluation, or backfill execution per [`RULES.md`](../../RULES.md) and [`phases/Phase 7/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Rule**: Any post-hoc modifications require a dated "Amendment" section; the original protocol text remains strictly unmodified.

---

## 1. Objectives & Scope

1. **Workstream A: GMP Backfill**:
   - Systematically source missing Grey Market Premium (GMP) data for 2025–2026 IPOs (starting with 2026Q3 and 2026Q4, then 2026Q1–Q2 and 2025).
   - Strict as-of date discipline: quotes must be as of the **last bidding day** (or evening before listing at the latest; never listing-day or post-listing).
   - Target: $\ge 80\%$ GMP coverage in 2026Q3 and 2026Q4.
2. **Workstream B: Data Verification v2**:
   - Random sample of 40 historical IPO rows (fixed seed = 42) audited against primary exchange / regulatory documents for listing date, issue price, listing price, and total subscription.
3. **Workstream C: Matched Rolling-Origin Re-evaluation**:
   - Re-run temporal walk-forward evaluation (2022Q1 to 2026Q4) on purified, backfilled dataset.
   - Compare Model Without GMP, Model With GMP, Raw GMP, and Linear Blend.
   - Matched-rows before/after comparison with Phase 6.
4. **Workstream D: Regime-Conditional Split-Conformal Intervals**:
   - Calibrate separate conformal quantiles $\hat{q}_{\text{obs}}$ (for `OBSERVED`) and $\hat{q}_{\text{unavail}}$ (for `CONFIRMED_UNAVAILABLE`) to fix the severe under-coverage observed in Phase 6 on cold and tail regimes.
5. **Workstream E: Ongoing Forward Test**:
   - Log predictions for all active/open unlisted mainboard IPOs before listing; update actuals strictly via script after listing.
6. **Workstream F: Evidence-Reflective User Interface**:
   - Update `README.md` and `predict.py` to transparently reflect empirical evidence and regime-specific guidance.

---

## 2. GMP Collection Protocol & Verification Rules

1. **Timing & Leakage Prevention**:
   - Every GMP quote must be strictly as of the **last bidding day** (`rule = last_bidding_day`) or at latest the evening before listing (`rule = day_before_listing`).
   - Sourcing GMP on listing day or post-listing is strictly prohibited (constitutes forward-looking leakage).
   - Any source reporting an undated, current, or floating quote is inadmissible.
2. **Provenance Registry**:
   - All sourced quotes must be logged in `data/gmp_sourced.csv` with schema:
     `company,listing_date,gmp_inr,gmp_pct,as_of_date,rule,source_url,page_date,accessed_on,confidence`
   - Confidence levels:
     - `high`: Dated historical archive table from reputable aggregator / financial database.
     - `medium`: Dated article, news release, or broker report.
     - `low`: Ambiguous timing or unconfirmed date; kept in file for record but excluded from model features.
3. **Independent Second-Source Accuracy Check**:
   - Draw a random sample of 30 newly sourced GMP values (`seed = 42`) and verify against an independent secondary source.
   - Tolerance threshold: within $\pm 2.0$ percentage points.
   - Requirement: $\ge 90\%$ match rate to maintain `high` confidence ranking.
4. **Coverage Reporting**:
   - Publish quarterly coverage before and after backfill in `phases/Phase 7/gmp_coverage.csv`.

---

## 3. Regime Definitions & Separation Protocol

Per [`references/gmp_status_definitions.md`](../../references/gmp_status_definitions.md), all IPOs are classified into three mutually exclusive categories:

1. **`OBSERVED`**:
   - Verified, dated pre-listing GMP quote is recorded.
   - Evaluated under Regime A (Active Grey Market).
2. **`NOT_RECORDED`**:
   - Data has not yet been collected or verified in the database.
   - **Strict Rule**: Kept strictly OUT of any "no-GMP" performance claims, conformal interval calibration, or regime conclusions.
3. **`CONFIRMED_UNAVAILABLE`**:
   - Multi-source search across portals confirms that no grey market trading or quotes existed prior to listing.
   - Evaluated under Regime B (Genuinely Cold / Unquoted Issues).

---

## 4. Regime-Conditional Conformal Prediction Protocol

In Phase 6, pooling all issues resulted in severe under-coverage (59.7%) on unquoted issues and 60.0% on top 10% pops. To resolve this:

1. **Calibration Splits**:
   For each rolling-origin test period $t$:
   - Let $\mathcal{D}_{\text{train}, t}$ be all training issues listed prior to period $t$.
   - Split $\mathcal{D}_{\text{train}, t}$ into inner training (80%) and conformal calibration set $\mathcal{D}_{\text{cal}, t}$ (20%).
2. **Regime-Conditional Nonconformity Quantiles**:
   - **Observed Regime Quantile ($\hat{q}_{\text{obs}}$)**:
     Computed from absolute residuals $R_j = |y_j - \hat{y}_j|$ on calibration issues where `gmp_status == 'OBSERVED'`.
     $$\hat{q}_{\text{obs}} = \text{Quantile}_{(1-\alpha)(1 + 1/n_{\text{obs}})}(\{R_j : j \in \mathcal{D}_{\text{cal}, t}^{\text{obs}}\})$$
   - **Unavailable Regime Quantile ($\hat{q}_{\text{unavail}}$)**:
     Computed from absolute residuals on calibration issues where `gmp_status == 'CONFIRMED_UNAVAILABLE'`.
     $$\hat{q}_{\text{unavail}} = \text{Quantile}_{(1-\alpha)(1 + 1/n_{\text{unavail}})}(\{R_j : j \in \mathcal{D}_{\text{cal}, t}^{\text{unavail}}\})$$
3. **Sample Size Safeguard**:
   - If a regime has fewer than 40 evaluated IPOs in the historical calibration set, report **"insufficient n for a coverage claim"** and fall back to pooled nonconformity quantile with an explicit disclaimer.
4. **Nominal Target**:
   - $1 - \alpha = 0.80$ (80% nominal coverage).
   - Acceptable empirical tolerance: **75.0% to 85.0%**.
   - Evaluated pooled, by regime (`OBSERVED` vs `CONFIRMED_UNAVAILABLE`), and for extreme positive pops (top 10% returns).

---

## 5. Mathematical Evaluation Metrics

1. **Continuous Point Prediction Error**:
   - **Mean Absolute Error (MAE)**:
     $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
   - **Median Absolute Error (MedAE)**:
     $$\text{MedAE} = \text{median}(|y_1 - \hat{y}_1|, \dots, |y_N - \hat{y}_N|)$$
2. **Classification & Calibration**:
   - **Binary Target**: $\mathbb{I}(y_i > 10.0\%)$.
   - **Discrimination**: ROC-AUC evaluated on continuous calibrated probabilities.
   - **Calibration**: Equal-frequency quantile Expected Calibration Error (ECE, 10 bins) and Brier score loss.
   - **Reliability Intervals**: Wilson 95% confidence intervals per calibration bin.
3. **Baselines & Model Variants**:
   - **Baseline 1**: Historical Expanding Mean.
   - **Model Without GMP**: Gradient boosted regressor using subscription, issue size, valuation, and market momentum features.
   - **Model With GMP**: Model incorporating dated pre-listing GMP percentage.
   - **Raw GMP**: The grey market premium percentage itself (unaltered market benchmark).
   - **Linear Blend**: $\hat{y}_{\text{blend}} = w \cdot \text{GMP} + (1-w) \cdot \hat{y}_{\text{model}}$, where $w \in [0, 1]$ is optimized on inner validation folds.

---

## 6. Paired Bootstrap Inference & Evidence Language

1. **Bootstrap Procedure**:
   - Exact $B = 2,000$ paired bootstrap resamples.
   - Fixed pseudo-random seed: `seed = 42`.
   - Two-sided percentile confidence interval: $CI_{95\%} = [\Delta_{(0.025)}, \Delta_{(0.975)}]$.
2. **Strict Vocabulary Rules**:
   - Terms such as *"beats"*, *"wins"*, *"improves"*, *"calibrated"*, or *"statistically significant"* are permitted **if and only if** the paired 95% bootstrap interval strictly excludes zero.
   - If the interval straddles zero, the findings must be described strictly as *"no demonstrated difference"* or *"no demonstrated advantage"*.
3. **Causal Attributions**:
   - Any explanation of underlying financial or market mechanisms (e.g., pricing by lead managers, institutional book building, retail liquidity constraints) must be explicitly labeled **"Hypothesis (untested)"** unless an empirical hypothesis test conducted within this project directly supports it.

---

## 7. Strict Research Discipline & Partition Integrity

1. **No Test-Set Tuning**:
   - `data/ipo_phase5_final_test.csv` must NEVER be read, inspected, or scored for feature engineering, hyperparameter selection, threshold choice, or calibration decisions.
2. **Zero Fabrication**:
   - No missing value may be imputed, estimated, backfilled, or guessed. Unverifiable values remain strictly empty (`NaN`).
3. **Traceability**:
   - Every single number appearing in markdown reports must be generated by and traceable to committed script output artifacts.
