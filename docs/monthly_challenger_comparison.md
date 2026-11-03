# Monthly Challenger Model Evaluation Report

| Metric | Champion (v4.0.0-champion) | Challenger | Delta | Policy Threshold | Status |
|---|---|---|---|---|---|
| Point MAE | 9.70% | 11.57% | +1.87% | Delta <= 0.0% | FAIL |
| 95% Paired Bootstrap CI | - | - | [+0.58%, +3.10%] | Upper CI <= +0.50% | FAIL |
| Equal-Frequency ECE | 0.0526 | 0.1474 | +0.0948 | ECE_chall <= ECE_champ + 0.01 | FAIL |
| Brier Score Loss | 0.1414 | 0.1639 | +0.0224 | Brier_chall <= Brier_champ + 0.005 | FAIL |
| ROC-AUC | 0.8728 | 0.8722 | -0.0006 | Information only | - |
| 80% Conformal Coverage | 90.5% | 85.1% | -5.4 pp | Range [75%, 95%] | PASS |

### Governance Decision
- **Promotion Status**: **DO NOT PROMOTE (Challenger does not demonstrate non-inferiority)**
- **Champion Artifact**: Model file in `model/` was **NOT modified** (automatic model promotion strictly prohibited).
