# Phase 21: Gate A Initial Verification Warnings Explanation

Per `PHASE_PROTOCOL.md` Section 2 (Step 1: "Gate exit: verify_all.py has 0 FAIL; every WARN explained in writing"):

At the start of Phase 21, `scripts/verify_all.py` was executed and its complete output saved to `phases/Phase 21/verify_start.txt`. The run completed with **83 PASS, 2 WARN, 1 FAIL**. The FAIL (`Phase 21: gate and preregistration commits exist`) was the expected pre-condition before committing Gate A and preregistration. The two WARN items are documented and explained below:

---

### Warning 1: `[WARN] Phase 21: three required files` (phase in progress)
- **Check Name**: `check_phases_and_defects` (line 198 of `scripts/verify_all.py`)
- **Reported Detail**: `phase in progress`
- **Root Cause & Explanation**:
  `RULES.md` and `PHASE_PROTOCOL.md` dictate that every completed phase directory must contain three standard documents: `1_planning_and_goals.md`, `2_building_and_execution.md`, and `3_outcome_and_verdict.md`. At the very beginning of Phase 21 (Gate A), the phase is just commencing. `1_planning_and_goals.md` is initialized, while `2_building_and_execution.md` (execution log) and `3_outcome_and_verdict.md` (outcome evaluation) are progressively drafted as workstreams execute and finalized at phase exit. `verify_all.py` detects that Phase 21 is the active, latest phase and flags it as a non-failing `WARN` ("phase in progress").
- **Resolution Plan**:
  `2_building_and_execution.md` and `3_outcome_and_verdict.md` will be fully populated and finalized during workstreams WS-A through WS-G and exit audit, clearing this warning at phase completion (`verify_end.txt`).

---

### Warning 2: `[WARN] earlier-phase files unchanged` (phase21-gate-a commit not found)
- **Check Name**: `check_immutable_history` (line 306 of `scripts/verify_all.py`)
- **Reported Detail**: `phase21-gate-a commit not found`
- **Root Cause & Explanation**:
  `check_immutable_history` enforces the immutability of historical phase artifacts by comparing the git tree against the parent of the phase gate commit:
  `gate = [x.split("\t")[0] for x in log if x.split("\t")[-1] == f"phase{n}-gate-a"]`
  `base = git("rev-parse", gate[0] + "^").strip()`
  Because `verify_start.txt` is mandated to be run at Step 0 *before* making the `phase21-gate-a` baseline commit, no commit titled `phase21-gate-a` existed in `git log` at the time `verify_start.txt` was captured.
- **Resolution & Status**:
  As soon as `phase21-gate-a` was committed (commit `c6c1b20`), `verify_all.py` resolved this warning to:
  `[PASS] earlier-phase artifacts unchanged since phase21-gate-a (errata may only add lines)`.
