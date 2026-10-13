# Master CSV schema

Column order must match exactly. Empty cell = unknown.

| Column | Type | Definition |
|---|---|---|
| company | text | Company name |
| sector | text | Broad sector |
| exchange | text | NSE, BSE or BOTH |
| open_date | YYYY-MM-DD | Bidding opens |
| close_date | YYYY-MM-DD | Bidding closes |
| listing_date | YYYY-MM-DD | First trading day |
| issue_price | number | Upper price band, INR |
| issue_size_cr | number | Total issue size, INR crore |
| fresh_issue_pct | number | % of issue that is fresh shares (0-100) |
| ofs_pct | number | % that is offer for sale (0-100) |
| lot_size | integer | Shares per lot |
| sub_qib | number | Final QIB subscription (times) |
| sub_nii | number | Final NII/HNI subscription (times) |
| sub_retail | number | Final retail subscription (times) |
| sub_total | number | Final overall subscription (times) |
| pe_ratio | number | Issue P/E on latest earnings (empty if loss-making) |
| peer_median_pe | number | Median P/E of listed peers |
| roe | number | Return on equity, % |
| roce | number | Return on capital employed, % |
| debt_equity | number | Debt to equity ratio |
| revenue_growth_pct | number | Latest year revenue growth, % |
| pat_margin_pct | number | Profit after tax margin, % |
| gmp_pct | number | Grey market premium as % of issue price, on last bidding day |
| nifty_30d_return | number | Nifty 50 return over 30 days before open_date, % |
| india_vix | number | India VIX close on close_date |
| recent_ipo_avg_gain | number | Average listing_gain_pct of the previous 5 mainboard IPOs before open_date |
| listing_price | number | Price at which it listed (opening price), INR |
| listing_gain_pct | number | (listing_price - issue_price) / issue_price x 100 |
| label_good | 0 or 1 | 1 if listing_gain_pct > 10 |
| source_urls | text | Semicolon-separated sources |
| notes | text | Conflicts, caveats |

Model features: sector, exchange, issue_price ... recent_ipo_avg_gain (excluding company and dates).
Targets: listing_gain_pct, label_good. `new_ipo.csv` has all columns but leaves the target, listing_price, source and notes columns empty or filled with sources only.
