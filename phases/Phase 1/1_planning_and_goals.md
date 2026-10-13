# Phase 1: Planning and Goals

## 1. Executive Summary & Objective
**Phase 1** represents the foundational baseline training milestone of the **India IPO Listing-Gain Predictor (OPI)**. 

The primary objective is to build an automated machine learning pipeline that accurately estimates:
1. **Continuous Listing Day Gain (%)**: Expected Day-1 opening return relative to the final issue price:
   $$\text{Listing Gain \%} = \frac{\text{Listing Price} - \text{Issue Price}}{\text{Issue Price}} \times 100$$
2. **Probability of a Successful Listing**: Binary classification estimating whether the IPO achieves a listing pop $> 10\%$.

---

## 2. Core Problem Statement & The Grey Market Benchmark
Retail and institutional investors in the Indian primary equity market traditionally rely on the **Grey Market Premium (GMP)** as an informal proxy for listing gains. However:
- GMP operates in an unregulated, thin-volume dealer market vulnerable to price manipulation.
- GMP frequently creates false positives in late-stage bull market euphoria and false negatives during market corrections.
- Historical data shows that GMP alone exhibits a high Mean Absolute Error ($\approx 17.3\%$).

**The Core Hypothesis of Phase 1:**
> *By combining multi-category demand signals (Institutional QIB, High Net-Worth NII, and Retail subscriptions), issue capital absorption dynamics (issue size, pricing), macro market momentum (Nifty 50 30-day trajectory, India VIX), and industry sector classifications, an ensemble Gradient Boosting model can achieve superior accuracy and lower volatility than relying on GMP alone.*

---

## 3. Data Strategy & Guardrails

### A. Scope Constraints
- **Strictly Indian Mainboard Issues (NSE & BSE)**: SME IPOs are explicitly excluded because their liquidity profiles, 100% retail/HNI allocation dynamics, and lot-size structures deviate drastically from mainboard price discovery.
- **Exclusion of Follow-on Public Offers (FPOs)**: FPOs (e.g., NTPC, REC) already have active secondary market pricing and do not represent initial price discovery.

### B. Anti-Leakage Discipline
Every predictor variable must be strictly knowable **prior to listing morning**:
- Subscription figures reflect the final bidding day counts.
- GMP is recorded on bidding day 3 (close of public subscription window).
- Market context (Nifty 50 returns and India VIX) are indexed up to the issue closing date.

### C. Strict Out-of-Sample Holdout Protocol
In accordance with user guidelines, **the model must never be trained on the full dataset**. 
- A chronological 80/20 train-test partition is established.
- **Training Set (662 IPOs)**: September 2006 through September 3, 2024.
- **Holdout Set (166 IPOs)**: September 4, 2024 through May 8, 2026.
- The 166 holdout IPOs remain completely untouched by the training algorithm and serve as the empirical validation ground to benchmark generalization against actual real-world outcomes.

---

## 4. Target Success Criteria & Milestones
For Phase 1 to be deemed successful, the baseline model must satisfy the following criteria on the unseen holdout dataset:
1. **Outperform Mean Baseline**: $MAE_{\text{model}} < MAE_{\text{historical mean}}$ ($\sim 19.6\%$).
2. **Beat the Naive GMP-Only Baseline**: $MAE_{\text{model}} < MAE_{\text{GMP}}$ ($\sim 17.3\%$) on holdout IPOs with recorded GMP.
3. **Classification Discrimination**: $ROC\text{-}AUC > 0.80$ and $Accuracy > 75\%$ for identifying IPOs gaining $> 10\%$.
4. **Data Hygiene**: 100% compliance with `validate_dataset.py` schema with zero unhandled missing-value exceptions during inference.
