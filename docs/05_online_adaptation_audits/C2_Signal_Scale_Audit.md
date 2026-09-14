# Task C2 — Audit Report: Signal-Scale Iterations-to-Tolerance Censoring

## Executive Summary
This audit resolves the ambiguity in Section C2 of `Student B — Final Correction & Audit Handoff.md`.
The previous report recorded $T_{\rm GLA} = T_{\rm FGLA} = T_{\rm Online} = 100$.

### Resolution: Case B (Right-Censored at max_iter = 100)
Inspection of the complete error trajectories demonstrates conclusively that:
- **Case B holds true**: No method reached the target tolerance $\tau = 10^{-2}$ within the budget of $100$ iterations.
- Initial orbit errors were $\approx 20.0$, and final errors at iteration $100$ remained in the range $[0.018, 18.5]$.
- Therefore, the value $100$ represents **right-censoring at $100$ iterations ($T_m(\tau) > 100$, `censored = true`)**, NOT exact attainment of tolerance at iteration 100.

---

## Censoring Audit Summary Table

| Signal Type | Method | Final Error ($k=100$) | Reached $\tau=10^{-2}$? | Correct Notation $T_m(10^{-2})$ | Censored? |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Harmonic** | GLA | 1.3178 | No | **>100** | **TRUE** |
| | FGLA (Fixed) | 1.1552 | No | **>100** | **TRUE** |
| | FGLA (Opt) | 1.3548 | No | **>100** | **TRUE** |
| | Online Adaptive | 1.3582 | No | **>100** | **TRUE** |
| **Chirp** | GLA | 1.3095 | No | **>100** | **TRUE** |
| | FGLA (Fixed) | 1.3208 | No | **>100** | **TRUE** |
| | FGLA (Opt) | 0.5197 | No | **>100** | **TRUE** |
| | Online Adaptive | 0.4829 | No | **>100** | **TRUE** |
| **Speech-like** | GLA | 1.1593 | No | **>100** | **TRUE** |
| | FGLA (Fixed) | 1.3357 | No | **>100** | **TRUE** |
| | FGLA (Opt) | 1.3368 | No | **>100** | **TRUE** |
| | Online Adaptive | 1.1766 | No | **>100** | **TRUE** |
| **Transient** | GLA | 1.1547 | No | **>100** | **TRUE** |
| | FGLA (Fixed) | 1.1547 | No | **>100** | **TRUE** |
| | FGLA (Opt) | 1.1547 | No | **>100** | **TRUE** |
| | Online Adaptive | 1.1547 | No | **>100** | **TRUE** |

---

## Formal Decision Rule Actions (Section C2.3)
1. **Removal of Iteration-Savings Claims**: Because all methods are right-censored at $100$ iterations ($100\%$ censoring fraction), this experiment does **not** provide valid statistical evidence for paired iteration savings ($S_{\rm iter}$). All claims of percentage iteration savings on these synthetic signals are formally removed from the report.
2. **Re-classification as Stability / Convergence Sanity Check**: The experiment is retained strictly as an empirical sanity check confirming that the safeguarded online algorithm converges stably without divergence or destabilizing updates on structured waveforms.
3. **Publication Figure Exclusion**: In accordance with the decision rule, this experiment is not used as a main-text figure.
