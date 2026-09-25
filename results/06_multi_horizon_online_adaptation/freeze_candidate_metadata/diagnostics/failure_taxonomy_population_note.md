# Diagnostic Note: Failure Taxonomy Population Clarification

> **Population clarification.** The following 41-case diagnostic taxonomy is derived from the broader configuration sweep and is distinct from the canonical 60-evaluation C1 multi-horizon ledger. Consequently, frequencies reported in this taxonomy should not be interpreted as frequencies within the canonical C1 experiment.

---

## 1. Overview of Experimental Populations

1. **Canonical Multi-Horizon Ledger (C1)**:
   - Contains exactly **60 evaluations** ($15\text{ cases} \times 4\text{ horizons}: H \in \{60, 120, 180, 360\}$).
   - Evaluated under the strictly frozen configuration (`dynamic_envelope`, memory $p=3$, block size $K=8$, margin $=0$, GLA fallback).
   - In this canonical ledger:
     - Fraction with negligible Oracle opportunity ($\Delta_{\rm oracle} < 10^{-4}$): **$0.0\%$** across all horizons.
     - Fraction with denominator clipped ($10^{-6}$): **$0.0\%$** across all horizons.

2. **Exploratory Diagnostic Failure Taxonomy (41 Cases)**:
   - Contains **41 non-win cases** collected across an exploratory, broader hyperparameter and initialization sweep conducted during preliminary phases to categorize failure modes.
   - Used specifically for qualitative boundary analysis and diagnostic classification.

---

## 2. Diagnostic Associative Framework (Task F5 Compliance)

In accordance with supervisor guidelines, failure categories describe **diagnostic associations**, not mathematically certified causal mechanisms:
- **Near-Degenerate Geometry ($N=9, 22.0\%$)**: The failure was associated with near-degenerate geometry (spectral condition $\lambda_+ \ge 0.9999$).
- **Negligible Oracle Headroom ($N=22, 53.7\%$)**: Cases in the broader sweep where baseline FGLA was already operating near the theoretical bound ($\Delta_{\rm oracle} < 10^{-4}$).
- **Estimator Maturation Latency ($N=5, 12.2\%$)**: Cases where observation horizon terminated before passive Ritz secants stabilized the dynamic envelope.
- **Safeguard Transient ($N=3, 7.3\%$)**: Fallback to GLA was triggered by transient non-convex energy oscillations to preserve monotonicity.
- **Spectral Perturbation & Non-convex Stall ($N=2, 4.9\%$)**: Exploratory trajectory stagnation diagnosed near off-target saddles or temporary Krylov subspace perturbations.
