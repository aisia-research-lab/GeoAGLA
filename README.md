# GeoAGLA: Geometry-Adaptive Acceleration in Phase Retrieval
## ICLR 2027 Research Repository (Consolidated & Refactored Edition)

This repository unifies all experimental code, mathematical specifications, empirical result ledgers, standalone notebooks, unit tests, and comprehensive documentation for the ICLR 2027 submission:
**"Geometry Determines Acceleration in Phase Retrieval"**.

All code and results from the initial baseline reproduction (Phases 1 & 2), through Next Experiments (Gate A, neutral mode exactness audit, real audio 202-file & 4,680-run basin transfer), to the final scientific freeze (Tasks C1–C4, canonical 60-eval C1 audit, computational microbenchmarks) are fully integrated, standardized, and self-contained.

---

## 1. Repository Architecture

```text
GeoAGLA_Consolidated/
│
├── src/geometry_gla/          # Core modular Python package
│   ├── algorithms/            # GLA, FGLA, AGLA, Minimax Oracle, Safe Online Policy
│   ├── audio/                 # Audio waveform loading, normalization, windowing
│   ├── estimators/            # Rayleigh-Ritz passive eigensolvers, power iteration
│   ├── geometry/              # Subspace principal angles, Jacobian, realification
│   ├── metrics/               # Spectral contraction rates, phase-gauge orbit distance
│   ├── operators/             # STFT / iSTFT, periodic transforms, range projectors
│   └── safeguards/            # Fixed checkpoint merit functions & fallback triggers
│
├── configs/                   # Frozen experimental parameter configurations (YAML & JSON)
│   ├── e6_heldout_geometry.json
│   ├── e6_heldout_manifest_frozen.json
│   ├── heldout_grid_spec.json
│   └── phase1c_grid.json ... phase2a_grid.json
│
├── data/                      # Standard evaluation datasets & reference caches
│   ├── audio_samples/         # 6 representative MUSAN speech, music, and noise waveforms (.wav)
│   └── frozen/                # Frozen reference evaluation caches (h2_multi.json, horizon_audit.json)
│
├── experiments/               # Modular standalone experiment runners (01 to 07)
│   ├── 01_linear_modal_dynamics/            # Linear modal dynamics & spectral correspondence
│   ├── 02_controlled_local_rates/           # Controlled multi-STFT grid sweeps & window audits
│   ├── 03_geometry_opportunity_gate_a/      # Gate A heldout evaluation, E6 ledgers, LaTeX tables
│   ├── 04_neutral_mode_exactness_audit/     # Leading neutral mode gauge symmetry exactness audits
│   ├── 05_real_audio_basin_transfer/        # Real audio basin sweeps, 202-file & 4,680-run evaluations
│   ├── 06_multi_horizon_online_adaptation/  # Maturation sweeps, failure taxonomy, Tasks C1-C4
│   └── 07_computational_cost_microbench/    # Unisolated vs isolated Ritz microbenchmarking
│
├── notebooks/                 # Standalone Jupyter & Kaggle notebooks (clean 01 to 07 sequence)
│   ├── 01_Linear_Modal_and_Spectrum_Reproduction.ipynb
│   ├── 02_Online_Estimator_Maturation_Reproduction.ipynb
│   ├── 03_Gate_A_Heldout_Geometry_Opportunity.ipynb
│   ├── 04_Safeguard_and_RealAudio_Basin_Exploration.ipynb
│   ├── 05_RealAudio_Basin_Transfer_and_Horizon_Audit.ipynb
│   ├── 06_Online_MultiHorizon_and_Claim_Correction_Audit.ipynb
│   └── 07_Final_Scientific_Freeze_Reconciliation_Standalone.ipynb
│
├── results/                   # Complete empirical result ledgers (202 verified result files)
│   ├── 01_phase1_reproduction/              # Phases 1B, 1C, 1D, 1E, 1E-R outputs & figures
│   ├── 02_phase2_transfer/                  # Phase 2A synthetic/wav and Phase 2B multi-batches
│   ├── 03_geometry_opportunity_gate_a/      # E6 ledgers, heldout grid results, LaTeX tables, figures A1-A3
│   ├── 04_neutral_mode_exactness_audit/     # Tolerance sweeps, top eigenvalues, solver stability
│   ├── 05_real_audio_basin_transfer/        # 202-file outputs, 4,680-run basin logs, horizon ordering
│   ├── 06_multi_horizon_online_adaptation/  # Maturation, scale, 12 iteration traces, C1 canonical, C2, C4
│   ├── 07_computational_cost_microbench/    # C3 runtime provenance, cost summary, crosscheck audit
│   └── figures/                             # Certified publication Figures B1 through B5
│
├── tests/                     # 8 unit test suites (15 tests, passing in ~0.2s)
├── docs/                      # 38 research markdown reports categorized across 7 phases
├── run_tests.py               # One-line unit test runner
├── pyproject.toml             # Package configuration
├── requirements.txt           # Python dependencies
└── .gitignore                 # Standardized repository ignore rules
```

