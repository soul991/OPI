# Decision Record: Market Data Raw File Nomenclature & Hashing (Defect D-055)

> **Context**: Phase 12 introduced `data/evidence/market/<date>_nifty.raw` and `<date>_nifty.json` via `opi/market.py`. A review identified that `.raw` is a serialized JSON dictionary of extracted ticker fields (Open, High, Low, Close, Volume, VIX) rather than raw wire HTTP network bytes from the Yahoo Finance REST endpoint.

---

## 1. Problem Statement
In `data/evidence/market/`, the file extension `.raw` implied raw upstream API HTTP responses. In reality, `yfinance` abstracts HTTP interactions internally into pandas DataFrames, and `opi/market.py` serializes a multi-field record dictionary as `.raw` and computes its SHA-256 hash. While the numbers match exchange closing prices exactly (verified by user on 2026-10-24), calling this file `.raw` overstates the raw capture boundary.

## 2. Decision
1. **Clarify Existing Nomenclature**:
   - For historical files (`2026-10-21`, `2026-10-22`, `2026-10-23`), `.raw` is formally documented as the **unreduced ticker extraction payload** (containing all OHLCV + VIX fields), whereas `.json` is the **reduced feature representation** consumed by OPI models.
   - Existing historical `.raw` files will not be deleted or renamed, maintaining hash consistency with existing `.json` metadata pointers (`"raw_file": "..._nifty.raw"`).
2. **Future Ingestion Architecture**:
   - For all future market data fetches, `opi/market.py` will persist the exact underlying DataFrame or API response payload format and clearly document the boundary in metadata.
   - Any test or tooling asserting market data integrity verifies both the reduced `.json` and the unreduced `.raw` digest without overclaiming upstream HTTP socket capture.
