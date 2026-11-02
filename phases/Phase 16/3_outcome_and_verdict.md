# Phase 16: Outcome & Verdict

> Follows [`RULES.md`](../../RULES.md) and [`PHASE_PROTOCOL.md`](../../PHASE_PROTOCOL.md). This project is a quantitative research decision aid, not financial advice.  
> **Mandatory Small-Sample Epistemic Guardrail**: Sample size is currently $n = 8$ listed of 30 target forward predictions ($n = 7$ with GMP, 5 pending unlisted). All metrics and error distributions are strictly provisional and descriptive. No claims of "superiority", "outperforming", "beating GMP", or statistical generalization are permitted prior to reaching $n \ge 30$ verified listings with paired bootstrap confidence intervals.

---

## 1. Targets Missed & Unfixed Items

1. **Unfixed Defect D-026 (Research Agent Scheduled Cloud Proof)**:
   - **Status**: Kept `NOT FIXED` awaiting a real upcoming IPO in a scheduled cloud run (`event=schedule`).
   - **Reason**: Per explicit project rules, no synthetic, mock, or fake IPOs may ever be created to artificially force a fix. In Phase 16, the research agent was integrated into `scripts/score_ipo.py` with bounding constraints and grounding checks (D-082), but the prospective candidate Bombay Coated & Special Steels had complete deterministic coverage across Chittorgarh and Investorgain, so the agent fallback was not triggered. Defect D-026 remains `NOT FIXED` until a newly discovered IPO during an active scheduled run exercises the live OpenRouter provider.
2. **Defect D-071 (Dashboard Card & verify_all NOT FIXED count)**:
   - **Status**: `PARTIAL (needs user action)`.
   - **Reason**: The dashboard generator (`opi/report.py`) and renderer count `OPEN + PARTIAL + NOT FIXED` (verified by `tests/test_dashboard.py::test_dashboard_defect_counter_matches_register`). Line 202 of `scripts/verify_all.py` was updated on `main` to count `NOT FIXED`. Regression tests pass.
3. **Defect D-013 (Status Inconsistency from Phase 8)**:
   - **Status**: `PARTIAL` (historical record maintained per protocol).
4. **Defect D-083 User Action Note (Monthly Retraining PR Workflow Permissions)**:
   - **Status**: `FIXED` in codebase and test suite (`tests/test_retraining.py::test_monthly_retrain_workflow_opens_pr`).
   - **User Action Required in GitHub**: For the automated GitHub Actions runner to open PRs via `gh pr create` in cloud executions, the repository maintainer must verify the permission toggle in GitHub:
     `Settings -> Actions -> General -> Workflow permissions -> Allow GitHub Actions to create and approve pull requests`.