---

## 2. Environment Setup

### 2.1 Clone and Install
```bash
# Navigate to the repository root
cd GeoAGLA_Consolidated

# Create and activate a Python virtual environment (Python 3.10+)
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Install the geometry_gla package in editable mode
pip install -e .
```

### 2.2 Data Path Configuration
By default, all scripts locate audio files under the local directory `data/audio_samples/`. If your audio files (e.g. the full MUSAN corpus) are stored elsewhere, set the `DATA_PATH` environment variable:

```bash
# On Linux / macOS / Bash:
export DATA_PATH="YOUR_DATA_PATH"

# On Windows PowerShell:
$env:DATA_PATH="YOUR_DATA_PATH"

# On Windows CMD:
set DATA_PATH=YOUR_DATA_PATH
```

---

## 3. Step-by-Step Instructions: Running Each Experiment

Every script in `experiments/` can be executed directly as a standalone program from the repository root.

### Experiment 01: Linear Modal Dynamics & Spectral Analysis (Phase 1B)
**Scientific Objective**: Verify linearization of the GLA operator around stationary points, establish that the leading neutral mode corresponds identically to $\lambda_1 = 1$ (phase gauge symmetry), and prove that the sub-dominant mode $\lambda_2$ governs asymptotic local contraction.

1. **Stationary Point Linearization**:
   ```bash
   python experiments/01_linear_modal_dynamics/01_s0_linear_modal_dynamics.py
   ```
   *Expected Output*: Prints analytical vs observed local contraction rates across $\lambda \in [0.2, 0.95]$ with absolute errors $< 0.012$.

2. **Spectral Correspondence to Subspace Angles**:
   ```bash
   python experiments/01_linear_modal_dynamics/02_h1_geometry_spectral_correspondence.py
   ```
   *Expected Output*: Exports `results/01_phase1_reproduction/phase1b/h1_results.json` showing relative spectral error $\approx 6.9 \times 10^{-16}$.

3. **Oracle Local Rate Prediction**:
   ```bash
   python experiments/01_linear_modal_dynamics/03_h2_oracle_rate_prediction.py
   ```
   *Expected Output*: Exports `results/01_phase1_reproduction/phase1b/h2_results.json` verifying $q_{\rm Oracle} \le q_{\rm FGLA} < q_{\rm GLA}$.

---

### Experiment 02: Controlled Local Contraction Rates (Phase 1C)
**Scientific Objective**: Evaluate local convergence rates across a systematic 2D grid of STFT parameters (redundancy $a/M$, window lengths $W$, and hop sizes), confirming that the spectral gap $\Delta = 1 - \lambda_2$ controls empirical convergence.

1. **Multi-STFT Grid Sweep**:
   ```bash
   python experiments/02_controlled_local_rates/01_controlled_multi_stft_grid_sweep.py
   ```
   *Inputs*: `configs/phase1c_grid.json`  
   *Outputs*: `results/01_phase1_reproduction/phase1c/h1_multi.csv` and `h2_multi.csv`.

---

