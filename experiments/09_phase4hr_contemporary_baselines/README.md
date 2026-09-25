# Phase 4H-R2: Literature-Faithful Baseline Repair (NAGLA & Standard AGLA)

## 1. Overview & Scientific Objective
Phase 4H-R2 provides the literature-faithful baseline repair comparing **GeoAGLA (Online Full)** against contemporary accelerated phase retrieval algorithms from the signal processing literature, strictly adhering to `PHASE4HR2_Literature_Faithful_Baseline_Repair_Guide.md`:
1. **Literature Primary NAGLA (`NAGLA_H49_primary`)**: Nesterov momentum recurrence $X_{i+1} = P_V(P_T(Y_i)), Y_{i+1} = X_{i+1} + \alpha_i(X_{i+1} - X_i)$ with $\alpha_i = \frac{i+H-2}{i+H+1}$ with primary literature parameter $H=49$ from contemporary 2026 null-phase phase retrieval experiments. Old $H=2$ is retained solely as sensitivity evidence (`NAGLA_H2_sensitivity`).
2. **Literature Primary AGLA (`AGLA_TableII_primary`)**: Genuine 3-state recurrence with non-trivial $(\beta, \gamma)$ from Nenov et al. Table II: $(\alpha = 1.05, \beta = 1.35, \gamma = 1.25)$, achieving the highest reported average SSNR in published numerical studies. Old $(\alpha = 0.99, \beta = 0.0, \gamma = 1.0)$ is relabeled as `FGLA_like_alpha099` because $\gamma=1.0$ collapses AGLA to FGLA dynamics.
3. **Oracle-optimal FGLA (`FGLA_opt`)**: Closed-form spectral minimax momentum parameter $\alpha^\star = \frac{1 - \sqrt{1 - \lambda_+^2}}{\lambda_+}$ with $\beta = \alpha^\star, \gamma = 1.0$.
4. **GLA**: Classical unaccelerated alternating projections ($\alpha=0, \beta=0, \gamma=1.0$).
5. **GeoAGLA (Online Full)**: Rayleigh-Ritz passive edge estimation ($p=3, K=8, \mu=0$), dynamic envelope, and energy safeguard rollback.

This experiment strictly enforces all 27 technical gates specified in Section 23 of `PHASE4HR2_Literature_Faithful_Baseline_Repair_Guide.md` without post-hoc retuning.

---

## 2. Directory Structure

```text
experiments/09_phase4hr_contemporary_baselines/
├── 01_freeze_baseline_parameters.py    # Step 1: Pre-registration of baseline parameters & RUN_KEY_FREEZE.csv
├── 02_validate_baseline_gates.py       # Step 2: Implementation equivalence gates (R2-A, R2-B, R2-C, R2-D)
├── 03_run_phase4hr_baselines.py        # Step 3: Central pairing runner across 4,752 instances (33,264 method-runs)
├── 04_analyze_and_report.py            # Step 4: Paired rescue, conditional rate analysis, bootstrap (B=5000), audit & firewall
├── protocol/
│   ├── BASELINE_PARAMETER_FREEZE.md    # Pre-registered baseline parameter specification (SHA-256 hashed)
│   ├── RUN_KEY_FREEZE.csv              # Exact population accounting (202 files, 396 file-profile cases, 4,752 keys)
│   └── protocol_manifest.json          # Protocol hash and metadata
├── tests/
│   ├── nagla_h49_recurrence_equivalence.csv # Gate R2-A: NAGLA recurrence equivalence (diff <= 1e-12)
│   ├── agla_tableII_recurrence_equivalence.csv # Gate R2-B: AGLA Table-II recurrence equivalence (diff <= 1e-12)
│   ├── determinism.csv                 # Gate R2-D: Determinism diff = 0.00 <= 1e-12
│   ├── common_initialization_audit.csv # Gate R2-E: Common initialization alignment (0 mismatches)
│   ├── success_flag_audit.csv          # Gate R2-F: 0 recomputed flag mismatches
│   ├── complete_pairing_audit.csv      # Gate R2-G: 0 missing pairs, 0 duplicate rows
│   └── pytest.log                      # Test execution logs
├── results/
│   ├── phase4hr2_baseline_ledger.csv   # Complete repaired 33,264-row ledger
│   ├── success_summary.csv             # Overall success rates
│   ├── initialization_stratified_success.csv # Regimes breakdown
│   ├── paired_rescue_summary.csv       # Net rescue tables (Rescue vs Lost)
│   ├── paired_rate_summary.csv         # Conditional contraction factor ratios (q_B / q_A)
│   ├── bootstrap_contrasts.csv         # Source-file cluster bootstrap CIs (B=5,000)
│   └── baseline_failure_ledger.csv     # Audit of all numerical failures (zero dropped)
├── audit/
│   ├── PHASE4HR2_FINAL_AUDIT.md        # Official audit report (ALL 27 GATES PASSED)
│   └── CLAIM_FIREWALL.md               # Legal phrasing guidelines for manuscript
└── provenance/
    ├── environment.txt                 # Platform, Python, NumPy, Pandas versions
    └── SHA256SUMS.txt                  # Cryptographic provenance hashes for all artifacts
```

---

## 3. Technical Verification Gates (Section 23)

All 27 technical gates are automated and strictly enforced:
- **Gates R2-A & R2-B (Recurrence Equivalence)**: Step-by-step unrolled execution against literature formulas achieves diff $= 0.00 \le 10^{-12}$.
- **Gate R2-C (AGLA Non-Collapse)**: Verifies $\beta \neq 0$ and $\gamma \neq 1$, with non-zero discrepancy against collapsed FGLA dynamics.
- **Gate R2-D (Machine Determinism)**: Across 3 fixed fixtures, repeat runs achieve $\max \|c_n^{(1)} - c_n^{(2)}\|_\infty = 0.00 \le 10^{-12}$.
- **Gate R2-E (Common Initialization)**: Cryptographic SHA-256 fingerprinting verifies 0 drift across methods.
- **Gate R2-F (Success Recomputation)**: Primitive values $e_{\rm final} \le 0.1 \cdot e_{\rm initial}$ and $r_{\rm mag} \le 10^{-5}$ re-evaluated row-by-row; 0 mismatches.
- **Gate R2-G (Complete Pairing)**: Exactly 5 primary methods per run key, 0 duplicate rows.

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
