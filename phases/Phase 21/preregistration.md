# Phase 21 Preregistration (v2): Telegram Alert System

> **Protocol Reference**: `RULES.md`, `PHASE_PROTOCOL.md` (Step 2), and `phases/Phase 21/1_planning_and_goals.md` (Section 3).  
> **Status**: APPROVED BY USER (v2: T1=10%, Marginal Band [5%, 10%) on GMP only).  
> **Regulatory Disclaimer**: Quantitative decision aid and research benchmark only. Not financial, investment, or trading advice.

---

## 1. Alert Triggers and Exact Times (IST)

Because GitHub Actions scheduled crons experience significant platform queue lag (mean 4.66 hours, measured in Phase 12), all precise alert times are triggered externally by Zoho Catalyst Cron via `workflow_dispatch` to `.github/workflows/notify.yml`.

| Stage | Schedule (IST) | Trigger Target / Action Criteria | Fallback Behavior |
| :--- | :--- | :--- | :--- |
| **`announce`** | **09:00 IST** & **20:00 IST** daily | Discovers newly visible Mainboard IPOs (`status == UPCOMING` or `BIDDING_OPEN`) with announced open, close, and listing dates. Skips SME issues and issues already listed (`SKIPPED_ALREADY_LISTED`). | If GitHub dispatch fails, Catalyst retries 2x and on final failure delivers a direct Telegram trigger failure alert. |
| **`preview`** | **11:45 IST** daily | Evaluates Mainboard IPOs with `status == BIDDING_OPEN` and `close_date == today (IST)`. Ingests live subscription (QIB, NII, Retail, Total), fetches latest GMP, and computes PREVIEW score. If no IPO closes today, exits cleanly without sending. | Never logs to `predictions/prediction_log.csv`. Ingests live feature snapshot into `predictions/preview_log.csv`. |
| **`listing`** | **11:30 IST** & **16:30 IST** daily | Evaluates IPOs with `listing_date <= today (IST)` that have a **verified outcome** in the repo and no sent listing alert. If an outcome is pending verification, sends **no message** (awaits verified exchange notice). | If outcome is pending verification, suppresses message delivery until verified by the two-tier chain. |

### Dispatch Latency Measurement
- Dispatch queue latency and runtime: **To be measured in WS-F with 5 dispatches of `notify.yml`** (recording `created_at`, `started_at`, `completed_at`, and queue latency directly from the GitHub API).

---

## 2. Idempotency Key & State Management

- **Idempotency Key**: `(company, close_date, alert_type)`
  - Where `alert_type` is one of `{"announce", "preview", "listing"}`.
- **State Store**: `predictions/alerts_sent.csv` with schema:
  ```csv
  sent_at_ist,company,close_date,listing_date,alert_type,stage,message_digest,run_id
  ```
- **Delivery Guarantee**:
  - Deduplication check `already_sent(company, close_date, alert_type)` is evaluated against `predictions/alerts_sent.csv` before dispatching any Telegram notification.
  - State record is appended **immediately after** successful HTTP 200 delivery from Telegram API (`ok: true`).
  - Guarantees at-most-once user receipt: a repeated trigger or re-run never sends duplicate phone notifications.
- **Git Concurrency & Writer Hygiene**:
  - `notify.yml` uses the shared concurrency group `opi-predictions-writer` with retry-rebase before push.
  - Commits made by automated runs touch data files only (`predictions/alerts_sent.csv`, `predictions/preview_log.csv`, and `data/evidence/`).

---

## 3. Apply / Skip / Marginal Decision Rule (Preview Alert)

### Epistemic Grounding & Labelling
The champion model (`v4.0.0-champion`) was trained on **final post-close subscription figures**. At 11:45 AM on the close date, subscription figures are **live/intraday**. Therefore:
- The model number in the preview alert is strictly labelled:
  > **"PREVIEW (live subscription, model trained on final figures)"**
