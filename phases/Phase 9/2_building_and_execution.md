# Phase 9: Building & Execution - Gate A9 Remediation, Research Agent, Input Validation, Streamlit Console & Learning Loop

> Standard sequential phase documentation per [`RULES.md`](../../RULES.md), [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md), and [`phases/Phase 9/1_planning_and_goals.md`](1_planning_and_goals.md).  
> **Mandatory Statement**: This project is a quantitative research framework and decision aid only, not financial, investment, or trading advice.

---

## 0. User Requirements Checklist (Section 0)
1. **Web access permission**: Yes, internet access is functional (Chittorgarh and exchange endpoints reachable via code).
2. **LLM API key**: Configured in `.env` (`OPI_LLM_PROVIDER=gemini`, using Gemini API / Mock fallback for offline hermetic testing).
3. **GitHub Actions & Pages**: GitHub CLI authenticated, workflow permissions verified; Actions run triggered and monitored.

---

## 1. Gate A9 Execution & Remediation Log (V1 to V8)

### V2: D-016 Backdated Timestamp Remediation
- **Action**: Row 7 in `predictions/prediction_log.csv` invalidated with status `INVALID_BACKDATED_TIMESTAMP`. `opi/log.py` refactored so `scored_at` is generated strictly at write time with an explicit timezone offset (`+05:30` IST). Disallowed arbitrary caller-supplied timestamps.
- **Re-scoring**: HD Fire Protect Limited re-scored using `python -m opi.run_daily` on 2026-10-16 post-bidding close with final features (Total subscription: 131.73x, QIB: 256.65x, GMP: 30.26%).
- **Logged Row**: Real write-time timestamp recorded: `2026-10-16T21:22:23.195683+05:30` with status `FORWARD`.
- **Regression Test**: `tests/test_forward_log.py::test_scored_at_is_real_run_time` PASSED.

### V1: D-015 / D-020 Model Availability on Clean Clone & CI
- **Action**: Champion model `model/ipo_model_phase4.joblib` and `model/ipo_model.joblib` tracked in git via `.gitignore` exception (`!model/*.joblib`). Model SHA-256 hash (`335dd32d3ab3127de378316d64690b1a9bd6c2e8377859671916b1347e9b9069`) registered in `model/registry.json`.
- **CI Workflow**: `.github/workflows/daily.yml` updated with fallback deterministic retraining check.
- **Regression Test**: `tests/test_ci.py::test_model_available_on_fresh_clone` PASSED.

### V3: D-017 Earlier Phase Artifact Immutability Restoration
- **Action**: All 8 non-`.md` CSV files in `phases/Phase 7/` and `phases/Phase 4/phase4_summary.json` restored byte-for-byte to their original pre-Phase 8 state from commit `e4f7a30`.
- **Phase 8 Clean Re-run Output**: Saved as an immutable copy under `phases/Phase 8/rerun_phase7_cleaned/` with stale note `+75 IPOs backfilled` removed and replaced with clean verification documentation.
- **Script Parameterization**: `scripts/phase7_rolling_train_evaluate.py` parameterized with `--output-dir` defaulting to the current phase.
- **Regression Test**: `tests/test_reporting.py::test_earlier_phases_immutable` PASSED.

### V4: D-018 Extreme GMP Rows Purged & Reverted
- **Action**: All 8 historical rows with GMP > 100% lacking code-saved snapshots (Motisons, Bls Eservices, Exicom, Mukka Proteins, Premier Energies, Bajaj Housing, Krn Heat Exchanger, Mamata) reverted to `NOT_RECORDED` in `data/ipo_master.csv`.
- **Corrections Record**: Detailed in `phases/Phase 9/data_corrections.csv`. `phases/Phase 9/gmp_outlier_review.csv` compiled removing all 'audited genuine' claims.
- **Regression Test**: `tests/test_data_integrity.py::test_extreme_gmp_have_snapshots` PASSED.

### V5: D-019 Status Consistency Erratum
- **Action**: Added `## ERRATA (Phase 9)` at top of `phases/Phase 8/3_outcome_and_verdict.md` explaining that D-001 was closed by reverting unverified backfill values without replacement.

### V6: D-013 Void Audits Flagged
- **Action**: Added `phases/Phase 9/duplicate_verification.csv` with `verification_status=UNVERIFIED` for the 15 unverified sample companies and documented in `README.md` under Known Limitations.

### V7: Register Hygiene
- **Action**: Appended D-015 to D-020 to `DEFECTS.md` with regression test references and updated resolved statuses.

### V8: D-005 HD Fire Protect Outcome Tracking
- **Action**: Scheduled listing date is 2026-10-21. Today is 2026-10-16. Outcome remains unlisted; carried over explicitly as `PARTIAL` per protocol rules.
