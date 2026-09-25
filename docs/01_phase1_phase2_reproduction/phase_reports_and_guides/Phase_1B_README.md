# Geometry-Certified Griffin-Lim — Phase-1B Reproducible Oracle Geometry Engine v1

This repository is the first executable diagnostic package for the project
**Geometry-Certified Acceleration of Griffin-Lim Phase Retrieval**.

Phase-1B deliberately focuses on theorem-facing checks before any large audio
benchmark:

- **S0:** exact modal recurrence and the closed-form spectral minimax design;
- **H1:** local Griffin-Lim Jacobian spectrum vs. squared principal-angle cosines;
- **H2:** predicted vs. observed local contraction for GLA, oracle-optimal FGLA,
  and Oracle-[lambda_minus, lambda_plus] dynamics on a controlled feasible STFT instance.

## Requirements

- Python 3.10+
- NumPy, SciPy, Matplotlib, pytest
- CPU only

## Install

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

## Run the complete Phase-1B smoke reproduction

```bash
python reproduce/run_phase1b.py
```

Expected outputs:

```text
results/phase1b/s0_results.json
results/phase1b/h1_results.json
results/phase1b/h2_results.json
```

## Run components separately

```bash
pytest -q
python -m experiments.s0_linear.run
python -m experiments.h1_geometry.run
python -m experiments.h2_oracle_rate.run
```

## Mathematical identities under test

At a regular feasible coefficient vector `c_star`, treating complex space as a
real Hilbert space,

```text
DP_C2(c_star) = P_T,
DG(c_star)|_U = P_U P_T |_U,
lambda_j(DG) = cos(theta_j)^2.
```

For transverse spectrum `[lambda_minus, lambda_plus]`, the Phase-0B minimax
parameters are implemented in `src/geometry_gla/algorithms/minimax.py`.

## Scope

This is intentionally a small explicit-matrix engine. It is designed for
proof diagnostics, not yet for large-scale audio processing. Phase-1C/1D will
replace explicit STFT matrices with scalable matrix-free operators while
preserving the same tested interfaces.

## Reproducibility policy

- deterministic seeds;
- no GPU requirement;
- raw JSON outputs;
- theorem identities encoded as pytest assertions;
- no manually edited numerical results.

## License

MIT.
