# OPI Dataset Audit Report (Phase 6, Gate A6 Item S1)

> Date: 2026-10-15  
> Auditor: Antigravity (Phase 6 Execution)  
> Dataset: `data/ipo_master.csv`  
> Baseline: Phase 5 Master (749 rows) -> Phase 6 Cleaned Master (731 rows)

---

## 1. Audit Methodology & Automated Flagging

Per [`references/inclusion_criteria.md`](../references/inclusion_criteria.md), every row in `data/ipo_master.csv` was subjected to seven automated integrity and inclusion checks via [`scripts/audit_dataset.py`](../scripts/audit_dataset.py):

1. **`PRICE_RATIO_LOW`**: `listing_price / issue_price < 0.40` (listing discount > 60%).
2. **`PRICE_RATIO_HIGH`**: `listing_price / issue_price > 4.0` (listing gain > 300%).
3. **`DATE_ORDER_ERROR`**: `listing_date <= close_date` (listing chronologically precedes bidding close).
4. **`DUPLICATE_COMPANY`**: Same company name appears multiple times in the master dataset.
5. **`NEGATIVE_SUBSCRIPTION`**: `sub_total < 0` or any category subscription < 0.
6. **`GAIN_INCONSISTENT`**: `|listing_gain_pct - ((listing_price / issue_price) - 1) * 100| > 1.0%`.
7. **`MISSING_ISSUE_PRICE`**: `issue_price` is null or <= 0.
8. **`EXCLUDED_ROW_PRESENT`**: Row matches a company listed in `data/excluded_rows.csv`.

---

## 2. Complete Inventory of Flagged Rows & Verified Outcomes

### A. Severe Anomalies / FPO Violations (3 Rows Flagged & Excluded)

| Company | Stated Dates (List) | Stated Issue Price | Stated Listing Price | Stated Listing Gain | Automated Flag | Exchange / Regulatory Verification Findings | Decision & Action |
|---|:---:|:---:|:---:|:---:|:---:|---|:---:|
| **Patanjali Foods** | 2022-04-08 | ₹650.00 | ₹31.23 | -95.20% | `PRICE_RATIO_LOW` (ratio 0.05), extreme negative gain | **FPO / Scraping Bug**: Company was previously listed as Ruchi Soya Industries Limited on BSE/NSE since the 1990s. In April 2022 it launched a ₹4,300 Cr FPO to meet SEBI minimum public shareholding requirements. On April 8, 2022, it listed at ₹850 on BSE (+30.77%) and ₹853 on NSE (+31.23%). The scraper mistakenly saved the string `31.23` (the percentage gain) as the rupee `listing_price`. Not a fresh mainboard IPO. | **EXCLUDED**<br>(Logged in `data/excluded_rows.csv`) |
| **Adani Enterprises** | 2023-02-08 | ₹3,276.00 | ₹437.20 | -86.65% | `PRICE_RATIO_LOW` (ratio 0.13), extreme negative gain | **Withdrawn FPO / Non-Listing**: Adani Enterprises has been listed on BSE since 1994. In Jan 2023 it launched a ₹20,000 Cr FPO. On Feb 1, 2023, following the Hindenburg Research report, the board called off the FPO and refunded all money. No shares were allotted and no listing occurred on Feb 8, 2023. `437.20` is a scraping artifact. Not a fresh mainboard IPO. | **EXCLUDED**<br>(Logged in `data/excluded_rows.csv`) |
| **Vodafone Idea** | 2024-04-25 | ₹75.00 | ₹35.85 | -52.20% | Extreme negative gain (< -50%) | **FPO / Data Conflation**: Vodafone Idea has been listed on BSE/NSE since March 2007 (Idea Cellular IPO). In April 2024 it conducted an ₹18,000 Cr FPO at ₹11/share (listing at ₹11.80, +7.27%). The dataset conflated the 2007 Idea Cellular IPO price (₹75) with the Government equity stake percentage (35.85%) and the 2024 FPO date. Not a fresh mainboard IPO. | **EXCLUDED**<br>(Logged in `data/excluded_rows.csv`) |

### B. Duplicate Entries (15 Companies, 30 Rows Flagged)

