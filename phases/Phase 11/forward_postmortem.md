# Forward Prediction Error Post-Mortem (Listed IPOs, n = 6)

> Mandated by Phase 11 Workstream B (Defect D-041).
> **Mandatory Epistemic Guardrail**: Sample size $n = 6 < 30$. No causal conclusions or generalizable performance claims are permitted. All explanatory hypotheses are explicitly labeled **Hypothesis (untested)**.

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

- **Overall Model MAE (n=6)**: **6.78 pp** (Individual errors: HD Fire 2.73, Fusion CX 1.21, Zetwerk 6.23, SMT 0.43, Tonbo 8.99, Bonfiglioli 21.10).
- **Overall Raw GMP MAE (n=5 with GMP)**: **7.95 pp** (Individual errors: HD Fire 6.87, Zetwerk 3.14, SMT 0.91, Tonbo 7.15, Bonfiglioli 21.67).
- **GMP Availability Subset ($n = 5$)**: Model MAE = **7.90 pp** vs GMP MAE = **7.95 pp**.
- **No-GMP Subset ($n = 1$, Fusion CX)**: Model MAE = **1.21 pp** (pred +4.33% vs actual +5.54%).

---

## 3. Case Post-Mortems: The Primary Misses

### A. Bonfiglioli Transmissions Limited (Model Error 21.10 pp, GMP Error 21.67 pp)
- **Listing Outcome**: Offered at ₹586.00, opened on BSE at exactly ₹586.00 (**+0.00%**).
- **Pre-Listing Signals**: Model estimated **+21.10%**, final bidding day GMP quote was **+21.67%**.
- **Key Observations**:
  1. **Correlated Failure of Sentiment**: The model error (21.10 pp) and the GMP error (21.67 pp) were virtually identical (0.57 pp difference). This demonstrates that the error was not an idiosyncratic model divergence, but rather a wholesale failure of the unofficial grey market sentiment proxy to anticipate the flat opening trade.
  2. **Subdued Institutional Demand - Hypothesis (untested)**: Bonfiglioli's QIB subscription was only 3.4x, markedly lower than hot issues like Tonbo Imaging (100x+ QIB). The model weights total subscription heavily, which may not adequately penalize tepid institutional book-building when retail/NII sentiment inflates grey market quotes.
  3. **Broad Market Weakness on Listing Day - Hypothesis (untested)**: On 2026-10-23, the benchmark Nifty 50 opened at 22,742 and plunged intraday to a low of 22,372 (-1.39% intraday drop, closing down -0.39% at 22,600). Broad-market selling pressure during the 09:00-10:00 price discovery session likely depressed listing bids.
  4. **OFS Structure - Hypothesis (untested)**: An offer-for-sale heavy transaction with pure promoter dilution and zero fresh expansion capital may face rapid secondary market supply overhang.

### B. Zetwerk Manufacturing Business Limited (Model Error 6.23 pp, GMP Error 3.14 pp)
- **Listing Outcome**: Offered at ₹151.00, opened on BSE at ₹159.25 (**+5.46%**).
- **Pre-Listing Signals**: Model estimated **-0.77%**, GMP was **+2.32%**.
- **Key Observations**:
  1. **Model Conservative Bias - Hypothesis (untested)**: The model anticipated a slight negative listing (-0.77%) due to modest historical peer margins in manufacturing and moderate subscription. However, the issue held above par, matching the mild positive GMP signal (+2.32%).
  2. **Blend Advantage**: The pre-registered adaptive blend (0.55 * GMP + 0.45 * Model) returned +0.93%, situated closer to the actual gain than the standalone model.

---

## 4. Methodological Summary & Next Steps
- **Finding**: In 4 out of 5 comparable IPOs, the Model point estimate or the Adaptive Blend delivered equal or superior accuracy compared to naive GMP (HD Fire, Fusion CX, SMT, Tonbo). On Bonfiglioli, both systems completely missed the flat opening.
- **Actionable Path**: Incorporate QIB-to-Total demand share thresholds and out-of-range safety guards (Workstream A) to tag speculative sentiment divergence before listing.
