# Monthly Challenger Model Evaluation Report

| Metric | Champion (v4.0.0-champion) | Challenger | Delta | Policy Threshold | Status |
|---|---|---|---|---|---|
| Point MAE | 9.72% | 11.59% | +1.86% | Delta <= 0.0% | FAIL |
| 95% Paired Bootstrap CI | - | - | [+0.58%, +3.08%] | Upper CI <= +0.50% | FAIL |
| Equal-Frequency ECE | 0.0537 | 0.1430 | +0.0893 | ECE_chall <= ECE_champ + 0.01 | FAIL |
| Brier Score Loss | 0.1424 | 0.1639 | +0.0215 | Brier_chall <= Brier_champ + 0.005 | FAIL |
| ROC-AUC | 0.8724 | 0.8715 | -0.0010 | Information only | - |
| 80% Conformal Coverage | 90.5% | 85.1% | -5.4 pp | Range [75%, 95%] | PASS |

### Governance Decision
- **Promotion Status**: **DO NOT PROMOTE (Challenger does not demonstrate non-inferiority)**
- **Champion Artifact**: Model file in `model/` was **NOT modified** (automatic model promotion strictly prohibited).
