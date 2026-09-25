# GeoAGLA: Geometry-Adaptive Acceleration in Griffin–Lim Phase Retrieval
## ICLR 2027 Research Repository (Fully Reproducible Edition)

This repository unifies all experimental code, mathematical specifications, empirical result ledgers, standalone runners, unit tests, automated pipelines, and verification tools for the ICLR 2027 submission:  
**"Geometry Determines Local Acceleration in Griffin–Lim Phase Retrieval"**.

The repository integrates the full contributions of both theoretical geometry and online empirical adaptation:
- **Theoretical foundations**: Geometry–spectrum correspondence, local contraction rate bounds, and the exact Chebyshev minimax Oracle rate $\rho^*(\lambda_-, \lambda_+)$.
- **Algorithmic architecture**: Passive Rayleigh–Ritz dominant-edge tracking ($p \in \{1, 3, 5\}$), dynamic running envelope damping, and guaranteed monotonic safeguard fallback.
- **Empirical validation**: Controlled multi-STFT grid sweeps, Gate A held-out generalization, large-scale real-audio basin of attraction evaluations on the MUSAN corpus ($4{,}680 + 4{,}752$ runs), finite-horizon audits, and full robustness mechanism ablations (E10-R2F forensic closure).

---

## 1. Repository Architecture

```text
GeoAGLA/
│
├── src/geometry_gla/          # Core modular Python package
│   ├── algorithms/            # GLA, FGLA, AGLA, Minimax Oracle, Safe Online Policy, Online Ablation
│   ├── estimators/            # Rayleigh-Ritz passive Krylov eigensolvers, power iteration
│   ├── geometry/              # Subspace principal angles, Jacobian spectrum, realification
│   ├── metrics/               # Spectral contraction rates, phase-gauge orbit distance
│   ├── operators/             # STFT / iSTFT, periodic transforms, range projectors
│   ├── safeguards/            # Fixed checkpoint merit functions & fallback triggers
│   └── signals.py             # Deterministic synthetic signals, audio loading & excerpting
│
├── configs/                   # Frozen experimental configurations (JSON)
│   ├── e6_heldout_geometry.json
│   ├── e10_ablation.json      # E10 6-variant ablation specification
│   ├── phase1c_grid.json      # Controlled STFT parameter grid
│   └── phase2b_grid.json      # Large-scale real-audio basin sweep configuration
│
├── data/                      # Evaluation datasets & frozen benchmark caches
│   ├── audio_samples/         # Included sample audio waveforms (.wav)
│   ├── frozen/                # Frozen reference evaluation caches (h2_multi.json, horizon_audit.json)
│   └── reproducibility/       # Certified benchmark ledgers (theory, basins, traces, canonical rate)
│
├── reproduce/                 # Standardized CLI experiment runners (S0, E1–E7, E10)
│   ├── run_s0_linear_modal.py # Experiment S0: Linear modal dynamics smoke test
│   ├── run_e1_geometry_spectrum.py # Experiment E1: Geometry-spectrum correspondence
│   ├── run_e2_oracle_rates.py # Experiment E2: Local contraction rate prediction
│   ├── run_e3_ritz_estimator.py # Experiment E3: Passive Rayleigh-Ritz edge tracking
│   ├── run_e4_online_horizon.py # Experiment E4: Online dynamics & horizon adaptation
│   ├── run_e5_real_audio_basin.py # Experiment E5: Real-audio basin transfer on MUSAN
│   ├── run_e6_gate_a_heldout.py # Experiment E6: Geometry opportunity Gate A suite
│   ├── run_e7_microbench.py   # Experiment E7: Computational cost microbenchmarking
│   ├── run_e10_mechanism_ablation.py # Experiment E10: Robustness mechanism ablation suite
│   ├── run_all_experiments.py # Master end-to-end runner (executes all S0, E1-E7, E10)
│   ├── run_verification_and_figures.py # Reproduces Panels A-D & 20/20 numerical claims audit
│   ├── run_final_patch_horizon_audit.py # Long-horizon failure audit (H in {360, 720, 1440})
│   └── run_final_freeze_reconciliation.py # Final scientific freeze reconciliation & sign-off
│
├── experiments/               # Modular standalone experiment implementations
│   ├── 01_linear_modal_dynamics/            # Experiments S0, E1, E2
│   ├── 02_controlled_local_rates/           # Experiments E1, E2 (multi-STFT sweep)
│   ├── 03_geometry_opportunity_gate_a/      # Experiment E6 (Gate A 8-step pipeline)
│   ├── 04_neutral_mode_exactness_audit/     # Experiment E6 (gauge symmetry audit)
│   ├── 05_real_audio_basin_transfer/        # Experiment E5 (basin sweep & checkpoint runner)
│   ├── 06_multi_horizon_online_adaptation/  # Experiments E3, E4 (maturation, C1-C4, long-horizon)
│   ├── 07_computational_cost_microbench/    # Experiment E7 (isolated Ritz microbench)
│   └── 08_e10_robustness_mechanism_ablation/# Experiment E10 (E10, E10-R, E10-R2, E10-R2F archive)
│
├── scripts/                   # Utility scripts & figure generators
│   ├── data/                  # Dataset preparation and stratified sampling
│   ├── figures/               # Subfigure plotting scripts
│   └── verification/          # Publication panels generator & manuscript numbers verifier
│
├── results/                   # Complete empirical result ledgers and figures
│   ├── publication_figures/   # Regenerated publication panels A-D and composite Figure_Main_ABCD
│   ├── 01_phase1_reproduction/
│   ├── 02_phase2_transfer/
│   ├── 03_geometry_opportunity_gate_a/
│   ├── 05_real_audio_basin_transfer/
│   ├── 06_multi_horizon_online_adaptation/
│   ├── 07_computational_cost_microbench/
│   └── 08_e10_robustness_mechanism_ablation/
│
├── tests/                     # Automated unit and forensic test suites (30 tests, 100% PASS)
├── run_tests.py               # Test runner (compatible with unittest & pytest)
├── pyproject.toml             # Package build specification
└── requirements.txt           # Environment dependencies
```

