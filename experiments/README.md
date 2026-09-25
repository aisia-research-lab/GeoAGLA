# Experiments Architecture & Directory Mapping (S0, E1–E7, E10)

This directory organizes all experimental modules for **GeoAGLA** according to the formal **ICLR 2027 Experimental Protocol**:
**S0, E1, E2, E3, E4, E5, E6, E7, E10**.

---

## 1. Experiment Mapping & Canonical Catalog

| ID | Title | Research Objective | Key Implementation Modules | One-Line CLI Reproducer |
| :--- | :--- | :--- | :--- | :--- |
| **S0** | **Linear Modal Dynamics Smoke Test** | Verify 2-mode scalar recurrence and spectral radius convergence rate $\rho = \lambda_+$ on synthetic signals. | `01_linear_modal_dynamics/01_s0_linear_modal_dynamics.py` | `python reproduce/run_s0_linear_modal.py` |
| **E1** | **Geometry–Spectrum Correspondence** | Validate exact identity between STFT tangent angles $\cos^2\theta$ and Jacobian spectrum $\lambda_\pm = \frac{1 \pm \cos\theta}{2}$. | `01_linear_modal_dynamics/02_h1_geometry_spectral_correspondence.py`<br>`02_controlled_local_rates/01_controlled_multi_stft_grid_sweep.py` | `python reproduce/run_e1_geometry_spectrum.py` |
| **E2** | **Exact Local Rate Prediction** | Verify local contraction hierarchy: GLA ($\lambda_+$) < FGLA ($\sqrt{\lambda_+}$) < Oracle ($\rho^*$) across Hann/Gaussian grids. | `01_linear_modal_dynamics/03_h2_oracle_rate_prediction.py`<br>`02_controlled_local_rates/01_controlled_multi_stft_grid_sweep.py` | `python reproduce/run_e2_oracle_rates.py` |
| **E3** | **Passive Rayleigh–Ritz Estimation** | Track dominant eigenvalue $\lambda_+$ online via passive Krylov projections ($p \in \{1, 3, 5\}$) without active perturbation. | `06_multi_horizon_online_adaptation/01_phase1d_online_edge_tracking.py` | `python reproduce/run_e3_ritz_estimator.py` |
| **E4** | **Online Dynamics & Horizon Adaptation** | Test adaptive Chebyshev acceleration, safeguarded fallback, horizon policies ($H \in \{30, 60, 120, 200, 360\}$), and long-horizon audit. | `06_multi_horizon_online_adaptation/02_phase1e_safeguarded_acceleration.py`<br>`03_phase1er_repair_and_horizon_policy.py`<br>`07_c1_canonical_capture_ratio_audit.py`<br>`11_final_patch_horizon_audit.py` | `python reproduce/run_e4_online_horizon.py` |
| **E5** | **Real-Audio Basin Transfer & Robustness** | Real-audio phase retrieval on MUSAN (4,680+ runs, random vs zero init, $+20$ pp basin gain over FGLA, checkpointed batch runner). | `05_real_audio_basin_transfer/01_phase2a_synthetic_transfer.py`<br>`02_phase2a_wav_transfer.py`<br>`03_phase2b_real_audio_basin_sweep.py`<br>`05_run_phase2b_checkpointed.py` | `python reproduce/run_e5_real_audio_basin.py` |
| **E6** | **Geometry-Opportunity Gate A Suite** | Quantify geometry opportunity gap across STFT configurations, evaluate 36 held-out cases, and audit neutral mode exactness. | `03_geometry_opportunity_gate_a/01_build_e6_ledger.py` .. `08_run_neutral_mode_audit.py`<br>`04_neutral_mode_exactness_audit/` | `python reproduce/run_e6_gate_a_heldout.py` |
| **E7** | **Computational Cost Microbenchmarking** | Benchmark per-iteration FLOPs and wall-clock times comparing isolated Rayleigh–Ritz step vs FFT projections and standard GLA. | `07_computational_cost_microbench/01_computational_cost_and_crosscheck.py`<br>`02_runtime_provenance_and_profiling.py`<br>`03_isolated_ritz_microbench.py` | `python reproduce/run_e7_microbench.py` |
| **E10** | **Robustness Mechanism Ablation Suite** | Rigorous ablation suite decomposing the 6 architectural mechanisms of GeoAGLA, locked test, canonical test, and forensic bitwise archive. | `08_e10_robustness_mechanism_ablation/01_run_e10_ablation.py`<br>`03_run_e10r_locked.py`<br>`04_run_e10r2_canonical.py`<br>`11_e10r2f_final_archive.py` | `python reproduce/run_e10_mechanism_ablation.py` |

