# Phase 10: Pre-Registration of Ingest, Discovery, Grounding, and Reporting Protocols

> Pre-registration document for Phase 10 per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Deterministic Parsing & Ingest Protocol (`opi/ingest.py`)

1. **Snapshot-First Ingestion**:
   - For any incoming IPO candidate, raw HTML/JSON responses must be fetched by code and saved under `data/evidence/<category>/<listing_date>_<company-slug>.<ext>`.
   - Cryptographic SHA-256 hash, access timestamp (IST), source URL, and page date must be recorded in evidence manifests.
2. **Deterministic Extraction**:
   - Each field (Issue price, issue size, subscription by category, GMP, lot size, dates) must be extracted by deterministic regex/DOM parsers tested against saved HTML fixtures.
3. **Strict Grounding Refusal Rule**:
   - If a candidate value is proposed by an operator, script parameter, or LLM, `opi/ingest.py` must verify the exact string or numeric representation within the code-saved snapshot.
   - If any proposed value mismatches or is absent from the snapshot, the ingest function must raise a `GroundingRefusalError` and halt ingestion. No typed-in or ungrounded values are permitted.
4. **Market Data Raw Provenance**:
   - Market benchmark metrics (Nifty 30-day return, India VIX) from `yfinance` or exchange APIs must be saved in their raw, unmodified response format with SHA-256 hash. `yfinance` data is explicitly classified as medium-confidence unofficial data.

---

## 2. Grey Market Premium (GMP) Selection Protocol

1. **Last Bidding Day Evening Rule**:
   - The authoritative GMP quote for model context and baseline evaluation is strictly defined as the quote recorded on the **evening of the final bidding day** (e.g., 18:00–23:59 IST on `close_date`).
   - Parsers must scan table rows for the matching date and select the final evening quote, recording its exact timestamp as `gmp_as_of`.
   - Parsers must NEVER blindly take the top/latest row of a GMP table, as quotes after bidding close represent secondary gray trading rather than the pre-close sentiment upon which the model is evaluated.
2. **Unobserved GMP Handling**:
   - When no verified quote exists for the final bidding day, `gmp_pct` is set to `None`, `gmp_status` to `NOT_RECORDED`, and the model operates under the `NO_GMP` regime.

---

## 3. Mainboard IPO Discovery Protocol (`opi/discover.py`)

1. **Candidate Universe**:
   - Scans official exchange IPO listings and aggregator schedules for issues that are currently:
     - Open for subscription.
     - Closed but not yet listed (between `close_date` and `listing_date`).
2. **Eligibility & Inclusion Rules**:
   - **Mainboard Only**: Must be listing on NSE/BSE Mainboard. SME board IPOs (NSE Emerge, BSE SME), Follow-on Public Offers (FPOs), rights issues, and InvITs/REITs are strictly excluded.
   - Listing date and issue price band must be confirmed from primary/exchange sources.
3. **Execution Gating**:
   - Candidate IPOs with open bidding windows are flagged `STATUS_BIDDING_OPEN` and cannot be scored as genuine FORWARD predictions until after 18:00 IST on their final close date.
   - Upon bidding closure, discovery triggers ingest and scoring with final subscription totals.

---

## 4. Console, Dashboard & Evidence Language Rules

1. **Calibrated Probability Suppressions**:
   - Predicted probabilities $P(\text{gain} > 10\%)$ are displayed if and only if they fall within the empirically calibrated out-of-sample range: `[0.091, 0.882]`.
   - Values outside this range must display `"not shown: outside measured range"`.
2. **Provisional Performance Notice**:
   - The forward evaluation dashboard and report must display the provisional banner:
     **Provisional: n = 1 of 30 listed forward predictions**.
   - No performance claims, superiority claims, or statistical generalization are permitted for sample sizes $n < 30$. Results are strictly descriptive.
3. **Unused Fundamentals**:
   - Fundamental features not utilized by the champion model must be explicitly labeled `(not used by model)` or omitted from decision cards.
4. **Non-Advisory Mandate**:
   - Absolute prohibition against prescriptive advice words: "apply", "avoid", "buy", "sell", "subscribe". All statements must characterize the system as a probabilistic quantitative decision aid.
