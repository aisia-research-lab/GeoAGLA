# GeoAGLA: Geometry-Adaptive Acceleration in Phase Retrieval
## ICLR 2027 Research Repository (Fully Reproducible Edition)

This repository unifies all experimental code, mathematical specifications, empirical result ledgers, standalone notebooks, unit tests, automated pipelines, and comprehensive documentation for the ICLR 2027 submission:
**"Geometry Determines Acceleration in Phase Retrieval"**.

All code and results from the initial baseline reproduction (Phases 1 & 2), through Next Experiments (Gate A, neutral mode exactness audit, real audio 202-file & 4,680-run basin transfer), to the final scientific freeze (Tasks C1–C4, canonical 60-eval C1 audit, computational microbenchmarks) are fully integrated, standardized, and self-contained.

---

## 1. Repository Architecture

```text
GeoAGLA/
│
├── src/geometry_gla/          # Core modular Python package
│   ├── algorithms/            # GLA, FGLA, AGLA, Minimax Oracle, Safe Online Policy
│   ├── estimators/            # Rayleigh-Ritz passive eigensolvers, power iteration
│   ├── geometry/              # Subspace principal angles, Jacobian, realification
│   ├── metrics/               # Spectral contraction rates, phase-gauge orbit distance
│   ├── operators/             # STFT / iSTFT, periodic transforms, range projectors
│   ├── safeguards/            # Fixed checkpoint merit functions & fallback triggers
│   └── signals.py             # Deterministic synthetic signals, audio loading & excerpting
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
├── reproduce/                 # One-command phase reproduction scripts (Phase 1B to 2B)
│   ├── run_phase1b.py         # Phase 1B: S0 + H1 + H2
│   ├── run_phase1c.py         # Phase 1C: Multi-STFT grid sweep
│   ├── run_phase1d.py         # Phase 1D: Ritz online dominant-edge tracking
│   ├── run_phase1e.py         # Phase 1E: Safeguarded online acceleration
│   ├── run_phase1er.py        # Phase 1E-R: Horizon policy & repair
│   ├── run_phase2a.py         # Phase 2A: Synthetic signal-scale transfer
│   ├── run_phase2a_real_audio.py # Phase 2A: Real audio wav transfer
│   ├── run_phase2b.py         # Phase 2B: Real-audio basin sweep
│   ├── run_phase2b_smoke.py   # Phase 2B: Fast smoke test (no external audio needed)
│   ├── run_phase2b_checkpointed.py # Phase 2B: Checkpointed/resumable batch runner
│   └── README.md              # Documentation for reproduce/ package
│
├── experiments/               # Modular standalone experiment runners (01 to 07)
│   ├── 01_linear_modal_dynamics/            # Linear modal dynamics & spectral correspondence
│   ├── 02_controlled_local_rates/           # Controlled multi-STFT grid sweeps & window audits
│   ├── 03_geometry_opportunity_gate_a/      # Gate A heldout evaluation, E6 ledgers, LaTeX tables
│   ├── 04_neutral_mode_exactness_audit/     # Leading neutral mode gauge symmetry exactness audits
│   ├── 05_real_audio_basin_transfer/        # Real audio basin sweeps, 202-file & 4,680-run evaluations
│   │   ├── 01_phase2a_synthetic_transfer.py
│   │   ├── 02_phase2a_wav_transfer.py
│   │   ├── 03_phase2b_real_audio_basin_sweep.py
│   │   ├── 04_real_audio_multi_sample_validation.py
│   │   └── 05_run_phase2b_checkpointed.py   # Checkpointed batch runner with deadline control
│   ├── 06_multi_horizon_online_adaptation/  # Maturation sweeps, failure taxonomy, Tasks C1-C4
│   ├── 07_computational_cost_microbench/    # Unisolated vs isolated Ritz microbenchmarking
│   └── README.md                            # Comprehensive experiment catalog
│
├── scripts/                   # Utility scripts & automated execution pipelines
│   ├── data/                  # Dataset preparation and sampling
│   │   ├── sample_musan_subset.py # Stratified random sampling of MUSAN audio
│   │   └── README.md
│   ├── runners/               # End-to-end automation pipelines
│   │   ├── run_full_pipeline.py # Full the pipeline execution pipeline (E3 to E5b)
│   │   └── README.md
│   └── figures/               # Publication figure generation scripts
│
├── notebooks/                 # Standalone Jupyter & Kaggle notebooks
│   ├── 01_Linear_Modal_and_Spectrum_Reproduction.ipynb
│   ├── 02_Online_Estimator_Maturation_Reproduction.ipynb
│   ├── 03_Gate_A_Heldout_Geometry_Opportunity.ipynb
│   ├── 04_Safeguard_and_RealAudio_Basin_Exploration.ipynb
│   ├── 05_RealAudio_Basin_Transfer_and_Horizon_Audit.ipynb
│   ├── 06_Online_MultiHorizon_and_Claim_Correction_Audit.ipynb
│   ├── 07_Final_Scientific_Freeze_Reconciliation_Standalone.ipynb
│   └── kaggle_execution/      # Dedicated Kaggle execution notebooks
│       ├── 25-subset-musan.ipynb
│       ├── musan_even_pipeline.ipynb      # Even-10% MUSAN pipeline
│       └── musan_odd_pipeline.ipynb # Odd-10% MUSAN pipeline
│
├── results/                   # Complete empirical result ledgers (202+ verified result files)
│   ├── 01_phase1_reproduction/              # Phases 1B, 1C, 1D, 1E, 1E-R outputs & figures
│   ├── 02_phase2_transfer/                  # Phase 2A synthetic/wav and Phase 2B multi-batches
│   ├── 03_geometry_opportunity_gate_a/      # E6 ledgers, heldout grid results, LaTeX tables
│   ├── 04_neutral_mode_exactness_audit/     # Tolerance sweeps, top eigenvalues, solver stability
│   ├── 05_real_audio_basin_transfer/        # 202-file outputs, 4,680-run basin logs, horizon ordering
│   ├── 06_multi_horizon_online_adaptation/  # Maturation, scale, 12 iteration traces, C1 canonical, C2, C4
│   ├── 07_computational_cost_microbench/    # C3 runtime provenance, cost summary, crosscheck audit
│   └── figures/                             # Certified publication Figures B1 through B5
│
├── tests/                     # 9 unit test suites (17 tests, passing in ~1.1s)
│   ├── test_geometry.py       # Jacobian principal angle spectrum
│   ├── test_minimax.py        # Chebyshev equioscillation minimax polynomial
│   ├── test_phase1c_grid.py   # STFT window definitions and grid parameter bounds
│   ├── test_phase1d_ritz.py   # Passive Ritz eigensolver accuracy
│   ├── test_phase1e_safeguard.py # Checkpoint merit function and fallback triggers
│   ├── test_phase1er_policy.py   # Switching horizon policies
│   ├── test_phase2a_fft.py    # FFT operator isometry and adjoint projection
│   ├── test_phase2b_audio.py  # Audio loading, resampling, and RMS excerpting
│   └── test_projector.py      # Range projector orthogonality (P^2 = P)
│
├── docs/                      # 38+ research markdown reports categorized across 7 phases
│   ├── 00_project_overview_and_guides/      # Student guides & ICLR design
│   ├── 01_phase1_phase2_reproduction/       # Phase 1/2 reports & historical guides
│   │   └── phase_reports_and_guides/        # Original Phase-1B to 2B reproduction guides & verification reports
│   ├── 02_geometry_opportunity_gate_a/
│   ├── 03_neutral_mode_exactness_audit/
│   ├── 04_real_audio_basin_transfer/
│   ├── 05_online_adaptation_audits/
│   ├── 06_final_scientific_freeze/
│   └── README.md                            # Documentation index
│
├── run_tests.py               # One-line unit test runner (compatible with unittest & pytest)
├── pyproject.toml             # Package configuration
├── requirements.txt           # Python dependencies
└── .gitignore                 # Standardized repository ignore rules
```

