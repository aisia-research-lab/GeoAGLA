# Phase-1C — Multi-Instance Oracle Geometry & Rate Verification Engine v1

Phase-1C extends the Phase-1B smoke tests to a deterministic multi-instance grid.

## Scientific targets

- **H1:** verify `spec(DG(c*)) = cos^2(theta_j)` across STFT configurations and seeds.
- **H2:** verify predicted local contraction rates for GLA, oracle-tuned FGLA, and the geometry-optimal oracle method.
- Audit finite-window bias in fitted accelerated rates rather than assuming the Phase-1B discrepancy is purely asymptotic.

## Frozen grid

- 6 STFT configurations: Gaussian/Hann; N = 16, 24, 32; multiple window/FFT sizes.
- 5 signal seeds per configuration.
- 3 perturbation magnitudes: `1e-3`, `1e-4`, `1e-5`.
- 180 local iterations per H2 run.

This yields 30 H1 cases and, when all are regular modulo global phase, 270 H2 method runs.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
python reproduce/run_phase1c.py
```

## Outputs

```text
results/phase1c/
├── h1_multi.json
├── h1_multi.csv
├── h2_multi.json
├── h2_multi.csv
├── finite_window_audit.json
├── summary.json
└── figures/
    ├── D1_geometry_identity.png
    ├── D2_rate_prediction.png
    └── D2b_finite_window_audit.png
```

## Gate logic

H1 requires the maximum relative spectrum discrepancy to be at most `1e-10` and exactly one neutral eigenvalue in every grid case. H2's robust first gate is the observed ordering

`q_oracle < q_FGLA,opt < q_GLA`

in at least 90% of matched local runs. Rate-fit errors are reported separately because repeated-root dynamics can create a finite-window `n q^n` prefactor.

The package preserves all Phase-1B tests and results for backward reproducibility.