---

## 2. Directory Structure Details

### [`01_linear_modal_dynamics/`](01_linear_modal_dynamics) — Experiments S0, E1, E2
- **`01_s0_linear_modal_dynamics.py`**: Validates the 2-mode scalar recurrence and asymptotic rate $\rho = \lambda_+$.
- **`02_h1_geometry_spectral_correspondence.py`**: Validates the direct link between tangent principal angles and spectrum.
- **`03_h2_oracle_rate_prediction.py`**: Compares empirical contraction factors against the Oracle minimax rate.

### [`02_controlled_local_rates/`](02_controlled_local_rates) — Experiments E1 & E2
- **`01_controlled_multi_stft_grid_sweep.py`**: Systematic parameter grid sweep over signal lengths ($N \in \{16, 24, 32\}$), window lengths ($W$), hop sizes, and window types (Hann, Gaussian).

### [`03_geometry_opportunity_gate_a/`](03_geometry_opportunity_gate_a) — Experiment E6
- **`01_build_e6_ledger.py`** to **`08_run_neutral_mode_audit.py`**: Complete 8-step pipeline constructing the 90-case canonical ledger, analyzing opportunity headroom, freezing the 36-case held-out grid, running generalization tests, and producing publication LaTeX tables.

### [`04_neutral_mode_exactness_audit/`](04_neutral_mode_exactness_audit) — Experiment E6 Diagnostic
- **`01_neutral_mode_exactness_audit.py`**: Diagnostic evaluation of global phase gauge invariance and null-space symmetry exactness under small perturbation regimes.

### [`05_real_audio_basin_transfer/`](05_real_audio_basin_transfer) — Experiment E5
- **`01_phase2a_synthetic_transfer.py`**: Operator isometry and FFT equivalence on deterministic signals.
- **`02_phase2a_wav_transfer.py`**: Rapid pilot evaluation on real audio waveforms.
- **`03_phase2b_real_audio_basin_sweep.py`**: Full real-audio basin sweep across perturbation levels ($10^{-3}$ to $1.0$).
- **`05_run_phase2b_checkpointed.py`**: Fault-tolerant batch runner supporting pause/resume and hard execution deadlines.

### [`06_multi_horizon_online_adaptation/`](06_multi_horizon_online_adaptation) — Experiments E3 & E4
- **`01_phase1d_online_edge_tracking.py`**: Online edge estimation via passive Ritz projections.
- **`02_phase1e_safeguarded_acceleration.py`**: Monotonic safeguard fallback evaluation.
- **`03_phase1er_repair_and_horizon_policy.py`**: Horizon switching policies and envelope damping.
- **`07_c1_canonical_capture_ratio_audit.py`**: Canonical 60-evaluation multi-horizon ledger audit across $H \in \{60, 120, 180, 360\}$.
- **`11_final_patch_horizon_audit.py`**: Final real-audio patch of near-neutral cases and 29-case long-horizon audit ($H \in \{360, 720, 1440\}$).
- **`12_final_freeze_reconciliation.py`**: Final scientific freeze reconciliation and 16-item diagnostic checklist verification.

### [`07_computational_cost_microbench/`](07_computational_cost_microbench) — Experiment E7
- **`01_computational_cost_and_crosscheck.py`**: Per-iteration operations breakdown (FLOP count and wall-clock time).
- **`02_runtime_provenance_and_profiling.py`**: Empirical runtime profiling and complexity scaling.
- **`03_isolated_ritz_microbench.py`**: Microbenchmark of the isolated $3 \times 3$ Ritz eigensolver (~0.05 ms amortized overhead, ~3.1% of GLA step).

### [`08_e10_robustness_mechanism_ablation/`](08_e10_robustness_mechanism_ablation) — Experiment E10
- **`01_run_e10_ablation.py`**: 6-way paired ablation across real-audio recordings.
- **`03_run_e10r_locked.py`**: Locked 395-geometry evaluation with fixed historical initialization.
- **`04_run_e10r2_canonical.py`**: Canonical 202-file baseline test with $10^{-5}$ threshold.
- **`11_e10r2f_final_archive.py`**: Bitwise cryptographic packaging and forensic closure verification (SHA-256 verified, 0 failures).

---

## 3. End-to-End Master Execution

To run all experiments sequentially in an automated pipeline:
```bash
python reproduce/run_all_experiments.py
```

To re-generate all publication figures (Panels A–D) and verify the 20/20 numerical manuscript claims:
```bash
python reproduce/run_verification_and_figures.py
```
