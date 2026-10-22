# Phase 10: Forward Results Log

> Updated as of 2026-10-23T01:38:22+05:30 (Post-Phase 10 Verification Patch). In accordance with RULES.md, PHASE_PROTOCOL.md, and Phase 10 Plan Section 2 (Gate Item X1).

## 1. Summary of Evaluated Forward IPOs

| Company | Bidding Close Date | Listing Date | Issue Price (INR) | Official Listing Price (INR) | Actual Listing Gain (%) | Model Predicted Gain (%) | GMP at Close (%) | Absolute Error: Model (% pts) | Absolute Error: Raw GMP (% pts) | Status & Evidence |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-15 | 2026-10-21 | 271.00 | 334.40 | +23.39% | +26.12% | +30.26% | 2.73 | 6.87 | **RECORDED** (Official BSE quote, snapshot `data/evidence/actuals/2026-10-21_hd-fire-protect-limited_1995cac2f37d.html`) |
| **Fusion CX Limited** | 2026-10-16 | 2026-10-22 | 289.00 | Pending | Pending | +4.33% | None (NOT_RECORDED) | Pending | N/A | **PENDING OFFICIAL EVIDENCE** (Listing 2026-10-22 passed; exchange automated fetch blocked by 403 / dynamic JS; awaiting browser-saved official snapshot) |
| **Zetwerk Manufacturing Business Limited** | 2026-10-19 | 2026-10-23 | 151.00 | Pending | Pending | -0.77% | +2.32% | Pending | Pending | **PENDING MARKET OPEN** (Scheduled 2026-10-23; market currently closed at 01:38 AM IST pre-open; opens 09:15 AM IST) |
| **Sahajanand Medical Technologies Limited** | 2026-10-19 | 2026-10-23 | 344.00 | Pending | Pending | +8.32% | +6.98% | Pending | Pending | **PENDING MARKET OPEN** (Scheduled 2026-10-23; market currently closed at 01:38 AM IST pre-open; opens 09:15 AM IST) |
| **Tonbo Imaging India Limited** | 2026-10-19 | 2026-10-23 | 700.00 | Pending | Pending | +74.70% | +72.86% | Pending | Pending | **PENDING MARKET OPEN** (Scheduled 2026-10-23; market currently closed at 01:38 AM IST pre-open; opens 09:15 AM IST) |
| **Bonfiglioli Transmissions Limited** | 2026-10-19 | 2026-10-23 | 586.00 | Pending | Pending | +21.10% | +21.67% | Pending | Pending | **PENDING MARKET OPEN** (Scheduled 2026-10-23; market currently closed at 01:38 AM IST pre-open; opens 09:15 AM IST) |

---

## 2. Evidence Verification for HD Fire Protect Limited
- **Exchange:** BSE (Scrip Code: 544994, Symbol: HDFIRE)
- **Source URL:** `https://www.bseindia.com/stock-share-price/hd-fire-protect-ltd/hdfire/544994`
- **Official Open Price:** INR 334.40
- **Pre-listing Issue Price:** INR 271.00
- **Computed Gain:** +23.39% ($((334.40 - 271.00) / 271.00) \times 100\%$)
- **Snapshot Path:** `data/evidence/actuals/2026-10-21_hd-fire-protect-limited_1995cac2f37d.html`
- **Manifest Path:** `data/evidence/actuals/2026-10-21_hd-fire-protect-limited_1995cac2f37d.json`
- **SHA-256 Digest:** `1995cac2f37d239f67aa80fb6bccf25a13d6aa6511ec2f9f7f50cbf6015b459e`
- **Verification Method:** Browser-saved official BSE quote page parsed and verified by `opi.actuals.record_actual_from_exchange`.

---

## 3. Explanations for Unrecorded Actual Outcomes
Under `PHASE_PROTOCOL.md` Section 4 and `RULES.md`, pre-listing features and actual outcomes cannot be recorded before official exchange trading commences, and no actual outcome may be typed by hand or recorded without verified exchange evidence.

1. **Fusion CX Limited (Listing Date: 2026-10-22)**:
   - **Status**: PENDING OFFICIAL EVIDENCE.
   - **Reason**: The scheduled listing date (2026-10-22) has passed. However, automated network fetching against official exchange endpoints (BSE Scrip 544995, NSE Symbol FUSIONCX) fails due to exchange infrastructure anti-bot defenses (Akamai HTTP 403 Forbidden on BSE API and NSE quote endpoints, and client-side dynamic JavaScript rendering on BSE HTML quote pages). Per project protocol, no outcome can be recorded without verified exchange snapshot evidence, and no browser-saved page (`--evidence-file`) has been provided by the user. Per instructions, the row remains pending until official evidence is saved and provided.

2. **Zetwerk Manufacturing Business Limited (Listing Date: 2026-10-23)**:
   - **Status**: PENDING MARKET OPEN.
   - **Reason**: As of 2026-10-23T01:38:22+05:30 IST, Indian stock exchanges (BSE & NSE) are in pre-market overnight off-hours. Regular equity market trading does not commence until 09:15 AM IST. Therefore, official opening trades and prices do not yet exist.

3. **Sahajanand Medical Technologies Limited (Listing Date: 2026-10-23)**:
   - **Status**: PENDING MARKET OPEN.
   - **Reason**: As of 2026-10-23T01:38:22+05:30 IST, markets are closed. Actuals cannot be recorded before market opening at 09:15 AM IST.

4. **Tonbo Imaging India Limited (Listing Date: 2026-10-23)**:
   - **Status**: PENDING MARKET OPEN.
   - **Reason**: As of 2026-10-23T01:38:22+05:30 IST, markets are closed. Actuals cannot be recorded before market opening at 09:15 AM IST.

5. **Bonfiglioli Transmissions Limited (Listing Date: 2026-10-23)**:
   - **Status**: PENDING MARKET OPEN.
   - **Reason**: As of 2026-10-23T01:38:22+05:30 IST, markets are closed. Actuals cannot be recorded before market opening at 09:15 AM IST.
