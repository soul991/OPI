# Phase 10: Forward Results Log

> As of 2026-10-21T12:53:35+05:30. In accordance with RULES.md, PHASE_PROTOCOL.md, and Phase 10 Plan Section 2 (Gate Item X1).

## 1. Summary of Evaluated Forward IPOs

| Company | Bidding Close Date | Listing Date | Issue Price (INR) | Official Listing Price (INR) | Actual Listing Gain (%) | Model Predicted Gain (%) | GMP at Close (%) | Absolute Error: Model (% pts) | Absolute Error: Raw GMP (% pts) | Status & Evidence |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-15 | 2026-10-21 | 271.00 | 334.40 | +23.39% | +26.12% | +30.26% | 2.73 | 6.87 | **RECORDED** (Official BSE quote, snapshot `data/evidence/actuals/2026-10-21_hd-fire-protect-limited_1995cac2f37d.html`) |
| **Fusion CX Limited** | 2026-10-16 | 2026-10-22 | 289.00 | Pending | Pending | +12.40% | N/A | - | - | **PENDING LISTING** (Scheduled 2026-10-22; cannot record before market opens) |
| **Zetwerk Manufacturing Business Limited** | 2026-10-19 | 2026-10-23 | 315.00 | Pending | Pending | +24.81% | +22.22% | - | - | **PENDING LISTING** (Scheduled 2026-10-23; cannot record before market opens) |
| **Sahajanand Medical Technologies Limited** | 2026-10-19 | 2026-10-23 | 414.00 | Pending | Pending | +28.94% | +31.40% | - | - | **PENDING LISTING** (Scheduled 2026-10-23; cannot record before market opens) |
| **Tonbo Imaging India Limited** | 2026-10-19 | 2026-10-23 | 525.00 | Pending | Pending | +19.65% | +17.14% | - | - | **PENDING LISTING** (Scheduled 2026-10-23; cannot record before market opens) |
| **Bonfiglioli Transmissions Limited** | 2026-10-19 | 2026-10-23 | 680.00 | Pending | Pending | +14.22% | +11.76% | - | - | **PENDING LISTING** (Scheduled 2026-10-23; cannot record before market opens) |

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
Under `PHASE_PROTOCOL.md` Section 4 and `RULES.md`, pre-listing features and actual outcomes cannot be recorded before official exchange trading commences.
- **Fusion CX Limited:** Listing scheduled for 2026-10-22. As today is 2026-10-21, trading has not yet commenced on NSE/BSE. Actuals must remain empty until 2026-10-22 post-market opening.
- **Zetwerk, Sahajanand Medical, Tonbo Imaging, Bonfiglioli:** Listing scheduled for 2026-10-23. As today is 2026-10-21, trading has not commenced. Actuals must remain empty until 2026-10-23.
