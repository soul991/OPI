# Inclusion Criteria for OPI Master Dataset

> Created: 2026-10-15 (Phase 6, Gate A6 Item S1)

## Rule

A row is included in `data/ipo_master.csv` if and only if **all** of the following hold:

1. **Fresh mainboard IPO**: The company was **not previously listed** on any recognized Indian stock exchange (NSE, BSE) before the issue.
2. **Initial public offering**: The issue is a fresh sale of equity shares (with or without an offer-for-sale component) to the public for the **first time**.
3. **Mainboard listing**: The issue listed on the NSE or BSE mainboard. SME-platform listings are excluded.
4. **Completed listing**: The company actually listed (received a listing price). Withdrawn or cancelled issues are excluded.

## Excluded Issue Types

The following are **not** fresh mainboard IPOs and must be excluded:

- **Follow-on Public Offerings (FPOs)**: Secondary offerings by companies already listed.
- **Rights Issues**: Offered to existing shareholders only.
- **Offer-for-Sale (OFS) of already-listed companies**: Pure OFS by promoters of listed companies.
- **Re-listings**: Companies that delisted and re-listed.
- **Withdrawn/cancelled issues**: Issues that were fully withdrawn before allotment or listing.
- **SME IPOs**: Issues listed on the SME platform of NSE or BSE.

## Automated Audit Flags

The audit script (`scripts/audit_dataset.py`) flags rows for manual verification if any of the following hold:

| Flag | Condition | Rationale |
|------|-----------|-----------|
| `PRICE_RATIO_LOW` | `listing_price / issue_price < 0.4` | Extreme loss suggests an FPO, corporate action, or data error |
| `PRICE_RATIO_HIGH` | `listing_price / issue_price > 4.0` | Extreme gain suggests a data error |
| `DATE_ORDER_ERROR` | `listing_date <= close_date` | Listing must be after the close of the issue |
| `DUPLICATE_COMPANY` | Same company name appears more than once | May indicate FPO or duplicate entry |
| `NEGATIVE_SUBSCRIPTION` | `sub_total < 0` or any category subscription < 0 | Impossible value |
| `GAIN_INCONSISTENT` | `abs(listing_gain_pct - (listing_price/issue_price - 1)*100) > 1.0` | Computed gain does not match stated gain |
| `MISSING_ISSUE_PRICE` | `issue_price` is NaN or <= 0 | Cannot compute gain without issue price |

Every flagged row must be manually verified against an exchange, SEBI, or prospectus source and resolved as:
- `KEEP (verified)`: Row is a genuine mainboard IPO.
- `CORRECTED (old -> new)`: Data error corrected.
- `EXCLUDED (reason)`: Row removed and logged in `data/excluded_rows.csv`.
