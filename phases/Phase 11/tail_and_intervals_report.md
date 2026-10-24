# Tail & Conformal Intervals Walk-Forward Evaluation Report

> Mandated by Phase 11 Workstream C (D-007, D-008).
> Conducted strictly walk-forward across 20 quarters (2022Q1 to 2026Q4) on $n = 398$ holdout IPOs.

---

## 1. Executive Summary Table

| Model Architecture | Overall Coverage (80% Nom) | Wilson 95% CI | Tail Coverage (Top 10% Pops) | Tail Wilson 95% CI | Mean Width | Target 1 (77-84%) | Target 2 (Tail >=70%) | Target 3 (Width -5pp) | Decision |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Champion (Pooled Conformal)** | 87.94% | [84.4%, 90.8%] | 55.00% | [39.8%, 69.3%] | 48.96 pp | FAIL | FAIL | FAIL | REJECTED (Keep Champion) |
| **Candidate 1 (Mondrian Conformal)** | 85.68% | [81.9%, 88.8%] | 57.50% | [42.2%, 71.5%] | 47.21 pp | FAIL | FAIL | FAIL | REJECTED (Keep Champion) |
| **Candidate 2 (Quantile CQR)** | 83.92% | [80.0%, 87.2%] | 67.50% | [52.0%, 79.9%] | 52.72 pp | PASS | FAIL | FAIL | REJECTED (Keep Champion) |

---

## 2. Paired Bootstrap Hypothesis Tests (Seed 42, 2,000 Resamples)

- **Candidate 1 vs Champion**:
  - Coverage Difference: -0.0226 (95% CI: [-0.0452, +0.0000]) -> Straddles Zero (No demonstrated difference).
  - Width Difference: -1.74 pp (95% CI: [-3.35, -0.03] pp) -> Excludes Zero (Significant).
- **Candidate 2 vs Champion**:
  - Coverage Difference: -0.0402 (95% CI: [-0.0805, +0.0000]) -> Straddles Zero (No demonstrated difference).
  - Width Difference: +3.76 pp (95% CI: [+0.75, +6.79] pp) -> Excludes Zero (Significant).

---

## 3. Honest Verdict & Defect Transitions

- Candidate 1 (Mondrian Conformal): Overall coverage 85.68%, Tail coverage 57.50%, Mean width 47.21 pp.
- Candidate 2 (Quantile CQR): Overall coverage 83.92%, Tail coverage 67.50%, Mean width 52.72 pp.

### Decision Protocol:
Per the pre-registered decision rules in `phases/Phase 11/preregistration.md` Section 3:
Neither candidate beats the champion while simultaneously satisfying all three frozen targets (Target 1: 77-84%, Target 2: >=70%, Target 3: -5pp width) with a paired bootstrap interval excluding zero.

Therefore, per protocol:
1. **Champion `v4.0.0-champion` and its replay file remain untouched**.
2. **Defects D-007 and D-008 transition to `ACCEPTED`** limitations documented under `README.md` Known Limitations.
3. No promotion is executed without explicit approval.
