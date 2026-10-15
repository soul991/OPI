# Grey Market Premium (GMP) Status Definitions

This reference document establishes the formal classification of Grey Market Premium (GMP) data availability for the Open Price Intelligence (OPI) framework, as mandated by Phase 7 Gate A7 Item T5.

---

## 1. Background & Problem Statement

In Phase 6, all IPOs lacking a recorded `gmp_pct` were aggregated into an undifferentiated "no-GMP regime" ($n=77$). A critical data audit revealed that **67 of these 77 IPOs (87.0%)** originated exclusively from 2026Q3 and 2026Q4, where collection had simply collapsed due to incomplete scraping and lack of backfilling, rather than an absence of grey market quotes in the real world.

Lumping uncollected missing data together with genuinely unquoted issues created severe regime confounding:
- Claims about the model's performance on "unquoted issues" were evaluating mostly uncollected recent issues that actually possessed active grey market trading.
- Conformal prediction intervals calibrated on this confounded pool suffered distorted nonconformity quantiles.

To prevent confounding, every IPO in the dataset must be explicitly assigned a validated `gmp_status`.

---

## 2. Permitted Status Values

The `gmp_status` column in `data/ipo_master.csv` must strictly take one of the following three categorical values:

### A. `OBSERVED`
- **Definition**: Active grey market trading occurred for the issue, and a verified, dated quote prior to listing has been collected.
- **Criteria**:
  1. The quote must represent the GMP as of the **last bidding day** (or at latest the evening prior to listing day).
  2. Quotes from listing day or post-listing are strictly prohibited (prevents lookahead leakage).
  3. Every quote must possess a primary or aggregator source URL, the page's own publication date, and the verification/access date.
  4. Stored in `data/gmp_sourced.csv` with confidence level `high` or `medium`.
- **Downstream Usage**: Used in Regime A evaluations (Model With GMP, Raw GMP benchmark, Blended strategy).

### B. `NOT_RECORDED`
- **Definition**: The IPO may or may not have traded in the grey market, but our dataset has not yet searched or recorded a validated quote.
- **Criteria**:
  1. No dated quote has been extracted or verified.
  2. The absence of data is an artifact of database coverage, not market reality.
- **Downstream Usage**: **Strict exclusion**. IPOs with `gmp_status == 'NOT_RECORDED'` must **NEVER** be included in "no-GMP" regime performance benchmarks, regime-conditional conformal calibration, or claims regarding unquoted market behavior.

### C. `CONFIRMED_UNAVAILABLE`
- **Definition**: A systematic search across primary sources and reputable aggregators (Chittorgarh, InvestorGain, IPOWatch, etc.) was conducted and confirmed that **no grey market quotes or trading existed** for this issue prior to listing.
- **Criteria**:
  1. Issue was systematically searched across at least two independent grey market tracking portals.
  2. Confirmed that no active grey market trades or published GMP quotes were established on or before the close date.
  3. Search audit documented in the data provenance log.
- **Downstream Usage**: Represents the true **Regime B (Genuinely Unquoted / Cold Issues)**. Only these issues may be used to assess the model's standalone operational utility in the absence of market sentiment signals.

---

## 3. Transition Rules

1. At initial baseline (Gate A7), all existing rows with non-null `gmp_pct` are marked `OBSERVED`. All rows with null `gmp_pct` are initialized as `NOT_RECORDED`.
2. During Workstream A (GMP Backfill), as missing rows are researched:
   - If a valid quote is found meeting the `last_bidding_day` rule, the row updates to `OBSERVED` and `gmp_pct` is populated.
   - If thorough multi-source verification confirms no quotes ever existed, the row updates to `CONFIRMED_UNAVAILABLE` (with `gmp_pct` remaining strictly null).
   - Any row that could not be verified remains `NOT_RECORDED`.
3. In downstream evaluation and reporting scripts (`phase7_rolling_train_evaluate.py`, `predict.py`), rows with `NOT_RECORDED` are treated strictly as missing data and filtered out of regime-specific comparisons.
