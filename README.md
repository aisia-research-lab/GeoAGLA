# GeoAGLA: Geometry-Adaptive Acceleration in Griffin–Lim Phase Retrieval

Official implementation for the manuscript *"Geometry Determines Local Acceleration in Griffin–Lim Phase Retrieval"* (submitted to *IEEE Transactions on Signal Processing*).

This repository provides a clean, self-contained Python library and reproducible experiment scripts covering:
- **Local spectral geometry**: Principal-angle characterization of the linearized Griffin–Lim operator and exact verification of the radial zero mode ($\lambda_- = 0$).
- **Minimax acceleration & sensitivity**: Closed-form one-edge minimax parameters on $[0, L]$, exact spectral-mismatch acceleration intervals, and the abstract two-edge transfer theorem on general PSD subspace pairs.
- **Safeguarded online acceleration**: Passive Rayleigh–Ritz secant estimation with running-envelope damping and fixed-merit checkpoint rollback to standard GLA.
- **Matched-budget evaluation**: Unified PyTorch (CPU/CUDA) projection-call and synchronized wall-clock benchmarks with paired cluster-bootstrap analysis.

---

## Repository Structure

```text
GeoAGLA/
├── configs/
│   └── solver_parameters.json       # STFT profiles, solver settings, and evaluation budgets
├── inputs/
│   ├── manifest.json                # 12 MUSAN source IDs, excerpt offsets, lengths and RMS values
│   └── prior_audit.json             # Source-file and decoded-PCM SHA256 for every manifest entry
├── src/geometry_gla/                # Core Python package
│   ├── algorithms/                  # AGLA, NAGLA, exact minimax/mismatch theory, online policies
│   ├── estimators/                  # Passive Rayleigh-Ritz dominant-edge estimator
│   ├── geometry/                    # Principal angles, tangent Jacobian, matrix-free spectrum
│   ├── metrics/                     # Phase-invariant orbit distance and contraction rate fits
│   ├── operators/                   # Explicit matrix, FFT, and PyTorch CPU/CUDA STFT operators
│   ├── safeguards/                  # Fixed-merit sufficient-decrease checkpoint filter
│   └── signals.py                   # Deterministic synthetic test signals
├── experiments/                     # Runnable experiment & analysis scripts (no prebaked results)
│   ├── common.py                    # Shared preprocessing, initializers, and PyTorch solver engine
│   ├── spectral_geometry.py         # Principal-sine Gram vs. direct tangent-Jacobian verification
│   ├── local_acceleration.py        # Controlled local oracle acceleration & mismatch sweep
│   ├── non_stft_transfer.py         # Two-edge minimax verification on non-STFT subspace pairs
│   ├── matched_budget_benchmark.py  # Equal-calls & wall-clock benchmarks and component ablation
│   ├── benchmark_analysis.py        # Paired cluster-bootstrap statistics & mechanism diagnostics
│   ├── parity_check.py              # NumPy reference vs. PyTorch backend parity verification
│   ├── ritz_microbench.py           # Isolated Rayleigh-Ritz SVD vs. STFT timing microbenchmark
│   └── run_cpu_suite.py             # One-command self-contained CPU verification suite
├── tests/                           # Unit tests covering operators, geometry, minimax, and solvers
├── pyproject.toml
├── requirements.txt
└── run_tests.py
```

---

## Installation

Python 3.10+ is required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

*(For GPU acceleration, install the PyTorch wheel matching your local CUDA toolkit from [pytorch.org](https://pytorch.org/get-started/locally/).)*

---

## Quick Verification (No External Data Required)

1. **Run the unit test suite**:
   ```bash
   python run_tests.py
   ```

2. **Run all self-contained CPU experiments end-to-end** (parity check, non-STFT two-edge transfer, synthetic spectral geometry & gap plot, local mismatch sweep, matched-budget smoke benchmark, and Ritz microbenchmark):
   ```bash
   python -m experiments.run_cpu_suite --out outputs/cpu_suite
   ```

All generated files are written under `outputs/` (gitignored).

---

## Reproducing Full Real-Audio Experiments

The real-audio experiments use 12 excerpts from the publicly available [MUSAN corpus](https://www.openslr.org/17/) listed in `inputs/manifest.json`. Download MUSAN locally and pass its root directory via `--audio-root /path/to/musan` (files may sit directly under the root or in the original nested MUSAN layout).

Before any audio is used, the loader checks each file against the source SHA256 and decoded-PCM SHA256 in `inputs/prior_audit.json`, and checks the excerpt RMS against the manifest. A missing, ambiguous or mismatching file raises an error; it is never silently replaced. Initial states are seeded from the first eight hex digits of SHA256(`source_id|profile|kind|seed|REBFINAL`), as described in the manuscript.

### 1. Backend Trajectory Parity Check
Verify exact agreement between the NumPy reference and PyTorch solver on your target device (`cpu` or `cuda:0`):
```bash
python -m experiments.parity_check --device cuda:0 --audio-root /path/to/musan --out outputs/parity.json
```

### 2. Spectral Geometry & Radial Zero Mode
Compute independent direct tangent-Jacobian and principal-sine Gram gaps across all 24 STFT geometries (12 signals $\times$ Gaussian/Hann windows) and generate the log-log gap identity figure:
```bash
python -m experiments.spectral_geometry --audio-root /path/to/musan --plot --out outputs/spectral_audio.jsonl
```

### 3. Controlled Local Acceleration & Mismatch Sensitivity
Evaluate controlled dominant-mode and radial perturbations across exact mismatch ratios and theoretical tolerance boundaries:
```bash
python -m experiments.local_acceleration --audio-root /path/to/musan --out outputs/local_audio.jsonl
```

### 4. Abstract Two-Edge Transfer (Non-STFT Subspace Pairs)
```bash
python -m experiments.non_stft_transfer --out outputs/non_stft_transfer.json
```

### 5. Matched-Budget Benchmarks & Component Ablation
Run equal projection-call (`--mode calls`) and synchronized wall-clock (`--mode wall`) comparisons across all 10 methods (`Online`, `OnlineRaw`, `OnlineNoFallback`, `OnlineGram`, `OneEdgeOracle`, `NAGLA_H2`, `RestartNAG`, `FGLA_095`, `AGLA_tuned`, `GLA`):
```bash
# Equal projection-call budgets (90 to 2,880 calls)
python -m experiments.matched_budget_benchmark --audio-root /path/to/musan --spectra outputs/spectral_audio.jsonl --mode calls --device cuda:0 --out outputs/calls_audio.jsonl
python -m experiments.benchmark_analysis --raw outputs/calls_audio.jsonl --mode calls --out outputs/calls_summary

# Synchronized wall-clock budgets (50 ms to 1.0 s)
python -m experiments.matched_budget_benchmark --audio-root /path/to/musan --spectra outputs/spectral_audio.jsonl --mode wall --device cuda:0 --out outputs/wall_audio.jsonl
python -m experiments.benchmark_analysis --raw outputs/wall_audio.jsonl --mode wall --out outputs/wall_summary
```

### 6. Rayleigh–Ritz Runtime Microbenchmark
```bash
python -m experiments.ritz_microbench --out outputs/ritz_microbench.json
```
