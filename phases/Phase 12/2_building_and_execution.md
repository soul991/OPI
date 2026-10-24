# Phase 12: Building & Execution Log

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.

---

## 1. Pipeline Architecture & Data Flow

Phase 12 executes Gate A12 re-verification of Phase 11, report transcription fixes, evidence-backed market data architecture, cloud research agent proof, and post-listing outcome tracking:
- **Independent Verification Suite**: `scripts/verify_all.py` (v3 with fresh clone and hygiene checks) and `scripts/verify_extra.py` (Phase 12 independent checks).
- **Gate A12 Audit**: Re-verification of Phase 11 artifacts, 10 random claim checks (seed 12), 5 headline number recomputations, schedule lag audit, and GitHub secret presence verification.
- **Reporting Grounding**: `scripts/forward_report.py` dynamically builds evidence citations from snapshot metadata (`exchange_used` / URL) rather than hardcoded security codes.
- **Coverage Reconciliation**: `scripts/reconcile_coverage.py` documents the protocol difference between static holdout calibration (91.2%) and expanding walk-forward calibration (87.94%).
- **Market Evidence Ingestion**: `opi/market.py` fetches evidenced exchange data (^NSEI and ^INDIAVIX) and persists raw responses and parsed payloads in `data/evidence/market/`.
- **Dynamic Post-Mortem Generation**: `scripts/forward_postmortem.py` reads exclusively from prediction logs and saved market evidence without hand-typed or hardcoded constants.
- **GitHub Pages Dashboard Publishing & Freshness Guard**: `scripts/verify_pages.py` validates live HTTP 200 delivery from `https://soul991.github.io/OPI/dashboard/` and guards against staleness (>36h vs scheduled Actions runs).

---

## 2. Scripts Created / Modified
- `DEFECTS.md`: Seeded defects D-045 through D-052; resolved D-046, D-047, D-048, D-049, D-050, D-051, D-052.
- `opi/market.py`: Created market history fetcher fetching ^NSEI and ^INDIAVIX via yfinance; saves raw responses (`.raw`) with SHA-256 and parsed `.json` evidence for all listing dates (D-048).
- `scripts/forward_report.py`: Fixed note string generation to inspect snapshot JSON metadata (`exchange_used`, `source_url`), eliminating erroneous hardcoding of BSE 544994 across NSE-listed IPOs (D-047).
- `scripts/forward_postmortem.py`: Fully rewritten to eliminate hard-coded constants (`LISTING_DAY_NIFTY_MOVES`); populates post-mortem tables and narrative templates strictly from `predictions/prediction_log.csv` and evidenced market files under `data/evidence/market/` (D-041, D-046, D-048).
- `scripts/verify_pages.py`: Live GitHub Pages deployment checker and staleness guard; ensures HTTP 200 and freshness relative to scheduled Actions runs without returning false PASS in sandboxes (D-050).
- `scripts/recompute_gate_a12.py`: Automated calculation of all 5 headline metrics directly from `predictions/prediction_log.csv`, `data/ipo_master.csv`, and `DEFECTS.md`.
- `scripts/reconcile_coverage.py`: Programmatic verification of the exact protocol difference between Phase 7 static calibration (91.2%) and Phase 11 walk-forward calibration (87.94%) (D-049).
- `scripts/record_schedule_lag.py`: Programmatic analysis of the last 10 GitHub Actions scheduled runs against cron triggers (D-051).
- `phases/Phase 11/3_outcome_and_verdict.md`: Added `## ERRATA (patch)` at top of file documenting Zetwerk retail multiple (11.8x vs log 0.77x), Tonbo QIB multiple (185.4x vs log 293.56x), BSE 544994 note citations, and correcting self-audit answer on hand-typed numbers (D-045).
- `phases/Phase 11/forward_postmortem.md`: Added `## ERRATA (patch)` at top of file documenting Bonfiglioli QIB multiple (3.4x vs log 120.78x) and hard-coded listing day Nifty moves (D-046, D-048).
- `phases/Phase 12/forward_postmortem.md`: Dynamically generated post-mortem report where all multiples, gains, and benchmark moves map 100% to logged data and market evidence files.
- `phases/Phase 12/pages_check.txt`: Evidence record proving HTTP 200 response and fresh timestamp from live GitHub Pages dashboard.
- `phases/Phase 12/results_log.md`: Log of Gate A stop compliance and user approval tracking (D-052).
- `README.md`: Updated Known Limitations and Known Weaknesses sections to explicitly explain the protocol difference between static and walk-forward conformal interval evaluation (D-049); added live public dashboard URL (D-050).
- `tests/test_reporting.py`: Added regression test `test_forward_report_exchange_matches_source` (D-047).
- `tests/test_conformal_experiment.py`: Added regression test `test_coverage_reconciliation_script_and_readme` (D-049).
- `tests/test_ci.py`: Added regression tests `test_schedule_lag_recorded` (D-051) and `test_pages_published_and_guarded` (D-050).
- `tests/test_postmortem.py`: Added regression test `test_narrative_numbers_from_log` (D-046, D-048).
- `tests/test_gate_a.py`: Added regression test `test_phase12_process_stop_and_results_log` (D-052).