---

## 2. Environment Setup

### 2.1 Installation
```bash
# Clone the repository
git clone https://github.com/aisia-research-lab/GeoAGLA.git
cd GeoAGLA

# Create and activate a Python virtual environment (Python 3.10+)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies and the core geometry_gla package in editable mode
pip install -r requirements.txt
pip install -e .
```

### 2.2 Automated Verification Test Suite
Verify that the complete mathematical and algorithmic test suite passes:
```bash
python run_tests.py
```
*Expected result:* **30/30 tests PASS in ~0.6 seconds** (covering projection idempotency, principal angle identities, Chebyshev equioscillation, passive Ritz tracking, safeguard monotonicity, and E10 forensic gates).

---

## 3. Quickstart: Master Execution & Verification

### Path A: Run All Experiments End-to-End
To execute the complete experimental suite (**S0, E1, E2, E3, E4, E5, E6, E7, E10**) in sequence:
```bash
python reproduce/run_all_experiments.py
```
*Execution time:* **~47 seconds total**. All 10 stages will execute and report `[PASS]`.

### Path B: Reproduce Publication Figures & Verify Manuscript Numbers
To regenerate the 4 publication panels (Panels A–D), the composite publication figure `Figure_Main_ABCD.pdf` (400 DPI), and verify all 20 numerical claims in the manuscript:
```bash
python reproduce/run_verification_and_figures.py
```
*Expected result:* **20/20 checks PASS (100% OK)** with zero tolerance violations.

---

## 4. Detailed Reproduction Guide: By Experiment

### Experiment S0: Linear Modal Dynamics Smoke Test
- **Scientific Goal**: Verify the fundamental 2-mode scalar recurrence and prove that the asymptotic error contraction rate matches the spectral radius: $\rho = \lambda_+$.
- **Data Required**: Purely synthetic; self-contained.
- **Execution Command**:
  ```bash
  python reproduce/run_s0_linear_modal.py
  ```
- **Primary Outputs**:
  - `results/phase1b/s0_results.json`
- **Expected Results**: Absolute error between observed contraction factor $q_{\rm obs}$ and theoretical rate $\rho = \lambda_+$ is $\le 0.012$ across all tested modes ($\lambda_+ \in \{0.2, 0.5, 0.8, 0.95\}$).

---

### Experiment E1: Geometry–Spectrum Correspondence
- **Scientific Goal**: Validate the theoretical correspondence between the principal angles of the STFT tangent subspaces $\cos^2\theta$ and the edge eigenvalues of the phase retrieval Jacobian:
  $$\lambda_\pm = \frac{1 \pm \cos\theta}{2}$$
- **Data Required**: Purely synthetic STFT operators (Hann and Gaussian windows).
- **Execution Command**:
  ```bash
  python reproduce/run_e1_geometry_spectrum.py
  ```
