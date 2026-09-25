# Protocol Artifact: Contemporary Baseline Parameter Freeze (Phase 4H-R2)
## Literature-Faithful Freezing Document (Anti-Tuning Firewall Compliance)
**Date/Time of Freeze**: 2026-09-25T14:30:00Z
**Code SHA / Commit**: 7b84f29a0e6c43df
**Confirmation**: *All baseline configurations recorded herein were frozen strictly before inspecting full Phase 4H-R2 outcomes. No retuning, post-hoc sweeps, or selective cherry-picking are permitted.*

---

### 1. Primary Baseline Comparators (Frozen)

#### `GLA`
- **Method Name**: GLA (Griffin-Lim Algorithm)
- **Literature Citation**: Griffin & Lim, IEEE Trans. ASSP, 32(2):236-243, 1984.
- **Recurrence Equation**: `Standard alternating projections: c_{n+1} = P_V(P_M(c_n))`
- **Parameters**: `{'alpha': 0.0, 'beta': 0.0, 'gamma': 1.0}`
- **Rationale**: Foundational unaccelerated baseline in phase retrieval (momentum-free, safe from overshoot).

#### `FGLA_opt`
- **Method Name**: FGLA_opt (Oracle-Optimal Fast Griffin-Lim)
- **Literature Citation**: Perraudin, Sigg, Balazs, IEEE WASPAA 2013.
- **Recurrence Equation**: `AGLA recurrence collapsed to 2 states with theoretical single-edge minimax momentum: alpha = beta = (1 - sqrt(1 - lambda_+^2)) / lambda_+, gamma = 1.0`
- **Parameters**: `Oracle-adaptive from local transverse eigenvalue lambda_+`
- **Rationale**: Exact theoretical closed-form single-edge optimal fixed momentum.

#### `NAGLA_H49_primary`
- **Method Name**: NAGLA_H49_primary (Literature Primary NAGLA)
- **Literature Citation**: Nesterov (1983); Perraudin et al. (2013); 2026 NAGLA contemporary null-phase study.
- **Recurrence Equation**: `X_{i+1} = P_V(P_T(Y_i)), Y_{i+1} = X_{i+1} + alpha_i * (X_{i+1} - X_i), alpha_i = (i + H - 2) / (i + H + 1)`
- **Parameters**: `{'H': 49, 'schedule': 'alpha_i = (i + 47) / (i + 50)', 'gamma': 1.0}`
- **Selection Basis**: Configuration used in the contemporary 2026 NAGLA literature in its principal null-phase comparative experiment; not selected on the GeoAGLA evaluation benchmark.

#### `AGLA_TableII_primary`
- **Method Name**: AGLA_TableII_primary (Literature Primary AGLA)
- **Literature Citation**: Nenov et al., Table II leading configuration; Perraudin et al. (2013).
- **Recurrence Equation**: `t_n = (1 - gamma)*d_{n-1} + gamma*P_C1(P_C2(c_{n-1})), c_n = t_n + alpha*(t_n - t_{n-1}), d_n = t_n + beta*(t_n - t_{n-1})`
- **Parameters**: `{'alpha': 1.05, 'beta': 1.35, 'gamma': 1.25}`
- **Selection Basis**: Configuration with the largest reported average SSNR among Table-II combinations in Nenov et al.; genuine 3-state recurrence with non-trivial beta and gamma != 1.

#### `Online_Full`
- **Method Name**: Online Full / GeoAGLA (Ours)
- **Literature Citation**: Anonymous ICLR 2027 Submission.
- **Recurrence Equation**: `Ritz-adaptive momentum synthesis (p=3) with dynamic envelope damping and energy safeguard rollback to GLA`
- **Parameters**: `{'Ritz_memory_p': 3, 'update_period_K': 8, 'burn_in': 8, 'policy': 'dynamic_envelope (1 - exp(-k/20))', 'fallback': 'GLA on energy increase'}`
- **Rationale**: Strictly frozen configuration from Phase 2B / Phase 4 robustness protocol.

#### `NAGLA_H2_sensitivity`
- **Method Name**: NAGLA_H2_sensitivity (Retained Sensitivity Comparator)
- **Literature Citation**: Nesterov (1983); Perraudin et al. (2013).
- **Parameters**: `{'H': 2, 'schedule': 'alpha_i = i / (i + 3)', 'gamma': 1.0}`
- **Selection Basis**: Retained only as sensitivity evidence from Phase 4H-R; must not be used as primary published NAGLA headline.

#### `FGLA_like_alpha099`
- **Method Name**: FGLA_like_alpha099 (Archived Pseudo-AGLA Comparator)
- **Literature Citation**: Perraudin et al. (2013) fixed-momentum setting.
- **Parameters**: `{'alpha': 0.99, 'beta': 0.0, 'gamma': 1.0}`
- **Selection Basis**: Relabeled from old Phase 4H-R pseudo-AGLA run; gamma=1 collapses recurrence to FGLA dynamics.

---

### 2. Mandatory Anti-Tuning Firewall Enforcements (Section 5)
- Do not sweep H; keep H=49 strictly frozen.
- Do not sweep AGLA triples; keep (1.05, 1.35, 1.25) strictly frozen.
- Do not modify GeoAGLA parameters.
- Do not alter the 360-iteration horizon.
- Do not alter initialization distributions or levels.
- Do not alter the frozen success criteria (e_final <= 0.10 * e_initial and r_mag_final <= 1e-5).
- All baseline outcomes (strong or poor) constitute valid scientific evidence.
