# Phase 15: Preregistration Amendment — Tier 2b Multi-Source Outcome Verification

> **Status**: FORMALLY ADOPTED & COMMITTED BEFORE IMPLEMENTATION  
> **Target Defect**: D-073 (Audited Append-Only Outcome Correction Engine)  
> **Parent Preregistration**: [`phases/Phase 15/preregistration.md`](preregistration.md) (remains immutable)

---

## 1. Context & Motivation

Phase 14 introduced a two-tier listing outcome recording architecture:
- **Tier 1**: Official stock exchange direct scrape (NSE / BSE).
- **Tier 2**: Yahoo Finance daily price history cross-checked with an independent Chittorgarh quote page within 1.0% tolerance.

In the case of **Paras Healthcare Limited** (listed on 2026-10-28), Tier 1 was blocked by cloud WAF / 403, and Yahoo Finance returned only two bars, both stamped after the listing date (`2026-10-29` and `2026-10-30` in IST). Because `fetch_yfinance_first_session_open` lacked date equality enforcement, it fell back to row 0 (2026-10-29 bar at ₹721.00, +4.04%), recording a post-listing day price.

Under Workstream A (D-072), `fetch_yfinance_first_session_open` strictly returns `LISTING_DAY_BAR_MISSING` when no bar matches `listing_date`. To allow verified outcome recording when Yahoo lacks the listing-day bar, this amendment formally defines **Tier 2b**.

---

## 2. Specification of Tier 2b

1. **Trigger Condition**:
   - Tier 1 (Official Exchange) is blocked or returns HTTP error.
   - Tier 2 (Yahoo Finance) is unreachable or returns `LISTING_DAY_BAR_MISSING`.

2. **The 1.0% Two-Independent-Page Rule**:
   - Tier 2b accepts a listing-day opening/listing price if and only if **two independent web pages fetched by code** (neither from Yahoo Finance), each explicitly stating the IPO's `listing_date` and official opening or listing price, agree within **1.0% relative tolerance**:
     $$\text{Relative Difference} = \frac{|\text{Price}_{\text{Source A}} - \text{Price}_{\text{Source B}}|}{\text{Price}_{\text{Source A}}} \le 0.01 \quad (1.0\%)$$
   - Candidate sources include:
     - **Source A**: Chittorgarh stock price quote page (`https://www.chittorgarh.com/stockpricequote/...`) or listing summary page (`https://www.chittorgarh.com/ipo/...`).
     - **Source B**: Secondary independent financial / IPO tracker (e.g., `https://www.gmpipowatch.in/...` or equivalent IPO listing day price publisher).

3. **Evidence Persistence**:
   - Both raw HTTP responses must be saved verbatim to `data/evidence/actuals/` as `.txt` files with content SHA256 hashes.
   - Accompanying `.json` manifests must document the source URL, access timestamp, page date, HTTP status, and parsed prices.

4. **Outcome Attribution & Tier Reporting**:
   - Rows recorded or corrected under this protocol must set `outcome_source=tier2b`.
   - All reports, evaluations, and dashboards must report Tier 2b rows under their distinct tier label (`Tier 2b: Multi-Source Independent Cross-Check`).
   - If two independent pages agreeing within 1.0% cannot be retrieved by code, **nothing is recorded**, status remains `PENDING_REVIEW`, and an alert is flagged.

5. **Log Immutability**:
   - If a row is already present in `predictions/prediction_log.csv` with an erroneous price, `prediction_log.csv` must **never be edited**.
   - The correction must be appended to `predictions/outcome_corrections.csv` and resolved via `opi.outcomes.effective_outcome()`.
