# Retraining Governance & Champion-Challenger Policy

> Governs model retraining, validation standards, and promotion workflows for the OPI system.  
> Non-negotiable: Automatic retraining or silent in-place promotion in continuous integration (CI) is strictly prohibited.

---

## 1. Retraining Triggers & Cadence

A model retraining cycle may only be triggered if at least one of the following conditions is satisfied:

1. **Sample Threshold Trigger**: At least **30 newly completed forward test IPOs** have accumulated in `predictions/prediction_log.csv` with verified post-listing actuals.
2. **Quarterly Calendar Trigger**: A scheduled quarterly review cycle has elapsed, provided at least 15 new verified IPO records have been added to the master dataset.

Ad-hoc, event-driven, or single-issue retraining is explicitly forbidden to prevent overfitting to idiosyncratic market events.

---

## 2. Data Ingestion Standards for Training Sets

Before any new forward test rows can be incorporated into training partitions:

1. **Evidence Standard Compliance**: Every new row must possess a verified primary source URL, page date, access date, and saved snapshot under `data/evidence/` (Protocol Section 4).
2. **Independent Audit**: 100% of newly ingested rows must pass `scripts/verify_all.py` data hygiene checks (no duplicates, no date violations, plausible price ratios, no data leakage).
3. **Registry Logging**: Newly ingested batches must be committed with explicit notes detailing the date range and verified counts.

---

## 3. Champion vs. Challenger Protocol

When retraining is triggered, the new model is designated as a **Challenger** and evaluated against the active **Champion**:

1. **Identical Out-of-Sample Split**: Both models must be evaluated on the identical expanding walk-forward rolling-origin partitions across historical quarters.
2. **Paired Statistical Comparison**:
   - Resampling: 2,000 paired bootstrap iterations with a fixed random seed (`seed = 42`).
   - Difference metric: $\Delta\text{MAE} = \text{MAE}_{\text{Challenger}} - \text{MAE}_{\text{Champion}}$.
   - Confidence interval: 95% empirical bootstrap percentile interval $[CI_{2.5\%}, CI_{97.5\%}]$.
3. **Calibration & Coverage Benchmarks**:
   - Expected Calibration Error (ECE): Challenger Equal-Frequency ECE must not exceed Champion ECE by more than 0.01.
   - Brier Score Loss: Challenger must demonstrate equal or lower mean squared probability error.
   - Conformal Coverage: Empirical coverage at nominal 80% level must remain within $[75.0\%, 95.0\%]$ on pooled issues and not deteriorate on tail pops ($> 50\%$ gain).

---

## 4. Promotion Criteria

A Challenger model is approved for promotion to Champion **if and only if** all of the following conditions are met:

1. **Non-Inferior Point Accuracy**: The 95% bootstrap difference interval $[\Delta\text{MAE}_{2.5\%}, \Delta\text{MAE}_{97.5\%}]$ does **not exclude zero in the wrong direction** (i.e. the upper bound must not indicate statistically significant degradation: $\Delta\text{MAE}_{97.5\%} \le +0.50\%$).
2. **Calibration Safeguard**: Platt-calibrated probabilities do not exhibit over-confidence at boundaries ($P \in [0.10, 0.85]$ guidance holds).
3. **No Automatic Promotion**: Evaluation scripts (including `scripts/retrain_challenger.py`) produce comparison reports only; promotion requires explicit human verification and manual version tagging.

---

## 5. Promotion Procedure

When promotion criteria are satisfied:

1. **Version Assignment**: Assign a new semantic model version identifier (e.g. `v5.0.0-champion`).
2. **Registry Update**: Update `model/registry.json` recording:
   - `model_version`
   - SHA-256 hash of training data + code + hyperparameter configuration
   - Date of creation and training window
   - Set `"champion": true` on the new version and `"champion": false` on the retired model.
3. **Artifact Persistence**: Save the new artifact under `model/` (e.g. `model/ipo_model_v5.joblib`). Never overwrite historical joblib artifacts.
4. **Dashboard & Errata**: Document the model version transition in `dashboard/` and log the rationale in the corresponding phase outcome document.

---

## 6. Owner Authorization & Autopilot Addendum (2026-11-07)

On 2026-11-07, the project owner explicitly authorized fully automated monthly retraining, shadow scoring, and rule-based prospective promotion in the cloud (Phase 20).

This addendum supersedes the "no automatic retraining or promotion in CI" restriction above **strictly** according to the following pre-registered constraints:
1. **Automated Monthly Retraining**: Runs on the 1st of every month via `.github/workflows/monthly_retrain.yml`. Newly verified forward test rows are appended to `data/ipo_master.csv` via `scripts/promote_forward_rows.py --apply`. The model is retrained on all verified rows except `data/ipo_holdout_test.csv` using the unchanged `model/train.py` recipe. The artifact is saved under `model/challengers/vMAJOR.MINOR.0-<yyyymm>.joblib` and registered with role `shadow` in `model/registry.json`. `active_champion` is never altered during retraining.
2. **Dual-Scoring**: Every newly discovered IPO is scored prospectively prior to listing by the active champion and by every registered shadow model. All prospective estimates are recorded in `predictions/model_versions.csv`.
3. **Automated Promotion Safeguards**: A shadow model may be promoted to `active_champion` automatically if and only if ALL of the following criteria are met on paired prospective forward predictions:
   - At least 20 listed IPOs scored by both models prior to listing.
   - Models are never evaluated on rows they were trained on or on holdout rows.
   - Paired point estimate $\Delta\text{MAE} = \text{MAE}_{\text{candidate}} - \text{MAE}_{\text{champion}} < 0$.
   - 95% paired bootstrap interval (2,000 resamples, seed 42) upper bound $\le +0.5$ percentage points.
   - Candidate Brier score not worse than champion by $> 0.005$.
   - Cooldown period: At least 60 days have elapsed since the prior model promotion.
4. **Promotion Logging**: Every evaluation cycle (including `NOT_ENOUGH_PAIRS`, `KEEP`, and `PROMOTE`) is logged to `model/promotions_log.csv`. On `PROMOTE`, the candidate is elevated to `active_champion` in `model/registry.json` and the prior champion is marked `retired`.
5. **Direct CI Push**: When monthly retraining, shadow registration, promotion evaluation, unit tests (`pytest`), and independent verification (`verify_all.py`) all pass cleanly, `github-actions[bot]` commits and pushes directly to `main` without opening pull requests. If any verification fails, nothing is pushed and an alert issue is raised.

