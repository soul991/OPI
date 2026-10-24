"""Authoritative single scoring module for OPI predictions and evaluations."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Union, Tuple, Optional
import joblib
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
model_dir = str(ROOT_DIR / "model")
if model_dir not in sys.path:
    sys.path.insert(0, model_dir)


# Pre-registered conformal interval half-width (80% nominal coverage)
DEFAULT_CONFORMAL_HALF_WIDTH_80 = 23.13


def load_feature_ranges() -> Dict[str, Any]:
    """Load pre-computed master feature training ranges (min, max, p01, p99)."""
    ranges_path = ROOT_DIR / "model" / "feature_ranges.json"
    if not ranges_path.exists():
        return {}
    with open(ranges_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_feature_ranges(
    input_data: Union[Dict[str, Any], pd.DataFrame, pd.Series]
) -> Tuple[list[str], str, bool]:
    """Audit candidate features against historical training ranges.
    
    Returns:
        (input_flags, confidence, display_probability)
        - input_flags: list of detected boundary violations or missingness
        - confidence: "LOW" if any out-of-range or mega-issue flag triggered, else "NORMAL"
        - display_probability: False if confidence is LOW, True otherwise
    """
    ranges_meta = load_feature_ranges()
    features_meta = ranges_meta.get("features", {})
    flags: list[str] = []

    def get_val(key: str) -> Any:
        if isinstance(input_data, dict):
            return input_data.get(key)
        if isinstance(input_data, pd.Series):
            return input_data.get(key)
        if isinstance(input_data, pd.DataFrame):
            if key in input_data.columns and len(input_data) > 0:
                return input_data[key].iloc[0]
        return None

    # 1. Issue size checks (Mega-issue & training maximum)
    issue_size = get_val("issue_size_cr")
    if issue_size is not None and pd.notna(issue_size):
        try:
            val = float(issue_size)
            max_size = features_meta.get("issue_size_cr", {}).get("max", 27870.16)
            if val > max_size:
                flags.append("ISSUE_SIZE_ABOVE_TRAIN_MAX")
            if val > 10000.0:
                flags.append("MEGA_ISSUE_GT_10000CR")
        except (ValueError, TypeError):
            pass
    else:
        flags.append("MISSING:issue_size_cr")

    # 2. Missingness on fundamental / valuation metrics
    for critical in ["pe_ratio", "peer_median_pe", "debt_equity"]:
        val = get_val(critical)
        if val is None or pd.isna(val) or str(val).strip() in ("", "None", "nan"):
            flags.append(f"MISSING:{critical}")

    # 3. Numeric bounds checks for all other features present in feature_ranges.json
    for feat, meta in features_meta.items():
        val = get_val(feat)
        if val is not None and pd.notna(val) and str(val).strip() not in ("", "None", "nan"):
            try:
                num_val = float(val)
                if num_val > meta["max"] and feat != "issue_size_cr":
                    flags.append(f"{feat.upper()}_ABOVE_TRAIN_MAX")
                elif num_val < meta["min"]:
                    flags.append(f"{feat.upper()}_BELOW_TRAIN_MIN")
            except (ValueError, TypeError):
                pass

    is_low = any(
        ("ABOVE_TRAIN_MAX" in f) or ("MEGA_ISSUE" in f) or ("BELOW_TRAIN_MIN" in f)
        for f in flags
    )
    confidence = "LOW" if is_low else "NORMAL"
    display_probability = not is_low

    return flags, confidence, display_probability


def load_model_registry() -> Dict[str, Any]:
    """Load model registry configuration."""
    reg_path = ROOT_DIR / "model" / "registry.json"
    if not reg_path.exists():
        return {
            "active_champion": "v4.0.0-champion",
            "models": {
                "v4.0.0-champion": {
                    "artifact_path": "model/ipo_model_phase4.joblib",
                    "model_version": "v4.0.0-champion",
                    "conformal_half_width_80": DEFAULT_CONFORMAL_HALF_WIDTH_80
                }
            }
        }
    with open(reg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_champion_model(custom_artifact_path: Optional[str] = None) -> Tuple[Dict[str, Any], str, float]:
    """Load the champion model artifact and return (artifact_dict, model_version, half_width)."""
    registry = load_model_registry()
    champ_key = registry.get("active_champion", "v4.0.0-champion")
    champ_meta = registry.get("models", {}).get(champ_key, {})
    
    artifact_rel = custom_artifact_path or champ_meta.get("artifact_path", "model/ipo_model_phase4.joblib")
    model_version = champ_meta.get("model_version", "v4.0.0-champion")
    half_width = champ_meta.get("conformal_half_width_80", DEFAULT_CONFORMAL_HALF_WIDTH_80)
    
    full_path = ROOT_DIR / artifact_rel
    if not full_path.exists():
        # Fallback to Phase 2 if Phase 4 missing
        full_path = ROOT_DIR / "model" / "ipo_model.joblib"
        model_version = "v2.0.0-baseline"
        
    if not full_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {full_path}")
        
    artifact = joblib.load(full_path)
    return artifact, model_version, half_width


def prep_features_for_scoring(df: pd.DataFrame, cat_levels: Optional[Dict[str, Any]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Transform input row into exact model feature matrix matching training and evaluation."""
    all_num = [
        "issue_price", "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
        "sub_qib", "sub_nii", "sub_retail", "sub_total", "pe_ratio", "peer_median_pe",
        "debt_equity", "gmp_pct", "nifty_30d_return", "india_vix", "recent_ipo_avg_gain"
    ]
    cat_cols = ["sector", "exchange"]
    
    X = pd.DataFrame(index=df.index)
    for c in all_num:
        X[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan
        
    levels = cat_levels or {c: sorted(df[c].dropna().astype(str).unique()) for c in cat_cols}
    for c in cat_cols:
        if c in df.columns:
            X[c] = pd.Categorical(df[c].astype(str), categories=levels.get(c, [])).codes
        else:
            X[c] = -1
            
    # Domain feature engineering
    X["pe_vs_peer"] = X["pe_ratio"] / X["peer_median_pe"].replace(0, np.nan)
    X["sub_retail_vs_qib"] = X["sub_retail"] / X["sub_qib"].replace(0, np.nan)
    X["sub_hni_vs_retail"] = X["sub_nii"] / X["sub_retail"].replace(0, np.nan)
    X["log_issue_size"] = np.log1p(X["issue_size_cr"].clip(lower=0))
    X["is_high_vix"] = (X["india_vix"] > 18.0).astype(float)
    X["gmp_vs_recent_avg"] = X["gmp_pct"] - X["recent_ipo_avg_gain"]
    
    X["log_sub_total"] = np.log1p(X["sub_total"].clip(lower=0))
    X["log_sub_qib"] = np.log1p(X["sub_qib"].clip(lower=0))
    X["log_sub_nii"] = np.log1p(X["sub_nii"].clip(lower=0))
    X["log_sub_retail"] = np.log1p(X["sub_retail"].clip(lower=0))
    X["qib_demand_share"] = X["sub_qib"] / (X["sub_total"].replace(0, np.nan))
    X["gmp_x_sub"] = X["gmp_pct"] * np.log1p(X["sub_total"].clip(lower=0))
    
    return X, levels


def score_ipo(
    input_data: Union[Dict[str, Any], pd.DataFrame, pd.Series],
    custom_artifact: Optional[Dict[str, Any]] = None,
    custom_model_version: Optional[str] = None
) -> Dict[str, Any]:
    """Score an upcoming IPO candidate with the champion model.
    
    Returns structured dictionary containing:
      - predicted_gain_pct
      - prob_gt10 (Platt-calibrated)
      - rule_applied
      - primary_expected_return
      - blend_expected_return
      - conformal_interval_80 (lower, upper)
      - model_version
    """
    if isinstance(input_data, dict):
        df = pd.DataFrame([input_data])
    elif isinstance(input_data, pd.Series):
        df = pd.DataFrame([input_data.to_dict()])
    else:
        df = input_data.copy()
        
    if custom_artifact:
        art = custom_artifact
        model_version = custom_model_version or "custom-model"
        half_width = DEFAULT_CONFORMAL_HALF_WIDTH_80
    else:
        art, model_version, half_width = load_champion_model()
        
    reg = art.get("reg")
    clf = art.get("cal_clf") or art.get("clf")
    cat_levels = art.get("levels")
    
    if reg is None or clf is None:
        raise ValueError("Model artifact is missing required regressor ('reg') or classifier ('cal_clf')")
        
    X, _ = prep_features_for_scoring(df, cat_levels)
    
    gain_pred = float(reg.predict(X)[0])
    probs = clf.predict_proba(X)[0]
    prob_gt10 = float(probs[1]) if len(probs) > 1 else float(probs[0])
    
    raw_gmp = df["gmp_pct"].iloc[0] if "gmp_pct" in df.columns else None
    has_gmp = pd.notna(raw_gmp) and str(raw_gmp).strip() != ""
    
    if has_gmp:
        gmp_val = float(raw_gmp)
        rule = "GMP observed: GMP is the primary signal, model is context"
        primary_return = gmp_val
        blend_return = round(0.55 * gmp_val + 0.45 * gain_pred, 2)
        lower_bound = round(gmp_val - half_width, 2)
        upper_bound = round(gmp_val + half_width, 2)
    else:
        gmp_val = None
        rule = "no GMP: model estimate with the regime-specific interval"
        primary_return = round(gain_pred, 2)
        blend_return = None
        lower_bound = round(gain_pred - half_width, 2)
        upper_bound = round(gain_pred + half_width, 2)
        
    input_flags, confidence, display_prob = check_feature_ranges(df)

    return {
        "company": str(df["company"].iloc[0]) if "company" in df.columns else "UNKNOWN",
        "predicted_gain_pct": round(gain_pred, 2),
        "prob_gt10": round(prob_gt10, 4),
        "gmp_pct": gmp_val,
        "rule_applied": rule,
        "primary_expected_return": primary_return,
        "blend_expected_return": blend_return,
        "conformal_interval_80": [lower_bound, upper_bound],
        "conformal_half_width_80": half_width,
        "model_version": model_version,
        "input_flags": input_flags,
        "confidence": confidence,
        "display_probability": display_prob
    }
