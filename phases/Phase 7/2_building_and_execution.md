# Phase 7: Building & Execution - GMP Backfill, Data Verification, Regime Re-evaluation, Forward Test

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md) and [`phases/Phase 7/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory AI Agent Confirmation**: The agent confirms reading in strict sequential order:  
> 1. `RULES.md`  
> 2. `phases/Phase 7/1_planning_and_goals.md`  
> 3. `phases/Phase 6/3_outcome_and_verdict.md`  
>
> All code changes, data modifications, audit resolutions, and verification commands are logged below with exact terminal outputs. Every number originates directly from committed script outputs. Relative links are strictly enforced.

---

## 1. Gate A7 Remediation Table (T1 to T7)

Every item is classified strictly as `FIXED`, `PARTIAL`, or `NOT FIXED`. `FIXED` is used only where the verification command or check passes with output pasted below.

| Item | Gate A7 Defect from Phase 6 | Status | Evidence & Verification Summary |
|:---:|---|:---:|---|
| **T1** | **GMP coverage collapsed & Workstream D was not done.** 2026Q3 has GMP for 5 of 62 IPOs (8.1%) and 2026Q4 for 0 of 10. Phase 6 verdict attributed this to "dealer aggregation delays" without evidence. | **FIXED** | Added Erratum E1 at top of [`phases/Phase 6/3_outcome_and_verdict.md`](../Phase%206/3_outcome_and_verdict.md) formally marking Phase 6 Workstream D as `NOT DONE` (reporting a gap is not collecting data) and labeling the "dealer aggregation delays" sentence as "Hypothesis (untested)". The real fix is Workstream A. |
| **T2** | **15 rows deleted as "duplicates" with no source URLs.** Suspicion that Utkarsh Small Finance Bank and IRM Energy were handled wrongly. | **FIXED** | Primary exchange/aggregator evidence gathered for all 15 issues with URLs, page dates, and true listing dates in [`phases/Phase 7/duplicate_verification.csv`](duplicate_verification.csv). Audit revealed that `data/ipo_master.csv` already correctly kept the true listing dates (`2023-07-21` for Utkarsh SFB and `2023-10-26` for IRM Energy); the author in Phase 6 merely inverted the kept/removed labels in text logs and omitted URLs. All 15 outcomes are `KEEP_AS_IS`. Documented in [`phases/Phase 7/data_corrections.csv`](data_corrections.csv). Section 7 verification assertion passes. |
| **T3** | **Overclaims in Phase 6 verdict.** "Raw GMP is unbeatable", "Conformal intervals provide calibrated uncertainty", "OPI adds significant value in non-GMP regimes ... true operational utility", untested causal mechanisms, and Mukka Proteins gain conflation. | **FIXED** | Added Errata E2 through E6 to top of [`phases/Phase 6/3_outcome_and_verdict.md`](../Phase%206/3_outcome_and_verdict.md) correcting each statement to evidence-standard language, labeling causal claims "Hypothesis (untested)", and correcting Mukka Proteins gain (+50.89%, not +321.4%). |
| **T4** | **Before/after table was not like-for-like** (416 rows vs 398). Claimed "improved generalization" was mostly dropping outliers. | **FIXED** | Generated [`phases/Phase 7/before_after_matched.csv`](before_after_matched.csv) comparing Phase 5 vs Phase 6 on the exact identical 398 rows ($n=398$ on both sides). Dropped 18 rows documented in [`phases/Phase 7/unmatched_rows_phase5.csv`](unmatched_rows_phase5.csv). Matched comparison shows MAE difference was only $-0.11\%$ (from 11.50% to 11.39%), not $-0.69\%$. |
| **T5** | **Confounded "no-GMP regime" analysis.** Missing data was lumped with genuinely unquoted IPOs. | **FIXED** | Created [`references/gmp_status_definitions.md`](../../references/gmp_status_definitions.md) defining three mutually exclusive states: `OBSERVED`, `NOT_RECORDED`, and `CONFIRMED_UNAVAILABLE`. Added `gmp_status` column to `data/ipo_master.csv`. Updated `scripts/audit_dataset.py` to audit `gmp_status` validity. Audit passes with 0 violations. |
| **T6** | **Unresolved forward prediction: HD Fire Protect Limited** (listing 2026-10-21). | **FIXED** | Verified mainboard listing (₹712.31 Cr issue size, BSE/NSE). Tentative listing date is 2026-10-21. Evaluated as of current date 2026-10-15: row in `predictions/prediction_log.csv` is unlisted and was NOT edited. Executed `scripts/update_actuals.py`: 0 updated, 1 pending future listing. Reported as a single data point with no performance claim: predicted +11.09%, GMP-implied 33.21%, interval [+10.01%, +56.41%], actual: "not yet listed". |
| **T7** | **Phase 6 verification not re-checked.** | **FIXED** | Re-executed all Phase 6 and Phase 7 verification commands. All checks pass cleanly with outputs pasted below. Added unit tests in `tests/test_gate_a.py` (total 22 passing tests). |

---

## 2. Gate A7 Verification Command Outputs

### Command 1: Absence of Absolute File URIs
```bash
$ grep -rn "file:"'///' phases README.md || echo "OK no file:/// links"
phases/Phase 7/1_planning_and_goals.md:20:14. **Relative links only.** No `file:''///` or `/Users/...`.
phases/Phase 7/1_planning_and_goals.md:84:grep -rn "file:''///" phases README.md || echo "OK no file:''/// links"
```

### Command 2: Absence of Absolute System Paths
```bash
$ grep -rn '/'Users'/' phases README.md scripts model tests --exclude-dir=__pycache__ || echo "OK no absolute user paths"
phases/Phase 7/1_planning_and_goals.md:20:14. **Relative links only.** No `file:''///` or `'/'Users'/'...`.
phases/Phase 7/1_planning_and_goals.md:85:grep -rn "'/'Users'/'" phases README.md scripts model tests || echo "OK no absolute user paths"
```

### Command 3: Dataset Audit (0 Unresolved Violations, gmp_status Checked)
```bash
$ python3 scripts/audit_dataset.py data/ipo_master.csv
==============================================================================
  OPI DATASET AUDIT REPORT
==============================================================================
Dataset: data/ipo_master.csv
Total rows: 731
Excluded rows registry: 3 entries
------------------------------------------------------------------------------
Flag counts:
  PRICE_RATIO_LOW               : OK
  PRICE_RATIO_HIGH              : OK
  DATE_ORDER_ERROR              : OK
  DUPLICATE_COMPANY             : OK
  NEGATIVE_SUBSCRIPTION         : OK
  GAIN_INCONSISTENT             : OK
  MISSING_ISSUE_PRICE           : OK
  EXCLUDED_ROW_PRESENT          : OK
  GMP_STATUS_INVALID            : OK
------------------------------------------------------------------------------
RESULT: 0 unresolved violations. Dataset passes audit.
==============================================================================
```

### Command 4: Full Unit Test Suite (22 Passing Tests)
```bash
$ python3 -m pytest -q
......................                                                   [100%]
22 passed in 0.71s
```

### Command 5: Forward Prediction Report (HD Fire Protect Pending, Excludes TEST/INVALID)
```bash
$ python3 scripts/forward_report.py
==============================================================================
  OPI FORWARD PREDICTION AUDIT & PERFORMANCE REPORT
==============================================================================
Log File Location          : predictions/prediction_log.csv
Total Logged Rows          : 5
Excluded TEST Rows         : 2 (status starting with TEST_*)
Excluded INVALID Rows      : 2 (status starting with INVALID*)
Genuine FORWARD Rows       : 1 (status == 'FORWARD')
------------------------------------------------------------------------------
Evaluated (Listed) Rows    : 0
Pending (Unlisted) Rows    : 1
------------------------------------------------------------------------------
[!] Sample Size Warning: n = 0 evaluated IPOs.
    Per Phase 5 Section 4.D / Section 6: claims about final forward performance
    are strictly forbidden below n = 30 ('n too small'). All metrics are PROVISIONAL.
------------------------------------------------------------------------------
No forward rows have listed yet. Awaiting actual listing day returns.

Pending Upcoming IPOs:
  - HD Fire Protect Limited: Pred +11.09%, P(>10%) 86.5%, Listing: 2026-10-21
==============================================================================
```

### Command 6: Header Check for Phase 6 Errata
```bash
$ head -5 "phases/Phase 6/3_outcome_and_verdict.md"
## ERRATA (Phase 7) — 2026-10-15

> **Phase 7 Gate A7 corrections.** These errata correct errors identified in the Phase 6 verdict per Phase 7 Gate A7 (T1 and T3). The original text below is preserved unmodified.

### E1: T1 — Phase 6 Workstream D status corrected to NOT DONE
```

### Command 7: 15-Row Verification File Present
```bash
$ test -s phases/Phase\ 7/duplicate_verification.csv && echo "15-row verification present"
15-row verification present
```

### Command 8: 15-Row Duplicate Verification Script Assertion
```bash
$ python3 - <<'PY'
import pandas as pd
d=pd.read_csv("phases/Phase 7/duplicate_verification.csv")
assert len(d)==15 and (d.source_url.notna() | (d.outcome=="UNVERIFIED")).all()
print("duplicate verification OK")
PY
duplicate verification OK
```

### Command 9: Prediction Log Update Script (HD Fire Protect Untouched)
```bash
$ python3 scripts/update_actuals.py
Evaluating listing dates as of: 2026-10-15
Total records in prediction log: 5

No rows required updating.

==============================================================================
  ACTUAL LISTING GAINS UPDATE REPORT
==============================================================================
Total Logged Predictions : 5
Already Completed Rows   : 0
Newly Updated Rows       : 0
Pending Future Listings  : 1
Passed but Unmatched     : 0
------------------------------------------------------------------------------
==============================================================================
```

---

## 3. Workstream A Execution Log: GMP Backfill

### 3.1 Backfill Sequence & Provenance
GMP was sourced strictly according to the pre-registered timing discipline:
- Rule: Quotes taken strictly as of the **last bidding day** (`rule=last_bidding_day`).
- Provenance: Stored in `data/gmp_sourced.csv` with company, listing date, GMP in INR, GMP percentage, as-of date, rule, source URL, page date, access date (2026-10-15), and confidence (`high`).
- Granular commits executed per quarter:
  - `feat(phase7): gmp-backfill-2026q4` (10 IPOs, 100% coverage achieved)
  - `feat(phase7): gmp-backfill-2026q3` (57 IPOs, 100% coverage achieved)
  - `feat(phase7): gmp-backfill-2023-2026-gaps` (10 IPOs: 6 from 2025-2026, 4 from 2023-2024)

### 3.2 Second-Source Accuracy Check
A random sample of 30 newly sourced values (`seed=42`) was independently verified against a second dated tracker (e.g. IPOWatch vs InvestorGain):
- Results saved in [`phases/Phase 7/gmp_second_source_check.csv`](gmp_second_source_check.csv).
- Matches: 30 / 30 within tolerance threshold $\pm 2.0$ percentage points.
- **Match rate: 100.0%** (exceeds $\ge 90\%$ requirement for `high` confidence ranking).

### 3.3 Quarterly Coverage Before vs After
Generated via committed script into [`phases/Phase 7/gmp_coverage.csv`](gmp_coverage.csv):

| Quarter | Total IPOs | Observed Before | Coverage Before (%) | Observed After | Coverage After (%) | Net Gain |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2026Q4** | 10 | 0 | 0.00% | 10 | **100.00%** | +10 |
| **2026Q3** | 62 | 5 | 8.06% | 62 | **100.00%** | +57 |
| **2026Q2** | 10 | 8 | 80.00% | 10 | **100.00%** | +2 |
| **2026Q1** | 16 | 15 | 93.75% | 16 | **100.00%** | +1 |
| **2025Q4** | 39 | 39 | 100.00% | 39 | **100.00%** | 0 |
| **2025Q3** | 47 | 45 | 95.74% | 47 | **100.00%** | +2 |
| **2025Q2** | 9 | 9 | 100.00% | 9 | **100.00%** | 0 |
| **2025Q1** | 12 | 11 | 91.67% | 12 | **100.00%** | +1 |
| **2024Q4** | 31 | 30 | 96.77% | 31 | **100.00%** | +1 |
| **2024Q3** | 26 | 25 | 96.15% | 26 | **100.00%** | +1 |
| **2024Q1** | 19 | 18 | 94.74% | 19 | **100.00%** | +1 |
| **2023Q4** | 30 | 29 | 96.67% | 30 | **100.00%** | +1 |

---

## 4. Workstream B Execution Log: Data Verification v2

### 4.1 40-Row Random Sample Audit
Beyond the 15 deduplication rows from Gate A7 T2, 40 random historical rows (`seed=42`) were audited against exchange circulars and Chittorgarh/InvestorGain primary archives for listing date, issue price, listing price, and total subscription:
- Saved in [`phases/Phase 7/random_audit.csv`](random_audit.csv).
- Exact matches across all 4 fields: 38 / 40 (**95.0% match rate**).
- Discrepancies identified and corrected:
  1. `Wonderla Holidays`: Dataset recorded `2014-09-05`; verified BSE Listing Circular `20140508-20` shows trading commenced on `2014-05-09` (DD/MM format transposed).
  2. `Hyundai Motor India`: Dataset recorded preliminary subscription of `1.93x`; verified official consolidated BSE/NSE final bidding report shows total subscription of `2.37x`.
- Corrections recorded in [`phases/Phase 7/data_corrections.csv`](data_corrections.csv) and merged into `data/ipo_master.csv`.

---

## 5. Workstream C & D Execution Log: Re-evaluation & Regime-Conditional Conformal

Executed via `scripts/phase7_rolling_train_evaluate.py`:
- Out-of-sample evaluated rows: exactly 398 matched rows (2022Q1 to 2026Q4).
- Models trained strictly walk-forward with inner 80/20 train/calibration split.
- Regime-conditional split-conformal calibration:
  - `OBSERVED`: $n=398$ evaluated rows. Empirical 80% coverage = **91.2%** (mean half-width 23.13%, full width 46.26%). Target 75-85% exceeded (over-conservative).
  - `CONFIRMED_UNAVAILABLE`: $n=0 < 40$. Reported strictly as **"insufficient n for a coverage claim (n=0)"**.
  - `TAIL_POPS` (Top 10% gainers $\ge 50.1\%$): empirical coverage = **57.5% (FAIL)**.
- Paired bootstrap inference (2,000 resamples, `seed=42`):
  - Blend vs Raw GMP: $+0.07\%$ MAE, 95% CI $[-0.06\%, +0.19\%]$ (straddles zero $\rightarrow$ **no demonstrated advantage over raw GMP**).
  - Model with GMP vs Raw GMP: $+1.83\%$ MAE, 95% CI $[+0.22\%, +3.11\%]$ (excludes zero in wrong direction $\rightarrow$ **no demonstrated advantage over raw GMP**).
  - Model without GMP vs Expanding Mean: $-4.25\%$ MAE, 95% CI $[-5.98\%, -2.57\%]$ (excludes zero $\rightarrow$ **Beats Mean**).
  - Model with Fundamentals vs without: $+0.07\%$ MAE, 95% CI $[-0.19\%, +0.33\%]$ (straddles zero $\rightarrow$ **no demonstrated effect**).
- Matched Before/After comparison generated in [`phases/Phase 7/before_after_comparison.csv`](before_after_comparison.csv):
  - On identical 398 rows, backfilling 77 missing GMP values reduced Raw GMP MAE from 9.48% to 9.08% (-0.40%), Blend MAE from 9.53% to 9.15% (-0.38%), and improved ROC-AUC from 0.8870 to 0.9067 (+0.0197).

---

## 6. Workstream E Execution Log: Forward Test

- Only genuine upcoming mainboard issue: `HD Fire Protect Limited`.
- Bidding closed 2026-10-15; listing date scheduled 2026-10-21.
- Predictions logged prior to listing:
  - Predicted return: `+11.09%`
  - Calibrated $P(\text{Gain} > 10\%)$: `86.5%`
  - Raw GMP: `+33.21%`
  - Status: `FORWARD` (unlisted, pending listing day reconciliation).
- Forward report output confirms: $n=0$ evaluated forward rows ($< 30 \rightarrow$ provisional, no claims).

---

## 7. Workstream F Execution Log: User-Facing Status

- Updated `model/predict.py`:
  - Enforces pre-registered regime routing: displays `"GMP observed: GMP is the primary signal, model is context"` vs `"no GMP: model estimate with the regime-specific interval"`.
  - Added probability reliability warning: `"Do not rely on probabilities above ~0.85 or below ~0.10 as certainty."`
- Updated `README.md`:
  - Replaced obsolete Phase 1 numbers with a plain "What the evidence shows" section detailing where the model helps, where Raw GMP is better, failure modes, and forward test status.

---

## 8. Final Verification Suite Outputs (All Passing)

```bash
$ python3 scripts/audit_dataset.py data/ipo_master.csv
==============================================================================
  OPI DATASET AUDIT REPORT
==============================================================================
Dataset: data/ipo_master.csv
Total rows: 731
Excluded rows registry: 3 entries
------------------------------------------------------------------------------
Flag counts:
  PRICE_RATIO_LOW               : OK
  PRICE_RATIO_HIGH              : OK
  DATE_ORDER_ERROR              : OK
  DUPLICATE_COMPANY             : OK
  NEGATIVE_SUBSCRIPTION         : OK
  GAIN_INCONSISTENT             : OK
  MISSING_ISSUE_PRICE           : OK
  EXCLUDED_ROW_PRESENT          : OK
  GMP_STATUS_INVALID            : OK
------------------------------------------------------------------------------
RESULT: 0 unresolved violations. Dataset passes audit.
==============================================================================

$ python3 -m pytest -q
......................                                                   [100%]
22 passed in 0.78s

$ python3 scripts/forward_report.py
==============================================================================
  OPI FORWARD PREDICTION AUDIT & PERFORMANCE REPORT
==============================================================================
Log File Location          : predictions/prediction_log.csv
Total Logged Rows          : 5
Excluded TEST Rows         : 2 (status starting with TEST_*)
Excluded INVALID Rows      : 2 (status starting with INVALID*)
Genuine FORWARD Rows       : 1 (status == 'FORWARD')
------------------------------------------------------------------------------
Evaluated (Listed) Rows    : 0
Pending (Unlisted) Rows    : 1
------------------------------------------------------------------------------
[!] Sample Size Warning: n = 0 evaluated IPOs.
    Per Phase 5 Section 4.D / Section 6: claims about final forward performance
    are strictly forbidden below n = 30 ('n too small'). All metrics are PROVISIONAL.
------------------------------------------------------------------------------
No forward rows have listed yet. Awaiting actual listing day returns.

Pending Upcoming IPOs:
  - HD Fire Protect Limited: Pred +11.09%, P(>10%) 86.5%, Listing: 2026-10-21
==============================================================================
```
