# Phase 20 Preregistration: Autopilot Governance, Exchange Policy, Divergence Resolution & Model Lifecycle

> Follows `RULES.md` and `PHASE_PROTOCOL.md`. Committed prior to any production feature code or pipeline modifications.
> Epistemic Status: Provisional ($n = 11$ listed forward IPOs of 30 target). All accuracy statements and error distributions are descriptive; no statistical superiority claims permitted below $n \ge 30$.

---

## 1. Exchange Policy for Actual Outcomes (D-105)

1. **Primary Exchange Principle**: For any IPO listed on the National Stock Exchange (NSE), the official outcome is defined strictly as the **first-session opening price on NSE**.
2. **Sole BSE Listing Exception**: For any IPO listed exclusively on the Bombay Stock Exchange (BSE) without an NSE listing (e.g. HD Fire Protect, BSE scrip 544994), the official outcome is the **first-session opening price on BSE**.
3. **Strict Exchange Isolation**: NSE and BSE price quotes are never blended, mixed, or averaged across exchanges.
4. **Master Dataset Consistency**: The historical master dataset (`data/ipo_master.csv`) reflects dual-listed (BOTH: 723 issues) opening prices primarily from NSE, with sole BSE listings (BSE: 15 issues) recorded from BSE. This pre-registered rule codifies the historical convention.

---

## 2. Tolerance & Divergence Resolution Rules (D-100, D-104)

1. **Strict 1.0% Tolerance Constant**: The 1.0% relative tolerance threshold ($|\text{price}_1 - \text{price}_2| / \text{price}_1 \le 0.01$) remains non-negotiable and unloosened.
2. **Majority-Based Arbitration Protocol**: When primary (Tier 2 Yahoo) and secondary sources diverge beyond 1.0%, arbitration evaluates all available candidate sources under the following constraints:
   - Only sources quoting the **identical exchange and quantity** (e.g. `(NSE, open)`) are compared.
   - Values with `UNKNOWN` exchange or quantity are excluded from agreement pools.
   - Yahoo Finance and any Yahoo-derived aggregator count strictly as one single publisher.
   - A verified outcome requires a strict 2-of-3 majority agreeing within 1.0% on the primary exchange.
3. **Audited Tagging**: Any outcome recorded via arbitration is tagged `tier2_arbitrated` in `prediction_log.csv` notes and evaluated both with and without arbitration in all subsequent reporting.
4. **Idempotent Pending Evidence Persistence (D-104)**: When Tier 2 or arbitration ends in `PENDING_REVIEW`, `SKIPPED_ARBITRATION_*`, or `SKIPPED_NO_MATCH`, every fetched source page is saved verbatim under `data/evidence/actuals/pending/` accompanied by a structured metadata manifest (`.manifest.json`). No outcome is recorded, and repeat runs with identical bytes write nothing new.

---

## 3. Epistemic & Provenance Guardrails

1. **Zero Manual Edits**:
   - `predictions/prediction_log.csv` is strictly machine-appended by GitHub Actions. No manual row edits, deletions, or column alterations are permitted.
   - Production evidence files under `data/evidence/` are authored strictly by GitHub Actions automated runners.
2. **Strict Verification Grounding**: Every number, run ID, file path, and SHA-256 hash quoted in phase deliverables must be physically grounded in repository files or committed raw `gh` outputs.
3. **Small-Sample Provisional Boundary**: With $n = 11$ listed forward IPOs, all metrics remain descriptive.

---

## 4. Model Registry & Artifact Guardrails (Part 1 vs Part 2)

1. **Part 1 Model Freeze**: In Part 1, no model artifact or registry entry may be modified. Active champion `v4.0.0-champion` (`model/ipo_model_phase4.joblib`) remains the sole scoring model.
2. **Part 2 Versioning Sidecar (D-106)**: Model versions are recorded in a separate append-only sidecar `predictions/model_versions.csv` (`scored_at, company, listing_date, model_version, role, pred_gain_pct, pred_prob_gt10, backfilled`). `predictions/prediction_log.csv` remains byte-identical in header and structure.

---

## 5. Retraining, Shadow Scoring & Rule-Based Automatic Promotion Policy (D-107, D-108)

> **Owner Authorization**: On 2026-11-07, the owner authorized fully autonomous cloud retraining, shadow scoring, and rule-based model promotion, superseding the manual promotion constraint in `docs/retraining_policy.md` Section 4(3) strictly as defined below.

1. **Monthly Cloud Retraining Cadence**:
   - Retraining executes on the 1st of each calendar month via `.github/workflows/monthly_retrain.yml`.
   - Training dataset: All verified master records plus newly promoted forward rows, strictly excluding `data/ipo_holdout_test.csv`.
   - Pipeline recipe: Exact unchanged `model/train.py` model architecture (HistGradientBoostingRegressor + calibrated HistGradientBoostingClassifier with Platt scaling) and hyperparameter configuration.
   - Naming & Registry: New artifacts are named `model/challengers/v<MAJOR>.<MINOR>.0-<yyyymm>.joblib` and registered with SHA-256, training window, and row count in `model/registry.json` under role `"shadow"`. A newly retrained model is **never** registered directly as champion.
2. **Prospective Shadow Scoring**:
   - The daily job (`opi/run_daily.py`) scores every newly closing IPO with the active champion AND each registered shadow model.
   - All predictions (champion and shadow) are logged prospective to listing before actual outcomes are knowable.
3. **Rule-Based Automatic Promotion Criteria**:
   A shadow candidate model is promoted to `active_champion` if and only if ALL of the following conditions are simultaneously satisfied on paired prospective forward test IPOs:
   - **Sample Threshold**: At least $n \ge 20$ listed forward IPOs scored by both champion and candidate before listing.
   - **Point Accuracy**: Paired $\Delta\text{MAE} = \text{MAE}_{\text{candidate}} - \text{MAE}_{\text{champion}} < 0$ (point estimate indicates lower absolute error).
   - **Statistical Non-Inferiority**: The upper bound of the 95% paired bootstrap interval (2,000 resamples, fixed seed 42) satisfies $CI_{97.5\%} \le +0.50$ percentage points.
   - **Calibration Safeguard**: Challenger Brier score on those paired IPOs does not deteriorate by more than 0.005 relative to the champion ($BS_{\text{candidate}} - BS_{\text{champion}} \le 0.005$).
   - **Cooldown Period**: A minimum of 60 calendar days has elapsed since the previous model promotion.
4. **Promotion Logging**:
   - Every monthly evaluation writes an audited decision row to `model/promotions_log.csv` (`decided_at, candidate, champion, n_pairs, mae_candidate, mae_champion, delta, ci_low, ci_high, decision, reason`).
   - Allowed decision values: `PROMOTE`, `KEEP`, `NOT_ENOUGH_PAIRS`.
   - On `PROMOTE`, the candidate is set as `active_champion`, the retired champion is marked `"retired"`, and the updated registry is committed directly to `main` after passing full verification.
