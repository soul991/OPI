"""OPI Interactive Analysis Console - Streamlit Application.

Usage:
    streamlit run app/main.py
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

# Setup repository root on sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]


def get_calibrated_probability_range():
    reg_path = ROOT_DIR / "model" / "registry.json"
    if reg_path.exists():
        try:
            import json
            data = json.loads(reg_path.read_text(encoding="utf-8"))
            champ = data.get("active_champion", "v4.0.0-champion")
            models = data.get("models", {})
            r = data.get("calibrated_probability_range") or models.get(champ, {}).get("calibrated_probability_range")
            if r:
                return float(r.get("min", 0.091)), float(r.get("max", 0.882))
        except Exception:
            pass
    return 0.091, 0.882
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from opi.schema import IPOCandidateSchema, FieldProposal
from opi.research_agent import execute_research_run
from opi.score import score_ipo
from opi.validate import (
    determine_prediction_mode,
    validate_mainboard_eligibility,
    validate_candidate_for_forward_logging
)
from opi.log import append_prediction_log

# Streamlit Page Setup
st.set_page_config(
    page_title="OPI - India IPO Listing-Gain Analysis Console",
    page_icon="📈",
    layout="wide"
)

# Mandatory Non-Advisory Header
st.caption("🔒 **OPI Research Console** | Strictly a Quantitative Research Framework | **Decision aid, not financial advice**")


@st.cache_data
def load_historical_master() -> pd.DataFrame:
    """Load historical master IPO dataset for nearest neighbors and distribution analysis."""
    master_path = ROOT_DIR / "data" / "ipo_master.csv"
    if master_path.exists():
        df = pd.read_csv(master_path, parse_dates=["listing_date"])
        return df.dropna(subset=["listing_gain_pct"]).copy()
    return pd.DataFrame()


def find_nearest_5_neighbors(master_df: pd.DataFrame, target_feat: dict) -> pd.DataFrame:
    """Find 5 most similar historical mainboard IPOs based on size, demand, and sector."""
    if master_df.empty:
        return pd.DataFrame()
    
    df = master_df.copy()
    target_sector = target_feat.get("sector") or "Industrial & Manufacturing"
    target_size = float(target_feat.get("issue_size_cr") or 500.0)
    target_sub = float(target_feat.get("sub_total") or 10.0)

    # Normalize metrics for distance
    size_std = df["issue_size_cr"].std() or 1.0
    sub_std = df["sub_total"].std() or 1.0

    # Sector bonus: 0 if sector matches, 1 otherwise
    same_sector = (df["sector"] != target_sector).astype(float) * 1.5

    dist = np.sqrt(
        ((df["issue_size_cr"] - target_size) / size_std) ** 2 +
        ((df["sub_total"] - target_sub) / sub_std) ** 2 +
        same_sector ** 2
    )
    df["distance"] = dist
    top5 = df.sort_values("distance").head(5)
    cols = ["company", "listing_date", "sector", "issue_size_cr", "sub_total", "gmp_pct", "listing_gain_pct"]
    return top5[[c for c in cols if c in top5.columns]]


# Title & Chat-Style Input
st.title("📊 Indian Mainboard IPO Listing-Gain Analyzer")
st.markdown(
    "Query an upcoming or recent Indian Mainboard IPO to trigger the grounded research agent, "
    "audit snapshot evidence, review parameter inputs, and inspect conformal gain ranges."
)

col_input, col_btn = st.columns([4, 1])
with col_input:
    query = st.text_input(
        "Enter Company Name (e.g. 'HD Fire Protect Limited' or 'Hyundai Motor India'):",
        value=st.session_state.get("current_query", "HD Fire Protect Limited")
    )
with col_btn:
    st.write("")
    st.write("")
    analyze_btn = st.button("🚀 Analyze IPO", use_container_width=True)

# State initialization
if "candidate_schema" not in st.session_state or analyze_btn:
    with st.spinner(f"Initiating grounded research agent for '{query}'..."):
        # Progress steps
        pbar = st.progress(20, text="Searching verified prospectus filings and aggregator tables...")
        try:
            schema = execute_research_run(query)
            pbar.progress(60, text="Fetching HTML pages and saving evidence snapshots under data/evidence/research/...")
            pbar.progress(90, text="Running code-based numeric and quote grounding verification...")
            st.session_state["candidate_schema"] = schema
            st.session_state["current_query"] = query
            pbar.progress(100, text="Research run complete.")
            pbar.empty()
        except PermissionError as exc:
            pbar.empty()
            st.error(str(exc))
            st.stop()

schema: IPOCandidateSchema = st.session_state["candidate_schema"]
metrics = schema.grounding_metrics()

# Tabs for Organized Interface
tab_analysis, tab_evidence, tab_neighbors, tab_track_record = st.tabs([
    "📈 Predictive Analysis",
    "🔍 Evidence & Grounding Audit",
    "🏢 Similar Historical IPOs",
    "📜 Track Record & Governance"
])

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1: PREDICTIVE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_analysis:
    st.subheader(f"Analysis: {schema.company}")
    features = schema.to_model_features()
    
    # Timing and Prediction Mode Check
    mode, mode_reasons = determine_prediction_mode(
        close_date_str=str(features.get("close_date", "")),
        listing_date_str=str(features.get("listing_date", "")),
        notes=str(features.get("notes", ""))
    )
    
    if mode == "PREVIEW":
        st.warning(f"⚠️ **INTERACTIVE PREVIEW ONLY**: {mode_reasons[0]}")
    elif mode == "INVALID":
        st.error(f"❌ **INVALID FOR FORWARD SCORING**: {mode_reasons[0]}")
    else:
        st.success(f"✅ **FORWARD ELIGIBLE**: Bidding closed. Prediction is eligible for forward audit logging.")

    # Run Authoritative Scoring
    try:
        scored = score_ipo(features)
    except Exception as score_err:
        st.error(f"Scoring Error: {score_err}")
        scored = None

    if scored:
        pt_est = scored["predicted_gain_pct"]
        gmp_val = scored["gmp_pct"]
        p_gt10 = scored["prob_gt10"]
        c_low, c_high = scored["conformal_interval_80"]
        rule = scored["rule_applied"]

        # 1. Headline Result Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Estimated Listing Gain", f"{pt_est:+.2f}%")
        with col2:
            st.metric("80% Conformal Interval", f"[{c_low:+.1f}%, {c_high:+.1f}%]")
        cal_min, cal_max = get_calibrated_probability_range()
        with col3:
            if cal_min <= p_gt10 <= cal_max:
                st.metric("P(Listing Gain > 10%)", f"{p_gt10 * 100:.1f}%", help=f"Platt-calibrated probability (measured range: {cal_min*100:.1f}% - {cal_max*100:.1f}%)")
            else:
                st.metric("P(Listing Gain > 10%)", "not shown: outside measured range", help=f"Value outside empirically calibrated range [{cal_min*100:.1f}%, {cal_max*100:.1f}%]")
        with col4:
            gmp_display = f"{gmp_val:+.2f}%" if gmp_val is not None else "Not Available"
            st.metric("Observed Final GMP", gmp_display)

        st.info(f"**Applied Decision Rule**: `{rule}` (Model Version: `{scored['model_version']}`)")

        # 2. Conformal Interval Visualizer
        st.write("#### 80% Conformal Prediction Range vs Signals")
        chart_df = pd.DataFrame({
            "Signal": ["80% Lower Bound", "Model Point Estimate", "Observed GMP" if gmp_val is not None else "Model Point Estimate", "80% Upper Bound"],
            "Gain (%)": [c_low, pt_est, gmp_val if gmp_val is not None else pt_est, c_high]
        }).set_index("Signal")
        st.bar_chart(chart_df)

        # 3. Historical Distribution Context
        master_df = load_historical_master()
        if not master_df.empty:
            st.write("#### Historical Mainboard Listing Gain Distribution")
            hist_values = master_df["listing_gain_pct"].clip(lower=-40, upper=150)
            hist, bin_edges = np.histogram(hist_values, bins=25)
            bin_labels = [f"{bin_edges[i]:.0f}%" for i in range(len(bin_edges)-1)]
            hist_chart_df = pd.DataFrame({"Listing Gain Frequency": hist}, index=bin_labels)
            st.bar_chart(hist_chart_df)
            st.caption(f"Historical sample size: {len(master_df)} mainboard issues (2010–2026).")

        # 4. Forward Prediction Logging Action
        st.write("---")
        st.write("#### Action: Record to Append-Only Prediction Log")
        
        can_log, log_issues = validate_candidate_for_forward_logging(features)
        
        col_log_btn, col_log_info = st.columns([1, 3])
        with col_log_btn:
            log_btn = st.button("📝 Log This Prediction", disabled=(not can_log), use_container_width=True)
            
        with col_log_info:
            if not can_log:
                st.caption(f"Logging disabled: {'; '.join(log_issues)}")
            else:
                st.caption("Eligible for permanent append-only audit logging.")

        if log_btn and can_log:
            try:
                rec = append_prediction_log(
                    company=schema.company,
                    open_date=str(features.get("open_date", "")),
                    close_date=str(features.get("close_date", "")),
                    listing_date=str(features.get("listing_date", "")),
                    features=features,
                    pred_gain_pct=pt_est,
                    pred_prob_gt10=p_gt10,
                    gmp_pct_at_scoring=gmp_val,
                    status="FORWARD",
                    notes=schema.notes or "Console user logged forward prediction",
                    model_version=scored["model_version"]
                )
                st.success(f"Successfully logged FORWARD row for {schema.company} at {rec['scored_at']}!")
            except Exception as append_err:
                st.error(f"Failed to append to log: {append_err}")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2: EVIDENCE & GROUNDING AUDIT
# ══════════════════════════════════════════════════════════════════════════════
with tab_evidence:
    st.subheader("Data Quality & Grounding Evidence Audit")
    st.write(
        f"**Grounding Rate**: `{metrics['grounding_rate_pct']}%` "
        f"({metrics['verified_fields']} of {metrics['populated_fields']} proposed fields confirmed in code-saved snapshots)."
    )

    rows = []
    for fname in [
        "issue_price", "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
        "sub_qib", "sub_nii", "sub_retail", "sub_total", "pe_ratio", "peer_median_pe",
        "debt_equity", "sector", "exchange", "gmp_pct", "open_date", "close_date", "listing_date"
    ]:
        prop: FieldProposal = getattr(schema, fname, FieldProposal())
        gv = prop.get_grounded_value()
        rv = prop.value
        label = f"{fname} (not used by model)" if fname in ("pe_ratio", "peer_median_pe", "debt_equity") else fname
        rows.append({
            "Feature": label,
            "Grounded Value": str(gv) if gv is not None else "None",
            "Raw Value": str(rv) if rv is not None else "None",
            "Grounding Status": prop.grounding_status,
            "Source URL": prop.source_url or "N/A",
            "Snapshot Path": prop.snapshot_path or "N/A",
            "Verbatim Quote": prop.verbatim_quote or "N/A"
        })
        
    audit_df = pd.DataFrame(rows)
    st.dataframe(audit_df, use_container_width=True)

    # JSON Download
    st.download_button(
        "⬇️ Download Research Evidence (JSON)",
        data=schema.model_dump_json(indent=2),
        file_name=f"{schema.company}_evidence_{schema.run_id}.json",
        mime="application/json"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3: NEAREST NEIGHBORS
# ══════════════════════════════════════════════════════════════════════════════
with tab_neighbors:
    st.subheader(f"Top 5 Similar Historical Mainboard IPOs")
    st.markdown("Comparables identified via normalized distance on issue size, subscription demand, and sector:")
    master_df = load_historical_master()
    if not master_df.empty:
        neighbors_df = find_nearest_5_neighbors(master_df, schema.to_model_features())
        st.dataframe(neighbors_df, use_container_width=True)
    else:
        st.info("Historical master data not available.")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4: TRACK RECORD & GOVERNANCE
# ══════════════════════════════════════════════════════════════════════════════
with tab_track_record:
    st.subheader("Live Forward Track Record & Retraining Governance")
    log_path = ROOT_DIR / "predictions" / "prediction_log.csv"
    if log_path.exists():
        log_df = pd.read_csv(log_path)
        forward_df = log_df[log_df["status"] == "FORWARD"]
        listed_forward = forward_df.dropna(subset=["actual_gain_pct"])
        
        # Provisional Banner
        if len(listed_forward) < 30:
            st.warning(
                f"⚠️ **PROVISIONAL EVALUATION BANNER**: Currently {len(listed_forward)} listed issues with recorded outcomes. "
                "Conformal and empirical calibration guarantees require n >= 30 completed forward issues. "
                "All performance numbers are provisional."
            )

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.metric("Total Forward Predictions Logged", len(forward_df))
        with col_t2:
            st.metric("Completed Listings (with Actuals)", len(listed_forward))
        with col_t3:
            st.metric("Active Champion Model", "v4.0.0-champion (Platt-calibrated)")

        st.write("#### Full Prediction Audit Ledger")
        st.dataframe(
            log_df[["scored_at", "company", "listing_date", "pred_gain_pct", "pred_prob_gt10", "gmp_pct_at_scoring", "actual_gain_pct", "status"]],
            use_container_width=True
        )
    else:
        st.info("No forward prediction log found.")

    st.write("---")
    st.caption(
        "Governance Policy: Automatic model promotion is strictly disabled in CI. "
        "Candidate models require paired bootstrap 95% non-inferiority intervals and manual authorization."
    )
