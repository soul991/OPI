"""
Stage 'preview' alert runner for OPI.
Evaluates Mainboard IPOs closing today (IST) at 11:45 AM IST snapshot.
Ingests live subscription, fetches GMP with timestamp, executes model scoring
in PREVIEW mode, applies preregistered decision rules, logs to predictions/preview_log.csv,
and dispatches Telegram preview alerts.
"""

from datetime import datetime, date, timezone, timedelta
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from opi.alert_state import already_sent, record_alert_sent
from opi.discover import discover_ipos, get_today_ist
from opi.notify import send_telegram
from opi.score import score_ipo
from opi.validate import determine_prediction_mode

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PREVIEW_CSV = ROOT_DIR / "predictions" / "preview_log.csv"

PREVIEW_COLUMNS = [
    "scored_at_ist",
    "company",
    "open_date",
    "close_date",
    "listing_date",
    "issue_price",
    "lot_size",
    "sub_qib",
    "sub_nii",
    "sub_retail",
    "sub_total",
    "gmp_pct",
    "gmp_source",
    "gmp_as_of",
    "pred_gain_pct",
    "pred_prob_gt10",
    "pi_lower",
    "pi_upper",
    "suggestion",
    "suggestion_basis",
    "features_snapshot_json",
    "run_id",
]

IST = timezone(timedelta(hours=5, minutes=30))


def compute_suggestion(
    gmp_pct: Optional[float],
    pred_gain: Optional[float],
    prob_gt10: Optional[float],
) -> Tuple[str, str]:
    """
    Compute Apply/Marginal/Skip suggestion according to Phase 21 preregistered v2 rules.
    T1 = 10.0%, Marginal band [5.0% to 10.0%) for GMP.
    T2 = 15.0% with P(gain > 10%) >= 0.60 for model fallback (no marginal band on model).
    """
    # Regime A: GMP observed
    if gmp_pct is not None and not pd.isna(gmp_pct):
        g = float(gmp_pct)
        if g >= 10.0:
            return "APPLY", f"Observed GMP (+{g:.1f}%) >= T1 (+10.0%)"
        elif 5.0 <= g < 10.0:
            return "MARGINAL: small expected gain, your call", f"Observed GMP (+{g:.1f}%) is in the marginal band [5.0% to 10.0%)"
        elif 0.0 <= g < 5.0:
            return "SKIP", f"Observed GMP (+{g:.1f}%) below 5.0% minimum threshold; historical mean return is flat/negative"
        else:
            return "SKIP", f"Negative GMP discount ({g:.1f}%) indicates elevated listing risk"

    # Regime B: No GMP recorded (Model fallback)
    if pred_gain is not None and not pd.isna(pred_gain) and prob_gt10 is not None and not pd.isna(prob_gt10):
        pg = float(pred_gain)
        p = float(prob_gt10)
        if pg >= 15.0 and p >= 0.60:
            return "APPLY", f"Model PREVIEW estimate (+{pg:.1f}%) >= T2 (+15.0%) with calibrated P(>10%) >= 60%"
        else:
            return "SKIP", f"Model PREVIEW estimate (+{pg:.1f}%) or calibrated probability ({p*100:.1f}%) below threshold"

    # Regime C: Critical missing data
    return "NO SUGGESTION", "Insufficient data to compute recommendation"


