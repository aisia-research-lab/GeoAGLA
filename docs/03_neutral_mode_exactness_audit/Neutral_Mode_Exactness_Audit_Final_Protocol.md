# Neutral-Mode Exactness Audit --- Final Targeted Test Protocol V1

### Objective
This protocol defines the targeted diagnostic procedure for verifying phase gauge invariance and mode multiplicity on real-audio signals.

### Verification Criteria
1. **Gauge Invariance:** $\lambda_1 \equiv 1.0$ within machine precision ($|\lambda_1 - 1.0| < 10^{-10}$).
2. **Spectral Gap:** $\Delta = 1 - \lambda_2 > 0$ for all non-degenerate signals.
3. **Solver Stability:** SciPy/ARPACK `eigsh` convergence across tolerance sweeps $\epsilon \in \{10^{-12}, 10^{-10}, 10^{-8}, 10^{-6}\}$.