- PREVIEW predictions are **never** written to `predictions/prediction_log.csv` and are never presented as FORWARD predictions.

### Evidence-Based Hierarchy
README empirical findings on 321 historical IPOs demonstrate:
- Raw GMP is the superior point estimator when observed (MAE 8.86 pp vs Model 11.48 pp; blend difference straddles zero).
- Therefore, **Raw GMP is the primary signal when observed**. The ML model provides contextual bounding and calibrated probability. When GMP is absent, the ML model serves as the primary estimator.

---

### Approved Thresholds & Decision Bands

The primary threshold $T1 = 10.0\%$ was chosen as a **hurdle**, not as a mathematical guarantee of positive return. Historical distribution of listing gains by GMP bucket from `data/ipo_master.csv` ($n=349$ observed issues) is reported below for descriptive context:

#### Historical Listing Gain by GMP Bucket (`data/ipo_master.csv`, Descriptive Only)
| GMP Bin | $n$ | Mean Listing Gain | Median Listing Gain | Share Gained > 0% |
|---|:---:|:---:|:---:|:---:|
| $< 0\%$ | 36 | -7.10% | -6.65% | 19.4% |
| $0\%$ to $< 5\%$ | 90 | -0.72% | +0.00% | 45.6% |
| **$5\%$ to $< 10\%$ (Marginal)** | **49** | **+6.08%** | **+6.52%** | **79.6%** |
| $10\%$ to $< 15\%$ | 34 | +9.53% | +11.23% | 82.4% |
| $15\%$ to $< 30\%$ | 55 | +19.28% | +18.18% | 89.1% |
| $30\%$ to $< 50\%$ | 53 | +37.07% | +36.57% | 100.0% |
| $\ge 50\%$ | 32 | +72.86% | +66.50% | 100.0% |

*(Descriptive historical summary only. Past listing performance does not guarantee future outcomes).*

---

### Decision Rules:

#### 1. Regime A — GMP Observed (Primary Path)
- **`APPLY`**: `gmp_pct >= 10.0%`  
  *(Basis: "Observed GMP (+X.X%) >= T1 (+10.0%)")*
- **`MARGINAL: small expected gain, your call`**: `5.0% <= gmp_pct < 10.0%`  
  *(Basis: "Observed GMP (+X.X%) is in the marginal band [5.0% to 10.0%)")*
- **`SKIP`**: `0.0% <= gmp_pct < 5.0%`  
  *(Basis: "Observed GMP (+X.X%) below 5.0% minimum threshold; historical mean return is flat/negative")*
- **`SKIP`**: `gmp_pct < 0.0%`  
  *(Basis: "Negative GMP discount (-X.X%) indicates elevated listing risk")*

#### 2. Regime B — No GMP Recorded (Model Fallback)
*(Note: No marginal band applies to model-only predictions; model estimates require strict threshold clearance).*
- **`APPLY`**: `pred_gain_pct >= 15.0%` **AND** `pred_prob_gt10 >= 0.60`  
  *(Basis: "Model PREVIEW estimate (+X.X%) >= T2 (+15.0%) with calibrated P(>10%) >= 60%")*
- **`SKIP`**: Otherwise  
  *(Basis: "Model PREVIEW estimate (+X.X%) or calibrated probability below threshold")*

#### 3. Regime C — Critical Missing Data
- **`NO SUGGESTION (Insufficient data)`**: If live subscription cannot be scraped or price band is unrecorded.  
  *(Basis: Honestly reports missing fields without guessing or hallucinatory imputation).*

---

## 4. Message Content Specifications

