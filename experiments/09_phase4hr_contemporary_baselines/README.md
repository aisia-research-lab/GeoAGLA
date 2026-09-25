# Phase 4H-R: Contemporary Baseline Closure (NAGLA & Standard AGLA)

## 1. Overview & Scientific Objective
Phase 4H-R provides the definitive empirical and methodological closure comparing **GeoAGLA (Online Full)** against contemporary accelerated phase retrieval algorithms from the signal processing literature:
1. **Published NAGLA (Nesterov Accelerated Griffin-Lim Algorithm)**: Nesterov momentum recurrence $\alpha_i = \frac{i+H-2}{i+H+1}$ with primary literature parameter $H=2$ (Perraudin, Sigg, Balazs, IEEE WASPAA 2013).
2. **Published Standard AGLA**: Fixed momentum parameters $(\alpha = 0.99, \beta = 0.0, \gamma = 1.0)$ (Perraudin et al., 2013, Section 3.1).
3. **Oracle-optimal FGLA**: Closed-form spectral minimax momentum parameter $\alpha^\star = \frac{1 - \sqrt{1 - \lambda_+^2}}{\lambda_+}$ with $\beta = \alpha^\star, \gamma = 1.0$.
4. **GLA**: Classical unaccelerated alternating projections ($\alpha=0, \beta=0, \gamma=1.0$).
5. **GeoAGLA (Online Full)**: Rayleigh-Ritz passive edge estimation ($p=3, K=8, \mu=0$), dynamic envelope, and energy safeguard rollback.

This experiment strictly adheres to the protocol specified in `PHASE4HR_Contemporary_Baseline_Closure_Bao_Guide.md` and implements all 22 technical gates without post-hoc retuning.

---

## 2. Directory Structure

```text
experiments/09_phase4hr_contemporary_baselines/
├── 01_freeze_baseline_parameters.py    # Gate B0: Pre-registration of baseline parameters
├── 02_validate_baseline_gates.py       # Gates B1-B4: Determinism, recurrence equivalence, init drift, transparency
├── 03_run_phase4hr_baselines.py        # Central pairing runner across 4,752 instances (23,760 method-runs)
├── 04_analyze_and_report.py            # Gate B5, paired rescue, cluster-bootstrap (B=5000), audit report & firewall
├── protocol/
│   ├── BASELINE_PARAMETER_FREEZE.md    # Pre-registered baseline parameter specification
│   └── protocol_manifest.json          # Protocol hash and metadata
├── tests/
│   ├── baseline_determinism.csv        # Gate B1: Determinism diff = 0.00
│   ├── published_recurrence_equivalence.csv # Gate B2: Equivalence diff = 0.00
│   ├── initial_state_alignment.csv     # Gate B3: Common initialization alignment
│   ├── no_hidden_retuning_audit.csv    # Gate B4: Parameter ledger verification
│   └── success_flag_audit.csv          # Gate B5: 0 recomputed flag mismatches
├── results/
│   ├── phase4hr_baseline_ledger.csv    # Complete paired 23,760-row ledger
│   ├── success_summary.csv             # Overall success rates
│   ├── initialization_stratified_success.csv # Regimes breakdown
│   ├── paired_rescue_summary.csv       # Net rescue tables (Rescue vs Lost)
│   ├── paired_rate_summary.csv         # Conditional contraction factor ratios (q_B / q_A)
│   ├── bootstrap_contrasts.csv         # Source-file cluster bootstrap CIs (B=5,000)
│   └── baseline_failure_ledger.csv     # Audit of all unsuccessful runs (zero dropped)
├── audit/
│   ├── PHASE4HR_BASELINE_AUDIT.md      # Official audit report (ALL GATES PASSED)
│   └── CLAIM_FIREWALL.md               # Legal phrasing guidelines for manuscript
└── provenance/
    ├── environment.txt                 # Platform, Python, NumPy, Pandas versions
    └── SHA256SUMS.txt                  # Cryptographic provenance hashes for all artifacts
```

---

## 3. Technical Verification Gates

All six implementation gates are automated and strictly enforced before and during analysis:
- **Gate B0 (Parameter Freeze)**: Parameters frozen and committed prior to results inspection.
- **Gate B1 (Machine Determinism)**: Across 3 fixed fixtures, repeat runs achieve $\max \|c_n^{(1)} - c_n^{(2)}\|_\infty = 0.00 \le 10^{-12}$.
- **Gate B2 (Recurrence Equivalence)**: Step-by-step unrolled execution against literature formulas achieves diff $= 0.00 \le 10^{-14}$.
- **Gate B3 (Common Initialization)**: Cryptographic SHA-256 fingerprinting verifies 0 drift across methods.
- **Gate B4 (No Hidden Retuning)**: Pre-registered parameter values are explicitly verified row-by-row in the results ledger.
- **Gate B5 (Success Recomputation)**: Primitive values $e_{\rm final} \le 0.1 \cdot e_{\rm initial}$ and $r_{\rm mag} \le 10^{-5}$ re-evaluated row-by-row; 0 mismatches across 23,760 rows.

---

## 4. Key Empirical Findings

### Overall Convergence Success (4,752 Paired Runs)
| Method | Successes | Success Rate (%) | Contrast vs FGLA | Contrast vs NAGLA |
|---|:---:|:---:|:---:|:---:|
| **GLA** | 3,387 | **71.28%** | +16.38 pp | +6.38 pp |
| **FGLA_opt** | 2,609 | **54.90%** | Baseline | -10.00 pp |
| **Published_AGLA** | 2,804 | **59.01%** | +4.10 pp | -5.90 pp |
| **Published_NAGLA** | 3,084 | **64.90%** | +10.00 pp | Baseline |
| **Online_Full (GeoAGLA)** | 3,483 | **73.30%** | **+18.39 pp** | **+8.40 pp** |

### Source-File Cluster Bootstrap (B=5,000 Resamples, 95% Confidence Intervals)
- $\Delta(\text{Online Full} - \text{FGLA\_opt}) = \mathbf{+18.39\text{ pp}}$ $[+17.03, +19.76]\text{ pp}$ (Net rescue: 889 rescued, 15 lost).
- $\Delta(\text{Online Full} - \text{Published NAGLA}) = \mathbf{+8.40\text{ pp}}$ $[+6.67, +10.12]\text{ pp}$ (Net rescue: 699 rescued, 300 lost).
- $\Delta(\text{Online Full} - \text{Published AGLA}) = \mathbf{+14.29\text{ pp}}$ $[+12.65, +15.99]\text{ pp}$ (Net rescue: 877 rescued, 198 lost).

---

## 5. How to Reproduce

### One-Command Pipeline
To reproduce the entire Phase 4H-R suite (pre-registration, gates verification, paired execution, and audit generation):
```bash
python reproduce/run_phase4hr_baselines.py
```

### Step-by-Step Execution
```bash
# 1. Gate B0: Pre-register baseline parameters
python experiments/09_phase4hr_contemporary_baselines/01_freeze_baseline_parameters.py

# 2. Gates B1-B4: Validate baseline technical gates
python experiments/09_phase4hr_contemporary_baselines/02_validate_baseline_gates.py

# 3. Step 3: Run paired 5-method baseline execution
python experiments/09_phase4hr_contemporary_baselines/03_run_phase4hr_baselines.py

# 4. Step 4: Run statistical analysis, cluster bootstrap & generate audit report
python experiments/09_phase4hr_contemporary_baselines/04_analyze_and_report.py
```
