# Project Rules & Protocols: India IPO Listing-Gain Predictor (OPI)

## Mandatory AI Agent Rule: Sequential Phase Reporting

Whenever any AI agent (Antigravity, Cursor, Claude Code, Copilot, ChatGPT, or custom agents) works on this codebase and executes a **major model training session** (e.g., baseline training, retraining, feature engineering upgrades, hyperparameter optimization, or dataset expansion), the agent **MUST** document the work in a standardized phase directory.

---

### 1. Sequential Phase Naming
- Reports must strictly follow the sequential naming scheme:
  - `Phase 1`: Initial baseline model, dataset collection, holdout partitioning, and baseline benchmark.
  - `Phase 2`: Next major iteration (e.g., deep feature engineering, macro data addition, or alternative algorithms).
  - `Phase 3`, `Phase 4`, ...: Subsequent iterations.
- Never overwrite previous phase reports. Each phase represents an immutable snapshot of that training generation.

---

### 2. Storage Directory
- All phase directories must reside in the `phases/` folder at the root of the project:
  ```
  phases/
  ├── Phase 1/
  ├── Phase 2/
  └── Phase 3/
  ```
- A root-level shortcut/folder `Phase 1/`, `Phase 2/` may also be maintained for immediate developer convenience.

---

### 3. Required File Structure in Every Phase Folder
Every `Phase <N>` directory **MUST** contain exactly three standard markdown documents:

#### File 1: `1_planning_and_goals.md`
- **Purpose**: Scope, planning, and objectives of the phase.
- **Required Sections**:
  1. Objectives and Scope (What are we aiming to achieve?)
  2. Hypotheses and Research Questions (e.g., can the model beat GMP? Can institutional subscription improve predictive accuracy?)
  3. Data Strategy (Holdout separation rules, source selection, leakage prevention).
  4. Success Criteria and Metrics (Target MAE, ROC-AUC, Accuracy thresholds).

#### File 2: `2_building_and_execution.md`
- **Purpose**: Full technical implementation log and reproduction guide.
- **Required Sections**:
  1. Pipeline Architecture & Data Flow.
  2. Scripts Created / Modified (File paths, key logic, parameters).
  3. Data Purification & Engineering Steps (Outlier handling, imputations, ratios).
  4. Exact Terminal Commands Executed (Step-by-step shell commands to reproduce).
  5. Artifacts and Generated Data Files.

#### File 3: `3_outcome_and_verdict.md`
- **Purpose**: Empirical findings, benchmark comparisons, and actionable conclusions.
- **Required Sections**:
  1. Key Performance Metrics (MAE, Accuracy for gain > 10%, ROC-AUC).
  2. Comparison vs Baselines:
     - Model vs Historical Mean.
     - Model vs Raw Grey Market Premium (GMP).
  3. Holdout Evaluation Table (Predicted vs Actual listing day performance on unseen IPOs).
  4. Honest Verdict & Failure Modes (Where the model excels, where it struggled).
  5. Actionable Recommendations for the next phase.

---

### 4. Machine Learning Guardrails
1. **Never Train on the Full Dataset**: Always maintain a strict chronological out-of-sample holdout test partition (`data/ipo_holdout_test.csv`) that the model never sees during training.
2. **Prevent Future Data Leakage**: Features must be knowable strictly before the IPO lists (e.g., GMP on final bidding day, 30-day prior Nifty return).
3. **Always Benchmark Against Naive GMP**: If an AI model cannot beat the simple Grey Market Premium baseline, it must not be trusted for production decisions.