def format_preview_message(
    company: str,
    close_date: str,
    listing_date: str,
    issue_price: Any,
    lot_size: Any,
    sub_qib: Any,
    sub_nii: Any,
    sub_retail: Any,
    sub_total: Any,
    sub_as_of: str,
    gmp_pct: Optional[float],
    gmp_source: Optional[str],
    gmp_as_of: Optional[str],
    pred_gain: Optional[float],
    prob_gt10: Optional[float],
    pi_lower: Optional[float],
    pi_upper: Optional[float],
    suggestion: str,
    suggestion_basis: str,
    n_listed: int = 13,
) -> str:
    """Format standardized Telegram Preview alert matching preregistration."""
    # Min bid amount
    min_bid = "TBD"
    try:
        p_val = float(str(issue_price).replace("₹", "").replace(",", "").strip())
        l_val = int(str(lot_size).replace(",", "").strip())
        min_bid = f"₹{int(p_val * l_val):,}"
    except Exception:
        pass

    # Format live subscription
    def fmt_sub(val: Any) -> str:
        try:
            return f"{float(val):.2f}x"
        except Exception:
            return str(val) if val else "TBD"

    # Format GMP line
    if gmp_pct is not None and not pd.isna(gmp_pct):
        source_str = gmp_source or "Market"
        ts_str = f", as of {gmp_as_of}" if gmp_as_of else ""
        gmp_line = f"+{float(gmp_pct):.1f}% ({source_str}{ts_str})"
    else:
        gmp_line = "No GMP recorded"

    # Format Model lines
    if pred_gain is not None and not pd.isna(pred_gain):
        model_line = f"+{float(pred_gain):.1f}% (live subscription; model trained on final figures)"
    else:
        model_line = "Not available"

    if prob_gt10 is not None and not pd.isna(prob_gt10):
        prob_line = f"{float(prob_gt10)*100:.1f}%"
    else:
        prob_line = "Not available"

    if pi_lower is not None and pi_upper is not None:
        pi_line = f"[{float(pi_lower):.1f}%, {float(pi_upper):.1f}%]"
    else:
        pi_line = "[N/A]"

    msg = (
        f"🎯 OPI PREVIEW ALERT: {company}\n"
        f"Status: Bidding Closes Today (11:45 AM IST Snapshot)\n\n"
        f"📅 Key Dates:\n"
        f"  • Bidding Closes: Today ({close_date})\n"
        f"  • Expected Listing: {listing_date or 'TBD'}\n"
        f"💰 Issue Price: ₹{issue_price} (Lot Size: {lot_size} shares = {min_bid})\n\n"
        f"📊 Live Subscription Status (as of {sub_as_of}):\n"
        f"  • QIB: {fmt_sub(sub_qib)}\n"
        f"  • NII: {fmt_sub(sub_nii)}\n"
        f"  • Retail: {fmt_sub(sub_retail)}\n"
        f"  • Total: {fmt_sub(sub_total)}\n\n"
        f"📈 Market Signals:\n"
        f"  • Grey Market Premium (GMP): {gmp_line}\n"
        f"  • Model PREVIEW Estimate: {model_line}\n"
        f"  • Calibrated P(Gain > 10%): {prob_line}\n"
        f"  • 80% Conformal Prediction Interval: {pi_line}\n\n"
        f"💡 Decision Suggestion: {suggestion}\n"
        f"  • Basis: {suggestion_basis}\n\n"
        f"⚠️ Sample Size Notice: n listed = {n_listed} of 30 (Provisional)\n"
        f"Decision aid only, not financial advice."
    )
    return msg


def ensure_preview_log_file(csv_path: Optional[Path] = None) -> Path:
    target_path = Path(csv_path) if csv_path else DEFAULT_PREVIEW_CSV
    if not target_path.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(",".join(PREVIEW_COLUMNS) + "\n")
    return target_path


