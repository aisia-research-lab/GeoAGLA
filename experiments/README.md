# Experiments Suite

The `experiments/` directory organizes all experimental research modules of the GeoAGLA project into 7 structured research areas:

---

## Structure and Execution Guide

### [01. Linear Modal Dynamics](01_linear_modal_dynamics)
- **Objective:** Verify theoretical predictions G1--G3 on linear models and small STFT matrices.
- **Key Scripts:**
  - `01_s0_linear_modal_dynamics.py`: Fundamental linear modal dynamics.
  - `02_h1_geometry_spectral_correspondence.py`: Correspondence between principal angles and Jacobian spectrum.
  - `03_h2_oracle_rate_prediction.py`: Contraction rate prediction under known geometry.
- **Quick Runner:** `python -m reproduce.run_phase1b`

### [02. Controlled Local Rates](02_controlled_local_rates)
- **Objective:** Systematic multi-STFT grid sweep validating the acceleration hierarchy: GLA < FGLA < Geometry Oracle.
- **Key Script:** `01_controlled_multi_stft_grid_sweep.py`
- **Quick Runner:** `python -m reproduce.run_phase1c`

### [03. Geometry Opportunity (Gate A)](03_geometry_opportunity_gate_a)
- **Objective:** Gate A heldout evaluation testing whether trajectory geometry provides meaningful optimization opportunity.
- **Key Scripts:** `01_build_e6_ledger.py` through `08_run_neutral_mode_audit.py`.

### [04. Neutral Mode Exactness Audit](04_neutral_mode_exactness_audit)
- **Objective:** Numerical audit of solver stability, phase gauge invariance, and spectral isolation conditions.
- **Key Script:** `01_run_neutral_mode_audit.py`

### [05. Real Audio Basin Transfer](05_real_audio_basin_transfer)
- **Objective:** Empirical basin of attraction evaluations on synthetic signals and real-world audio waveforms (Phases 2A & 2B).
- **Key Scripts:**
  - `01_phase2a_synthetic_transfer.py`: Signal-scale transfer on synthetic signals.
  - `02_phase2a_wav_transfer.py`: Real-audio waveform transfer.
  - `03_phase2b_real_audio_basin_sweep.py`: Comprehensive real-audio basin sweep.
  - `04_real_audio_multi_sample_validation.py`: Multi-sample acoustic validation.
  - `05_run_phase2b_checkpointed.py`: Resumable batch runner with deadline enforcement.
- **Quick Runners:** `python -m reproduce.run_phase2a` or `python -m reproduce.run_phase2b_smoke`.

### [06. Multi-Horizon Online Adaptation](06_multi_horizon_online_adaptation)
- **Objective:** Evaluate online Ritz estimation dynamics, safeguard envelopes, and multi-horizon convergence.
- **Key Scripts:** `01_phase1d_online_edge_tracking.py` through `10_package_and_report.py`.
- **Quick Runners:** `python -m reproduce.run_phase1d` or `python -m reproduce.run_phase1er`.

### [07. Computational Cost Microbenchmarks](07_computational_cost_microbench)
- **Objective:** Quantify algorithmic runtime overhead, profiling execution latency, and microbenchmarking the Ritz eigensolver.
- **Key Scripts:** `01_computational_cost_and_crosscheck.py` through `03_isolated_ritz_microbench.py`.