### Experiment 03: Geometry Opportunity Gate A & Heldout Grid (E6)
**Scientific Objective**: Execute the Gate A heldout protocol to evaluate whether trajectory geometry provides meaningful optimization opportunity $\Delta_{\rm oracle} = q_{\rm FGLA} - q^\star > 0$, and generate publication LaTeX summary tables.

1. **Build the E6 Case Ledger**:
   ```bash
   python experiments/03_geometry_opportunity_gate_a/01_build_e6_ledger.py
   ```
   *Outputs*: Generates `results/03_geometry_opportunity_gate_a/e6_case_ledger.csv`.

2. **Analyze Geometry Opportunity**:
   ```bash
   python experiments/03_geometry_opportunity_gate_a/02_analyze_geometry_opportunity.py
   ```
   *Outputs*: Computes rank correlation between $\Delta_{\rm oracle}$ and geometric gap parameters.

3. **Freeze the Heldout Grid**:
   ```bash
   python experiments/03_geometry_opportunity_gate_a/03_freeze_heldout_grid.py
   ```
   *Outputs*: Creates frozen hash-verified manifest `configs/e6_heldout_manifest_frozen.json`.

4. **Run Heldout Grid Experiments**:
   ```bash
   python experiments/03_geometry_opportunity_gate_a/04_run_heldout_experiments.py
   ```
   *Outputs*: Executes all heldout cases, writing `e6_heldout_ledger.csv`.

5. **Validate Integrity & Assertions**:
   ```bash
   python experiments/03_geometry_opportunity_gate_a/05_validate_results.py
   ```
   *Expected Output*: `[OK] All integrity checks passed.`

6. **Generate LaTeX Publication Tables**:
   ```bash
   python experiments/03_geometry_opportunity_gate_a/06_make_tables.py
   ```
   *Outputs*: `table_e6_summary.tex` and `table_e6_summary.csv`.

---

### Experiment 04: Neutral Mode Exactness Audit
**Scientific Objective**: Audit solver stability and confirm that the leading eigenvalue is numerically and identically $1.0$ (gauge invariance) across speech, music, and noise audio waveforms.

1. **Run Full Neutral Mode Audit**:
   ```bash
   python experiments/04_neutral_mode_exactness_audit/01_run_neutral_mode_audit.py
   ```
   *Inputs*: Audio samples in `data/audio_samples/` (or `$env:DATA_PATH`).  
   *Outputs*: Writes `results/04_neutral_mode_exactness_audit/`:
   - `neutral_tolerance_sweep.csv`
   - `top_eigenvalues.csv`
   - `solver_stability.csv`
   - `phase_alignment.csv`

---

### Experiment 05: Real Audio Basin Transfer Experiments
**Scientific Objective**: Measure the empirical basin of attraction on real speech, music, and noise waveforms under initial phase perturbations, and evaluate large-scale basin robustness across 4,680 runs.

1. **Synthetic Signal Transfer**:
   ```bash
   python experiments/05_real_audio_basin_transfer/01_phase2a_synthetic_transfer.py
   ```

2. **Real Audio Waveform Transfer**:
   ```bash
   python experiments/05_real_audio_basin_transfer/02_phase2a_wav_transfer.py
   ```

3. **Real Audio Basin Robustness Sweep**:
   ```bash
   python experiments/05_real_audio_basin_transfer/03_phase2b_real_audio_basin_sweep.py
   ```
   *Outputs*: Generates basin profiles and initialization distance curves.

4. **Multi-Sample Real Audio Validation**:
   ```bash
   python experiments/05_real_audio_basin_transfer/04_real_audio_multi_sample_validation.py
   ```
   *Outputs*: Validates cross-category convergence behaviors across diverse acoustic sources.

---

### Experiment 06: Multi-Horizon Online Adaptation & Scientific Audit Pipeline
**Scientific Objective**: Characterize the online Ritz estimator maturation delay ($m^\star \approx 10\dots 15$), classify failure modes across multi-horizon evaluations ($H \in \{30, 60, 120, 200, 360\}$), and perform the canonical Tasks C1–C4 audit.

