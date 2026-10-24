"""Unit and regression tests for OpenRouter Research Agent integration (Workstream D)."""

import os
import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from opi.research_agent import OpenRouterResearchProvider, ground_field_proposal

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_models_config_exists_and_valid():
    """Verify that config/research_models.json contains required free-tier models."""
    cfg_path = ROOT_DIR / "config" / "research_models.json"
    assert cfg_path.exists(), "config/research_models.json is missing"

    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    models = data.get("models", [])
    assert len(models) >= 3, "Expected at least 3 models in config"
    assert "nvidia/nemotron-3.5-super-vl:free" in models
    assert "google/gemma-4-31b-it:free" in models
    assert "nvidia/nemotron-3-super-120b-a12b:free" in models


def test_openrouter_provider_requires_key():
    """Verify ValueError is raised if OPENROUTER_API_KEY is not in env or arguments."""
    with patch.dict(os.environ, {}, clear=True):
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable required"):
            OpenRouterResearchProvider()


def test_openrouter_404_fallthrough():
    """Mock HTTP 404 on model 1, verify provider falls through to model 2."""
    dummy_key = "test_key_non_secret"
    provider = OpenRouterResearchProvider(api_key=dummy_key)

    mock_resp_404 = MagicMock()
    mock_resp_404.status_code = 404

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({"company": "Test Co", "issue_price": {"value": 250.0}})
                }
            }
        ]
    }

    with patch("requests.post", side_effect=[mock_resp_404, mock_resp_200]) as mock_post:
        res = provider.extract_ipo("Test Co", {"https://source": "Sample page"})
        assert res.get("company") == "Test Co"
        assert res.get("_model_used") == provider.models[1]
        assert mock_post.call_count == 2


def test_openrouter_429_retry():
    """Mock HTTP 429 on first try, verify provider retries and succeeds."""
    dummy_key = "test_key_non_secret"
    provider = OpenRouterResearchProvider(api_key=dummy_key)

    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({"company": "Retry Co", "issue_price": {"value": 300.0}})
                }
            }
        ]
    }

    with patch("requests.post", side_effect=[mock_resp_429, mock_resp_200]), patch("time.sleep") as mock_sleep:
        res = provider.extract_ipo("Retry Co", {"https://source": "Sample page"})
        assert res.get("company") == "Retry Co"
        assert mock_sleep.called


def test_ungrounded_field_dropped(tmp_path):
    """Verify that ungrounded fields are suppressed to None."""
    html_fixture = {"https://example.com": "<html><body>No price here</body></html>"}
    proposal = {"value": 999.0, "url": "https://example.com", "quote": "Rs 999"}
    field = ground_field_proposal("issue_price", proposal, "test_ungrounded", float, html_fixture, target_dir=tmp_path)

    assert field.grounding_status != "VERIFIED_IN_SNAPSHOT"
    assert field.value is None
    assert field.get_grounded_value() is None


def test_no_openrouter_keys_committed():
    """Verify that no actual OpenRouter secret keys are committed or staged."""
    res = subprocess.run(["git", "grep", "-E", r"sk-or-[a-zA-Z0-9]{8,}"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    assert len(res.stdout.strip()) == 0, f"Found actual OpenRouter key committed: {res.stdout}"

    # Also verify all sk-or- matches in repo are strictly safety rule/command references
    res2 = subprocess.run(["git", "grep", "sk-or-"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    doc_tokens = ("planning_and_goals", "preregistration", "2_building_and_execution", "3_outcome_and_verdict", "test_openrouter_agent", "verify_extra")
    unexpected = [l for l in res2.stdout.splitlines() if not any(t in l for t in doc_tokens)]
    assert len(unexpected) == 0, f"Found unexpected sk-or- match outside phase docs: {unexpected}"
