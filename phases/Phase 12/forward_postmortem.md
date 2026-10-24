# Forward Prediction Error Post-Mortem (Listed IPOs, n = 6)

> Mandated by Phase 12 Workstream A (Defects D-041, D-045, D-046, D-048).
> **Mandatory Epistemic Guardrail**: Sample size $n = 6 < 30$. No causal conclusions or generalizable performance claims are permitted. All explanatory hypotheses are strictly labeled **Hypothesis (untested)**.

---

## 1. Complete Forward Listed Post-Mortem Table

| Company | Listing Date | Issue Size (₹ Cr) | Model Pred | Actual Gain | Model Err (pp) | GMP at Close | GMP Err (pp) | Sub (QIB / NII / Retail / Total) | GMP Present? | Nifty Move on Listing Day |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **HD Fire Protect Limited** | 2026-10-21 | ₹712.31 | +26.12% | **+23.39%** | **2.73 pp** | +30.26% | 6.87 pp | 256.6x / 203.2x / 30.6x / 131.7x | YES | -0.34% |
| **Fusion CX Limited** | 2026-10-22 | ₹702.00 | +4.33% | **+5.54%** | **1.21 pp** | NOT_RECORDED | N/A | 4.2x / 4.7x / 6.0x / 4.7x | NO | -0.54% |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹5,012.33 | -0.77% | **+5.46%** | **6.23 pp** | +2.32% | 3.14 pp | 4.7x / 1.4x / 0.8x / 3.1x | YES | -0.39% |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹475.48 | +8.32% | **+7.89%** | **0.43 pp** | +6.98% | 0.91 pp | 34.7x / 14.6x / 3.0x / 14.2x | YES | -0.39% |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹852.18 | +74.70% | **+65.71%** | **8.99 pp** | +72.86% | 7.15 pp | 293.6x / 156.4x / 31.1x / 132.8x | YES | -0.39% |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹2,533.81 | +21.10% | **+0.00%** | **21.10 pp** | +21.67% | 21.67 pp | 120.8x / 40.4x / 5.9x / 46.0x | YES | -0.39% |

---

## 2. Error Breakdown by Feature Availability & Structure

- **Overall Model MAE (n=6)**: **6.78 pp**.
- **Overall Raw GMP MAE (n=5 with GMP)**: **7.95 pp**.
- **GMP Availability Subset ($n = 5$)**: Model MAE = **7.90 pp** vs GMP MAE = **7.95 pp**.
- **No-GMP Subset ($n = 1$, Fusion CX)**: Model MAE = **1.21 pp** (pred +4.33% vs actual +5.54%).

---

## 3. Case Post-Mortems: Detailed Reviews

### HD Fire Protect Limited
- **Listing Outcome**: Issue price ₹271.00, actual listing gain **+23.39%**.
- **Pre-Listing Signals**: Model prediction **+26.12%**, GMP quote was **+30.26%**.
- **Subscription Breakdown**: QIB 256.65x, NII 203.21x, Retail 30.55x, Total 131.73x.
- **Market Benchmark Context**: On 2026-10-21, Nifty 50 moved **-0.34%**.
- **Observation**: Model error was 2.73 pp while GMP error was 6.87 pp (spread 4.14 pp).
- **Hypothesis (untested)**: Issue structure contained 100.0% offer-for-sale.
- **Hypothesis (untested)**: Substantial institutional demand (QIB 256.65x) was present during bidding.

### Fusion CX Limited
- **Listing Outcome**: Issue price ₹289.00, actual listing gain **+5.54%**.
- **Pre-Listing Signals**: Model prediction **+4.33%**, GMP quote was **NOT_RECORDED**.
- **Subscription Breakdown**: QIB 4.21x, NII 4.73x, Retail 5.99x, Total 4.68x.
- **Market Benchmark Context**: On 2026-10-22, Nifty 50 moved **-0.54%**.
- **Hypothesis (untested)**: Issue structure contained 28.8% offer-for-sale.
- **Hypothesis (untested)**: Moderate institutional demand (QIB 4.21x) was recorded.

### Zetwerk Manufacturing Business Limited
- **Listing Outcome**: Issue price ₹151.00, actual listing gain **+5.46%**.
- **Pre-Listing Signals**: Model prediction **-0.77%**, GMP quote was **+2.32%**.
- **Subscription Breakdown**: QIB 4.71x, NII 1.45x, Retail 0.77x, Total 3.10x.
- **Market Benchmark Context**: On 2026-10-23, Nifty 50 moved **-0.39%**.
- **Observation**: Model error was 6.23 pp while GMP error was 3.14 pp (spread 3.09 pp).
- **Hypothesis (untested)**: Issue structure contained 43.5% offer-for-sale.
- **Hypothesis (untested)**: Moderate institutional demand (QIB 4.71x) was recorded.

### Sahajanand Medical Technologies Limited
- **Listing Outcome**: Issue price ₹344.00, actual listing gain **+7.89%**.
- **Pre-Listing Signals**: Model prediction **+8.32%**, GMP quote was **+6.98%**.
- **Subscription Breakdown**: QIB 34.70x, NII 14.64x, Retail 3.04x, Total 14.21x.
- **Market Benchmark Context**: On 2026-10-23, Nifty 50 moved **-0.39%**.
- **Observation**: Model error was 0.43 pp while GMP error was 0.91 pp (spread 0.48 pp).
- **Hypothesis (untested)**: Issue structure contained 100.0% offer-for-sale.
- **Hypothesis (untested)**: Moderate institutional demand (QIB 34.70x) was recorded.

### Tonbo Imaging India Limited
- **Listing Outcome**: Issue price ₹700.00, actual listing gain **+65.71%**.
- **Pre-Listing Signals**: Model prediction **+74.70%**, GMP quote was **+72.86%**.
- **Subscription Breakdown**: QIB 293.56x, NII 156.36x, Retail 31.11x, Total 132.81x.
- **Market Benchmark Context**: On 2026-10-23, Nifty 50 moved **-0.39%**.
- **Observation**: Model error was 8.99 pp while GMP error was 7.15 pp (spread 1.84 pp).
- **Hypothesis (untested)**: Issue structure contained 100.0% offer-for-sale.
- **Hypothesis (untested)**: Substantial institutional demand (QIB 293.56x) was present during bidding.

### Bonfiglioli Transmissions Limited
- **Listing Outcome**: Issue price ₹586.00, actual listing gain **+0.00%**.
- **Pre-Listing Signals**: Model prediction **+21.10%**, GMP quote was **+21.67%**.
- **Subscription Breakdown**: QIB 120.78x, NII 40.39x, Retail 5.90x, Total 46.05x.
- **Market Benchmark Context**: On 2026-10-23, Nifty 50 moved **-0.39%**.
- **Observation**: Model error was 21.10 pp while GMP error was 21.67 pp (spread 0.57 pp).
- **Hypothesis (untested)**: Issue structure contained 100.0% offer-for-sale.
- **Hypothesis (untested)**: Substantial institutional demand (QIB 120.78x) was present during bidding.

---

## 4. Methodological Summary & Next Steps
- **Empirical Observation**: Across the 6 evaluated issues, model error averaged 6.78 pp.
- **Protocol Compliance**: All metrics in this report are dynamically populated from `predictions/prediction_log.csv` and evidenced market files under `data/evidence/market/`. Zero numbers are typed by hand.
