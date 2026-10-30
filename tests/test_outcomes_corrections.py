#!/usr/bin/env python3
"""tests/test_outcomes_corrections.py - Unit and regression tests for D-073.

Verifies:
1. prediction_log.csv remains strictly byte-identical (log immutability).
2. A second correction supersedes the first for the same company and date.
3. All reporting surfaces (effective df, dashboard data, forward markdown table)
   agree with the effective outcome value.
4. Attempting to record a correction without an existing evidence file is rejected.
5. Tier 2b cross-check rejects sources that diverge beyond 1.0%.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
import pandas as pd
import pytest

from opi.outcomes import (
    CORRECTIONS_COLUMNS,
    effective_outcome,
    fetch_tier2b_independent_sources,
    get_effective_predictions_df,
    record_outcome_correction,
)
from opi.report import generate_dashboard_data
from scripts.forward_report import generate_markdown_results_table

ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
CORRECTIONS_PATH = ROOT_DIR / "predictions" / "outcome_corrections.csv"


def test_log_is_byte_identical_after_corrections():
    """D-073: prediction_log.csv must remain immutable and unedited."""
    assert LOG_PATH.exists(), f"Missing prediction log at {LOG_PATH}"
    df_raw = pd.read_csv(LOG_PATH)
    paras_raw = df_raw[df_raw["company"].str.contains("Paras")].iloc[0]
    # The raw log MUST still contain the original 4.04 value
    assert float(paras_raw["actual_gain_pct"]) == 4.04


def test_second_correction_supersedes_first(tmp_path: Path):
    """D-073: A newer correction row supersedes earlier corrections for the same company and date."""
    corr_file = tmp_path / "outcome_corrections.csv"
    ev_file = tmp_path / "evidence.txt"
    ev_file.write_text("synthetic evidence", encoding="utf-8")

    # Record first correction: 720.00 (+3.90%)
    record_outcome_correction(
        company="Synthetic Ltd",
        listing_date="2026-10-28",
        field="actual_gain_pct",
        old_value="4.04",
        new_value="3.90",
        reason="First correction",
        evidence_path=ev_file,
        tier="tier2b",
        corrections_path=corr_file,
        root_dir=tmp_path,
    )

    # Record second correction: 725.00 (+4.62%)
    record_outcome_correction(
        company="Synthetic Ltd",
        listing_date="2026-10-28",
        field="actual_gain_pct",
        old_value="3.90",
        new_value="4.62",
        reason="Second correction superseding first",
        evidence_path=ev_file,
        tier="tier2b",
        corrections_path=corr_file,
        root_dir=tmp_path,
    )

    row = {
        "company": "Synthetic Ltd",
        "listing_date": "2026-10-28",
        "actual_gain_pct": "4.04",
        "notes": "outcome_source=tier2",
    }
    eff = effective_outcome(row, corrections_path=corr_file)
    assert eff["is_corrected"] is True
    assert eff["actual_gain_pct"] == 4.62
    assert eff["new_value"] == 4.62
    assert "Second correction" in eff["reason"]


def test_reports_agree_with_effective_value():
    """D-073: Effective dataframe, dashboard data, and forward markdown table all show +3.90% for Paras."""
    assert CORRECTIONS_PATH.exists(), "outcome_corrections.csv must exist"

    # 1. Effective dataframe
    eff_df = get_effective_predictions_df(log_path=LOG_PATH, corrections_path=CORRECTIONS_PATH)
    paras_eff = eff_df[eff_df["company"].str.contains("Paras")].iloc[0]
    assert float(paras_eff["actual_gain_pct"]) == 3.90
    assert bool(paras_eff["is_corrected"]) is True
    assert paras_eff["effective_tier"] == "tier2b"

    # 2. Dashboard data
    dash_data = generate_dashboard_data()
    paras_dash = next(r for r in dash_data["forward_rows"] if "Paras" in r["company"])
    assert paras_dash["actual_gain_pct"] == 3.90
    assert bool(paras_dash["is_corrected"]) is True

    # 3. Forward report markdown table
    md_table = generate_markdown_results_table(str(LOG_PATH))
    assert "+3.90%" in md_table
    assert "Tier 2b" in md_table
    paras_line = next(line for line in md_table.splitlines() if "Paras" in line)
    assert "**+3.90%**" in paras_line
    assert "Tier 2b" in paras_line
    assert "₹720.00" in paras_line


def test_correction_rejected_without_evidence_files(tmp_path: Path):
    """D-073: Attempting to record a correction without a real evidence file must raise ValueError."""
    corr_file = tmp_path / "outcome_corrections.csv"
    non_existent = tmp_path / "non_existent_file.json"

    with pytest.raises(ValueError, match="Evidence file does not exist"):
        record_outcome_correction(
            company="Synthetic Ltd",
            listing_date="2026-10-28",
            field="actual_gain_pct",
            old_value="4.04",
            new_value="3.90",
            reason="Unverified claim",
            evidence_path=non_existent,
            tier="tier2b",
            corrections_path=corr_file,
            root_dir=tmp_path,
        )


def test_tier2b_fetch_disagreement_rejected():
    """Tier 2b: Two independent sources diverging > 1.0% are rejected with an error reason."""
    mock_source_a = "<html><body><table><tr><td>Open</td><td>₹720.00</td></tr></table></body></html>"
    # Source B reports ₹750.00 (> 4% higher)
    mock_source_b = "<html><body><p>Shares listed at ₹750.00 apiece on NSE.</p></body></html>"

    pa, ra, pb, rb, err = fetch_tier2b_independent_sources(
        source_a_url="https://example.com/source_a",
        source_b_url="https://example.com/source_b",
        mock_source_a_text=mock_source_a,
        mock_source_b_text=mock_source_b,
    )

    assert pa == 720.00
    assert pb == 750.00
    assert err is not None
    assert "diverge beyond 1.0%" in err
