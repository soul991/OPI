# Standardized Definitions: Fundamental Metrics (OPI Phase 5)

This document standardizes the extraction, calculation, and provenance auditing methodology for all fundamental valuation and financial performance metrics across Indian Mainboard IPOs (2021–2026).

---

## 1. Statutory Source Hierarchy
All metrics must be extracted strictly from statutory pre-listing documents or audited restated financial statements, prioritizing:
1. **Red Herring Prospectus (RHP) / Prospectus**: Section titled *"Financial Statements Summary"*, *"Restated Consolidated Summary Statement of Profit and Losses"*, and *"Basis for Issue Price"*.
2. **Draft Red Herring Prospectus (DRHP)** / Statutory Exchange Filings (NSE/BSE Public Offerings Portal).
3. **Primary Aggregator Verification**: Chittorgarh / Moneycontrol IPO Financials Summary (used for cross-auditing and spot-checks only; secondary).

**Rule**: Always use the **latest full fiscal year (FY) completed immediately prior to the issue opening date**. E.g., for an issue opening in September 2024, use FY2024 (ended March 31, 2024) audited restated numbers. Do NOT use annualized stub or partial quarters unless explicitly noted.

---

## 2. Metric Formulas & Calculation Standards

### A. Return on Equity (ROE) (%)
- **Definition**: Profit After Tax divided by Average Total Net Worth.
- **Formula**:
  $$\text{ROE} = \frac{\text{PAT}_{\text{FY}}}{\text{Average Net Worth}} \times 100$$
  where $\text{Average Net Worth} = \frac{\text{Net Worth}_{\text{FY}} + \text{Net Worth}_{\text{FY}-1}}{2}$.
- **Fallback**: If Net Worth for FY-1 is unavailable, use closing Net Worth for FY: $\text{PAT}_{\text{FY}} / \text{Net Worth}_{\text{FY}} \times 100$.
- **Field Name**: `roe`

### B. Return on Capital Employed (ROCE) (%)
- **Definition**: Earnings Before Interest and Taxes (EBIT) divided by Capital Employed.
- **Formula**:
  $$\text{ROCE} = \frac{\text{EBIT}_{\text{FY}}}{\text{Capital Employed}_{\text{FY}}} \times 100$$
  where $\text{Capital Employed} = \text{Total Assets} - \text{Current Liabilities}$ (or $\text{Total Net Worth} + \text{Total Debt}$).
- **Field Name**: `roce`

### C. Revenue Growth (%)
- **Definition**: Year-over-Year percentage growth in Total Revenue from Operations.
- **Formula**:
  $$\text{Revenue Growth \%} = \frac{\text{Revenue}_{\text{FY}} - \text{Revenue}_{\text{FY}-1}}{\text{Revenue}_{\text{FY}-1}} \times 100$$
- **Field Name**: `revenue_growth_pct`

### D. Profit After Tax (PAT) Margin (%)
- **Definition**: Restated Consolidated Net Profit after Tax divided by Total Revenue from Operations.
- **Formula**:
  $$\text{PAT Margin \%} = \frac{\text{PAT}_{\text{FY}}}{\text{Revenue}_{\text{FY}}} \times 100$$
- **Field Name**: `pat_margin_pct`

### E. Debt-to-Equity Ratio (D/E)
- **Definition**: Total Borrowings (Long-Term + Short-Term Debt) divided by Total Equity / Net Worth.
- **Formula**:
  $$\text{D/E} = \frac{\text{Total Debt}_{\text{FY}}}{\text{Net Worth}_{\text{FY}}}$$
- **Field Name**: `debt_equity`

### F. Price-to-Earnings Ratio (P/E)
- **Definition**: Issue Price divided by Restated Basic/Diluted EPS for the latest fiscal year prior to issue.
- **Formula**:
  $$\text{P/E} = \frac{\text{Issue Price}}{\text{Restated Diluted EPS}_{\text{FY}}}$$
- **Field Name**: `pe_ratio`

### G. Peer Median P/E
- **Definition**: Median P/E of the listed industry peers disclosed in the *"Basis for Issue Price"* section of the RHP.
- **Field Name**: `peer_median_pe`

---

## 3. Provenance & Confidence Tagging

Every sourced metric stored in `data/fundamentals_sourced.csv` requires:
- `company`: Official issuer company name matching master dataset.
- `metric`: Column name (`roe`, `roce`, `revenue_growth_pct`, `pat_margin_pct`, `debt_equity`, `pe_ratio`, `peer_median_pe`).
- `value`: Numeric calculated value.
- `fiscal_year`: Fiscal year audited (e.g., `FY24`).
- `source_url`: URL or file identifier for the prospectus/statutory filing.
- `page_or_section`: Section/Page identifier in the RHP.
- `confidence`:
  - `high`: Extracted directly from audited RHP restated financials table.
  - `medium`: Extracted from reputable statutory aggregator filing sheet with verified match.
  - `low`: Ambiguous or unverified source (forbidden in production dataset).

---

## 4. Phase 5 Acceptance Criteria
1. **Coverage Target**: $\ge 70\%$ populated across 2021–2026 for any metric to enter the feature matrix. Any column failing $70\%$ coverage is excluded from modeling.
2. **Spot-Check Accuracy**: A random sample of 40 filled rows verified against secondary sources must achieve $\ge 95\%$ match within a $2\%$ relative tolerance.
