# October 21 Listing Readiness Checklist: HD Fire Protect Limited

**Target Company:** HD Fire Protect Limited  
**Scheduled Listing Date:** 2026-10-21  
**Listing Exchange:** BSE, NSE  
**Issue Price:** INR 271.00  
**Active Prediction Row Status:** FORWARD (Predicted gain: +26.12%, P(gain > 10%): 95.5%)

---

## 1. Pre-Flight Verification (Read-Only)

Confirm that HD Fire Protect Limited is pending listing and has not yet had an actual recorded:

```bash
python scripts/update_actuals.py
```

Expected output:
```text
Pending FORWARD outcomes (read-only):
- HD Fire Protect Limited | 2026-10-21 | scheduled for 2026-10-21
- Fusion CX Limited | 2026-10-22 | scheduled for 2026-10-22
```

---

## 2. Listing-Day Verification Rules

1. **Wait for Market Opening:** The official listing price must be observed strictly after official trading begins (10:00 AM IST on October 21, 2026).
2. **Official Source Required:** Evidence must come directly from HTTPS pages on `nseindia.com` or `bseindia.com`.
3. **No Direct Gain Typing:** The tool computes listing gain automatically from `official_opening_price` and the recorded pre-listing `issue_price` (INR 271.00). Direct entry is disabled.
4. **Immutable Snapshots:** Evidence files and cryptographic SHA-256 manifests are saved automatically under `data/evidence/actuals/`. No existing actuals can be overwritten.

---

## 3. Execution Commands

### Mode A: Direct URL Mode (Code-Fetched Official Exchange Page)

Use when the exchange page is accessible directly via HTTPS requests:

```bash
python scripts/update_actuals.py \
  --company "HD Fire Protect Limited" \
  --source-url "https://www.nseindia.com/get-quote/equity/HDFIRE" \
  --actual-listing-price <OFFICIAL_OPEN_PRICE> \
  --page-date "2026-10-21" \
  --company-quote "HD Fire Protect Limited" \
  --price-quote "Open <OFFICIAL_OPEN_PRICE>"
```

*Note: `--price-quote` accepts either `"Open Price <PRICE>"`, `"Listing Price <PRICE>"`, or `"Open <PRICE>"` as displayed on the exchange quote page.*

---

### Mode B: Evidence File Mode (Browser-Saved Official Exchange Page)

Use if network firewalls, bot detection, or JavaScript rendering block direct code fetching from the host machine:

1. Open the official NSE or BSE quote page in a browser:
   - NSE: `https://www.nseindia.com/get-quote/equity/HDFIRE`
   - BSE: `https://www.bseindia.com/stock-share-price/hd-fire-protect-ltd/...`
2. Save the complete web page (HTML) to disk, e.g. `data/evidence/actuals/hdfire_20261021_browser.html`.
3. Execute the update with `--evidence-file`:

```bash
python scripts/update_actuals.py \
  --company "HD Fire Protect Limited" \
  --source-url "https://www.nseindia.com/get-quote/equity/HDFIRE" \
  --evidence-file "data/evidence/actuals/hdfire_20261021_browser.html" \
  --actual-listing-price <OFFICIAL_OPEN_PRICE> \
  --page-date "2026-10-21" \
  --company-quote "HD Fire Protect Limited" \
  --price-quote "Open <OFFICIAL_OPEN_PRICE>"
```

---

## 4. Post-Update Verification

1. Re-run pending check to confirm HD Fire Protect is completed:
   ```bash
   python scripts/update_actuals.py
   ```
2. Verify repo integrity and evidence manifests:
   ```bash
   python scripts/verify_all.py
   ```
3. Commit and push the updated log and evidence snapshot within 2 hours:
   ```bash
   git add predictions/prediction_log.csv data/evidence/actuals/ dashboard/index.html
   git commit -m "record: HD Fire Protect official listing outcome"
   git push origin main
   ```