def run_preview_stage(
    candidates: Optional[List[Dict[str, Any]]] = None,
    dry_run: bool = False,
    run_id: Optional[str] = None,
    alerts_csv: Optional[Any] = None,
    preview_csv: Optional[Any] = None,
    as_of_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Run preview stage:
    1. Filter candidates closing today (IST) with BIDDING_OPEN status.
    2. Ingest live subscription & GMP.
    3. Score in PREVIEW mode.
    4. Log exclusively to preview_log.csv (never prediction_log.csv).
    5. Deliver alert and record in alerts_sent.csv.
    """
    today_str = as_of_date or get_today_ist()
    target_preview_csv = ensure_preview_log_file(preview_csv)

    if candidates is None:
        raw_candidates = discover_ipos(as_of_date=today_str)
    else:
        raw_candidates = candidates

    sent_previews: List[Dict[str, Any]] = []

    for cand in raw_candidates:
        company = cand.get("company", "").strip()
        close_date = str(cand.get("close_date", "")).strip()
        listing_date = str(cand.get("listing_date", "")).strip()
        status = cand.get("status", "").upper()
        ipo_type = cand.get("type", "Mainboard")

        if not company or close_date != today_str:
            continue
        if ipo_type and "sme" in ipo_type.lower():
            continue
        if status not in ("BIDDING_OPEN", "UPCOMING"):
            continue

        # Check idempotency
        if already_sent(company, close_date, "preview", csv_path=alerts_csv):
            logger.info(f"Skipping {company}: preview alert already sent for close_date {close_date}.")
            continue

        # Validate prediction mode is strictly PREVIEW
        mode, reasons = determine_prediction_mode(
            close_date_str=close_date,
            listing_date_str=listing_date or "2099-01-01",
            notes="live bidding 11:45 AM preview",
        )
        if mode != "PREVIEW":
            logger.warning(f"Unexpected prediction mode '{mode}' for preview candidate {company}: {reasons}")

        # Extract features
        issue_price = cand.get("issue_price") or "TBD"
        lot_size = cand.get("lot_size") or "TBD"
        sub_qib = cand.get("sub_qib")
        sub_nii = cand.get("sub_nii")
        sub_retail = cand.get("sub_retail")
        sub_total = cand.get("sub_total")
        sub_as_of = cand.get("sub_as_of") or datetime.now(IST).strftime("%H:%M IST")

        gmp_pct = cand.get("gmp_pct")
        gmp_source = cand.get("gmp_source") or cand.get("source_url") or "Market"
        gmp_as_of = cand.get("gmp_as_of") or datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

        # Execute model scoring if subscription is present
        pred_gain = None
        prob_gt10 = None
        pi_lower = None
        pi_upper = None
        features_json = "{}"

        # If we have numeric features, score with champion model
        try:
            score_df = pd.DataFrame(
                [
                    {
                        "company": company,
                        "issue_price": float(issue_price) if str(issue_price).replace(".", "").isdigit() else 100.0,
                        "lot_size": float(lot_size) if str(lot_size).isdigit() else 50.0,
                        "sub_qib": float(sub_qib) if sub_qib is not None else 1.0,
                        "sub_nii": float(sub_nii) if sub_nii is not None else 1.0,
                        "sub_retail": float(sub_retail) if sub_retail is not None else 1.0,
                        "sub_total": float(sub_total) if sub_total is not None else 1.0,
                        "gmp_pct": float(gmp_pct) if gmp_pct is not None else None,
                    }
                ]
            )
            score_res = score_ipo(score_df)
            pred_gain = score_res.get("predicted_gain_pct")
            prob_gt10 = score_res.get("prob_gt10")
            ci = score_res.get("conformal_interval_80", [None, None])
            pi_lower, pi_upper = ci[0], ci[1]
            features_json = json.dumps(score_df.iloc[0].to_dict())
        except Exception as e:
            logger.warning(f"Could not compute model score for {company}: {e}")

        # Compute recommendation rule
        suggestion, suggestion_basis = compute_suggestion(
            gmp_pct=float(gmp_pct) if gmp_pct is not None else None,
            pred_gain=pred_gain,
            prob_gt10=prob_gt10,
        )

        # Format message
        message_text = format_preview_message(
            company=company,
            close_date=close_date,
            listing_date=listing_date,
            issue_price=issue_price,
            lot_size=lot_size,
            sub_qib=sub_qib,
            sub_nii=sub_nii,
            sub_retail=sub_retail,
            sub_total=sub_total,
            sub_as_of=sub_as_of,
            gmp_pct=float(gmp_pct) if gmp_pct is not None else None,
            gmp_source=gmp_source,
            gmp_as_of=gmp_as_of,
            pred_gain=pred_gain,
            prob_gt10=prob_gt10,
            pi_lower=pi_lower,
            pi_upper=pi_upper,
            suggestion=suggestion,
            suggestion_basis=suggestion_basis,
        )

        # Deliver message
        success = send_telegram(message_text, dry_run=dry_run)
        if success:
            # Append strictly to preview_log.csv
            sent_at = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
            row_data = {
                "scored_at_ist": sent_at,
                "company": company,
                "open_date": str(cand.get("open_date", "")),
                "close_date": close_date,
                "listing_date": listing_date,
                "issue_price": str(issue_price),
                "lot_size": str(lot_size),
                "sub_qib": str(sub_qib) if sub_qib is not None else "",
                "sub_nii": str(sub_nii) if sub_nii is not None else "",
                "sub_retail": str(sub_retail) if sub_retail is not None else "",
                "sub_total": str(sub_total) if sub_total is not None else "",
                "gmp_pct": str(gmp_pct) if gmp_pct is not None else "",
                "gmp_source": str(gmp_source),
                "gmp_as_of": str(gmp_as_of),
                "pred_gain_pct": str(pred_gain) if pred_gain is not None else "",
                "pred_prob_gt10": str(prob_gt10) if prob_gt10 is not None else "",
                "pi_lower": str(pi_lower) if pi_lower is not None else "",
                "pi_upper": str(pi_upper) if pi_upper is not None else "",
                "suggestion": suggestion,
                "suggestion_basis": suggestion_basis,
                "features_snapshot_json": features_json,
                "run_id": str(run_id or os.environ.get("GITHUB_RUN_ID", "local")),
            }
            pd.DataFrame([row_data]).to_csv(
                target_preview_csv, mode="a", header=not target_preview_csv.exists(), index=False
            )

            # Record alert in alerts_sent.csv
            record_alert_sent(
                company=company,
                close_date=close_date,
                listing_date=listing_date,
                alert_type="preview",
                stage="preview",
                text=message_text,
                run_id=run_id,
                csv_path=alerts_csv,
            )

            sent_previews.append({"company": company, "close_date": close_date, "suggestion": suggestion})
            logger.info(f"Preview alert delivered for {company}.")
        else:
            logger.error(f"Failed to deliver preview alert for {company}.")

    return sent_previews
