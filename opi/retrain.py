"""Automated monthly cloud retraining, shadow registration, and prospective promotion engine (D-107, D-108).

Authoritative module for Workstreams E and F:
1. Retrains monthly candidate model on all verified rows except data/ipo_holdout_test.csv.
2. Names model vMAJOR.MINOR.0-<yyyymm> and registers it as 'shadow' in model/registry.json.
3. Evaluates shadow models on paired prospective forward predictions using pre-registered rules.
4. Logs promotion evaluations and decisions to model/promotions_log.csv.
5. On PROMOTE, elevates candidate to active_champion and retires prior champion.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, brier_score_loss

ROOT_DIR = Path(__file__).resolve().parents[1]
model_dir = str(ROOT_DIR / "model")
if model_dir not in sys.path:
    sys.path.insert(0, model_dir)

from model.train import prep, PlattCalibrator, FEATURES, CAT, NUM

IST = timezone(timedelta(hours=5, minutes=30))
REGISTRY_PATH = ROOT_DIR / "model" / "registry.json"
CHALLENGERS_DIR = ROOT_DIR / "model" / "challengers"
PROMOTIONS_LOG_PATH = ROOT_DIR / "model" / "promotions_log.csv"
MODEL_VERSIONS_PATH = ROOT_DIR / "predictions" / "model_versions.csv"
PREDICTION_LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
MASTER_PATH = ROOT_DIR / "data" / "ipo_master.csv"
HOLDOUT_PATH = ROOT_DIR / "data" / "ipo_holdout_test.csv"

PROMOTIONS_LOG_COLUMNS = [
    "decided_at",
    "candidate",
    "champion",
    "n_pairs",
    "mae_candidate",
    "mae_champion",
    "delta",
    "ci_low",
    "ci_high",
    "decision",
    "reason",
]


def paired_bootstrap_diff(
    y_true: np.ndarray,
    pred_cand: np.ndarray,
    pred_champ: np.ndarray,
    n_resamples: int = 2000,
    seed: int = 42,
) -> Tuple[float, float]:
    """Compute 95% paired bootstrap interval for MAE(Candidate) - MAE(Champion)."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    err_cand = np.abs(pred_cand - y_true)
    err_champ = np.abs(pred_champ - y_true)
    diffs = []
    for _ in range(n_resamples):
        idx = rng.randint(0, n, size=n)
        diffs.append(err_cand[idx].mean() - err_champ[idx].mean())
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def get_next_minor_version(registry_data: Dict[str, Any], year_month: Optional[str] = None) -> str:
    """Derive next version name vMAJOR.MINOR.0-<yyyymm> incrementing MINOR (D-107)."""
    ym = year_month or datetime.now(IST).strftime("%Y%m")
    models = registry_data.get("models", {})
    max_minor = 0
    major = 4
    for m_key in models.keys():
        match = re.match(r"v(\d+)\.(\d+)\.", m_key)
        if match:
            maj = int(match.group(1))
            min_val = int(match.group(2))
            major = max(major, maj)
            max_minor = max(max_minor, min_val)
    next_minor = max_minor + 1
    return f"v{major}.{next_minor}.0-{ym}"


