# Phase 4H-R: Baseline Parameter Freeze Document
**Project**: GeoAGLA (ICLR 2027)
**Freeze Timestamp**: `2026-09-25T12:00:00Z`
**Frozen Before Full Results Inspected**: **YES (STRICT ANTI-TUNING FIREWALL)**

---

## 1. Mandatory Protocol Identity

- **Protocol Name**: Phase 4H-R Contemporary Baseline Closure
- **Canonical Benchmark Ledger**: `data/reproducibility/basin_musan_odd/basin_results.csv`
- **Total Paired Runs in Ledger**: 4752 runs across 202 files.
- **Success Criterion**: $e_{\rm final} \le 0.1 \cdot e_{\rm initial}$ and $r_{\rm mag}^{\rm final} \le 10^{-5}$ (Uniform for all methods).
- **Rate Fit Window**: Last 35% of valid iterations above numerical floor $10^{-11}$.
- **Cluster Bootstrap**: $B=5,000$ resamples clustered by source file, seed `20270925`.

## 2. Frozen Contemporary Baseline Specifications

### GLA (Griffin-Lim Algorithm)
- **Source Paper**: *Signal estimation from modified short-time Fourier transform*
- **Bibliographic Citation**: Griffin & Lim, IEEE Trans. ASSP, 32(2):236-243, 1984.
- **Algorithm / Recurrence**: `Standard alternating projections without momentum`
- **Exact Frozen Parameters**: `{"alpha": 0.0, "beta": 0.0, "gamma": 1.0}`
- **Parameter-Selection Rationale**: Foundational unaccelerated baseline in phase retrieval.
- **Date Frozen**: `2026-09-25T12:00:00Z`
- **Frozen Before Full Results Inspected**: **YES**

### FGLA (Fast Griffin-Lim Algorithm, Oracle-Tuned)
- **Source Paper**: *A Fast Griffin-Lim Algorithm*
- **Bibliographic Citation**: Perraudin, Sigg, Balazs, IEEE WASPAA 2013.
- **Algorithm / Recurrence**: `AGLA t-recurrence with theoretically optimal momentum alpha=beta=(1-sqrt(1-lambda_+))/(1+sqrt(1-lambda_+)), gamma=1.0`
- **Exact Frozen Parameters**: `"Oracle-adaptive from local transverse eigenvalue lambda_+"`
- **Parameter-Selection Rationale**: Exact theoretical closed-form single-edge optimal fixed momentum.
- **Date Frozen**: `2026-09-25T12:00:00Z`
- **Frozen Before Full Results Inspected**: **YES**

### Published Standard AGLA (Fixed Parameters)
- **Source Paper**: *A Fast Griffin-Lim Algorithm*
- **Bibliographic Citation**: Perraudin, Sigg, Balazs, IEEE WASPAA 2013, Section 3.1.
- **Algorithm / Recurrence**: `AGLA recurrence with literature-recommended fixed parameters`
- **Exact Frozen Parameters**: `{"alpha": 0.99, "beta": 0.0, "gamma": 1.0}`
- **Sensitivity Variant**: `{"alpha": 0.99, "beta": 0.99, "gamma": 1.0}`
- **Parameter-Selection Rationale**: Canonical published default momentum alpha=0.99 from Perraudin et al. 2013.
- **Date Frozen**: `2026-09-25T12:00:00Z`
- **Frozen Before Full Results Inspected**: **YES**

### Published NAGLA (Nesterov Accelerated Griffin-Lim)
- **Source Paper**: *Accelerated Griffin-Lim Algorithm with Nesterov Momentum / Fast Phase Retrieval*
- **Bibliographic Citation**: Nesterov (1983) momentum schedule applied to GLA projection map; Perraudin et al. (2013).
- **Algorithm / Recurrence**: `alpha_i = (i + H - 2) / (i + H + 1), t_{i+1} = P_S P_M(t_i + alpha_i (t_i - t_{i-1}))`
- **Exact Frozen Parameters**: `{"H": 2, "schedule": "alpha_i = i / (i + 3)", "gamma": 1.0}`
- **Primary Parameter**: $H=2$
- **Sensitivity Parameter**: $H=3$
- **Parameter-Selection Rationale**: Canonical primary literature parameter H=2 yields standard Nesterov momentum schedule.
- **Date Frozen**: `2026-09-25T12:00:00Z`
- **Frozen Before Full Results Inspected**: **YES**

### Online Full / GeoAGLA (Ours)
- **Source Paper**: *Geometry Determines Acceleration in Phase Retrieval (ICLR 2027)*
- **Bibliographic Citation**: Anonymous ICLR 2027 Submission.
- **Algorithm / Recurrence**: `Ritz-adaptive momentum synthesis with safeguard rollback to GLA`
- **Exact Frozen Parameters**: `{"Ritz_memory_p": 3, "update_period_K": 8, "margin_mu": 0.0, "policy": "dynamic_envelope", "fallback": "GLA on energy increase"}`
- **Parameter-Selection Rationale**: Strictly frozen configuration from Phase 2B / Phase 4 robustness protocol.
- **Date Frozen**: `2026-09-25T12:00:00Z`
- **Frozen Before Full Results Inspected**: **YES**

## 3. Anti-Tuning Firewall Compliance Declaration
Under Section 2 of `PHASE4HR_Contemporary_Baseline_Closure_Bao_Guide.md`:
1. Zero post-hoc hyperparameter tuning has been performed on test evaluations.
2. Contemporary baselines (NAGLA, Published AGLA) are implemented faithfully from published equations.
3. The existing GeoAGLA / Online Full configuration is preserved exactly without alteration.
4. All comparisons share identical initializations, STFT operators, horizons, stopping rules, and success criteria.