- **Primary Outputs**:
  - `results/phase1b/h1_results.json`
- **Expected Results**: Relative spectral error between direct Jacobian eigenvalues and principal angle cosine formula is $< 10^{-14}$ (machine precision agreement).

---

### Experiment E2: Exact Local Contraction Rate Prediction
- **Scientific Goal**: Confirm that under local geometry, standard Griffin–Lim (GLA) contracts at rate $\rho_{\rm GLA} = \lambda_+$, Fast Griffin–Lim (FGLA) contracts at $\rho_{\rm FGLA} = \sqrt{\lambda_+}$, and the geometry-informed minimax Oracle contracts at:
  $$\rho^*(\lambda_-, \lambda_+) = \frac{\sqrt{\lambda_+} - \sqrt{\lambda_-}}{\sqrt{\lambda_+} + \sqrt{\lambda_-}}$$
  yielding the strict hierarchy: $\rho^* < \rho_{\rm FGLA} < \rho_{\rm GLA}$.
- **Data Required**: Purely synthetic controlled STFT configurations.
- **Execution Commands**:
  ```bash
  # Rapid smoke test:
  python reproduce/run_e2_oracle_rates.py

  # Full multi-STFT parameter sweep:
  python reproduce/run_e2_oracle_rates.py --full
  ```
- **Primary Outputs**:
  - `results/phase1b/h2_results.json`
  - `results/01_phase1_reproduction/phase1c/h2_multi.json`
- **Expected Results**: Hierarchy pass fraction $> 85\%$ across all evaluated geometries; median final error reduction of Oracle over GLA $\approx 8.97\times$.

---

### Experiment E3: Passive Rayleigh–Ritz Dominant-Edge Estimation
- **Scientific Goal**: Evaluate passive tracking of the dominant Jacobian eigenvalue $\lambda_+$ along the optimization trajectory using Krylov subspaces with memory depths $p \in \{1, 3, 5\}$, without active subspace perturbation.
- **Data Required**: Controlled synthetic signal trajectories.
- **Execution Command**:
  ```bash
  python reproduce/run_e3_ritz_estimator.py
  ```
- **Primary Outputs**:
  - `results/01_phase1_reproduction/phase1d/tracking_traces.json`
  - `results/01_phase1_reproduction/phase1d/figures/D3_online_edge_tracking.png`
- **Expected Results**: $p=3$ memory depth achieves median relative estimation error $\approx 0.23\%$, with $100\%$ under-estimation safety, proving that dynamic envelope damping is necessary and sufficient.

---

### Experiment E4: Online Dynamics, Safeguarding & Finite-Horizon Adaptation
- **Scientific Goal**: Evaluate online adaptive acceleration under running-envelope damping $\lambda_{\rm env}$ and Rayleigh quotient fallback safeguarding across finite observation horizons $H \in \{30, 60, 120, 200, 360\}$.
- **Data Required**: Synthetic test trajectories and canonical multi-horizon audio cases.
- **Execution Commands**:
  ```bash
  # Phase 1E-R Repair and Horizon Policy (Default):
  python reproduce/run_e4_online_horizon.py

  # Canonical C1 capture ratio audit (60 evaluations across H in {60, 120, 180, 360}):
  python reproduce/run_e4_online_horizon.py --audit

  # Long-horizon 29-case audit (H in {360, 720, 1440}):
  python reproduce/run_e4_online_horizon.py --patch

  # Run all E4 sub-experiments:
  python reproduce/run_e4_online_horizon.py --all
  ```
- **Primary Outputs**:
  - `results/01_phase1_reproduction/phase1er/policy_summary.json`
  - `data/reproducibility/canonical_rate/C1_capture_ratio_audit.csv`
  - `results/final_patch_horizon_audit/transition_table.csv`
- **Expected Results**: Gate G-R4 pass: Zero safeguard fallback failures ($0/192$ failures); Online algorithm beats FGLA in $86.7\%$ of cases at $H=60$; monotonic error non-expansion guaranteed.

---

