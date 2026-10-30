# PHASE_PROTOCOL.md - How Every Phase Is Run (applies to Phase 8 onward)

> Add this file to the repo root and add one line to `RULES.md`: "All phases must follow `PHASE_PROTOCOL.md`." Reason: each phase so far has fixed older problems and introduced new ones, and the project's own reports have sometimes marked work as done that was not. This protocol makes problems visible, tracked and testable.

## 1. The Three Control Files
1. **`scripts/verify_all.py`** - independent checks of the repo (data integrity, forward-log rules, GMP evidence, defect register consistency, git order, recomputation of headline metrics from raw predictions). It does not read conclusions from the reports. **Do not edit it to make a failing check pass.** You may add new checks.
2. **`DEFECTS.md`** - every known problem, with ID, severity, status, due phase, regression test.
3. **`tests/`** - every fixed defect has a regression test, named in `DEFECTS.md`.

## 2. Phase Lifecycle (in this order)
**Step 0 - Start.** Run `python scripts/verify_all.py` and save the complete output as `phases/Phase N/verify_start.txt`. Read `DEFECTS.md`. Any FAIL line or WARN that is not already a defect becomes a new defect (new ID, severity, status OPEN) **before** you fix anything.

**Step 1 - Gate A: re-verify the previous phase.** For Phase N, check Phase N-1 yourself:
- Re-run its main script(s) from a clean checkout and compare outputs with the committed artifacts.
- Recompute at least 5 headline numbers from raw files (not copy from the verdict).
- Open and check **10 random claims** in the previous verdict against the underlying files; record claim, file, and result in `phases/Phase N/prior_phase_recheck.csv`.
- Re-check any data collected in that phase against the evidence standard (Section 4).
- Look for new faults introduced by the previous phase (changed files, new columns, silent row changes) by diffing `data/` between the last two phases.
- Fix by severity: Critical, then High, then the rest. Each fix: code change, regression test, `DEFECTS.md` update, commit.
- Gate exit: `verify_all.py` has 0 FAIL; every WARN explained in writing; commit `phaseN-gate-a`.

**Step 2 - Preregistration.** Commit `phases/Phase N/preregistration.md` (metrics, decision rules, data rules) as `phaseN-preregistration` before any new modelling or automation work.

**Step 3 - Workstreams.** One commit per workstream. Every fix gets a register entry before its commit, goes on a branch, and passes `ci_local.py` before push (D-076). Direct pushes to `main` for fixes or features are prohibited; changes are reviewed and merged via pull requests. Before **every** push run `python scripts/ci_local.py` (stand-alone entrypoint smoke test, daily run, pytest, and verify_all, executed in an isolated copy) and push only on `CI_LOCAL: PASS`. A red CI run sends the owner an alert issue.

**Step 4 - Exit.** Run `verify_all.py` again, save as `phases/Phase N/verify_end.txt`. In `3_outcome_and_verdict.md` include the **Defect Ledger**: defects opened, fixed, carried over (IDs and statuses), plus anything that regressed. Update `DEFECTS.md`. Attach the self-audit.

## 3. Status Rules
- `FIXED` only if its verification command or regression test passes and the output is pasted. 60% done is `PARTIAL`.
- The verdict's first section ("Targets missed and unfixed items") may say "None" only if `DEFECTS.md` has no `OPEN` or `PARTIAL` rows. `verify_all.py` checks this.
- `ACCEPTED` limitations must be written in README under "Known limitations".
- Critical or High defects that are `OPEN` block all new feature work in the same phase.

## 4. Evidence Standard for Collected Data
- Every collected value has: source URL, the page's own date, access date, **and a saved snapshot** at `data/evidence/<type>/<listing_date>_<company-slug>.<ext>` (saved HTML, PDF, or an archived-page copy). A value without a snapshot is `NOT_RECORDED`.
- **Independent second source** means: a different publisher, collected separately, with the difference between sources reported as measured. Two independent trackers will normally differ by some points (GMP trackers do); an exact match across many values is a red flag, not a pass. Never copy one source's value into the other column.
- **Time realism:** if collecting N values from web pages finishes much faster than a person or browser could visit them, state the method (bulk download, API, cached dataset) in `2_building_and_execution.md`. "Sourced from many pages in a few minutes" with no method is treated as unverified.
- Never use listing-day or later information for any pre-listing feature.

## 5. Reporting Rules (carried from Phases 5-7)
- Numbers in reports come from committed script outputs (`verify_all.py` recomputes the main ones).
- Words such as "beats", "wins", "proves", "rejected", "falsified", "significant", "unbeatable" need a paired bootstrap 95% interval excluding zero; otherwise use "no demonstrated difference".
- Explanations of why something happens are labelled "Hypothesis (untested)" unless tested.
- Example tables are complete, random (seed stated) or labelled best/worst N.
- Earlier phase files are corrected by an `## ERRATA` section at the top; originals stay.
- Commit per workstream; a gate/preregistration commit must precede other work for that phase.
- This project is a decision aid, not financial advice.

## 6. Template for Future Phase Guides (what each guide will contain)
1. Non-negotiable rules (link to this protocol)
2. **Gate A: re-verify Phase N-1, plus every carried defect with a fix and a verification command**
3. Objectives, scope, hypotheses
4. Data strategy and leakage rules
5. Workstreams with acceptance checks
6. Success criteria and decision rules
7. Task list in strict order, verification commands
8. Required verdict structure (starting with missed targets and the Defect Ledger)
9. Self-audit
