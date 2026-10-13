# Phase Reporting Protocol for Model Training Sessions

Whenever performing a model training or dataset enhancement session on this repository:
1. Follow sequential phase numbering: `Phase 1`, `Phase 2`, `Phase 3`, ...
2. Store each phase report inside `phases/Phase <N>/`.
3. Provide exactly three files in each phase folder:
   - `1_planning_and_goals.md`: Planning, goals, scope, and target metrics.
   - `2_building_and_execution.md`: Full build process, data enrichment, and exact commands run.
   - `3_outcome_and_verdict.md`: Empirical results, holdout evaluation vs actual IPO gains, GMP comparison, verdict, and review.
4. Never train on the full dataset without preserving a strictly untouched out-of-sample holdout test partition.