---

## 3. Data Purification & Engineering Steps
- Re-verified all 731 rows of `data/ipo_master.csv`.
- Confirmed all 8 FORWARD rows in `predictions/prediction_log.csv` comply with chronological scoring rules (scored post-close, prior to listing).
- Confirmed zero OpenRouter API key material in tracked files via `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"`.
- Saved official exchange index and VIX evidence files under `data/evidence/market/`:
  - `2026-10-21_nifty.raw` and `2026-10-21_nifty.json` (close 22811.35, prev 22888.95, day return -0.34%, VIX 15.68)
  - `2026-10-22_nifty.raw` and `2026-10-22_nifty.json` (close 22687.65, prev 22811.35, day return -0.54%, VIX 15.76)
  - `2026-10-23_nifty.raw` and `2026-10-23_nifty.json` (close 22600.00, prev 22687.65, day return -0.39%, VIX 16.86)
- Audited GitHub Pages deployment pipeline and verified that `[skip ci]` bot commits do not suppress the internal `pages-build-deployment` workflow.

---

## 4. Exact Terminal Commands Executed
```bash
# 1. Verification start check and extra verification run
python scripts/verify_all.py | Out-File -FilePath "phases\Phase 12\verify_start.txt" -Encoding utf8
python scripts/verify_extra.py | Out-File -FilePath "phases\Phase 12\verify_extra_start.txt" -Encoding utf8

# 2. Gate A12 headline recomputation and prior phase claim check
python scripts/recompute_gate_a12.py
python scripts/reconcile_coverage.py
python scripts/record_schedule_lag.py

# 3. Secret and workflow status verification
gh secret list
gh run list --workflow daily.yml --event schedule --limit 10

# 4. Workstream A: Evidenced market fetch & post-mortem generation
python opi/market.py --start 2026-10-21 --end 2026-10-23
python scripts/forward_postmortem.py

# 5. Workstream D: GitHub Pages publishing & freshness verification
gh api repos/soul991/OPI/pages
gh run list --workflow "pages-build-deployment"
python scripts/verify_pages.py

# 6. Regression tests execution
pytest tests/test_reporting.py
pytest tests/test_conformal_experiment.py
pytest tests/test_ci.py
pytest tests/test_postmortem.py
pytest tests/test_gate_a.py -k "test_phase12_process_stop_and_results_log"
```

---

## 5. Artifacts and Generated Data Files
- `phases/Phase 12/verify_start.txt`: Initial verification run output.
- `phases/Phase 12/verify_extra_start.txt`: Initial verify_extra run output (5 expected FAILs).
- `phases/Phase 12/prior_phase_recheck.csv`: 10 sampled claims (seed 12) from Phase 11 and 5 headline recomputations.
- `phases/Phase 12/actions_schedule_lag.md`: Analysis of schedule delay across last 10 scheduled runs.
- `phases/Phase 12/forward_postmortem.md`: Dynamic evidence-grounded post-mortem report.
- `phases/Phase 12/pages_check.txt`: Saved HTTP 200 and freshness verification output for live GitHub Pages deployment.
- `phases/Phase 12/results_log.md`: Log of Gate A stop compliance and user approval tracking.
- `data/evidence/market/2026-10-21_nifty.json` / `.raw`: Market evidence for HD Fire Protect listing.
- `data/evidence/market/2026-10-22_nifty.json` / `.raw`: Market evidence for Fusion CX listing.
- `data/evidence/market/2026-10-23_nifty.json` / `.raw`: Market evidence for Zetwerk, SMT, Tonbo, Bonfiglioli listings.
