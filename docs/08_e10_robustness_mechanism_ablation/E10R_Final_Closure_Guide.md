# Experiment E10-R: Final Mechanism Attribution & Reproducibility Closure Guide

- **Project:** GeoAGLA: Geometry-Adaptive Acceleration for Phase Retrieval (ICLR 2027)
- **Experiment Module:** `08_e10_robustness_mechanism_ablation` (Closure Run: E10-R)
- **Protocol:** Locked 395-Geometry Finite-Horizon Robustness Protocol
- **Target Output:** `results/08_e10r_locked/`

---

## 1. Executive Objective

Experiment **E10-R (Final Closure)** establishes the definitive, publication-frozen mechanism attribution for the GeoAGLA framework prior to manuscript submission. Rather than searching for alternative hyperparameters or filtering criteria, E10-R enforces strict reproducibility:

1. Evaluates on an **exact, locked geometry population** (395 valid STFT geometry cases), eliminating inter-machine ARPACK numerical convergence variance.
2. Employs the **historical Phase-2B Kaggle seed convention** (`--seed-mode historical_batch2`), resetting the file index component within consecutive batches of two files.
3. Simultaneously executes all **six method variants** on identical paired problem instances (4,740 paired cases, 28,440 method rows).
4. Locks the causal mechanism attribution decomposition:
   - Fixed asymptotic oracle (`fgla_oracle`)
   - Fixed minimax single-edge oracle (`fixed_1e_oracle`)
   - Trajectory-adaptive online Rayleigh estimator (`online_raw`)
   - Dynamic stability envelope gating (`online_env`)
   - Conservative GLA fallback policy (`online_fallback`)
   - Canonical full GeoAGLA policy (`online_full`)

---

## 2. Locked Population & Cardinality Gates

All runs in E10-R must adhere strictly to the frozen geometry specification:
- **Locked Specification File:** `experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv`
- **Locked Geometry Cases:** Exactly **395** `(file, profile)` pairs:
  - `agla_gaussian`: 202 cases
  - `mezza_hann`: 193 cases
- **Perturbation Basins per Case:** 12 conditions (3 transverse levels $\times$ 3 phase-jitter levels $\times$ 2 seeds).
- **Paired Instances:** $395 \times 12 = \mathbf{4,740}$ paired problem instances.
- **Total Method Rows:** $4,740 \times 6 = \mathbf{28,440}$ method rows.

> [!IMPORTANT]
> **Hard Cardinality Requirement:** Under no circumstances should geometry eligibility be re-evaluated at runtime. If any audio file or geometry computation fails, execution halts and logs the anomaly. The final run ledger must contain exactly **28,440 rows**.

---

## 3. Method Variants Specification

Each paired problem instance is evaluated synchronously across six distinct algorithms initialized from the identical initial state $c_0$:

| Variant Name | Online Ritz Tracking | Dynamic Stability Envelope | Fallback / Rollback | Theoretical Objective |
| :--- | :---: | :---: | :---: | :--- |
| `fgla_oracle` | No | No | No | Optimal fixed momentum computed from true asymptotic $\lambda_+$ |
| `fixed_1e_oracle` | No | No | No | Minimax fixed momentum on single-edge interval $[0, \lambda_+]$ |
| `online_raw` | Yes | No | No | Pure online block-wise Rayleigh quotient estimation |
| `online_env` | Yes | Yes | No | Online estimation with dynamic stability envelope gating |
| `online_fallback` | Yes | No | Yes | Online estimation with conservative GLA rollback |
| `online_full` | Yes | Yes | Yes | Canonical GeoAGLA combining adaptation, envelope, and fallback |

---

## 4. Frozen Experimental Configuration

Configuration parameters are locked in `configs/phase2b_grid.json`:

```json
{
  "n_iter": 360,
  "warmup": 12,
  "block_size": 8,
  "memory": 3,
  "margin": 0.0,
  "lambda_ceiling": 0.99999999,
  "svd_rtol": 1e-9,
  "cond_max": 1e10,
  "alpha_safe": 0.0,
  "beta_safe": 0.0,
  "gamma_safe": 1.0,
  "K_safe": 0.25,
  "descent_a": 1e-4,
  "stft_profiles": [
    {"id": "agla_gaussian", "window": "gaussian", "window_length": 128, "hop": 32, "n_fft": 256},
    {"id": "mezza_hann", "window": "hann", "window_length": 256, "hop": 64, "n_fft": 256}
  ],
  "basin_initializations": [
    {"kind": "transverse", "levels": [0.001, 0.01, 0.05]},
    {"kind": "phase_jitter", "levels": [0.05, 0.15, 0.30]}
  ],
  "seeds": [0, 1],
  "basin_success": {
    "final_orbit_ratio_max": 0.10,
    "final_magnitude_residual_max": 1e-5
  }
}
```

---

## 5. Execution Protocol

### 5.1. Preflight Verification
Execute mandatory preflight tests before launching the full run:

```bash
PYTHONPATH=src pytest -q \
  tests/test_e10_ablation.py \
  tests/test_phase1d_ritz.py \
  tests/test_phase1e_safeguard.py \
  tests/test_phase2b_audio.py
```

### 5.2. Running the Locked Experiment

```bash
python experiments/08_e10_robustness_mechanism_ablation/03_run_e10r_locked.py \
  --audio-dir data/audio_benchmark \
  --out results/08_e10r_locked \
  --seed-mode historical_batch2
```

Convenience one-line wrapper:

```bash
python reproduce/run_e10r_locked.py --audio-dir data/audio_benchmark --out results/08_e10r_locked
```

### 5.3. Unified Audit and Statistical Analysis
Run the independent integrity audit and clustered bootstrap ($B=5,000$ replicates, clustered by source audio file):

```bash
python experiments/08_e10_robustness_mechanism_ablation/04_audit_and_analyze_e10r.py \
  results/08_e10r_locked/e10r_run_ledger.csv \
  --out results/08_e10r_locked \
  --B 5000 --seed 20270920
```

---

## 6. Sanity Reference Values

On the locked 395-case population, the frozen reference metrics provide an orientation baseline:

| Variant | Reference Success Rate |
| :--- | :---: |
| `fgla_oracle` | 55.02% |
| `fixed_1e_oracle` | 40.72% |
| `online_raw` | 72.85% |
| `online_env` | 72.19% |
| `online_fallback` | 72.87% |
| `online_full` | **73.16%** |

Reference contrasts:
- `fgla_oracle` $\to$ `online_full`: $\approx \mathbf{+18.14\text{ pp}}$
- `fixed_1e_oracle` $\to$ `online_raw`: $\approx \mathbf{+32.13\text{ pp}}$
- `online_raw` $\to$ `online_env`: $\approx \mathbf{-0.65\text{ pp}}$
- `online_raw` $\to$ `online_fallback`: $\approx \mathbf{+0.02\text{ pp}}$
- `online_env` $\to$ `online_full`: $\approx \mathbf{+0.97\text{ pp}}$

---

## 7. Closure Acceptance Deliverables

All outputs must be packaged into the final return archive `E10R_FINAL_RETURN.zip`:

```text
E10R_FINAL_RETURN/
├── results/
│   ├── e10r_run_ledger.csv
│   ├── e10r_run_ledger.json
│   ├── e10r_event_ledger.csv
│   ├── e10r_success_summary.csv
│   └── e10r_contrasts.csv
├── audit/
│   ├── E10R_AUDIT.md
│   └── integrity_summary.json
├── logs/
│   ├── full_run.log
│   ├── pytest.log
│   └── e10r_pip_freeze.txt
└── executed_code/
    └── 03_run_e10r_locked.py
```