### Experiment E5: Real-Audio Basin Transfer & Robustness on MUSAN
- **Scientific Goal**: Evaluate basin of attraction convergence transfer from synthetic signals to genuine acoustic speech, music, and noise recordings from the MUSAN corpus under random and zero initializations across perturbation scales ($10^{-3}$ to $1.0$).
- **Data Required**: Sample audio waveforms in `data/audio_samples/` (or external full MUSAN via `--audio-dir`).
- **Execution Commands**:
  ```bash
  # Fast STFT-FFT operator isometry verification:
  python reproduce/run_e5_real_audio_basin.py --stft-fft

  # Real-audio waveform pilot on local samples:
  python reproduce/run_e5_real_audio_basin.py --pilot

  # Checkpointed batch runner with deadline control (recommended for large datasets/cloud):
  python reproduce/run_e5_real_audio_basin.py --checkpointed --audio-dir data/audio_samples --batch-size 2
  ```
- **Primary Outputs**:
  - `results/02_phase2_transfer/phase2a/summary.json`
  - `results/05_real_audio_basin_transfer/checkpointed_run/summary.json`
  - `results/05_real_audio_basin_transfer/checkpointed_run/figures/`
- **Expected Results**: Online algorithm achieves $74.94\%$ basin success vs $54.87\%$ for FGLA ($+20.06$ pp gain) on the original branch, and $73.30\%$ vs $54.90\%$ ($+18.39$ pp gain) on the disjoint MUSAN-ODD branch; zero safeguard fallback failures across all $9{,}432$ combined runs.

---

### Experiment E6: Geometry Opportunity Gate A & Held-Out Suite
- **Scientific Goal**: Construct the canonical 90-case opportunity ledger, analyze the geometry acceleration headroom $\Delta_{\rm oracle} = \rho_{\rm FGLA} - \rho^*$, evaluate generalization on 36 held-out STFT configurations, and audit neutral mode gauge symmetry.
- **Data Required**: Frozen reference caches in `data/frozen/`.
- **Execution Commands**:
  ```bash
  # Run entire 8-step Gate A pipeline:
  python reproduce/run_e6_gate_a_heldout.py

  # Or run individual steps (e.g. step 1: build ledger):
  python reproduce/run_e6_gate_a_heldout.py --step 1
  ```
- **Primary Outputs**:
  - `results/e6_geometry_opportunity/e6_case_ledger.csv` (90 canonical cases)
  - `results/e6_geometry_opportunity/e6_summary.json`
  - `results/e6_geometry_opportunity/latex_tables/`
- **Expected Results**: Gate A PASS: Non-negligible geometry headroom exists in $> 80\%$ of STFT configurations; held-out generalization confirms that geometry directly governs achievable speedup.

---

### Experiment E7: Computational Cost Microbenchmarking
- **Scientific Goal**: Measure the wall-clock execution time and FLOP count of the isolated passive Rayleigh–Ritz $3 \times 3$ eigensolver, comparing it against the forward/inverse STFT projections and GLA step latency.
- **Data Required**: Synthetic timing benchmark; self-contained.
- **Execution Command**:
  ```bash
  python reproduce/run_e7_microbench.py
  ```
- **Primary Outputs**:
  - Direct console profiling output and latency breakdown.
- **Expected Results**:
  - Isolated update execution time: $\approx 0.42$ ms per update.
  - Amortized per-iteration cost ($K=8$ block cadence): $\approx 0.05$ ms per iteration.
  - Relative computational overhead: **$\approx 3.1\%$ to $3.2\%$** of a single GLA iteration.

---

### Experiment E10: Robustness Mechanism Ablation Suite
- **Scientific Goal**: Perform a rigorous paired ablation decomposing the 6 architectural mechanisms of GeoAGLA, verify historical locked-seed equivalence (E10-R), validate canonical 202-case threshold behavior (E10-R2), and verify the bitwise cryptographic archive (E10-R2F).
- **Data Required**: Included locked benchmarks and `E10R2F_FINAL_ARCHIVE.zip`.
- **Execution Commands**:
  ```bash
  # Run 6-variant paired mechanism ablation:
  python reproduce/run_e10_mechanism_ablation.py

  # Run E10-R locked historical evaluation:
  python reproduce/run_e10_mechanism_ablation.py --locked

  # Run E10-R2 canonical baseline evaluation:
  python reproduce/run_e10_mechanism_ablation.py --canonical

  # Verify E10-R2F forensic bitwise archive (SHA-256 verified):
  python reproduce/run_e10_mechanism_ablation.py --archive
  ```
- **Primary Outputs**:
  - `E10R2F_FINAL_ARCHIVE.zip` (29.13 MB, SHA-256: `3f94f44e...`)
  - `results/08_e10_robustness_mechanism_ablation/`
- **Expected Results**: All 6 variants confirm that passive Ritz tracking, dynamic envelope damping, and monotonic safeguard fallback are all necessary and mutually reinforcing; zero oracle leakage ($12/12$ PASS); bitwise event cardinality verified ($834{,}240$ rows).

