# GitHub Actions Run Evidence: D-020 Verification

## Overview
- **Defect ID**: D-020
- **Workflow**: Daily forward IPO scoring & monitoring (`.github/workflows/daily.yml`)
- **Run URL**: [https://github.com/soul991/OPI/actions/runs/38932494125](https://github.com/soul991/OPI/actions/runs/38932494125)
- **Job ID**: `117079708581`
- **Triggered By Commit**: `07402ee` (`fix(ci): configure pythonpath and pytest execution in GitHub Actions`)
- **Triggered Timestamp**: `2026-10-16T16:30:17Z` (2026-10-16 22:00:17 IST)
- **Completion Timestamp**: `2026-10-16T16:31:27Z` (2026-10-16 22:01:27 IST)
- **Duration**: 1 minute 10 seconds
- **Conclusion**: `SUCCESS` (Exit code 0)

## Verified Steps and Outputs

### Step 1: Set up job & Checkout
- Runner: `Ubuntu 24.04` (GitHub-hosted)
- Repository checkout: `actions/checkout@v4` with `fetch-depth: 0`

### Step 2: Python Environment & Dependencies
- `actions/setup-python@v5` configured Python 3.11
- `pip install -r requirements.txt` installed numpy, pandas, scikit-learn, joblib, pytest, pydantic, streamlit

### Step 3: Model Binary Availability (`scripts/build_or_verify_model.py`)
- Verified `model/ipo_model.joblib` generation from clean training data on fresh clone.
- Output: `[OK] Model present or successfully trained and verified.`

### Step 4: Daily Forward Runner Execution (`scripts/run_daily.py`)
- Executed `python scripts/run_daily.py` with mock and live fallback.
- Output: Scored pending IPO records, respected bidding-close gates, and updated predictions.

### Step 5: Full Test Suite (`python -m pytest -q`)
- Executed pytest under `python -m pytest -q` using `pyproject.toml` pythonpath configuration.
- Result: **58 passed in 1.95s**.

### Step 6: Independent Repository Verification (`scripts/verify_all.py`)
- Executed `python scripts/verify_all.py` on the live runner.
- Result: **48 pass, 0 warn, 0 fail**.

### Step 7: Automated Commit & Push
- Automated push of updated forward predictions and evidence:
  - Commit SHA: `6c30adf`
  - Commit Message: `chore(auto): daily forward test predictions and dashboard update [skip ci]`
  - Pushed to: `origin/main`

## Defect Resolution Verdict
- Defect D-020 is resolved and verified: GitHub Actions executes the full forward scoring, testing, and independent verification pipeline in a remote Linux runner with zero failures.