---

## 2. Environment Setup

### 2.1 Clone and Install
```bash
# Navigate to the repository root
cd GeoAGLA

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

### 2.2 Verify Installation
Run the complete unit test suite (17 tests, 0 failures):
```bash
python run_tests.py
```

### 2.3 Data Path Configuration
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

## 3. Quickstart: Reproducing Experiments (Multiple Execution Paths)

Depending on your objective and computational environment, you can reproduce the results via any of the following paths:

### Path A: One-Command Phase Runners (Recommended for Verification)
The `reproduce/` package provides simple one-line commands matching each phase of the project:
```bash
# 1. Phase 1B (Linear modal dynamics, geometry-spectrum correspondence, Oracle rate):
python -m reproduce.run_phase1b

# 2. Phase 1C (Multi-STFT grid sweep):
python -m reproduce.run_phase1c

# 3. Phase 1D (Online Ritz dominant-edge tracking):
python -m reproduce.run_phase1d

# 4. Phase 1E-R (Horizon policy & repair):
python -m reproduce.run_phase1er

# 5. Phase 2A (Controlled synthetic signal-scale transfer):
python -m reproduce.run_phase2a

# 6. Phase 2B Smoke Test (Fast ~15s run on synthetic dual-signal, no external audio required):
python -m reproduce.run_phase2b_smoke

