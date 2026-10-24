# Phase 12: Pre-Registration of Evidence-Backed Market Data, Cloud Research Agent Proof, Jio/Paras Ingestion, and Dashboard Publishing Protocols

> Pre-registration document for Phase 12 per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 12/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 1. Evidence-Backed Market Data Protocol (Workstream A, D-045, D-046, D-048)

1. **Market Data Sourcing & Evidence Storage**:
   - `opi/market.py` fetches daily ^NSEI history and India VIX for requested listing dates.
   - The **raw** response payload is saved under `data/evidence/market/<date>_nifty.raw` with its SHA-256 hash.
   - Parsed values are written to `data/evidence/market/<date>_nifty.json` containing `nifty_close`, `nifty_prev_close`, `nifty_day_return_pct`, `source`, and `accessed_at`.
   - If the external source is unreachable or missing, the pipeline records `NOT_AVAILABLE`; synthetic imputation or manual interpolation is strictly prohibited.
2. **Deterministic Post-Mortem Generator**:
   - `scripts/forward_postmortem.py` is refactored to read solely from `predictions/prediction_log.csv` and hash-verified evidence files in `data/evidence/market/`.
   - The legacy hard-coded `LISTING_DAY_NIFTY_MOVES` constant dictionary is permanently removed.
   - Narrative sentences must be populated programmatically from log and evidence fields (e.g., `"QIB {sub_qib}x"`).
   - Explanatory hypotheses are restricted to a fixed list of templates citing computed metrics and labeled **Hypothesis (untested)**. Free-text ungrounded narrative is prohibited.
   - Output writes to `phases/Phase 12/forward_postmortem.md` and is guarded by regression test `tests/test_postmortem.py::test_narrative_numbers_from_log`.

---

## 2. Cloud Research Agent Proof Protocol (Workstream B, D-026)

1. **Cloud Execution Environment**:
   - Research agent executes within the scheduled GitHub Actions workflow (`.github/workflows/daily.yml`) running on Ubuntu runners.
   - Authentication utilizes the repository secret `OPENROUTER_API_KEY` configured by the repository owner.
   - Models are defined in `config/research_models.json`.
2. **Criteria for FIXED Status**:
   - Requires a green **scheduled** run (`event=schedule`) logged in GitHub Actions.
   - Run log must report: LLM provider, model identifier, request count, and per-field grounding rate.
   - Generated snapshot artifacts must be committed to the repository by the workflow bot.
   - Sanitization check: `gh run view <id> --log | grep -c sk-or-` must return strictly 0.
   - Blocked web sources are flagged as `SKIPPED_BLOCKED_SOURCE`; hallucinated or guessed values are strictly forbidden.

---

## 3. Jio Platforms and Paras Healthcare Listing Ingestion Protocol (Workstream C)

1. **Exchange-Only Outcome Evidence**:
   - Ingestion is executed post-listing (after 2026-10-28) using `scripts/update_actuals.py` backed by official exchange opening prices (BSE/NSE) and code-saved HTML snapshots under `data/evidence/actuals/`.
2. **Out-of-Range Handling & Reporting Stratification**:
   - Jio Platforms Limited (issue size ₹30,213 cr exceeding historical training maximum ₹27,870 cr) remains flagged as `LOW` confidence with probability display suppressed.
   - Forward accuracy is reported both **with** and **without** LOW-confidence rows.
   - Total listed forward sample reaches $n = 8$ of 30 target forward predictions; the formal notice "provisional, descriptive only, no performance claims permitted below $n = 30$" is strictly maintained.

---

## 4. Dashboard Publishing & Staleness Guard Protocol (Workstream D, D-050)

1. **GitHub Pages Deployment Verification**:
   - Live URL `https://soul991.github.io/OPI/dashboard/` must return HTTP 200.
   - The live page must reflect the latest `scored_at` or run timestamp from `predictions/prediction_log.csv`.
   - Results of the verification check are recorded in `phases/Phase 12/pages_check.txt`.
2. **Bot Commit `[skip ci]` Staleness Assessment**:
   - Investigate whether automated bot commits carrying `[skip ci]` prevent GitHub Pages deployment rebuilds.
   - If the live page is determined to be stale, remediate by separating deployment triggers or configuring GitHub Actions Pages deployment (`actions/deploy-pages`).
3. **Automated Staleness Guard**:
   - Implement `scripts/verify_pages.py` to fetch the live dashboard and issue a warning or failure if the published timestamp is more than 36 hours older than the last scheduled Actions run.
   - If network sandboxing prevents external HTTP access, the script outputs `NOT_CHECKED` and never falsifies a `PASS`.

---

## 5. Process Governance & Gate Enforcement Protocol (D-052)

1. **Enforced Gate Stop**:
   - In compliance with Defect D-052, execution halts immediately following the completion and pushing of `phase12-gate-a` and `phase12-preregistration`.
   - Workstream A through D will not commence until the user explicitly issues the "continue" command in the session chat.
