# Phase 21: Preregistration — Telegram Alert System

> **Protocol Reference**: `PHASE_PROTOCOL.md` Step 2 and `phases/Phase 21/1_planning_and_goals.md` Section 3.  
> **Status**: PROPOSED — PENDING USER APPROVAL FOR THRESHOLDS T1 / T2.  
> **Mandatory Disclaimer**: Quantitative decision aid and research benchmark only. Not financial, investment, or trading advice.

---

## 1. Alert Stages & Trigger Schedule (IST)

Precise scheduling is triggered externally by Zoho Catalyst Cron to bypass GitHub Actions cron queue jitter (~4–5 hours). Catalyst dispatches `.github/workflows/notify.yml` with the appropriate `stage` input.

| Stage | Schedule (IST) | Trigger Target / Action Criteria | Fallback Behavior |
| :--- | :--- | :--- | :--- |
| **`announce`** | Daily at **09:00 IST** and **20:00 IST** | Acts on newly discovered Mainboard IPOs (`status == UPCOMING` or `BIDDING_OPEN`) with known dates. Filter: SME ignored, `SKIPPED_ALREADY_LISTED` ignored. | If GitHub dispatch fails, Catalyst retries 2x then notifies Telegram directly ("Trigger failed: announce"). |
| **`preview`** | Daily at **11:45 IST** | Acts strictly on Mainboard IPOs with `status == BIDDING_OPEN` and `close_date == today (IST)`. Ingests live subscription (QIB, NII, Retail, Total), fetches GMP, computes PREVIEW score. | If no closing IPO today, exits quietly without sending alerts. Never logs to `predictions/prediction_log.csv`. |
| **`listing`** | Daily at **11:30 IST** and **16:30 IST** | Acts on IPOs with `listing_date <= today (IST)` that have a **verified outcome** in the repo and no listing alert sent yet. | If outcome is still pending/unverified, sends NO price or gain. Waits for verification. |

---

## 2. Idempotency & Deduplication Architecture

- **Idempotency Key**: `(company, close_date, alert_type)`
  - `alert_type` is one of `{"announce", "preview", "listing"}`.
- **State Store**: `predictions/alerts_sent.csv` with schema:
  `sent_at_ist,company,close_date,listing_date,alert_type,stage,message_digest,run_id`
- **Delivery Guarantee**: At-least-once network transmission, at-most-once deduplication via immutable state commit.
  - A message is recorded in `predictions/alerts_sent.csv` **immediately after** successful HTTP 200 delivery to Telegram.
  - Before sending any message, `already_sent(company, close_date, alert_type)` is evaluated against `predictions/alerts_sent.csv`.
- **Concurrency & Git Hygiene**:
  - `notify.yml` runs under GitHub concurrency group `opi-predictions-writer` with retry-rebase before commit-and-push.
  - Bot commits touch **data files only** (`predictions/alerts_sent.csv`, `predictions/preview_log.csv`, `data/evidence/`).

---

## 3. Decision Rules & Apply/Skip Thresholds (Preview Alert)

Because the champion model (`v4.0.0-champion`) was trained on **final** post-close subscription figures, all 12 PM predictions are explicitly labelled:
> **"PREVIEW (live subscription, model trained on final figures)"**

Per README empirical findings: Raw GMP is the superior point estimator when observed (8.86% MAE vs model). Therefore, GMP is the primary signal when available, with the model providing interval context.

### Proposed Default Thresholds for User Approval:
- **`T1` (Observed Raw GMP Threshold)**: **`+15.0%`**
- **`T2` (Model Point Estimate Threshold, when GMP is unrecorded)**: **`+15.0%`**
- **`P_min` (Calibrated Probability Gate)**: **`P(gain > 10%) >= 0.60`**

### Decision Logic Tree:
1. **Regime A — GMP Observed**:
   - If `gmp_pct >= T1` (+15.0%): Suggestion = **`APPLY`**
   - If `0.0% <= gmp_pct < T1`: Suggestion = **`SKIP (Sub-threshold gain)`**
   - If `gmp_pct < 0.0%`: Suggestion = **`SKIP (Negative GMP discount)`**
2. **Regime B — No GMP Recorded (Model Routing)**:
   - If `pred_gain_pct >= T2` (+15.0%) **AND** `pred_prob_gt10 >= P_min` (60.0%): Suggestion = **`APPLY`**
   - Otherwise: Suggestion = **`SKIP`**
3. **Regime C — Critical Missing Data**:
   - If live subscription cannot be fetched or price band is missing: Suggestion = **`NO SUGGESTION (Insufficient data)`**. The alert provides whatever fields are verified and honestly states the missing inputs without guessing.

---

## 4. Message Content Specifications

### A. Preview Alert Format (11:45 IST)
```
📢 OPI IPO PREVIEW ALERT: <Company Name>
Status: Bidding Closes Today

📅 Dates:
  • Close Date: <YYYY-MM-DD>
  • Expected Listing: <YYYY-MM-DD>
💰 Issue Price: ₹<Price> (Lot Size: <N> shares = ₹<Min_Investment>)

📊 Live Subscription Status (as of <Timestamp IST>):
  • QIB: <X>x
  • NII: <X>x
  • Retail: <X>x
  • Total: <X>x

🎯 Market Signals:
  • Grey Market Premium (GMP): <+X.X% / ₹X> (<Source>, <Date>) [or "No GMP recorded"]
  • Model PREVIEW Estimate: <+X.X%> (live subscription; trained on final figures)
  • Calibrated P(Gain > 10%): <X.X%>
  • 80% Conformal Interval: [<Min%>, <Max%>]

💡 Suggestion: [APPLY / SKIP / NO SUGGESTION]
  • Rule Reason: <e.g. Raw GMP +25.0% >= T1 (+15.0%)>

⚠️ Sample Size Banner: n listed = 13 of 30 (Provisional)
Decision aid only, not financial advice.
```

### B. Listing Alert Format (11:30 / 16:30 IST)
```
🔔 OPI LISTING DAY OUTCOME: <Company Name>
Status: Verified Exchange Opening

💰 Pricing & Returns:
  • Issue Price: ₹<Issue>
  • Official Listing Open: ₹<Open> (Exchange: <NSE/BSE>)
  • Actual Listing Gain: <+X.XX%>
  • Profit / Loss per Lot: ₹<P&L> (<Lot Size> shares)

📈 Pre-Listing Forecast Audit:
  • Raw GMP at Close: <+X.X%> (Diff: <X.X pp>)
  • Model Final Prediction: <+X.X%> (Diff: <X.X pp>)
  • 12 PM Preview Estimate: <+X.X%>

🔍 Verified Evidence: <Evidence JSON digest> (Tier <1/2/2b>)
Decision aid only, not financial advice.
```

---

## 5. Scope Boundaries
1. **No Retraining or Promotion**: Models and holdout remain untouched.
2. **No Secret Leaks**: Tokens passed via environment variables only; zero tokens in code, tests, PRs, logs, or issues.
3. **Allotment Alert**: Dropped (registrars lack public machine-readable APIs).