# 7. Phase 2B Checkpointed (Real-audio basin transfer with resume & deadline control):
python -m reproduce.run_phase2b_checkpointed --audio-dir data/audio_samples --batch-size 2
```

### Path B: Automated Full Pipeline (E3 to E5b)
For complete end-to-end automated execution without manual notebook intervention:
```bash
python scripts/runners/run_full_pipeline.py \
    --audio-dir data/audio_samples \
    --out-dir results/pipeline_runs \
    --run-pilot --batch-size 2 --zip-bundle
```

### Path C: Dataset Preparation (MUSAN Subsampling)
To extract a stratified, reproducible subset of the MUSAN dataset (e.g. 25% or 10%):
```bash
python scripts/data/sample_musan_subset.py \
    --src-root /path/to/musan \
    --dst-root data/musan_25 \
    --ratio 0.25 --seed 42 --zip-path data/musan_25.zip
```

### Path D: Checkpointed Batch Execution for Limited-Time Environments (Kaggle / Colab)
When running large sweeps on cloud environments subject to timeout (e.g. Kaggle 12h limit):
```bash
python experiments/05_real_audio_basin_transfer/05_run_phase2b_checkpointed.py \
    --audio-dir /path/to/musan_subset \
    --batch-size 2 \
    --time-budget-sec 36000 \
    --out results/phase2b_checkpointed