1. **Estimator Maturation Sweep**:
   ```bash
   python experiments/06_multi_horizon_online_adaptation/04_estimator_maturation_sweep.py
   ```
   *Outputs*: Maturation ledger and trajectory traces in `results/06_multi_horizon_online_adaptation/`.

2. **Multi-Horizon & Failure Taxonomy Evaluation**:
   ```bash
   python experiments/06_multi_horizon_online_adaptation/05_multi_horizon_and_failure_taxonomy.py
   ```
   *Outputs*: Classifies failure cases into maturation delay, premature stagnation, and horizon cutoff.

3. **Signal Scale Invariance Validation**:
   ```bash
   python experiments/06_multi_horizon_online_adaptation/06_signal_scale_validation.py
   ```
   *Outputs*: Confirms invariance of the algorithm across dynamic ranges $[10^{-3}, 10^3]$.

4. **Task C1 — Canonical Capture Ratio Audit ($R_{\rm capture}$)**:
   ```bash
   python experiments/06_multi_horizon_online_adaptation/07_c1_canonical_capture_ratio_audit.py
   ```
   *Inputs*: 15 canonical configurations across 4 horizons ($H=60, 120, 180, 360$, total 60 runs).  
   *Condition*: Evaluates exact criterion $q_{\rm Online} < q_{\rm FGLA}$.  
   *Outputs*: `C1_capture_ratio_audit.csv`, `C1_capture_ratio_summary.json`, `C1_capture_ratio_audit.md`.

5. **Task C2 — Signal Scale Censoring Check**:
   ```bash
   python experiments/06_multi_horizon_online_adaptation/08_c2_signal_scale_censoring.py
   ```
   *Outputs*: `C2_signal_scale_censoring.csv`.

6. **Task C4 — Claim Discipline Checker**:
   ```bash
   python experiments/06_multi_horizon_online_adaptation/09_c4_claim_discipline_checker.py
   ```
   *Expected Output*: Verifies that manuscript claims strictly adhere to empirical boundaries.

7. **Packaging & Freeze Candidate Generation**:
   ```bash
   python experiments/06_multi_horizon_online_adaptation/10_package_and_report.py
   ```

---

### Experiment 07: Computational Cost & Isolated Microbenchmarking
**Scientific Objective**: Quantify the algorithmic runtime overhead of the passive Rayleigh-Ritz eigensolver and decouple unisolated operating-system CLI load from the true $O(m^2)$ algebraic cost.

1. **Full Pipeline Cost & Crosscheck Timing**:
   ```bash
   python experiments/07_computational_cost_microbench/01_computational_cost_and_crosscheck.py
   ```
   *Outputs*: Measures end-to-end execution time across full iterations.

2. **Runtime Provenance & Profiling**:
   ```bash
   python experiments/07_computational_cost_microbench/02_runtime_provenance_and_profiling.py
   ```
   *Outputs*: Generates `C3_runtime_provenance.csv` and `C3_runtime_summary.json`.

3. **Isolated Passive Ritz Eigensolver Microbenchmark**:
   ```bash
   python experiments/07_computational_cost_microbench/03_isolated_ritz_microbench.py
   ```
   *Expected Output*:
   ```text
   =================================================================
   ISOLATED PASSIVE RITZ EIGENSOLVER MICROBENCHMARK
   =================================================================
   Memory dimension (p):            3 (yielding 3x3 generalized eigenproblem)
   Block update interval (K):       8 iterations
   Number of timing trials:         1000
   Execution time per update:       ~0.0381 ms/update
   Amortized cost per iteration:    ~0.0048 ms/iteration
   Relative overhead (vs ~1.69 ms): < 0.3%
   =================================================================
   ```

---

## 4. Running the Unit Test Suite

Execute the complete test suite with a single command:

```bash
python run_tests.py
```

