"""Tests for research agent integration in daily scoring pipeline (D-082)."""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd

from scripts.score_ipo import score_and_log_ipo
from opi.schema import IPOCandidateSchema, FieldProposal

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_score_ipo_calls_research_agent_for_missing_fields(tmp_path, monkeypatch):
    """Verify research agent is called for missing fields and logs stats to run_log.csv."""
    monkeypatch.setenv("OPI_ENV", "test")
    monkeypatch.setenv("OPI_LLM_PROVIDER", "mock")

    # Mock ingest_ipo_data to return deterministic values with missing fundamentals
    mock_parsed = {
        "issue_price": 100.0,
        "issue_size_cr": 200.0,
        "fresh_issue_pct": 50.0,
        "ofs_pct": 50.0,
        "lot_size": 50,
        "sub_qib": 10.0,
        "sub_nii": 5.0,
        "sub_retail": 2.0,
        "sub_total": 7.0,
        "gmp_pct": 15.0,
        "gmp_as_of_date": "2026-11-02",
    }

    mock_schema = MagicMock(spec=IPOCandidateSchema)
    mock_schema.notes = "Research run via mock provider (model: test-model)"
    mock_schema.grounding_metrics.return_value = {
        "total_fields": 18,
        "populated_fields": 15,
        "verified_fields": 12,
        "failed_grounding": 3,
        "fetch_failed": 0,
        "grounding_rate_pct": 80.0,
    }
    mock_schema.to_model_features.return_value = {
        "pe_ratio": 22.5,
        "debt_equity": 0.45,
        "peer_median_pe": 28.0,
    }
    mock_schema.model_dump.return_value = {
        "pe_ratio": {"grounding_status": "VERIFIED_IN_SNAPSHOT"},
        "debt_equity": {"grounding_status": "VERIFIED_IN_SNAPSHOT"},
        "peer_median_pe": {"grounding_status": "NOT_FOUND_IN_SNAPSHOT"},  # Not grounded: must be dropped
    }

    synthetic_run_log = tmp_path / "run_log.csv"
    synthetic_pred_log = tmp_path / "prediction_log.csv"
    monkeypatch.setattr("opi.log.RUN_LOG_PATH", synthetic_run_log)
    monkeypatch.setattr("opi.log.LOG_PATH", synthetic_pred_log)
    monkeypatch.setattr("scripts.score_ipo.render_dashboard_html", lambda: None)

    with patch("scripts.score_ipo.ingest_ipo_data", return_value=mock_parsed):
        with patch("scripts.score_ipo.get_market_data", return_value=(2.5, 14.0, 15.0)):
            with patch("opi.research_agent.execute_research_run", return_value=mock_schema) as mock_agent:
                res = score_and_log_ipo(
                    company="Grounded Agent Test Limited",
                    listing_date="2026-11-20",
                    close_date="2026-11-15",
                    overview_url="https://mock.com/overview",
                    sub_url="https://mock.com/sub",
                    dry_run=False,
                )

                assert mock_agent.called, "Research agent was not invoked for missing fundamentals!"
                assert res is not None

                # Verify run_log was appended with agent stats
                assert synthetic_run_log.exists()
                df = pd.read_csv(synthetic_run_log)
                agent_rows = df[df["action"] == "RESEARCH_AGENT"]
                assert not agent_rows.empty, "No RESEARCH_AGENT entry in run_log.csv!"
                details = agent_rows.iloc[-1]["details"]
                assert "provider=" in details
                assert "model=" in details
                assert "grounded=" in details
                assert "grounding_rate=" in details


def test_research_agent_failure_falls_back_to_deterministic(tmp_path, monkeypatch):
    """Verify that when research agent raises, scoring continues via deterministic path."""
    monkeypatch.setenv("OPI_ENV", "test")
    monkeypatch.setenv("OPI_LLM_PROVIDER", "mock")

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

    synthetic_run_log = tmp_path / "run_log.csv"
    synthetic_pred_log = tmp_path / "prediction_log.csv"
    monkeypatch.setattr("opi.log.RUN_LOG_PATH", synthetic_run_log)
    monkeypatch.setattr("opi.log.LOG_PATH", synthetic_pred_log)
    monkeypatch.setattr("scripts.score_ipo.render_dashboard_html", lambda: None)

    with patch("scripts.score_ipo.ingest_ipo_data", return_value=mock_parsed):
        with patch("scripts.score_ipo.get_market_data", return_value=(1.0, 15.0, 10.0)):
            with patch("opi.research_agent.execute_research_run", side_effect=RuntimeError("All OpenRouter models failed")):
                res = score_and_log_ipo(
                    company="Fallback Test Limited",
                    listing_date="2026-11-20",
                    close_date="2026-11-15",
                    overview_url="https://mock.com/overview",
                    sub_url="https://mock.com/sub",
                    dry_run=False,
                )
                assert res is not None
                assert "predicted_gain_pct" in res
                assert "no GMP" in res.get("rule_applied", "")

                df = pd.read_csv(synthetic_run_log)
                fail_rows = df[(df["action"] == "RESEARCH_AGENT") & (df["status"] == "FAILED")]
                assert not fail_rows.empty
