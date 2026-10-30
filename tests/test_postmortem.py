"""Tests for Workstream A forward errors post-mortem (D-041, D-046, D-048)."""

import csv
import json
from pathlib import Path
import re
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]

from scripts.forward_postmortem import generate_postmortem


def test_forward_postmortem_table_generated():
    """D-041: forward_postmortem.md must be generated and contain all required audit fields."""
    content = generate_postmortem()
    out_file = ROOT_DIR / "phases" / "Phase 12" / "forward_postmortem.md"
    assert out_file.exists(), "phases/Phase 12/forward_postmortem.md must exist"

    # Verify table headers
    assert "| Company |" in content
    assert "Model Err (pp)" in content
    assert "GMP Err (pp)" in content
    assert "Nifty Move on Listing Day" in content
    assert "Sub (QIB / NII / Retail / Total)" in content

    # Verify Bonfiglioli and Zetwerk post-mortems are present
    assert "Bonfiglioli Transmissions Limited" in content
    assert "21.10 pp" in content
    assert "Zetwerk Manufacturing Business Limited" in content

    # Verify epistemic discipline
    assert "Hypothesis (untested)" in content
    assert re.search(r"n\s*=\s*\d+\s*<\s*30", content) or "n=" in content


def test_narrative_numbers_from_log():
    """D-046 & D-048: Every multiple (\\d+(\\.\\d+)?x) and percentage in forward_postmortem.md must map to log/evidence."""
    postmortem_path = ROOT_DIR / "phases" / "Phase 12" / "forward_postmortem.md"
    assert postmortem_path.exists(), "phases/Phase 12/forward_postmortem.md must exist"
    content = postmortem_path.read_text(encoding="utf-8")

    # Load valid values from prediction log and feature snapshots
    log_path = ROOT_DIR / "predictions" / "prediction_log.csv"
    assert log_path.exists()
    log = list(csv.DictReader(log_path.open(encoding="utf-8")))

    valid_values = set()
    for r in log:
        if r["status"] == "FORWARD":
            for k in ["pred_gain_pct", "actual_gain_pct", "gmp_pct_at_scoring"]:
                if r.get(k) and r[k] != "nan":
                    try:
                        valid_values.add(round(float(r[k]), 2))
                        valid_values.add(round(float(r[k]), 1))
                    except Exception:
                        pass
            try:
                feats = json.loads(r["features_snapshot_json"])
                for fk in ["sub_qib", "sub_nii", "sub_retail", "sub_total", "ofs_pct", "fresh_issue_pct"]:
                    if feats.get(fk) is not None:
                        try:
                            v = float(feats[fk])
                            valid_values.add(round(v, 2))
                            valid_values.add(round(v, 1))
                        except Exception:
                            pass
            except Exception:
                pass

    # Load valid values from saved market evidence files
    market_dir = ROOT_DIR / "data" / "evidence" / "market"
    for p in market_dir.glob("*_nifty.json"):
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
            if "nifty_day_return_pct" in m and m["nifty_day_return_pct"] is not None:
                valid_values.add(round(float(m["nifty_day_return_pct"]), 2))
                valid_values.add(round(float(m["nifty_day_return_pct"]), 1))
        except Exception:
            pass

    # Check multiples (e.g. 120.78x, 3.1x)
    multiples = re.findall(r"(\d+(?:\.\d+)?)\s*x", content)
    unmatched_multiples = [
        m for m in multiples if not any(abs(float(m) - val) < 0.06 for val in valid_values)
    ]
    assert len(unmatched_multiples) == 0, f"Found ungrounded subscription multiples: {unmatched_multiples}"

    # Check percentages (e.g. +21.10%, -0.39%, 100.0%)
    percentages = re.findall(r"([+-]?\d+(?:\.\d+)?)\s*%", content)
    unmatched_pcts = [
        p for p in percentages if not any(abs(float(p) - val) < 0.06 for val in valid_values)
    ]
    assert len(unmatched_pcts) == 0, f"Found ungrounded percentage values: {unmatched_pcts}"
