# Phase 4H-R: Claim and Interpretation Firewall
## Strict Manuscript Phrasing Guidelines (Sections 18 & 19 Compliance)

To maintain absolute scientific objectivity and prevent reviewer-sensitive overstatements, the following wording rules are legally binding for the manuscript:

### 1. Mandatory Safe Wording for Empirical Comparison
> **Permitted Statement**:

> *Under the frozen real-audio protocol on the MUSAN benchmark, Online Full (GeoAGLA) attains higher empirical convergence success (73.30%) than the evaluated published NAGLA (64.90%), standard AGLA (59.01%), and fixed FGLA (54.90%) configurations, demonstrating the practical value of online geometric adaptation and safeguard rollback.*

### 2. Prohibited Phrasings
- ❌ **PROHIBITED**: `GeoAGLA is the state of the art in Griffin-Lim phase retrieval.`
- ❌ **PROHIBITED**: `GeoAGLA universally dominates all existing momentum algorithms.`
- ❌ **PROHIBITED**: Describing empirical percentages as `theoretical basin volumes`.

### 3. Separation of Conditional Speed and Convergence Robustness
- Robustness and local asymptotic contraction are distinct mathematical endpoints.
- Unaccelerated GLA has conservative convergence behavior but contracts slowly ($q \approx \lambda_+$).
- Aggressive fixed momentum (such as published AGLA with $\alpha=0.99$) achieves rapid local contraction once inside the basin, but suffers from momentum overshoot and lower basin robustness under large perturbations.
- Online GeoAGLA successfully bridges this gap by combining local acceleration with safeguard stability.