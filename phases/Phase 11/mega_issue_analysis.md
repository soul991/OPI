# Mega-Issue Historical Analysis (Issues > ₹10,000 Cr, n=13)

> Mandated by Phase 11 Workstream A (D-040).
> **Epistemic Notice**: Descriptive report only. Due to small sample size ($n = 13$), no generalizable statistical claims or causal inferences are made.

---

## 1. Context & Motivation
Jio Platforms Limited has an issue size of **₹30,213.00 Cr**, which exceeds the maximum issue size present in the entire historical training dataset (`data/ipo_master.csv`, max ₹27,870.16 Cr = Hyundai Motor India). Scoring an issue larger than any issue the model was trained on represents an out-of-distribution extrapolation.

---

## 2. Descriptive Historical Table ($n = 13$)

The table below lists all 13 issues in `data/ipo_master.csv` with `issue_size_cr > 10,000.00 Cr`, sorted by issue size descending:

| Company | Listing Date | Issue Size (₹ Cr) | Listing Gain (%) | Observed GMP (%) |
|---|:---:|:---:|:---:|:---:|
| **Hyundai Motor India** | 2024-10-22 | ₹27,870.16 | -1.33% | +3.16% |
| **Life Insurance Corporation of India (LIC)** | 2022-05-17 | ₹21,008.48 | -8.62% | -2.74% |
| **One 97 Communications (Paytm)** | 2021-11-18 | ₹18,915.90 | -9.07% | NOT_RECORDED |
| **Tata Capital** | 2025-10-13 | ₹15,511.87 | +1.23% | +0.00% |
| **Coal India** | 2010-11-04 | ₹15,199.44 | +18.78% | NOT_RECORDED |
| **HDB Financial Services** | 2025-07-02 | ₹12,500.00 | +12.84% | +10.14% |
| **SBI Funds Management** | 2026-07-21 | ₹11,692.91 | +6.85% | NOT_RECORDED |
| **LG Electronics India** | 2025-10-14 | ₹11,607.01 | +50.01% | +40.35% |
| **Swiggy** | 2024-11-13 | ₹11,327.43 | +7.69% | +0.00% |
| **General Insurance Corporation of India** | 2017-10-25 | ₹11,175.84 | -6.80% | NOT_RECORDED |
| **ICICI Prudential Asset Management** | 2025-12-19 | ₹10,602.65 | +20.09% | +7.48% |
| **SBI Cards and Payment Services** | 2020-03-16 | ₹10,354.77 | -12.45% | NOT_RECORDED |
| **NTPC Green Energy** | 2024-11-27 | ₹10,009.71 | +3.24% | +0.93% |

---

## 3. Summary Observations (Descriptive)
- **Top 3 Mega-Issues**: The three largest historical IPOs (Hyundai ₹27,870 Cr, LIC ₹21,008 Cr, Paytm ₹18,916 Cr) all listed with negative listing gains (-1.33%, -8.62%, -9.07%).
- **Overall Statistics ($n = 13$)**:
  - Mean Listing Gain: **+6.34%**
  - Median Listing Gain: **+3.24%**
  - Positive Listings: 8 of 13 (61.5%)
  - Negative Listings: 5 of 13 (38.5%)
  - Maximum Pop: +50.01% (LG Electronics India, supported by +40.35% GMP)
  - Minimum Listing: -12.45% (SBI Cards, listed during the March 2020 market crash)
- **Extrapolation Risk**:
  Jio Platforms (₹30,213 Cr) is 8.4% larger than Hyundai and 43.8% larger than LIC. Because tree-based gradient boosted models cannot extrapolate beyond training extremes, model point estimates for issues exceeding training maximums carry severe uncertainty and are flagged as `LOW` confidence.
