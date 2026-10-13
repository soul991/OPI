# India IPO Listing-Gain Predictor: Plan

**Goal:** estimate the listing-day gain (and the probability of a good listing) for Indian mainboard IPOs, using a model trained on as many past IPOs as possible.

> This is a decision aid, not financial advice. Expect modest accuracy: IPO listings are noisy and depend on market mood.

## 1. Pipeline overview

```
[Skill 1: ipo-data-collector] -> data/ipo_master.csv (past IPOs + actual listing gain)
              |
        model/train.py -> model/ipo_model.joblib + metrics report
              |
[Skill 2: ipo-research-analyst] -> new_ipo.csv (one row, same columns, no target)
              |
        model/predict.py -> probability + estimated gain + warnings
```

## 2. Decisions (improvements over the first idea)

| Topic | Decision | Why |
|---|---|---|
| Scope | India mainboard IPOs (NSE/BSE). SME IPOs kept in a separate file. | SME IPOs behave very differently and would pollute the data. |
| Target | `listing_gain_pct` = (listing price - issue price) / issue price x 100. Also `label_good` = gain > 10%. | Clean, measurable right away. |
| Model | Gradient boosting (scikit-learn HistGradientBoosting), regression plus classification. | Best fit for small tabular data; handles missing values. |
| "Train until maximum" | Replaced by time-based validation and an early stop when test metrics stop improving. | Training until it matches the past perfectly = overfitting. |
| Validation | Train on older IPOs, test on the newest ~20%. Plus walk-forward by year. | Random splits leak future information. |
| Baselines | Compare against "always predict the average" and "GMP only". | If the model can't beat GMP alone, it isn't adding value. |
| Leakage rule | Only use information available **before listing**. GMP is taken on the last bidding day. | The backtest must match real usage. |

## 3. Data schema (one row per IPO)

See `skills/ipo-data-collector/references/schema.md` for full definitions. Groups:

- **Identity:** company, sector, exchange, open_date, close_date, listing_date
- **Issue:** issue_price, issue_size_cr, fresh_issue_pct, ofs_pct, lot_size
- **Subscription:** sub_qib, sub_nii, sub_retail, sub_total
- **Valuation and financials:** pe_ratio, peer_median_pe, roe, roce, debt_equity, revenue_growth_pct, pat_margin_pct
- **Market context:** gmp_pct, nifty_30d_return, india_vix, recent_ipo_avg_gain (previous 5 IPOs)
- **Target (training only):** listing_gain_pct, label_good

## 4. Phases

1. **Collect:** run Skill 1 in batches (year by year, newest to oldest). Aim for every mainboard IPO since about 2010 (roughly 500+ rows). Validate with `scripts/validate_dataset.py`.
2. **Train:** `python model/train.py data/ipo_master.csv`. Read the metrics report. If the model does not beat the GMP-only baseline, say so honestly and improve features before trusting it.
3. **Research a new IPO:** give Skill 2 to an AI with web access plus the company name. It researches, writes a prompt for other AIs, you paste their reports back, and it reconciles everything into `new_ipo.csv`.
4. **Predict:** `python model/predict.py new_ipo.csv`.
5. **Improve:** after each IPO lists, add its row (with the actual gain) to the master CSV and retrain periodically.

## 5. Honest limits

- Small dataset (hundreds of rows), so results will be rough.
- Data quality decides everything; AI-collected numbers must be spot-checked against exchange or Chittorgarh pages.
- A regime change (bull to bear market) can break the model. Check `recent_ipo_avg_gain` and the market mood yourself.
- Qualitative risks (governance, promoter issues, sector hype) are not in the numbers. Skill 2 lists them separately.