### A. Stage `announce` (09:00 & 20:00 IST)
```text
📢 OPI IPO ANNOUNCEMENT: <Company Name>

📅 Issue Schedule:
  • Bidding Opens: <YYYY-MM-DD>
  • Bidding Closes: <YYYY-MM-DD>
  • Listing Date: <YYYY-MM-DD or 'TBD'>
💰 Issue Structure:
  • Price Band: ₹<Min> - ₹<Max> (Issue Price: ₹<Price>)
  • Lot Size: <N> shares (Minimum Bid: ₹<Amount>)
  • Issue Size: ₹<Size> Cr (Fresh: <Fresh>%, OFS: <OFS>%)
🏢 Exchange: <NSE / BSE / Both>

ℹ️ First-look notice. Full PREVIEW analysis will be delivered on close date at 11:45 AM IST.
Decision aid only, not financial advice.
```

### B. Stage `preview` (11:45 IST on Close Date)
```text
🎯 OPI PREVIEW ALERT: <Company Name>
Status: Bidding Closes Today (11:45 AM IST Snapshot)

📅 Key Dates:
  • Bidding Closes: Today (<YYYY-MM-DD>)
  • Expected Listing: <YYYY-MM-DD>
💰 Issue Price: ₹<Price> (Lot Size: <Lot> shares = ₹<Amount>)

📊 Live Subscription Status (as of <HH:MM IST>):
  • QIB: <X.XX>x
  • NII: <X.XX>x
  • Retail: <X.XX>x
  • Total: <X.XX>x

📈 Market Signals:
  • Grey Market Premium (GMP): <+X.X% / ₹X> (<Source>, as of <YYYY-MM-DD HH:MM IST>) [or 'No GMP recorded']
  • Model PREVIEW Estimate: <+X.X%> (live subscription; model trained on final figures)
  • Calibrated P(Gain > 10%): <X.X%>
  • 80% Conformal Prediction Interval: [<Min%>, <Max%>]

💡 Decision Suggestion: [APPLY / MARGINAL: small expected gain, your call / SKIP / NO SUGGESTION]
  • Basis: <Rule statement>

⚠️ Sample Size Notice: n listed = 13 of 30 (Provisional)
Decision aid only, not financial advice.
```

### C. Stage `listing` (11:30 & 16:30 IST on Listing Date)
```text
🔔 OPI LISTING DAY OUTCOME: <Company Name>
Status: Official Exchange Listing Verified

💰 Outcome & Per-Lot Return:
  • Issue Price: ₹<Issue>
  • Official Listing Open: ₹<Open> (Exchange: <NSE/BSE>)
  • Actual Listing Gain: <+X.XX%>
  • Profit / Loss per Lot: ₹<P&L> (<Lot Size> shares)

📊 Pre-Listing Signal Audit:
  • Raw GMP at Close: <+X.X%> (Error: <X.X pp>)
  • Model Final Prediction: <+X.X%> (Error: <X.X pp>)
  • 12 PM Preview Estimate: <+X.X%> (Error: <X.X pp>)

🔍 Verification Provenance: <Evidence JSON digest> (Tier <1/2/2b>)
Decision aid only, not financial advice.
```
*(If the outcome remains pending verification by the two-tier chain, NO message is sent until official verification succeeds).*

---

## 5. Explicit Design Exclusions
- **Allotment Alert**: Dropped. Registrars (Link Intime, KFintech, Bigshare) provide no authenticated, machine-readable public API. Dropping this is recorded as a product decision, not a defect.
- **Model Promotion / Retraining**: No retraining, no shadow model promotion, and no modification to `model/` artifacts during this phase.

---

## 6. Success & Verification Criteria
1. `alerts_sent.csv` maintains strict idempotency: 0 duplicate sends on re-triggers.
2. `prediction_log.csv` remains strictly unpolluted: 0 PREVIEW rows or alert rows.
3. Every collected preview feature snapshot has saved HTML/JSON evidence under `data/evidence/`.
4. `scripts/ci_local.py` passes (`CI_LOCAL: PASS`) on every workstream branch before PR creation.
5. `scripts/verify_all.py` passes with 0 FAIL at phase conclusion.
