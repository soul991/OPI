"""OPI - Indian Mainboard IPO Listing-Gain Prediction & Verification Framework."""

__version__ = "0.8.0"

from opi.score import score_ipo, load_champion_model
from opi.validate import validate_ipo_features, validate_timing_and_leakage
from opi.collect import collect_ipo_data, save_evidence_snapshot
from opi.log import append_prediction_log, update_actual_outcome
from opi.report import generate_dashboard_data, render_dashboard_html

__all__ = [
    "score_ipo",
    "load_champion_model",
    "validate_ipo_features",
    "validate_timing_and_leakage",
    "collect_ipo_data",
    "save_evidence_snapshot",
    "append_prediction_log",
    "update_actual_outcome",
    "generate_dashboard_data",
    "render_dashboard_html",
]
