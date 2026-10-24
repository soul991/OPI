# Phase 11: Pre-Registration of Safety Guards, Tail Modeling, Conformal Intervals, and Cloud Research Protocols

> Pre-registration document for Phase 11 per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 11/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Out-of-Range and Mega-Issue Guard Protocol (Workstream A, D-040)

1. **Training Range Computation**:
   - Feature ranges per numeric input feature are computed from `data/ipo_master.csv` (minimum, maximum, 1st percentile, 99th percentile) and persisted at `model/feature_ranges.json` along with the SHA-256 hash of the training dataset.
2. **Flagging Mechanism**:
   - `opi/score.py` inspects incoming inputs against `model/feature_ranges.json`.
   - Any input exceeding training bounds triggers explicit flags (e.g. `ISSUE_SIZE_ABOVE_TRAIN_MAX`, `MEGA_ISSUE_GT_10000CR`, `MISSING:<feature>`).
3. **Execution Gating & UI Behavior**:
   - Rows carrying range or mega-issue flags are logged as `FORWARD` with `confidence=LOW`.
   - Applications (`app/main.py`) and dashboards (`dashboard/index.html`) must display the input flag warning and **strictly suppress probability output** for that row.
   - Historical issues in `data/ipo_master.csv` with issue size > ₹10,000 cr ($n = 13$) are analyzed purely descriptively without statistical claims.

---

## 2. Forward Error Post-Mortem Protocol (Workstream B, D-041)

1. **Deterministic Error Ledger**:
   - `scripts/forward_postmortem.py` processes `predictions/prediction_log.csv` to generate a comprehensive markdown post-mortem table.
   - Columns include: company name, model error (pp), GMP error (pp), category subscriptions (QIB, NII, Retail), issue size, GMP availability flag, and listing-day market move (Nifty return).
2. **Epistemic Discipline**:
   - Any explanatory hypotheses regarding error causes (e.g., "weak listing day market", "OFS heavy", "retail over-allocation") must be explicitly labeled **Hypothesis (untested)**.
   - Causal inferences are prohibited for forward sample sizes $n < 30$.

---

## 3. Tail & Conformal Prediction Protocol (Workstream C, D-007, D-008)

1. **Walk-Forward Evaluation Setup**:
   - Strictly walk-forward over 20 rolling quarters (identical to Phase 7/8 benchmarks).
   - Random seed for bootstrap resamples: frozen at `42` with `2,000` resamples.
   - Hyperparameter selection and conformal nonconformity scoring performed strictly on inner validation folds, never touching the evaluated holdout quarter.
2. **Candidates Under Evaluation**:
   - **Candidate 1 (Regime-Conditional Mondrian Conformal)**: Stratified by GMP presence (`HAS_GMP` vs `NO_GMP`) and predicted gain terciles. Strata with $n < 30$ must explicitly report `"insufficient n"`.
   - **Candidate 2 (Upper-Tail Quantile Regressor)**: Dedicated 90th percentile pinball loss regressor for extreme pop prediction.
3. **Formal Adoption Targets**:
   - **Target 1 (Overall Coverage)**: Empirical 80% coverage must fall strictly within `[77.0%, 84.0%]` (baseline champion is over-conservative at 91.2%).
   - **Target 2 (Tail Coverage)**: Top 10% gain issues must achieve at least `70.0%` coverage (baseline champion is 57.5%).
   - **Target 3 (Efficiency / Width)**: Mean interval width must narrow by at least 5.0 percentage points without violating Targets 1 or 2.
4. **Adoption & Challenger Rules**:
   - A candidate is adopted if and only if it satisfies all 3 targets AND demonstrates statistically significant error/coverage improvement on a paired bootstrap 95% confidence interval excluding zero.
   - If no candidate satisfies these criteria, D-007 and D-008 transition to `ACCEPTED` status under `README.md` Known Limitations.
   - Champion model `v4.0.0-champion` and its artifacts remain immutable.

---

## 4. Cloud Research-Agent & OpenRouter Protocol (Workstream D, D-026)

1. **Provider & Cloud Architecture**:
   - Primary LLM provider: **OpenRouter** API (`https://openrouter.ai/api/v1/chat/completions`).
   - Execution is cloud-native via GitHub Actions scheduled workflow (`daily.yml`); zero dependency on local workstation uptime.
   - API authentication: Read strictly from repository secret `OPENROUTER_API_KEY` injected into workflow environment (`env: OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}`).
2. **Credential Safety & Hygiene**:
   - The API key must never be written to disk, printed, logged, committed, or embedded in evidence files.
   - Mandatory pre-push safety verification: `git grep sk-or-` must return 0 lines before any commit or push.
3. **Model Selection & Redundancy**:
   - Model candidates specified strictly in `config/research_models.json`:
     1. `nvidia/nemotron-3.5-super-vl:free`
     2. `google/gemma-4-31b-it:free`
     3. `nvidia/nemotron-3-super-120b-a12b:free`
   - Dynamically filters active models against `https://openrouter.ai/api/v1/models`.
   - Graceful failover: HTTP 429 triggers exponential backoff sleep; HTTP 404 falls through to the next candidate model.
4. **Verification & Grounding**:
   - Real URLs, code-saved snapshots under `data/evidence/`, and deterministic string/numeric matching.
   - Ungrounded or unverified fields are marked `UNGROUNDED` and excluded from model inputs.

---

## 5. Forward Tracking & App Protocol (Workstream E)

1. **Calibrated Probability Suppressions**:
   - Probabilities outside `[0.091, 0.882]` suppressed from display.
2. **Low-Confidence Tagging**:
   - Low-confidence or out-of-range rows flagged prominently in dashboard and web app.
3. **Sample Size Notice**:
   - All reports must prominently display provisional warning while $n < 30$.
