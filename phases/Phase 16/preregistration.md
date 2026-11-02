# Phase 16: Preregistration of Pre-Listing Predictions, GMP Discovery, Research Agent Integration, and Reporting Retraining

> Committed prior to any Workstream implementation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 16/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Epistemic Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice. Sample size is $n = 8 < 30$ ($n = 7$ with GMP, 4 pending unlisted). All forward metrics are descriptive.

---

## 1. Timing and Scoring Rules (Task 0 & Pre-Listing Governance)

1. **Strict Scoring Window**:
   - Scoring of any prospective IPO row occurs strictly **after bidding has officially closed (final subscription figures available)** and **before the company lists on an exchange**.
   - Before bidding closes: Candidate IPOs in `BIDDING_OPEN` state appear on the dashboard and pre-listing list solely as "Bidding open: scored after close on <close_date>". No prediction number or model estimate may be generated or displayed while bidding is open.
   - No day-1, live, or intraday subscription numbers may enter any feature representation.
   - Scoring after listing date is strictly prohibited. No backfilled rows are permitted.
2. **Handling Missed Forward IPOs (D-080)**:
   - Any IPO whose bidding closed, that sat unscored, and that lists without a prospective prediction must NOT be silently dropped.
   - It is recorded in `predictions/missed_forward.csv` as `MISSED_FORWARD` with company name, bidding dates, listing date, and root cause reason.
   - This ensures the prospective $n = 30$ sample accounting remains completely transparent and honest.

---

## 2. Feature Grounding and Data Leakage Prevention

1. **Features Knowable Strictly Before Listing**:
   - Only final category subscriptions (QIB, NII, Retail, Total) as of bidding close.
   - Grey Market Premium (GMP) as of the last bidding day (no later date, preventing post-close sentiment leakage).
   - Market macro features (Nifty 30-day return, India VIX) knowable before listing.
   - All feature values must be grounded with verbatim quotes in saved local snapshots under `data/evidence/`. A feature without a saved snapshot is `NOT_RECORDED`.
2. **Log Immutability**:
   - `predictions/prediction_log.csv` is strictly append-only. Existing rows are never modified in place.
   - If an IPO was scored without GMP (e.g., the four 2026-11-01 rows), its row remains unchanged even if a GMP page is later discovered.

---

## 3. Automatic GMP Discovery Protocol (D-081)

1. **Deterministic Discovery (First Priority)**:
   - Live list page of the GMP aggregator (`investorgain.com`) is fetched by the cloud runner.
   - Company name is matched using strict normalization against the candidate company name.
   - Exact matching only: fuzzy matching of different entities is strictly prohibited.
   - When matched, the company's dedicated GMP page URL is resolved, and GMP as of the last bidding day is extracted.
   - The raw HTTP response is saved to `data/evidence/gmp/` with SHA256 checksum.
2. **Grounded Agent Fallback**:
   - If deterministic matching fails, the research agent may be queried strictly for the aggregator's GMP page URL.
   - The proposed URL is validated by code: the fetched page must contain the verbatim company name.
3. **No-GMP Regime Handling**:
   - If neither deterministic nor agent discovery resolves a GMP page, the IPO is scored in the model-only regime.
   - The row is flagged with note `NO_GMP` in `prediction_log.csv`, and displayed with `NO_GMP (model-only regime)` in the dashboard and pre-listing table.

---

## 4. Research Agent Guardrails in Daily Scoring (D-082, D-026)

1. **Operational Boundaries**:
   - The research agent is invoked strictly from the scoring pipeline (`opi/run_daily.py` / `scripts/score_ipo.py`) only for missing fields that deterministic scrapers cannot resolve.
   - Strictly enforced budget caps: maximum 6 tool calls and 8,000 tokens per IPO run.
   - Verbatim quote grounding check: any proposed fact without an exact substring match in a fetched, saved HTML snapshot is dropped.
2. **Audit Logging in `run_log.csv`**:
   - Every agent invocation logs: timestamp, IPO name, provider, model ID, tool request count, number of fields proposed, number grounded, and grounding rate.
3. **Secret Hygiene**:
   - The OpenRouter API key (`OPENROUTER_API_KEY`) is read from the runner environment.
   - The key must NEVER be printed to stdout, logged in issues, committed to disk, or embedded in snapshots. `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` must always return 0 lines.
4. **Resolution of D-026**:
   - Defect D-026 may be marked `FIXED` ONLY when a green scheduled GitHub Actions workflow run (`event: schedule`) scores a real newly discovered IPO using the agent and saves verified evidence. Tests and manual runs do not count.

---

## 5. Pre-Listing Predictions Display Specification (D-079)

1. **Dashboard Section & Markdown Report**:
   - A dedicated section "Pre-listing predictions (awaiting listing)" is published on the public dashboard and written to `predictions/pre_listing_predictions.md`.
   - Table 1 (Pending Forward Predictions): All FORWARD rows with no actual outcome whose listing date is today or later. Columns: Company, Bidding Dates, Listing Date, Days to Listing, Model Estimate, P(>10%), 80% Conformal Interval, Last Bidding Day GMP (or `NO_GMP`), Confidence Flag, Scored At, and Regime Note.
   - Table 2 (Active Bidding): Discovered IPOs currently in `BIDDING_OPEN` state, clearly stating "Bidding open: scored after close on <close_date>".
2. **Tone and Labeling**:
   - Labeled strictly as "Model Estimate", never "will list at".
   - Displays the mandatory disclaimer banner: "Provisional forward evaluations below n = 30".

---

## 6. Monthly Retraining with Pull Request Reporting (D-083)

1. **Promotion and Evaluation on Branch**:
   - `monthly_retrain.yml` executes `scripts/promote_forward_rows.py --apply` on a dedicated automated branch.
   - Evaluates eligible listed rows (verified outcomes, saved snapshots, corrections-aware effective outcome).
   - Trains challenger model and generates a comparison table (Champion vs Challenger) saved to `docs/`.
   - Opens a GitHub Pull Request against `main` with the comparison table in the PR description for human maintainer review.
   - Never modifies `model/ipo_model.joblib` on `main` and never auto-merges.

---

## 7. Small-Sample Epistemic Rules

1. **No Performance Claims ($n < 30$)**:
   - While listed sample count $n < 30$, no statistical superiority claims ("beats GMP", "proven edge") are permitted.
   - Headline metrics remain descriptive and provisional.
