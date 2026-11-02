# Phase 16 GitHub Actions Health & Scheduled Runs Audit (G3)

**Audit Timestamp**: 2026-11-02T13:20:00+05:30  
**Repository**: `soul991/OPI`  
**Auditor**: Antigravity (Phase 16 Gate A16)

---

## 1. Last 10 Scheduled Runs

Audited via `gh run list --event schedule -L 12`:

| Run ID | Workflow | Event | Status | Conclusion | Started At (UTC) | Duration | Notes |
|---|---|---|---|---|---|---|---|
| **41338045829** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-01T18:43:13Z | 1m34s | Green scheduled run; scored M.K.Sons, BLS Polymers, SFC Environmental, EAAA India Alternatives |
| **41327176620** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-11-01T16:36:11Z | 41s | Green scheduled run |
| **41307153260** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-11-01T12:34:40Z | 2m9s | Green scheduled run |
| **41296833925** | Weekly Canary Dependency Build | schedule | completed | **success** | 2026-11-01T10:17:32Z | 1m6s | Green scheduled run |
| **41275742845** | Monthly Challenger Model Evaluation | schedule | completed | **success** | 2026-11-01T05:08:20Z | 48s | Green scheduled run (dry run; D-083) |
| **41227872216** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-10-31T18:07:51Z | 2m7s | Green scheduled run |
| **41215698134** | Watchdog Freshness & Provider Health | schedule | completed | **success** | 2026-10-31T15:36:54Z | 38s | Green scheduled run |
| **41197560818** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-10-31T11:36:30Z | 2m13s | Green scheduled run |
| **41111227719** | Daily Forward Test & Verification | schedule | completed | **success** | 2026-10-30T18:57:16Z | 5m7s | Green scheduled run |
| **41090951686** | Watchdog Freshness & Provider Health | schedule | completed | **failure** | 2026-10-30T16:33:19Z | 31s | Watchdog failed with ModuleNotFoundError; resolved via D-075 |

---

## 2. Issues Audit (`gh api repos/soul991/OPI/issues?state=all`)

- **Open Alert Issues**: **0** open issues.
- **Closed Pull Requests / Issues**:
  - PR #9: `fix(discover): harden derive_subscription_url against edge cases (D-078)` - Merged 2026-11-01T17:18:27Z.
  - PR #8: `fix(discover): derive subscription URL from overview URL (D-077)` - Merged 2026-11-01T16:47:04Z.
  - PR #7: `feat(phase15): Phase 15 workstreams A, B, C` - Merged 2026-10-31T02:26:08Z.
  - Issue #6: `Watchdog run failed: 41090951686` - Closed 2026-10-30T17:12:32Z.

---

## 3. Commit History Audit Since `phase15-gate-a` (Defect Mapping)

All 18 commits since `phase15-gate-a` (`da1ce5353553e65a347d9fb94501b119bba60950`):

| Commit SHA | Commit Message | Files Changed Scope | Defect / Reason Mapping | Compliant Process? |
|---|---|---|---|:---:|
| `fe6f83a` | `phase15-preregistration` | `phases/Phase 15/preregistration.md` | Phase 15 protocol | YES |
| `5cc5462` | `fix(phase15): sanitize secret pattern in actions_status.md...` | `phases/Phase 15/actions_status.md`, `dashboard/` | Gate A15 sanitization | YES |
| `bf57012` | `phase15-workstream-a: enforce listing-day date match in yfinance...` | `opi/actuals.py`, `tests/` | Defect D-072 | YES (on branch) |
| `278f80d` | `phase15-workstream-b: audited append-only outcome corrections...` | `opi/outcomes.py`, `predictions/`, `tests/` | Defect D-073 | YES (on branch) |
| `7fa8d15` | `phase15-workstream-c: workflow entrypoints smoke test...` | `scripts/ci_local.py`, `tests/`, `PHASE_PROTOCOL.md` | Defect D-075, D-076 | YES (on branch) |
| `167242f` | `chore(probe): commit cloud runner probe output [skip ci]` | `phases/Phase 15/source_probe_runner.md` | Defect D-074 runner evidence | YES (on branch) |
| `79869f6` | `phase15-workstream-c: mark D-074 fixed with runner probe test` | `DEFECTS.md`, `tests/` | Defect D-074 | YES (on branch) |
| `eca59d2` | `Merge pull request #7 from soul991/feat/phase15-workstreams` | Git merge | PR #7 merge to main | YES |
| `a552d80` | `chore(auto): daily forward test predictions... [skip ci]` | `predictions/`, `dashboard/` | Automated daily bot | YES |
| `f49a4f7` | `docs(phase15): complete phase 15 building, outcome, and verification exit...` | `phases/Phase 15/` | Phase 15 exit deliverables | YES |
| `9f1d94b` | `chore(auto): daily forward test predictions... [skip ci]` | `predictions/`, `dashboard/` | Automated daily bot | YES |
| `599e0bd` | `chore(auto): daily forward test predictions... [skip ci]` | `predictions/`, `dashboard/` | Automated daily bot | YES |
| `f5f100f` | `chore(auto): daily forward test predictions... [skip ci]` | `predictions/`, `dashboard/` | Automated daily bot | YES |
| `35fbb5a` | `fix(discover): derive sub_url from overview_url for candidate IPOs (D-077)` | `opi/discover.py`, `DEFECTS.md`, `tests/` | Defect D-077 | YES (on branch) |
| `89fdc33` | `Merge pull request #8 from soul991/fix/derive-sub-url` | Git merge | PR #8 merge to main | YES |
| `cd04f35` | `chore(auto): daily forward test predictions... [skip ci]` | `predictions/`, `dashboard/` | Automated daily bot | YES |
| `75b4556` | `fix(discover): harden derive_subscription_url against URL variations...` | `opi/discover.py`, `DEFECTS.md`, `tests/` | Defect D-078 | YES (on branch) |
| `d60bf80` | `Merge pull request #9 from soul991/fix/derive-sub-url-edge-cases` | Git merge | PR #9 merge to main | YES |
| `77d1d0e` | `chore(auto): daily forward test predictions and dashboard update [skip ci]` | `predictions/`, `dashboard/`, `data/evidence/` | Automated daily bot; 4 candidate IPOs scored | YES |

---

## 4. Secret Sanitization Audit (G5)

- `gh secret list` confirms `OPENROUTER_API_KEY` exists.
- OpenRouter secret key scan returns strictly 0 lines. Zero secret key tokens committed to repository.
