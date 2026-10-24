# Forward Test Weekly Status & App Hygiene Report

> Generated directly from `predictions/prediction_log.csv`.
> **Notice: Provisional, n < 30 (n = 6 listed). Strictly descriptive, no performance claims permitted.**

---

## 1. Summary Headline Metrics (n = 6 of 30)

- **Total FORWARD rows logged**: 8
- **Completed Listings (n listed)**: 6
- **Pending Listings (n pending)**: 2 (`Jio Platforms Limited`, `Paras Healthcare Limited`; list date 2026-10-28)
- **Model MAE (n = 6)**: 6.78 percentage points
- **Raw GMP MAE (n = 5 with observed GMP)**: 7.95 percentage points
- **80% Conformal Interval Empirical Coverage**: 6 / 6 (100.0%)

---

## 2. Prospective Prediction Tracking Table

| Company | Scored At | Listing Date | Predicted Gain | GMP at Scoring | Actual Listing Gain | Model Error | GMP Error | 80% Conformal Interval | Covered? | Confidence & Guard Flags | D-044 Sector Audit |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|:---:|
| **HD Fire Protect Limited** | 2026-10-16 21:22 | 2026-10-21 | +26.12% | +30.26% | +23.39% | 2.73 pp | 6.87 pp | [+5.8%, +54.7%] | YES | **NORMAL** | VERIFIED |
| **Fusion CX Limited** | 2026-10-17 10:19 | 2026-10-22 | +4.33% | None | +5.54% | 1.21 pp | N/A | [-20.1%, +28.8%] | YES | **NORMAL** | VERIFIED |
| **Zetwerk Manufacturing Business Limited** | 2026-10-20 14:01 | 2026-10-23 | -0.77% | +2.32% | +5.46% | 6.23 pp | 3.14 pp | [-22.2%, +26.8%] | YES | **NORMAL** | VERIFIED |
| **Sahajanand Medical Technologies Limited** | 2026-10-20 14:01 | 2026-10-23 | +8.32% | +6.98% | +7.89% | 0.43 pp | 0.91 pp | [-17.5%, +31.5%] | YES | **NORMAL** | VERIFIED |
| **Tonbo Imaging India Limited** | 2026-10-20 14:01 | 2026-10-23 | +74.70% | +72.86% | +65.71% | 8.99 pp | 7.15 pp | [+48.4%, +97.3%] | YES | **NORMAL** | VERIFIED |
| **Bonfiglioli Transmissions Limited** | 2026-10-20 14:01 | 2026-10-23 | +21.10% | +21.67% | +0.00% | 21.10 pp | 21.67 pp | [-2.8%, +46.2%] | YES | **NORMAL** | VERIFIED |
| **Jio Platforms Limited** | 2026-10-24 02:41 | 2026-10-28 | +22.14% | +22.34% | *Pending (Oct 28)* | Pending | Pending | [-2.1%, +46.8%] | Pending | **LOW**<br><small>ISSUE_SIZE_ABOVE_TRAIN_MAX, MEGA_ISSUE_GT_10000CR, MISSING:pe_ratio, MISSING:debt_equity</small> | UNVERIFIED (D-044) |
| **Paras Healthcare Limited** | 2026-10-24 02:42 | 2026-10-28 | -2.56% | +1.59% | *Pending (Oct 28)* | Pending | Pending | [-22.9%, +26.1%] | Pending | **NORMAL** | VERIFIED |

---

## 3. Defect Resolutions in Workstream E

### D-044: Jio Platforms Sector Label Audit
- **Finding**: The sector label for Jio Platforms Limited was recorded as `'IT & Technology'`. Review of the saved Chittorgarh snapshot (`data/evidence/research/2026-10-28_jio-platforms-limited.html`) indicates Chittorgarh listed numeric industry code `196` without an explicit textual sector quote, and no RHP filing quote was matched.
- **Resolution**: Flagged explicitly as `UNVERIFIED` in errata and forward tracking tables. Per the Phase 11 protocol, the existing logged row in `prediction_log.csv` was **not** retroactively edited, preserving complete historical ledger immutability.
- **Regression Test**: Verified via `tests/test_forward_log.py::test_jio_sector_flagged_unverified`.

### D-029 Follow-Up: Calibrated Probability Bounds & App Safety
- Calibrated probability bounds `[0.091, 0.882]` are strictly enforced in `app/main.py`.
- Inputs flagged with out-of-range features (such as Jio's mega-issue size) display a prominent safety alert banner and suppress probability estimates entirely.
- `dashboard/index.html` marks all low-confidence rows with a distinct `LOW CONF` badge and suppresses misleading model probability figures.
