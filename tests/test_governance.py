"""Governance regression tests: zero auto-promotion and governed learning loop."""

import os
import re
from pathlib import Path
import pandas as pd
import pytest

from scripts.promote_forward_rows import check_forward_row_eligibility, promote_forward_rows

ROOT = Path(__file__).resolve().parents[1]


def test_zero_automatic_model_promotion_in_codebase():
    """Verify that no script or workflow automatically promotes or overwrites champion artifacts."""
    suspicious_patterns = [
        re.compile(r"cp\s+.*challenger.*model/ipo_model", re.IGNORECASE),
        re.compile(r"shutil\.copy.*challenger.*ipo_model", re.IGNORECASE),
        re.compile(r"auto_promote\s*=\s*True", re.IGNORECASE),
    ]

    files_to_scan = list((ROOT / "scripts").glob("*.py")) + \
                    list((ROOT / ".github" / "workflows").glob("*.yml")) + \
                    list((ROOT / "opi").glob("*.py"))

    for filepath in files_to_scan:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        for pat in suspicious_patterns:
            assert not pat.search(content), f"Suspicious auto-promotion pattern found in {filepath}: {pat.pattern}"


def test_promote_forward_rows_dry_run_preserves_data():
    """Verify that promote_forward_rows(apply=False) is strictly read-only."""
    master_path = ROOT / "data" / "ipo_master.csv"
    prom_path = ROOT / "data" / "promotions.csv"

    master_before = master_path.read_text(encoding="utf-8") if master_path.exists() else ""
    prom_before = prom_path.read_text(encoding="utf-8") if prom_path.exists() else ""

    promote_forward_rows(apply=False)

    master_after = master_path.read_text(encoding="utf-8") if master_path.exists() else ""
    prom_after = prom_path.read_text(encoding="utf-8") if prom_path.exists() else ""

    assert master_before == master_after, "Dry run must NOT mutate data/ipo_master.csv"
    assert prom_before == prom_after, "Dry run must NOT mutate data/promotions.csv"


def test_promote_forward_rows_rejects_pending_actuals():
    """Verify that forward rows without verified actual listing gains are rejected."""
    master_df = pd.read_csv(ROOT / "data" / "ipo_master.csv")
    pending_row = pd.Series({
        "company": "Pending Listing Tech Limited",
        "listing_date": "2026-10-28",
        "status": "FORWARD",
        "actual_gain_pct": None,
        "features_snapshot_json": '{"issue_size_cr": 500.0}'
    })
    ok, reason, _ = check_forward_row_eligibility(pending_row, master_df)
    assert ok is False
    assert "pending" in reason.lower() or "not yet recorded" in reason.lower()