```
*If interrupted, simply re-run the exact same command. Completed batches are automatically detected and skipped.*

---

## 4. Detailed Modular Experiment Catalog

Every script in `experiments/` can be executed directly as a standalone program:

### Experiment 01: Linear Modal Dynamics & Spectral Analysis (Phase 1B)
- `python experiments/01_linear_modal_dynamics/01_s0_linear_modal_dynamics.py`
- `python experiments/01_linear_modal_dynamics/02_h1_geometry_spectral_correspondence.py`
- `python experiments/01_linear_modal_dynamics/03_h2_oracle_rate_prediction.py`

### Experiment 02: Controlled Local Contraction Rates (Phase 1C)
- `python experiments/02_controlled_local_rates/01_controlled_multi_stft_grid_sweep.py`

### Experiment 03: Geometry Opportunity Gate A & Heldout Grid (E6)
- `python experiments/03_geometry_opportunity_gate_a/01_build_e6_ledger.py`
- `python experiments/03_geometry_opportunity_gate_a/02_analyze_geometry_opportunity.py`
- `python experiments/03_geometry_opportunity_gate_a/03_freeze_heldout_grid.py`
- `python experiments/03_geometry_opportunity_gate_a/04_run_heldout_experiments.py`
- `python experiments/03_geometry_opportunity_gate_a/05_validate_results.py`
- `python experiments/03_geometry_opportunity_gate_a/06_make_tables.py`

### Experiment 04: Neutral Mode Exactness Audit
- `python experiments/04_neutral_mode_exactness_audit/01_run_neutral_mode_audit.py`

### Experiment 05: Real Audio Basin Transfer Experiments (Phase 2A & 2B)
- `python experiments/05_real_audio_basin_transfer/01_phase2a_synthetic_transfer.py`
- `python experiments/05_real_audio_basin_transfer/02_phase2a_wav_transfer.py`
- `python experiments/05_real_audio_basin_transfer/03_phase2b_real_audio_basin_sweep.py`
- `python experiments/05_real_audio_basin_transfer/04_real_audio_multi_sample_validation.py`
- `python experiments/05_real_audio_basin_transfer/05_run_phase2b_checkpointed.py`

### Experiment 06: Multi-Horizon Online Adaptation & Scientific Audit Pipeline
- `python experiments/06_multi_horizon_online_adaptation/01_phase1d_online_edge_tracking.py`
- `python experiments/06_multi_horizon_online_adaptation/02_phase1e_safeguarded_acceleration.py`
- `python experiments/06_multi_horizon_online_adaptation/03_phase1er_repair_and_horizon_policy.py`
- `python experiments/06_multi_horizon_online_adaptation/04_estimator_maturation_sweep.py`
- `python experiments/06_multi_horizon_online_adaptation/05_multi_horizon_and_failure_taxonomy.py`
- `python experiments/06_multi_horizon_online_adaptation/06_signal_scale_validation.py`
- `python experiments/06_multi_horizon_online_adaptation/07_c1_canonical_capture_ratio_audit.py`
- `python experiments/06_multi_horizon_online_adaptation/08_c2_signal_scale_censoring.py`
- `python experiments/06_multi_horizon_online_adaptation/09_c4_claim_discipline_checker.py`
- `python experiments/06_multi_horizon_online_adaptation/10_package_and_report.py`

### Experiment 07: Computational Cost & Isolated Microbenchmarking
- `python experiments/07_computational_cost_microbench/01_computational_cost_and_crosscheck.py`
- `python experiments/07_computational_cost_microbench/02_runtime_provenance_and_profiling.py`
- `python experiments/07_computational_cost_microbench/03_isolated_ritz_microbench.py`

---

## 5. Standalone Jupyter & Kaggle Notebooks

All notebooks in `notebooks/` can be executed locally or in cloud environments:

| Notebook | Topic & Primary Research Content |
| :--- | :--- |
| **`01_Linear_Modal_and_Spectrum_Reproduction.ipynb`** | S0 linear dynamics, H1/H2 spectral correspondence, leading mode identification. |
| **`02_Online_Estimator_Maturation_Reproduction.ipynb`** | Online Ritz estimator tracking, memory depth $m$, and maturation curves. |
| **`03_Gate_A_Heldout_Geometry_Opportunity.ipynb`** | Gate A heldout grid validation, E6 case ledger, and $\Delta_{
m oracle}$ correlation. |
| **`04_Safeguard_and_RealAudio_Basin_Exploration.ipynb`** | Merit safeguard logic, fallback triggers, and initial basin exploration. |
| **`05_RealAudio_Basin_Transfer_and_Horizon_Audit.ipynb`** | Real audio basin transfer across speech, music, noise, and horizon audits. |
| **`06_Online_MultiHorizon_and_Claim_Correction_Audit.ipynb`** | Multi-horizon runs ($H \in \{30, 60, 120, 200, 360\}$), Tasks C1–C4 claim audits. |
| **`07_Final_Scientific_Freeze_Reconciliation_Standalone.ipynb`** | Complete standalone reconciliation, canonical 60-eval C1 audit, and freeze sign-off. |
| **`kaggle_execution/25-subset-musan.ipynb`** | Kaggle audio subset extraction and manifest generation. |
| **`kaggle_execution/musan_even_pipeline.ipynb`** | the pipeline full pipeline on even-10% MUSAN subset. |
| **`kaggle_execution/musan_odd_pipeline.ipynb`** | the pipeline full pipeline on odd-10% MUSAN subset. |

---

## 6. Core Scientific Findings & Claim Discipline

1. **Geometry Determines Acceleration**: The local asymptotic contraction rate of momentum acceleration in phase retrieval is governed by the active spectral radius $\lambda_+$ of the gauge-invariant projection operator.
2. **Online Geometry Adaptation**: The passive $3 	imes 3$ Ritz estimator extracts trajectory-active geometry on the fly without extra operator evaluations. The true algorithmic overhead of the $3 	imes 3$ eigensolver is **$0.0381	ext{ ms/update}$** ($0.0048	ext{ ms/iteration}$, $< 0.3\%$ relative to the baseline $1.691	ext{ ms}$ step).
3. **Basin Robustness vs Paired Local Rate Distinction**:
   $$oxed{	extbf{Basin Robustness} 
eq 	extbf{Paired Local-Rate Superiority}}$$
   - **Basin Robustness**: Online adaptation increases empirical convergence success across 4,680 random initializations on real speech by **$20.07$ percentage points** ($74.94\%$ vs $54.87\%$) with **0 safeguard failures**.
   - **Local Rate**: In short horizons ($H=60$), Online achieves an $86.7\%$ win rate; over extended horizons ($H \ge 120$), fixed-momentum FGLA remains highly competitive.
4. **Finite-Horizon $R_{
m capture}$ Interpretation**:
   Values of $R_{
m capture} > 1$ in finite-horizon fitted-rate comparisons reflect transient regression fits and negligible Oracle headroom ($\Delta_{
m oracle} < 10^{-4}$), not Online exceeding the theoretical infinite-horizon Oracle optimum.

---

## 7. Scientific Freeze Status
All experimental ledgers, empirical values, figures, and code are strictly frozen. Certified under [docs/06_final_scientific_freeze/Final_Freeze_Reconciliation_SignOff.md](docs/06_final_scientific_freeze/Final_Freeze_Reconciliation_SignOff.md).
