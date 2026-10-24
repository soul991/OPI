"""Tests for Workstream C: Walk-Forward Conformal Interval & Tail Experiment (D-007, D-008)."""

from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_conformal_experiment_artifacts_exist():
    csv_path = ROOT_DIR / "phases" / "Phase 11" / "conformal_experiment.csv"
    md_path = ROOT_DIR / "phases" / "Phase 11" / "tail_and_intervals_report.md"

    assert csv_path.exists(), "conformal_experiment.csv not found"
    assert md_path.exists(), "tail_and_intervals_report.md not found"

    df = pd.read_csv(csv_path)
    assert len(df) == 3, f"Expected 3 model evaluations, found {len(df)}"
    assert "Adopted" in df.columns
    assert "Mean_Width_pp" in df.columns
    assert "Tail_Coverage_Pct" in df.columns


def test_champion_model_and_replay_intact():
    model_path = ROOT_DIR / "model" / "ipo_model_phase4.joblib"
    replay_path = ROOT_DIR / "predictions" / "champion_replay_v4.0.0-champion.csv"

    assert model_path.exists(), "Production champion model file missing"
    assert replay_path.exists(), "Champion replay file missing"


def test_conformal_candidates_rejected_per_preregistration():
    csv_path = ROOT_DIR / "phases" / "Phase 11" / "conformal_experiment.csv"
    df = pd.read_csv(csv_path).set_index("Model")

    c1 = df.loc["Candidate 1 (Mondrian Conformal)"]
    c2 = df.loc["Candidate 2 (Quantile CQR)"]

    assert not bool(c1["Adopted"]), "Candidate 1 must not be adopted"
    assert not bool(c2["Adopted"]), "Candidate 2 must not be adopted"

    # Verify Target 2 was not met by either candidate
    assert not bool(c1["Target2_Met"])
    assert not bool(c2["Target2_Met"])


def test_defects_documented_in_readme():
    readme_path = ROOT_DIR / "README.md"
    content = readme_path.read_text(encoding="utf-8")
    assert "D-007" in content, "D-007 not documented in README"
    assert "D-008" in content, "D-008 not documented in README"