Automated check flagged 15 companies appearing twice in `data/ipo_master.csv` due to merging overlapping data feeds (Bansal dataset vs. Chittorgarh scraping):

| Company | Occurrence 1 (Kept) | Occurrence 2 (Removed) | Root Cause & Resolution |
|---|---|---|---|
| **Aeroflex Industries** | 2023-09-01 (sub: 69.39x) | 2023-08-31 (duplicate date) | Duplicate scraper feed entry; kept row with full metadata. |
| **Ags Transact Technologies** | 2022-02-01 (sub: 5.23x) | 2022-01-31 (duplicate date) | Duplicate scraper feed entry; kept row with verified listing date. |
| **Anthem Biosciences** | 2025-07-21 (sub: 47.37x) | 2025-07-15 (sub: 63.86x) | Inconsistent sub figures from early bidding; kept final allotment row. |
| **Arisinfra Solutions** | 2025-06-25 (sub: 1.96x) | 2025-02-10 (sub: 2.65x) | Date revision; kept finalized listing row. |
| **Gopal Snacks** | 2024-03-14 (sub: 9.02x) | 2024-03-13 (sub: 6.88x) | Day-2 vs Day-3 bidding log; kept final closing demand row. |
| **Innovision** | 2026-03-23 (sub: 3.47x) | 2026-03-20 (sub: 3.35x) | Day-2 vs Day-3 bidding log; kept final closing demand row. |
| **Irm Energy** | 2023-10-31 (sub: 19.30x) | 2023-10-26 (duplicate) | Feed duplication; kept row with complete financials. |
| **Mankind Pharma** | 2023-05-09 (sub: 15.32x) | 2023-05-08 (sub: 11.01x) | Final day 3 subscription vs day 2; kept final total demand. |
| **Mukka Proteins** | 2024-03-07 (sub: 136.99x) | 2024-03-04 (sub: 95.35x) | Day 2 vs Day 3 bidding; kept final 136.99x demand and NSE listing price. |
| **Plaza Wires** | 2023-10-13 (sub: 113.74x) | 2023-10-12 (duplicate) | Duplicate listing notice; kept final closing row. |
| **Pyramid Technoplast** | 2023-08-30 (sub: 14.98x) | 2023-08-29 (duplicate) | Listing date adjustment; kept finalized row. |
| **Travel Food Services** | 2025-07-14 (sub: 2.88x) | 2025-07-10 (sub: 2.40x) | Final allotment demand vs day 2 demand; kept final row. |
| **Utkarsh Small Finance Bank** | 2023-07-24 (sub: 61.41x) | 2023-07-21 (duplicate) | Feed duplication; kept finalized allotment row. |
| **Veranda Learning Solutions** | 2022-04-11 (sub: 188.38x) | 2022-04-07 (sub: 2.35x) | Early bidding vs final closed subscription; kept final allotment. |
| **Western Carriers India** | 2024-09-24 (sub: 30.57x) | 2024-09-23 (sub: 22.51x) | Final day subscription update; kept final row. |

---

## 3. Dataset Audit Summary (Before vs After)

| Metric / Check | Before Audit (Phase 5 Master) | After Audit (Phase 6 Master) | Net Change |
|---|:---:|:---:|:---:|
| **Total Rows** | 749 | 731 | -18 rows (-3 FPOs, -15 duplicates) |
| **FPOs / Rights Issues** | 3 (Patanjali, Adani, Vodafone Idea) | **0** | -3 (100% purged) |
| **Duplicate Companies** | 15 companies (30 rows) | **0** | -15 duplicates purged |
| **Minimum Listing Gain** | -95.20% (Patanjali bug) | **-49.38%** | +45.82% (unphysical tails removed) |
| **Maximum Listing Gain** | +252.76% | **+252.76%** | Unchanged |
| **Mean Listing Gain** | +22.45% | **+23.08%** | +0.63% |
| **Unresolved Audit Violations** | 18 | **0** | PASS (0 violations) |

Every row removed from `data/ipo_master.csv` is documented with source evidence in [`data/excluded_rows.csv`](excluded_rows.csv).
