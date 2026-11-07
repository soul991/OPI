"""Tests for research agent schema validation and sanitization (D-111)."""

import json
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest
from pydantic import ValidationError

from opi.schema import IPOCandidateSchema, FieldProposal
from opi.research_agent import ground_field_proposal, sanitize_proposed_numeric_value


def test_bombay_coated_schema_validation_reproduced():
    """D-111: Reproduce 2 validation errors when uncoerced strings enter IPOCandidateSchema."""
    fp_price = FieldProposal(value="₹82", grounding_status="VERIFIED_IN_SNAPSHOT")
    fp_lot = FieldProposal(value="182 Shares", grounding_status="VERIFIED_IN_SNAPSHOT")

    with pytest.raises(ValidationError) as exc_info:
        IPOCandidateSchema(
            company="Bombay Coated & Special Steels",
            issue_price=fp_price,
            lot_size=fp_lot,
        )

    err_text = str(exc_info.value)
    assert "2 validation errors for IPOCandidateSchema" in err_text
    assert "issue_price.value" in err_text
    assert "lot_size.value" in err_text


def test_bombay_coated_sanitizer_fixes_validation_error(tmp_path):
    """D-111: Sanitizer cleans currency symbols and unit strings, allowing schema instantiation."""
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "data" / "evidence" / "research" / "run_20261102_145250_bombay-coate"
    assert fixture_dir.exists(), f"Evidence fixture dir missing: {fixture_dir}"

    issue_html = (fixture_dir / "issue-price.html").read_text(encoding="utf-8")
    fixtures = {"default": issue_html}

    raw_issue_price = {
        "value": "₹82",
        "quote": "Bombay Coated & Special Steels IPO is set issue price band at ₹78 to ₹82",
        "url": "https://www.chittorgarh.com/ipo/bombay-coated-special-steels-ipo/1897/",
    }
    raw_lot_size = {
        "value": "182 Shares",
        "quote": "Bombay Coated & Special Steels IPO lot size is 182",
        "url": "https://www.chittorgarh.com/ipo/bombay-coated-special-steels-ipo/1897/",
    }

    test_ev_dir = tmp_path / "mock_ev"
    test_ev_dir.mkdir(parents=True, exist_ok=True)

    fp_price = ground_field_proposal(
        "issue_price",
        raw_issue_price,
        "run_test",
        float,
        html_fixtures=fixtures,
        target_dir=test_ev_dir,
    )
    fp_lot = ground_field_proposal(
        "lot_size",
        raw_lot_size,
        "run_test",
        int,
        html_fixtures=fixtures,
        target_dir=test_ev_dir,
    )

    # Values must be cleaned to valid numbers
    assert fp_price.value == 82.0
    assert isinstance(fp_price.value, float)
    assert fp_lot.value == 182
    assert isinstance(fp_lot.value, int)

    # Must validate cleanly into IPOCandidateSchema
    schema = IPOCandidateSchema(
        company="Bombay Coated & Special Steels",
        issue_price=fp_price,
        lot_size=fp_lot,
    )
    assert schema.issue_price.value == 82.0
    assert schema.lot_size.value == 182


def test_research_agent_failure_raises_alert(tmp_path, monkeypatch, capsys):
    """D-111: A research agent failure during scoring raises a visible alert and logs ALERT action."""
    from scripts.score_ipo import score_and_log_ipo

    monkeypatch.setenv("OPI_ENV", "test")
    monkeypatch.setenv("OPI_LLM_PROVIDER", "mock")

    test_log = tmp_path / "prediction_log.csv"
    test_run_log = tmp_path / "run_log.csv"
    test_model_versions = tmp_path / "model_versions.csv"
    monkeypatch.setattr("opi.log.LOG_PATH", test_log)
    monkeypatch.setattr("opi.log.RUN_LOG_PATH", test_run_log)
    monkeypatch.setattr("opi.log.MODEL_VERSIONS_PATH", test_model_versions)
    monkeypatch.setattr("scripts.score_ipo.render_dashboard_html", lambda: None)

    mock_parsed = {
        "issue_price": 80.0,
        "issue_size_cr": 150.0,
        "fresh_issue_pct": 100.0,
        "ofs_pct": 0.0,
        "lot_size": 100,
        "sub_qib": 1.0,
        "sub_nii": 1.0,
        "sub_retail": 1.0,
        "sub_total": 1.0,
        "gmp_pct": None,
        "gmp_as_of_date": "2026-11-02",
    }

    with patch("scripts.score_ipo.ingest_ipo_data", return_value=mock_parsed):
        with patch("scripts.score_ipo.get_market_data", return_value=(1.0, 15.0, 10.0)):
            with patch("opi.research_agent.execute_research_run", side_effect=RuntimeError("Simulated LLM API failure")):
                score_and_log_ipo(
                    company="Alert Test Corp",
                    listing_date="2026-11-20",
                    close_date="2026-11-15",
                    overview_url="https://mock.com/overview",
                    sub_url="https://mock.com/sub",
                    dry_run=False,
                )

    out = capsys.readouterr().out
    assert "[ALERT]" in out
    assert "[Research Agent Failure]" in out

    assert test_run_log.exists()
    df_rl = pd.read_csv(test_run_log)
    alert_rows = df_rl[(df_rl["action"] == "ALERT") & (df_rl["status"] == "RESEARCH_AGENT_ALERT")]
    assert len(alert_rows) >= 1
    assert "Alert Test Corp" in alert_rows["company"].values
