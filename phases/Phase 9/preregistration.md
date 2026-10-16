# Phase 9 Preregistration: Research Agent, Console UI, Validation & Governance

> **Binding Protocol Specification**  
> **Phase**: Phase 9 (OPI Console, Grounded Research Agent & Learning Loop)  
> **Committed**: 2026-10-16  
> **Disclaimer**: This software and quantitative framework is an analytical decision aid, not financial or investment advice.

---

## 1. Grounding Tolerances & Verification Rules

Every data point extracted or proposed by the research agent must undergo a code-executed grounding check against a fetched and saved HTML snapshot in `data/evidence/research/<run_id>/`:

1. **Numerical Fields (`issue_price`, `issue_size_cr`, `gmp_pct`, `sub_qib`, `sub_nii`, `sub_retail`, `sub_total`, `pe_ratio`, `debt_equity`)**:
   - **Floats / Percentages**: Absolute numeric tolerance $\le 0.05$ (e.g., $30.26\%$ matches text containing `30.26` or `30.3`).
   - **Integers (`lot_size`)**: Exact string/integer match.
   - **Negative Values**: Sign must match exactly.
2. **Text Fields (`company`, `sector`, `exchange`)**:
   - Case-insensitive substring match or normalized alias match.
3. **Grounding Status Codes**:
   - `VERIFIED_IN_SNAPSHOT`: Number/string confirmed inside saved snapshot by code.
   - `NOT_FOUND_IN_SNAPSHOT`: Proposal failed text grounding. Field remains `null`.
   - `FETCH_FAILED`: Source URL was unreachable, timed out, or returned non-200. Field remains `null`.
4. **LLM Constraint**:
   - The LLM acts solely as a parser and extraction proposer. No field is ever populated directly from the LLM's parametric weights or memory without passing the grounding check.

---

## 2. Validation & Timing Rules (PREVIEW vs FORWARD)

1. **Mainboard Requirement**:
   - SME IPOs, FPOs, and rights issues are strictly excluded.
   - Verified by post-issue paid-up capital / issue size ($> \text{INR } 25\text{ Cr}$) and exchange listing metadata (`NSE`, `BSE`, or `BOTH`).
2. **Scoring Timing & Subscription Gating**:
   - **Post-Close Only for FORWARD**: An issue can only be scored and logged with status `FORWARD` after bidding has closed (after 18:00 IST on `close_date`).
   - **PREVIEW Mode**: Any scoring executed while bidding is ongoing is strictly labeled `PREVIEW`. `PREVIEW` predictions are displayed interactively in the UI but are **NEVER** logged to `predictions/prediction_log.csv` as `FORWARD`.
3. **GMP Gating**:
   - `gmp_pct` must be dated on or before the final bidding day. Post-close or listing-day GMP is strictly prohibited to prevent outcome leakage.

---

## 3. UI Console Specifications & Non-Advisory Language

1. **Required Console Elements (`app/main.py`)**:
   - **Chat / Query Input**: IPO name search with progress steps.
   - **Headline Result Card**: Estimated listing gain point estimate, 80% conformal interval range (`[lower, upper]`), calibrated $P(\text{gain} > 10\%)$ (displayed only when within the validated range $[0, 0.98]$), and active regime rule applied.
   - **Conformal Interval Visualizer**: Visual bar highlighting the 80% uncertainty bounds and GMP marker.
   - **Historical Context Histogram**: Distribution of historical listing gains with current prediction placed in context.
   - **Nearest 5 Neighbors**: Table of the 5 most similar historical issues (by sector, size, subscription) and their actual listing gains.
   - **Data Quality & Grounding Audit**: Table showing each feature, extracted value, source URL, snapshot link, and verification status.
   - **Live Track Record Panel**: Dynamic performance statistics computed live from `predictions/prediction_log.csv` ($n$, MAE model vs GMP vs baseline) with a mandatory provisional disclaimer banner when $n < 30$.
2. **Strict Language Constraints**:
   - The app must display: *"Decision aid, not financial advice"*.
   - Words like *"apply"*, *"avoid"*, *"buy"*, *"sell"*, or *"recommend"* are strictly prohibited throughout all UI pages and logs.

---

## 4. Resource Caps & Safety Net

1. **Token & Call Caps**:
   - Per-query tool calls capped at 6 web searches.
   - Total prompt + completion tokens capped at 8,000 tokens per research run.
2. **Prompt Injection Defense**:
   - Untrusted web content is isolated as raw data payloads; system prompts explicitly instruct the agent to ignore any embedded directives or prompt jailbreaks.
3. **Offline Mock Provider**:
   - Offline tests execute using fixture snapshots without requiring live network access or API credentials.

---

## 5. Retraining Governance & Learning Loop

1. **Zero Auto-Promotion**:
   - No workflow, script, or CI pipeline may automatically promote a candidate model to champion or overwrite production artifacts in `model/`.
2. **Promotion Workflow**:
   - Monthly retraining evaluates a candidate model against the champion on the holdout partition using 2,000-sample paired bootstrap 95% confidence intervals.
   - Promotion requires non-inferiority in MAE, calibration parity, defect register sign-off, and explicit human approval with version bump in `model/registry.json`.
