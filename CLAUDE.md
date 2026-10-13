# Claude Code Rules: OPI Project

## Model Training Phase Protocol
Whenever executing a model training or refinement session:
1. Sequential Phase Numbering: Phase 1 (Base train), Phase 2, Phase 3, etc.
2. Store reports in `phases/Phase <N>/`.
3. Three mandatory markdown files per phase:
   - `1_planning_and_goals.md`: Planning, research goals, hypotheses.
   - `2_building_and_execution.md`: Implementation steps, scripts, data pipelines, commands executed.
   - `3_outcome_and_verdict.md`: Results, holdout predictions vs actual IPO gains, comparison to GMP, verdict.
4. Machine Learning Rule: Keep an un-used holdout test partition (`data/ipo_holdout_test.csv`) to validate generalization against actual historical listing gains.
