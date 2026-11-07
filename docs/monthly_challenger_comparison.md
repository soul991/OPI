# Monthly Challenger Model Evaluation Report

| Metric | Champion (v4.0.0-champion) | Challenger | Delta | Policy Threshold | Status |
|---|---|---|---|---|---|
| Point MAE | 9.72% | 12.14% | +2.43% | Delta <= 0.0% | FAIL |
| 95% Paired Bootstrap CI | - | - | [+1.06%, +3.87%] | Upper CI <= +0.50% | FAIL |
| Equal-Frequency ECE | 0.0487 | 0.1190 | +0.0702 | ECE_chall <= ECE_champ + 0.01 | FAIL |
| Brier Score Loss | 0.1434 | 0.1572 | +0.0138 | Brier_chall <= Brier_champ + 0.005 | FAIL |
| ROC-AUC | 0.8718 | 0.8759 | +0.0041 | Information only | - |
| 80% Conformal Coverage | 90.6% | 82.6% | -8.1 pp | Range [75%, 95%] | PASS |

### Governance Decision
- **Promotion Status**: **DO NOT PROMOTE (Challenger does not demonstrate non-inferiority)**
- **Champion Artifact**: Model file in `model/` was **NOT modified** (automatic model promotion strictly prohibited).