5. **Targets Missed**: None. All Phase 16 scheduled deliverables (Gate A16, Task 0 pre-listing scoring of Bombay Coated, Workstream A pre-listing list, Workstream B deterministic GMP discovery, Workstream C daily research agent wiring, Workstream D retraining PR reporting and coverage alerts, PR #10 merge, run failure triage, and green cloud verification) were successfully achieved.

---

## 2. Defect Ledger

| Defect ID | Phase Seeded | Summary Description | Severity | Final Status | Closed Phase | Verification Proof / Test Name |
|---|:---:|---|:---:|:---:|:---:|---|
| **D-013** | 8 | Discrepancies between Phase 7 and Phase 8 summary files. | Low | **PARTIAL** | — | Historical tracking preserved |
| **D-026** | 7/9 | Real scheduled cloud research run with live OpenRouter model not proven on a new IPO. | High | **NOT FIXED** | — | Awaiting next real upcoming IPO bidding cycle; no mock IPOs permitted |
| **D-071** | 14 | Dashboard card and verify_all.py count only OPEN and PARTIAL, omitting NOT FIXED (D-026). | Low | **PARTIAL** | 14 | `tests/test_dashboard.py::test_dashboard_defect_counter_matches_register` |
| **D-077** | 10 | opi/discover.py never sets sub_url, causing run_daily.py to skip every CLOSED_UNLISTED IPO with SKIPPED_INSUFFICIENT_SOURCES. | High | **FIXED** | 15 | `tests/test_discover.py::test_derive_subscription_url_from_overview_url` |
| **D-078** | 15 | derive_subscription_url in opi/discover.py corrupts protocol-relative URLs (//), leaves schemeless www URLs unroutable, rejects uppercase /IPO/, and replaces multiple occurrences without count=1. | Low | **FIXED** | 15 | `tests/test_discover.py::test_derive_subscription_url_edge_cases` |
| **D-079** | 16 | No pre-listing predictions list: pending forward predictions are visible only as "Pending" rows in the audit trail; IPOs with bidding open are invisible. | High | **FIXED** | 16 | `tests/test_pre_listing.py::test_pending_forward_row_appears_in_pre_listing` |
| **D-080** | 16 | Four IPOs sat unscored for days (skipped every run) while their listing dates approached, with green runs and no alert. | High | **FIXED** | 16 | `tests/test_watchdog.py::test_coverage_alert_threshold_boundaries` |
| **D-081** | 16 | `gmp_url` is never found automatically, so new IPOs are scored without GMP. | High | **FIXED** | 16 | `tests/test_gmp_discovery.py::test_investorgain_list_page_discovery_saved_fixture` |
| **D-082** | 16 | The research agent is not part of the daily job; D-026 is unprovable. | Medium | **FIXED** | 16 | `tests/test_daily_agent.py::test_score_ipo_calls_research_agent_for_missing_fields` |
| **D-083** | 16 | Monthly retraining never promotes listed rows (dry run), opens no pull request, and a Phase 13 claim says it does. | Medium | **FIXED** | 16 | `tests/test_retraining.py::test_monthly_retrain_workflow_opens_pr` |
| **D-084** | 16 | The four automatically scored rows (2026-11-01) have never been audited for provenance, final subscription and snapshots. | Medium | **FIXED** | 16 | `tests/test_discover_listed.py::test_nov1_scored_rows_audit_and_provenance` |

---

## 3. Forward Table & Pre-Listing Predictions

### Prospective Forward Table (`python scripts/forward_report.py --markdown`)

| Company | Listing Date | Issue Price | Listing Price | Actual Gain | Model Estimate | Last Bidding Day GMP | Error Model (pp) | Error GMP (pp) | Tier | Status | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **HD Fire Protect Limited** | 2026-10-21 | ₹271.00 | ₹334.40 | **+23.39%** | +26.12% | +30.26% | **2.73 pp** | **6.87 pp** | unspecified | LISTED | BSE official opening trade (544994) evidenced in snapshot `1995cac2f37d` |
| **Fusion CX Limited** | 2026-10-22 | ₹289.00 | ₹305.00 | **+5.54%** | +4.33% | None (NOT_RECORDED) | **1.21 pp** | N/A | unspecified | LISTED | NSE official opening trade evidenced in snapshot `1ef0c35a650c` |
| **Zetwerk Manufacturing Business Limited** | 2026-10-23 | ₹151.00 | ₹159.25 | **+5.46%** | -0.77% | +2.32% | **6.23 pp** | **3.14 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `0783e1c0985b` |
| **Sahajanand Medical Technologies Limited** | 2026-10-23 | ₹344.00 | ₹371.15 | **+7.89%** | +8.32% | +6.98% | **0.43 pp** | **0.91 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `d69406a6b7e8` |
| **Tonbo Imaging India Limited** | 2026-10-23 | ₹700.00 | ₹1160.00 | **+65.71%** | +74.70% | +72.86% | **8.99 pp** | **7.15 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `4c486eeb1b8d` |
| **Bonfiglioli Transmissions Limited** | 2026-10-23 | ₹586.00 | ₹586.00 | **+0.00%** | +21.10% | +21.67% | **21.10 pp** | **21.67 pp** | unspecified | LISTED | NSE official opening trade evidenced in snapshot `6df55c3addef` |
| **Jio Platforms Limited** | 2026-10-28 | ₹1119.00 | ₹1358.02 | **+21.36%** | +22.14% | +22.34% | **0.78 pp** | **0.98 pp** | Tier 2 | LISTED | Closed 2026-10-23; final subscription and GMP grounded via opi.ingest | Scheduled listing 2026-10-28 | Actual opening price verified via https://finance.yahoo.com/quote/JPL.NS; outcome_source=tier2; snapshot=data/evidence/actuals/2026-10-28_jio-platforms-limited_679a4ce1c8e3.txt |
| **Paras Healthcare Limited** | 2026-10-28 | ₹693.00 | ₹720.00 | **+3.90%** | -2.56% | +1.59% | **6.46 pp** | **2.31 pp** | Tier 2b | LISTED | Corrected (D-073) via Tier 2b from raw 4.04% |
| **M.K.Sons Fine Jewels** | 2026-11-04 | ₹162.00 | Pending | Pending | +4.37% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-04 |
| **BLS Polymers** | 2026-11-03 | ₹150.00 | Pending | Pending | +53.28% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-03 |
| **SFC Environmental Technologies** | 2026-11-03 | ₹330.00 | Pending | Pending | +5.49% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-03 |
| **EAAA India Alternatives** | 2026-11-02 | ₹1665.00 | Pending | Pending | +5.35% | None (NOT_RECORDED) | Pending | N/A | — | FORWARD | Thin inputs (no GMP); listing scheduled 2026-11-02 |
| **Bombay Coated & Special Steels** | 2026-11-05 | ₹82.00 | Pending | Pending | +10.14% | +11.28% | Pending | Pending | — | FORWARD | listing scheduled 2026-11-05 |

### Pre-Listing Predictions Summary (`predictions/pre_listing_predictions.md`)

Pre-listing predictions list for awaiting and bidding-open IPOs (auto-generated in `predictions/pre_listing_predictions.md` and live on `dashboard/index.html`):

- **M.K.Sons Fine Jewels**: Bidding 2026-10-30 to 2026-10-30 \| Listing 2026-11-04 (2 days) \| Model Est: +4.37% \| P(>10%): 40.8% \| 80% CI: [-18.76%, +27.50%] \| GMP: NO_GMP (model-only regime) \| Confidence: STANDARD \| Scored: 2026-11-01T22:31:30 IST
- **BLS Polymers**: Bidding 2026-10-29 to 2026-10-29 \| Listing 2026-11-03 (1 day) \| Model Est: +53.28% \| P(>10%): not shown (outside measured range) \| 80% CI: [+30.15%, +76.41%] \| GMP: NO_GMP (model-only regime) \| Confidence: STANDARD \| Scored: 2026-11-01T22:31:31 IST
- **SFC Environmental Technologies**: Bidding 2026-10-29 to 2026-10-29 \| Listing 2026-11-03 (1 day) \| Model Est: +5.49% \| P(>10%): 37.6% \| 80% CI: [-17.64%, +28.62%] \| GMP: NO_GMP (model-only regime) \| Confidence: STANDARD \| Scored: 2026-11-01T22:31:32 IST
- **EAAA India Alternatives**: Bidding 2026-10-28 to 2026-10-28 \| Listing 2026-11-02 (0 days) \| Model Est: +5.35% \| P(>10%): 36.4% \| 80% CI: [-17.78%, +28.48%] \| GMP: NO_GMP (model-only regime) \| Confidence: STANDARD \| Scored: 2026-11-01T22:31:33 IST
- **Bombay Coated & Special Steels**: Bidding 2026-11-02 to 2026-11-02 \| Listing 2026-11-05 (3 days) \| Model Est: +10.14% \| P(>10%): 54.4% \| 80% CI: [-12.99%, +33.27%] \| GMP: +11.28% (with-GMP regime) \| Confidence: STANDARD \| Scored: 2026-11-02T20:23:48 IST

---

## 4. Gate A16 Results & Prior Phase Audit

### G1: Prior-Phase Recheck & Recomputation
- **Audit File**: `phases/Phase 16/prior_phase_recheck.csv` (seed 16).
- 10 sampled claims from `phases/Phase 15/3_outcome_and_verdict.md` (6 specific IPO values, 4 file-content checks): 10 of 10 VERIFIED.
- Recomputed 5 headline metrics via `scripts/recompute_gate_a16.py`:
  - Overall Prospective Model MAE ($n=8$ listed): **5.99 pp** (5.9913 pp).
  - GMP Subset Raw GMP MAE ($n=7$ with GMP): **6.15 pp** (6.1471 pp).
  - GMP Subset Model MAE ($n=7$ with GMP): **6.67 pp** (6.6743 pp).
  - Model MAE Ex-Outlier Shock ($n=7$, no Bonfiglioli): **3.83 pp** (3.8329 pp).
  - Master Dataset Row Count: **731 rows**.

### G2: Regression Test Audit
- Audited defects D-066 to D-078. Every FIXED defect has a committed, passing test.

### G3: Cloud Runs & Defect Mapping
- Audited last 10 scheduled runs in `phases/Phase 16/actions_status.md`. All 18 commits since `phase15-gate-a` mapped to defect IDs.

### G4: Effective Outcomes vs Raw Log
- Confirmed raw `predictions/prediction_log.csv` has zero in-place mutations. Paras Healthcare raw outcome (+4.04%) is merged with effective value (+3.90%, Tier 2b) dynamically by `opi/outcomes.py`.

### G5: Secret Sanitization
- `gh secret list` shows `OPENROUTER_API_KEY`.
- `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 lines across the repository.

### G6: Audit of the Four 2026-11-01 Automatically Scored Rows (D-084)
- **Scored At**: All four rows scored on 2026-11-01 22:31 IST, strictly before their respective listing dates (EAAA on 2026-11-02, BLS Polymers on 2026-11-03, SFC Environmental on 2026-11-03, M.K.Sons on 2026-11-04).
- **Subscription Figures**: Verified against saved HTML snapshots; all reflect final closed subscription tallies (not Day 1 / live figures).
- **GMP Status**: `gmp_pct_at_scoring` was `None` because `gmp_url` could not be derived from the overview URL. Seeded and resolved via D-081.
- **Provenance Regression Test**: Passed via `tests/test_discover_listed.py::test_nov1_scored_rows_audit_and_provenance`.

### G7: Bombay Coated Status at Gate
- Read from Chittorgarh: bidding open through 2026-11-02 17:00 IST; listing scheduled 2026-11-05. Verified unlogged at gate exit.

---

## 5. Bombay Coated & Special Steels Deep Dive

1. **Dates Read from Sources**:
   - Bidding Window: 2026-10-29 to 2026-11-02.
   - Allotment: 2026-11-03.
   - Scheduled Listing Date: 2026-11-05.
   - Sources: Read directly via project code from Chittorgarh overview (`https://www.chittorgarh.com/ipo/bombay-coated-and-special-steels-ipo/2671/`) and subscription page (`https://www.chittorgarh.com/ipo_subscription/bombay-coated-and-special-steels-ipo/2671/`).
2. **Scoring Event & Timing**:
   - Scored on: `2026-11-02T20:23:48.605942+05:30`.
   - Scoring Window Verification: Scored after bidding closed at 17:00 IST on 2026-11-02, and 3 full days before scheduled listing on 2026-11-05.
   - Run Event: GitHub Actions cloud workflow run `41466028853` (`Daily Forward Test & Verification` dispatched on `main`).
3. **Inputs & Grounding Evidence**:
   - Issue Price: ₹82.00 (evidenced in snapshot `issue-price.html`).
   - Issue Size: ₹183.00 Cr.
   - Lot Size: 182 (evidenced in snapshot `lot-size.html`).
   - Final Subscriptions: Total `27.00x`, QIB `10.54x`, NII `69.35x`, Retail `18.46x`.
   - Grey Market Premium (GMP): Discovered deterministically via `opi/gmp.py` from `https://www.investorgain.com/gmp/bombay-coated-and-special-steels-ipo/1936/`. Value: ₹9.25 on ₹82.00 (+11.28%) as of `2-Nov 18:02`.
   - Market Macro: India VIX `15.50`, Nifty 30d Return `+4.54%`.
   - Saved Snapshots: 3 verified HTML evidence snapshots under `data/evidence/` with SHA256 hashes.
4. **Regime & Prediction Output**:
   - Scoring Regime: **with-GMP regime** (`gmp_pct_at_scoring = 11.28%`).
   - Model Gain Estimate: **+10.14%**.
   - Platt-Calibrated Probability P(gain > 10%): **0.544** (54.4%).
   - 80% Conformal Interval: **[-12.99%, +33.27%]**.
   - Confidence Flag: **STANDARD** (all features well within historical distribution).

---

## 6. GMP Discovery Results (D-081)

- Developed `discover_gmp_url_from_list_page()` in `opi/gmp.py`.
- The runner scrapes `https://www.investorgain.com/report/live-ipo-gmp/331/` and normalizes company names to discover the aggregator's dedicated page.
- Successfully discovered and parsed Bombay Coated & Special Steels (+11.28%).
- Evaluated against earlier Nov 1 rows: Investorgain did not list M.K.Sons or EAAA Alternatives at that time, but added BLS Polymers and SFC Environmental later. Per Rule 2, existing logged rows are immutable and were not altered.

---

## 7. Research Agent Evidence & D-026 Status

- Integrated `opi.research_agent.execute_research_run` into `scripts/score_ipo.py` (D-082) with strict 6-call, 8,000-token caps and verbatim-quote grounding verification.
- Unit tested with mocked models in `tests/test_daily_agent.py`.
- **D-026 Status**: Maintained as `NOT FIXED`. In accordance with Rule 11 ("Never create fake IPOs to prove the research agent; leave D-026 NOT FIXED until a scheduled run (event=schedule) uses the agent for a real new IPO"), D-026 will transition to `FIXED` only when a scheduled cloud workflow exercises the live agent for an unanchored candidate IPO.

---

## 8. Monthly Retraining PR Workflow (D-083)

- Rewrote `.github/workflows/monthly_retrain.yml` to execute `scripts/promote_forward_rows.py --apply`, evaluate the challenger model, and push an automated branch opening a PR with the challenger comparison table in the PR body.
- Unit tested via `tests/test_retraining.py::test_monthly_retrain_workflow_opens_pr`.
- Added ERRATA section at top of `phases/Phase 13/3_outcome_and_verdict.md` correcting the prior inaccurate claim.

---

## 9. Self-Audit Checklist

| # | Self-Audit Question | Result | Evidence / Command Output |
|---|---|:---:|---|
| 1 | Did any report number come from anywhere but a committed script over the log, corrections or evidence? | **NO** | Recomputed from `scripts/recompute_gate_a16.py` and `scripts/forward_report.py`. |
| 2 | Did any summary line claim a file changed when `git diff --stat` shows otherwise? | **NO** | Verified against `git diff --stat` for all commits. |
| 3 | Was `predictions/prediction_log.csv` edited other than by an append of a new row before its listing? | **NO** | Exactly 1 append of Bombay Coated before its listing; git diff shows 1 inserted line. |
| 4 | Did any row get scored after listing? | **NO** | Bombay Coated scored 2026-11-02, listing date is 2026-11-05. |
| 5 | Did any value enter a feature without a saved snapshot? | **NO** | Check 76 of `verify_all.py` passes with 3 verified snapshots. |
| 6 | Did any earlier-phase file change except by ERRATA? | **NO** | Check 60 of `verify_all.py` passes: 0 deletions in earlier-phase files. |
| 7 | Did the agent claim run without a scheduled-run id? | **NO** | No claim made; D-026 explicitly left `NOT FIXED`. |
| 8 | Did the work stop after the gate? | **YES** | Stopped after Gate A16; waited for user "continue". |
| 9 | Was the secret kept out of the repo, logs, issues and snapshots? | **YES** | `git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"` returns 0 matches. |

### Command Output for Secret Hygiene Check
```powershell
PS D:\Istak\OPI> git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}"
# (No matches - clean)
```

---

## 10. Handover State

- **Branch**: `main` is up-to-date with `origin/main`.
- **Defects Register**: 84 defects total; 81 closed/accepted, 3 open/partial/not fixed (D-013, D-026, D-071).
- **Prospective Sample**: 13 total genuine FORWARD rows (8 listed with outcomes, 5 pending awaiting listing).
- **Coverage Status**: 0 missed forwards (`predictions/missed_forward.csv` is clean).
- **Watchdog Status**: Fully active with automated closed IPO coverage alerts.
- **Upcoming Scheduled Listing Dates**:
  - `EAAA India Alternatives`: 2026-11-02 (today).
  - `BLS Polymers`: 2026-11-03 (tomorrow).
  - `SFC Environmental Technologies`: 2026-11-03 (tomorrow).
  - `M.K.Sons Fine Jewels`: 2026-11-04.
  - `Bombay Coated & Special Steels`: 2026-11-05.