def train_monthly_shadow_model(
    master_path: Optional[Path] = None,
    holdout_path: Optional[Path] = None,
    registry_path: Optional[Path] = None,
    challengers_dir: Optional[Path] = None,
    as_of_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Train new candidate model on all verified master rows excluding holdout (D-107).

    Registers the newly trained model strictly as 'shadow' in model/registry.json.
    Never alters active_champion during retraining.
    """
    m_path = Path(master_path) if master_path else MASTER_PATH
    h_path = Path(holdout_path) if holdout_path else HOLDOUT_PATH
    r_path = Path(registry_path) if registry_path else REGISTRY_PATH
    c_dir = Path(challengers_dir) if challengers_dir else CHALLENGERS_DIR

    if not m_path.exists():
        raise FileNotFoundError(f"Master dataset not found: {m_path}")
    if not h_path.exists():
        raise FileNotFoundError(f"Holdout dataset not found: {h_path}")

    master_df = pd.read_csv(m_path, parse_dates=["listing_date"]).dropna(subset=["listing_gain_pct"]).reset_index(drop=True)
    holdout_df = pd.read_csv(h_path, parse_dates=["listing_date"])

    # Exclude holdout rows by (company, listing_date)
    h_keys = set(zip(holdout_df["company"].astype(str).str.strip(), holdout_df["listing_date"].dt.strftime("%Y-%m-%d")))
    train_mask = [
        (r["company"].strip(), r["listing_date"].strftime("%Y-%m-%d")) not in h_keys
        for _, r in master_df.iterrows()
    ]
    train_df = master_df[train_mask].copy().sort_values("listing_date").reset_index(drop=True)

    if len(train_df) < 50:
        raise ValueError(f"Insufficient training rows ({len(train_df)}) after excluding holdout.")

    # Prepare features
    Xtr, levels = prep(train_df)
    ytr_r = train_df["listing_gain_pct"].astype(float)
    ytr_c = (ytr_r > 10.0).astype(int)
    cat_idx = [list(Xtr.columns).index(c) for c in CAT]

    # Fit Regressor using unchanged model/train.py hyper-parameters
    reg = HistGradientBoostingRegressor(
        loss="absolute_error",
        max_depth=4,
        learning_rate=0.03,
        max_iter=350,
        min_samples_leaf=15,
        l2_regularization=0.1,
        categorical_features=cat_idx,
        random_state=42,
    ).fit(Xtr, ytr_r)

    # Fit Classifier
    clf = HistGradientBoostingClassifier(
        max_depth=4,
        learning_rate=0.03,
        max_iter=300,
        min_samples_leaf=15,
        l2_regularization=0.5,
        categorical_features=cat_idx,
        random_state=42,
    ).fit(Xtr, ytr_c)

    # Conformal half width (80% empirical residual quantile on training)
    train_residuals = np.abs(reg.predict(Xtr) - ytr_r)
    half_width_80 = round(float(np.quantile(train_residuals, 0.80)), 2)

    # Load registry
    if r_path.exists():
        with open(r_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = {"active_champion": "v4.0.0-champion", "models": {}}

    now_ist = datetime.now(IST)
    ym = as_of_date.strftime("%Y%m") if as_of_date else now_ist.strftime("%Y%m")
    version_name = get_next_minor_version(registry, year_month=ym)

    c_dir.mkdir(parents=True, exist_ok=True)
    artifact_filename = f"{version_name}.joblib"
    artifact_full_path = c_dir / artifact_filename
    artifact_rel_path = f"model/challengers/{artifact_filename}"

    date_min = train_df["listing_date"].min().strftime("%Y-%m-%d")
    date_max = train_df["listing_date"].max().strftime("%Y-%m-%d")
    training_window = f"{date_min} to {date_max}"

    artifact_dict = {
        "reg": reg,
        "clf": clf,
        "levels": levels,
        "features": list(Xtr.columns),
        "base_features": FEATURES,
        "cat_idx": cat_idx,
        "train_rows": len(train_df),
        "training_window": training_window,
        "conformal_half_width_80": half_width_80,
        "created_at": now_ist.isoformat(),
        "model_version": version_name,
    }

    # Save artifact
    joblib.dump(artifact_dict, artifact_full_path)

    # Calculate SHA256
    with open(artifact_full_path, "rb") as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()

    # Verify artifact loads cleanly
    try:
        loaded = joblib.load(artifact_full_path)
        assert "reg" in loaded and "clf" in loaded, "Corrupt model artifact dictionary"
    except Exception as e:
        if artifact_full_path.exists():
            artifact_full_path.unlink()
        raise RuntimeError(f"Artifact loading verification failed for {version_name}: {e}")

    # Register as SHADOW in registry (never change active_champion here)
    if "models" not in registry:
        registry["models"] = {}

    current_champion = registry.get("active_champion", "v4.0.0-champion")

    registry["models"][version_name] = {
        "model_version": version_name,
        "artifact_path": artifact_rel_path,
        "training_window": training_window,
        "train_rows": len(train_df),
        "created_at": now_ist.isoformat(),
        "champion": False,
        "role": "shadow",
        "sha256": sha256_hash,
        "conformal_half_width_80": half_width_80,
        "description": f"Retrained HistGradientBoosting shadow model on {len(train_df)} master rows ({training_window})",
    }
    # Ensure active champion remains untouched
    registry["active_champion"] = current_champion

    with open(r_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    return {
        "model_version": version_name,
        "artifact_path": artifact_rel_path,
        "sha256": sha256_hash,
        "train_rows": len(train_df),
        "training_window": training_window,
        "conformal_half_width_80": half_width_80,
        "active_champion": current_champion,
    }


def evaluate_shadow_promotions(
    registry_path: Optional[Path] = None,
    model_versions_path: Optional[Path] = None,
    prediction_log_path: Optional[Path] = None,
    promotions_log_path: Optional[Path] = None,
    holdout_path: Optional[Path] = None,
    current_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Evaluate registered shadow models for promotion against Section 6 (7) rules (D-108).

    Rules:
    - At least 20 listed IPOs scored by both models prior to listing.
    - Neither model trained on the evaluated rows.
    - Not evaluated on holdout rows.
    - Point estimate Delta(MAE) < 0 (candidate strictly lower error).
    - 95% paired bootstrap CI upper bound <= +0.5 percentage points (2000 resamples, seed 42).
    - Candidate Brier score not worse than champion by > 0.005.
    - No promotion within 60 days of prior promotion.
    """
    r_path = Path(registry_path) if registry_path else REGISTRY_PATH
    mv_path = Path(model_versions_path) if model_versions_path else MODEL_VERSIONS_PATH
    pl_path = Path(prediction_log_path) if prediction_log_path else PREDICTION_LOG_PATH
    promo_path = Path(promotions_log_path) if promotions_log_path else PROMOTIONS_LOG_PATH
    h_path = Path(holdout_path) if holdout_path else HOLDOUT_PATH

    now_ist = datetime.now(IST)
    decided_at = now_ist.isoformat()
    today = current_date or now_ist.date()

    if not r_path.exists() or not mv_path.exists() or not pl_path.exists():
        return []

    with open(r_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    champ_version = registry.get("active_champion", "v4.0.0-champion")
    models = registry.get("models", {})

    mv_df = pd.read_csv(mv_path)
    pl_df = pd.read_csv(pl_path)
    
    # Filter prediction log for listed forward rows with actual outcome
    actuals_df = pl_df[
        (pl_df["status"] == "FORWARD") &
        (pl_df["actual_gain_pct"].notna()) &
        (pl_df["actual_gain_pct"].astype(str).str.strip() != "")
    ].copy()
    actuals_df["actual_gain_pct"] = pd.to_numeric(actuals_df["actual_gain_pct"], errors="coerce")
    actual_map = dict(zip(zip(actuals_df["company"].str.strip(), actuals_df["listing_date"].astype(str).str.strip()), actuals_df["actual_gain_pct"]))

    # Holdout keys to exclude
    h_keys = set()
    if h_path.exists():
        h_df = pd.read_csv(h_path)
        h_keys = set(zip(h_df["company"].astype(str).str.strip(), h_df["listing_date"].astype(str).str.strip()))

    # Check 60-day cooldown from promotions log
    promo_records: List[Dict[str, Any]] = []
    last_promo_date: Optional[date] = None
    promo_path.parent.mkdir(parents=True, exist_ok=True)
    if promo_path.exists():
        try:
            p_df = pd.read_csv(promo_path)
            promoted_rows = p_df[p_df["decision"] == "PROMOTE"]
            if not promoted_rows.empty:
                last_dt_str = promoted_rows["decided_at"].iloc[-1][:10]
                last_promo_date = datetime.strptime(last_dt_str, "%Y-%m-%d").date()
        except Exception:
            pass

    decisions: List[Dict[str, Any]] = []

    for mod_name, mod_meta in models.items():
        if mod_name == champ_version:
            continue
        role = mod_meta.get("role") or ("champion" if mod_meta.get("champion") else "shadow")
        if role != "shadow":
            continue

        cand_df = mv_df[mv_df["model_version"] == mod_name].copy()
        champ_df = mv_df[mv_df["model_version"] == champ_version].copy()

        # Find paired predictions scored before listing date
        paired_records = []
        for _, c_row in cand_df.iterrows():
            co = str(c_row["company"]).strip()
            ld = str(c_row["listing_date"]).strip()
            sa = str(c_row["scored_at"])[:10]

            # Prospective requirement: scored before listing date
            if ld <= sa:
                continue
            # Must have actual outcome
            if (co, ld) not in actual_map:
                continue
            # Exclude holdout
            if (co, ld) in h_keys:
                continue

            # Must also have champ prediction scored before listing
            champ_match = champ_df[(champ_df["company"].astype(str).str.strip() == co) & (champ_df["listing_date"].astype(str).str.strip() == ld)]
            if champ_match.empty:
                continue
            champ_sa = str(champ_match["scored_at"].iloc[0])[:10]
            if ld <= champ_sa:
                continue

            # Invariant: model must not have been trained on this row
            t_window = mod_meta.get("training_window", "")
            if " to " in t_window:
                _, t_end = t_window.split(" to ")
                if ld <= t_end.strip():
                    continue

            y_val = actual_map[(co, ld)]
            p_cand = float(c_row["pred_gain_pct"])
            p_champ = float(champ_match["pred_gain_pct"].iloc[0])
            prob_cand = float(c_row["pred_prob_gt10"])
            prob_champ = float(champ_match["pred_prob_gt10"].iloc[0])

            paired_records.append({
                "company": co,
                "listing_date": ld,
                "actual": y_val,
                "pred_cand": p_cand,
                "pred_champ": p_champ,
                "prob_cand": prob_cand,
                "prob_champ": prob_champ,
            })

        n_pairs = len(paired_records)

        if n_pairs < 20:
            dec = {
                "decided_at": decided_at,
                "candidate": mod_name,
                "champion": champ_version,
                "n_pairs": n_pairs,
                "mae_candidate": "",
                "mae_champion": "",
                "delta": "",
                "ci_low": "",
                "ci_high": "",
                "decision": "NOT_ENOUGH_PAIRS",
                "reason": f"Only {n_pairs} prospective paired predictions available (threshold >= 20)",
            }
            decisions.append(dec)
            continue

        # Evaluate metrics on paired cohort
        y_true = np.array([r["actual"] for r in paired_records])
        pred_cand = np.array([r["pred_cand"] for r in paired_records])
        pred_champ = np.array([r["pred_champ"] for r in paired_records])
        prob_cand = np.array([r["prob_cand"] for r in paired_records])
        prob_champ = np.array([r["prob_champ"] for r in paired_records])
        y_binary = (y_true > 10.0).astype(int)

        mae_cand = mean_absolute_error(y_true, pred_cand)
        mae_champ = mean_absolute_error(y_true, pred_champ)
        delta = mae_cand - mae_champ
        ci_low, ci_high = paired_bootstrap_diff(y_true, pred_cand, pred_champ, n_resamples=2000, seed=42)

        brier_cand = brier_score_loss(y_binary, prob_cand)
        brier_champ = brier_score_loss(y_binary, prob_champ)
        brier_delta = brier_cand - brier_champ

        cooldown_ok = True
        cooldown_reason = ""
        if last_promo_date is not None:
            days_since_promo = (today - last_promo_date).days
            if days_since_promo < 60:
                cooldown_ok = False
                cooldown_reason = f"Cooldown in effect ({days_since_promo} days < 60 days required)"

        passes_all = (
            delta < 0.0 and
            ci_high <= 0.5 and
            brier_delta <= 0.005 and
            cooldown_ok
        )

        if passes_all:
            decision = "PROMOTE"
            reason = "All 4 promotion criteria satisfied on prospective paired cohort."
            # Elevate candidate to active_champion in registry
            registry["models"][champ_version]["champion"] = False
            registry["models"][champ_version]["role"] = "retired"
            registry["models"][champ_version]["retired_at"] = decided_at

            registry["models"][mod_name]["champion"] = True
            registry["models"][mod_name]["role"] = "champion"
            registry["active_champion"] = mod_name

            with open(r_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2)
            champ_version = mod_name
        else:
            decision = "KEEP"
            reasons = []
            if delta >= 0:
                reasons.append(f"Delta MAE {delta:+.2f} pp not < 0")
            if ci_high > 0.5:
                reasons.append(f"Bootstrap 95% CI upper bound {ci_high:+.2f} pp > +0.5 pp")
            if brier_delta > 0.005:
                reasons.append(f"Brier score delta {brier_delta:+.4f} > +0.005")
            if not cooldown_ok:
                reasons.append(cooldown_reason)
            reason = "; ".join(reasons)

        dec = {
            "decided_at": decided_at,
            "candidate": mod_name,
            "champion": champ_version,
            "n_pairs": n_pairs,
            "mae_candidate": round(float(mae_cand), 4),
            "mae_champion": round(float(mae_champ), 4),
            "delta": round(float(delta), 4),
            "ci_low": round(float(ci_low), 4),
            "ci_high": round(float(ci_high), 4),
            "decision": decision,
            "reason": reason,
        }
        decisions.append(dec)

    # Log decisions to promotions_log.csv
    file_exists = promo_path.exists() and promo_path.stat().st_size > 0
    with open(promo_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(PROMOTIONS_LOG_COLUMNS)
        for d in decisions:
            writer.writerow([d[c] for c in PROMOTIONS_LOG_COLUMNS])

    return decisions


def run_monthly_retrain_cli():
    """CLI entrypoint for .github/workflows/monthly_retrain.yml."""
    parser = argparse.ArgumentParser(description="Monthly Retraining and Promotion Runner")
    parser.add_argument("--execute", action="store_true", help="Execute retraining and promotion evaluation")
    args = parser.parse_args()

    print("=" * 78)
    print("  OPI AUTOMATED MONTHLY RETRAINING & PROMOTION RUNNER")
    print("=" * 78)

    # 1. Train monthly shadow model
    print("\n[Step 1] Retraining monthly shadow model on verified data...")
    res = train_monthly_shadow_model()
    print(f"  Trained Model Version : {res['model_version']}")
    print(f"  Artifact Path         : {res['artifact_path']}")
    print(f"  SHA-256 Digest        : {res['sha256']}")
    print(f"  Training Window       : {res['training_window']} ({res['train_rows']} rows)")
    print(f"  Active Champion       : {res['active_champion']} (UNMODIFIED)")

    # 2. Evaluate promotion rules
    print("\n[Step 2] Evaluating promotion criteria for shadow models...")
    decisions = evaluate_shadow_promotions()
    if not decisions:
        print("  No shadow models eligible for prospective evaluation.")
    for d in decisions:
        print(f"  Candidate: {d['candidate']} vs Champion: {d['champion']}")
        print(f"    Pairs: {d['n_pairs']} | Decision: {d['decision']} | Reason: {d['reason']}")

    print("\n[Step 3] Monthly retraining execution complete.")
    return 0


if __name__ == "__main__":
    sys.exit(run_monthly_retrain_cli())