The test runner discovers and executes all 15 tests across 8 test suites:
- `test_geometry.py`: Verifies Jacobian principal angle spectrum matches canonical operators.
- `test_minimax.py`: Validates Chebyshev equioscillation minimax polynomial properties.
- `test_phase1c_grid.py`: Validates STFT window definitions and grid parameter bounds.
- `test_phase1d_ritz.py`: Tests passive Ritz eigensolver accuracy on invariant subspaces.
- `test_phase1e_safeguard.py`: Tests checkpoint merit function and residual fallback triggers.
- `test_phase1er_policy.py`: Verifies switching horizon policies and safe GLA updates.
- `test_phase2a_fft.py`: Tests FFT operator isometry and adjoint projection properties.
- `test_projector.py`: Confirms range projectors are orthogonal projection operators ($P^2 = P$).

*Expected Execution Time*: $< 0.3$ seconds (`15/15 tests OK`).

---

## 5. Standalone Jupyter & Kaggle Notebooks

All notebooks in `notebooks/` are completely standalone and can be executed either locally or on Kaggle/Google Colab:

| Notebook | Topic & Primary Research Content |
| :--- | :--- |
| **`01_Linear_Modal_and_Spectrum_Reproduction.ipynb`** | S0 linear dynamics, H1/H2 spectral correspondence, leading mode identification. |
| **`02_Online_Estimator_Maturation_Reproduction.ipynb`** | Online Ritz estimator tracking, memory depth $m$, and maturation curves. |
| **`03_Gate_A_Heldout_Geometry_Opportunity.ipynb`** | Gate A heldout grid validation, E6 case ledger, and $\Delta_{\rm oracle}$ correlation. |
| **`04_Safeguard_and_RealAudio_Basin_Exploration.ipynb`** | Merit safeguard logic, fallback triggers, and initial basin exploration. |
| **`05_RealAudio_Basin_Transfer_and_Horizon_Audit.ipynb`** | Real audio basin transfer across speech, music, noise, and horizon audits. |
| **`06_Online_MultiHorizon_and_Claim_Correction_Audit.ipynb`** | Multi-horizon runs ($H \in \{30, 60, 120, 200, 360\}$), Tasks C1–C4 claim audits. |
| **`07_Final_Scientific_Freeze_Reconciliation_Standalone.ipynb`** | Complete standalone reconciliation, canonical 60-eval C1 audit, and freeze sign-off. |

---

## 6. Core Scientific Findings & Claim Discipline

1. **Geometry Determines Acceleration**: The local asymptotic contraction rate of momentum acceleration in phase retrieval is governed by the active spectral radius $\lambda_+$ of the gauge-invariant projection operator.
2. **Online Geometry Adaptation**: The passive $3 \times 3$ Ritz estimator extracts trajectory-active geometry on the fly without extra operator evaluations. The true algorithmic overhead of the $3 \times 3$ eigensolver is **$0.0381\text{ ms/update}$** ($0.0048\text{ ms/iteration}$, $< 0.3\%$ relative to the baseline $1.691\text{ ms}$ step).
3. **Basin Robustness vs Paired Local Rate Distinction**:
   $$\boxed{\textbf{Basin Robustness} \neq \textbf{Paired Local-Rate Superiority}}$$
   - **Basin Robustness**: Online adaptation increases empirical convergence success across 4,680 random initializations on real speech by **$20.07$ percentage points** ($74.94\%$ vs $54.87\%$) with **0 safeguard failures**.
   - **Local Rate**: In short horizons ($H=60$), Online achieves an $86.7\%$ win rate; over extended horizons ($H \ge 120$), fixed-momentum FGLA remains highly competitive.
4. **Finite-Horizon $R_{\rm capture}$ Interpretation**:
   Values of $R_{\rm capture} > 1$ in finite-horizon fitted-rate comparisons reflect transient regression fits and negligible Oracle headroom ($\Delta_{\rm oracle} < 10^{-4}$), not Online exceeding the theoretical infinite-horizon Oracle optimum.

---

## 7. Scientific Freeze Status
All experimental ledgers, empirical values, figures, and code are strictly frozen. Certified under [docs/06_final_scientific_freeze/Final_Freeze_Reconciliation_SignOff.md](docs/06_final_scientific_freeze/Final_Freeze_Reconciliation_SignOff.md).