---

## 5. Formal Numerical Verification Audit (20/20 Checks)

Running `python reproduce/run_verification_and_figures.py` executes an automated audit verifying all numbers reported in the paper:

| Check # | Category | Metric Name | Evaluated Result | Paper Value | Tolerance | Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | Basin Headline | Original Online success (%) | 74.94% | 74.94% | $\pm 0.03$ | **PASS** |
| 2 | Basin Headline | Original FGLA success (%) | 54.87% | 54.87% | $\pm 0.03$ | **PASS** |
| 3 | Basin Headline | MUSAN-ODD Online success (%) | 73.30% | 73.30% | $\pm 0.03$ | **PASS** |
| 4 | Basin Headline | MUSAN-ODD FGLA success (%) | 54.90% | 54.90% | $\pm 0.03$ | **PASS** |
| 5 | Basin Headline | Original paired beat (%) | 34.47% | 34.47% | $\pm 0.03$ | **PASS** |
| 6 | Basin Headline | MUSAN-ODD paired beat (%) | 35.74% | 35.74% | $\pm 0.03$ | **PASS** |
| 7 | Theory Validation | Evaluated geometry cases ($n$) | 202 | 202 | Exact | **PASS** |
| 8 | Theory Validation | Evaluated rate cases ($n$) | 202 | 202 | Exact | **PASS** |
| 9 | Theory Validation | Median geometry rel error | $1.438\times 10^{-3}$ | $1.44\times 10^{-3}$ | $\pm 10^{-4}$ | **PASS** |
| 10 | Theory Validation | Max geometry rel error | $2.897\times 10^{-3}$ | $2.90\times 10^{-3}$ | $\pm 10^{-4}$ | **PASS** |
| 11 | Theory Validation | Hierarchy pass count | 173 / 202 | 173 / 202 | Exact | **PASS** |
| 12 | Theory Validation | Hierarchy pass fraction | 85.64% | 85.64% | $\pm 0.005$ | **PASS** |
| 13 | Theory Validation | Median error red FGLA vs GLA | $5.086\times$ | $5.086\times$ | $\pm 0.02$ | **PASS** |
| 14 | Theory Validation | Median error red Oracle vs GLA | $8.967\times$ | $8.967\times$ | $\pm 0.02$ | **PASS** |
| 15 | Robustness | Original basin runs count | 4,680 | 4,680 | Exact | **PASS** |
| 16 | Robustness | MUSAN-ODD basin runs count | 4,752 | 4,752 | Exact | **PASS** |
| 17 | Robustness | Original Online-FGLA gain | +20.06 pp | +20.06 pp | $\pm 0.05$ | **PASS** |
| 18 | Robustness | MUSAN-ODD Online-FGLA gain | +18.39 pp | +18.39 pp | $\pm 0.05$ | **PASS** |
| 19 | Bootstrap CI | Original 95% Cluster CI | [18.61, 21.51] pp | [18.6, 21.5] pp | Enclosed | **PASS** |
| 20 | Bootstrap CI | MUSAN-ODD 95% Cluster CI | [16.96, 19.80] pp | [17.0, 19.8] pp | Enclosed | **PASS** |

---

## 6. Generated Publication Figures

When `reproduce/run_verification_and_figures.py` completes, high-resolution vector PDF and 400 DPI PNG figures are generated in `results/publication_figures/figures/`:
1. `panel_A_geometry_spectrum.png` / `.pdf`: Principal angle prediction $\cos^2\theta$ vs direct Jacobian edge $\lambda_+$ ($n=202$).
2. `panel_B_predicted_observed.png` / `.pdf`: Predicted vs observed contraction factors for GLA, FGLA, and Oracle minimax.
3. `panel_C_estimator_maturation.png` / `.pdf`: Passive Ritz edge-estimator trajectories across low, medium, and high opportunity regimes ($p=3$).
4. `panel_D_replicated_robustness.png` / `.pdf`: Basin convergence success rates comparing Online vs FGLA across $9{,}432$ total runs.
5. `Figure_Main_ABCD.png` / `.pdf`: Full two-column $2 \times 2$ composite evidence figure matching the manuscript layout.

---

## 7. Citation & Academic Reference

```bibtex
@inproceedings{geoagla2027iclr,
  title     = {Geometry Determines Local Acceleration in Griffin--Lim Phase Retrieval},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2027}
}
```
