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
│   ├── prior_audit.json             # Source-file and decoded-PCM SHA256 for every manifest entry
│   └── prior_spectrum.jsonl         # Frozen numerical spectral edge L for the 24 geometries (oracle/diagnostics only)
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
│   ├── audit_ledger.py              # Independent raw-ledger audit (pairing, success, calls, budget selection)
│   ├── parity_check.py              # NumPy reference vs. PyTorch backend parity verification
│   ├── ritz_microbench.py           # Isolated Rayleigh-Ritz SVD vs. STFT timing microbenchmark
│   ├── verify_switching_certificate.py  # Exact-rational certificate for Proposition 7 (switching)
│   └── run_cpu_suite.py             # One-command self-contained CPU verification suite
├── results/
│   └── k1k2_cpu_replication/        # K1/K2 aggregate data (spectra, audit, gap figure) + raw-ledger SHA256
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

2. **Run all self-contained CPU experiments end-to-end** (parity check, non-STFT two-edge transfer, synthetic spectral geometry & gap plot, local mismatch sweep, matched-budget smoke benchmark with raw-ledger audit, Ritz microbenchmark, and the exact-rational switching certificate):
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

# Independent raw-ledger audit (192 start keys per seed in the manuscript)
python -m experiments.audit_ledger --raw outputs/calls_audio.jsonl --mode calls --expected-keys 192 --out outputs/calls_audit.json
python -m experiments.audit_ledger --raw outputs/wall_audio.jsonl --mode wall --expected-keys 192 --out outputs/wall_audit.json
```

**Reproducing the manuscript tables (Tables I, II and V).** Raw ledgers and result tables are not distributed with this repository; they are regenerated with the commands above using these settings:
- `--spectra inputs/prior_spectrum.jsonl` (the frozen numerical spectrum used in the manuscript, 24 geometries) instead of a freshly computed spectrum file. It is used only by `OneEdgeOracle` and the tolerance diagnostics, never by `Online`.
- `--seeds 1` (192 start keys: 144 historical, 24 signal-noise, 24 random-phase), complex128, all 10 methods.
- Budgets and horizons are fixed in code: calls mode runs 2,884 committed steps for caps 90–2,880; wall mode stops at 1.0 s of synchronized solver time (safety limit 100,000 steps). Primary caps are 360 calls and 200 ms.
- Hardware: one NVIDIA H200 MIG 2g.35gb partition. Run wall mode with no other job on the same partition; timing on other hardware will differ, while calls-mode success labels should not depend on timing.
- Run `experiments.parity_check --device cuda:0 --audio-root ...` first; all 16 cases must pass.
- Record `nvidia-smi` and `pip freeze` alongside your outputs.

Environment of the manuscript run (from the run's own configuration record):

| Item | Value |
|---|---|
| GPU | NVIDIA H200, one MIG `2g.35gb` slice (32 SMs, 33,280 MiB); other MIG slices on the same physical node were in use by unrelated jobs, none on this slice |
| Driver / CUDA | NVIDIA driver 580.126.20 (recorded on the same node after the run), CUDA 13.0, cuDNN 9.24 |
| OS | Ubuntu 24.04.4 LTS, Linux 6.8.0-106-generic |
| Python / packages | Python 3.12.13, PyTorch 2.14.0+cu130, NumPy 2.5.3, SciPy 1.18.1, soundfile 0.14.0 |
| Threads | `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `torch.set_num_threads(1)` |
| Run layout | one job, no sharding, a single timing repeat; calls mode, then wall mode, on the same slice |
| Checks | GPU parity 16/16 (max state discrepancy 5.45e-11); audit PASS in both modes, 0 failed records, 11,520 calls-mode and 9,600 wall-mode budget rows |

That run used the frozen experiment package from which this repository was derived (same manifest, spectrum, seeds and methods; `OnlineGram0C` there is `OnlineGram` here), not the scripts in this repository verbatim.

### 6. Rayleigh–Ritz Runtime Microbenchmark
```bash
python -m experiments.ritz_microbench --out outputs/ritz_microbench.json
```

### 7. Exact-Rational Switching Certificate (Proposition 7)
Checks every inequality in the proof of the switching counterexample with `fractions.Fraction`
(Jury slacks, the bounds on tr P and det P, and the sign at x = -(0.685)^16):
```bash
python -m experiments.verify_switching_certificate --out outputs/switching_certificate.json
```

---

## Aggregate Data

`results/k1k2_cpu_replication/` contains the aggregate output of the independent CPU replication of the
spectral-identity (K1) and mismatch-replay (K2) experiments on the 12 manifest files:
`spectrum_summary.csv` (24 geometries: L, principal-sine vs. Jacobian and prior-spectrum discrepancies),
`audit.json` (24/24 resolved, 5,184/5,184 mismatch records), and `gap_identity.svg`.
The raw JSONL ledgers are not stored in this repository; `raw_ledger_sha256.txt` lists their SHA256 checksums,
The corresponding experiments in this repository are `experiments.spectral_geometry` (K1) and
`experiments.local_acceleration` (K2); their outputs are not guaranteed to be byte-identical to the archived ledgers.
Results of the GPU matched-budget benchmark are not distributed; see "Reproducing the manuscript tables" in Section 5.
