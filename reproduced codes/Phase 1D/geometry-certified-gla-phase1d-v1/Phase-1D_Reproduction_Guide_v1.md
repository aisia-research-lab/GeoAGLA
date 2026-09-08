# Phase-1D — Reproduction Guide v1

## Install

```bash
cd geometry-certified-gla-phase1d-v1
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

## Recommended complete run

```bash
python reproduce/run_phase1d.py
```

Expected first-stage output:

```text
9 passed
```

Then the D0/D1/D2 diagnostics run and write `results/phase1d/summary.json`.

## Run components separately

```bash
pytest -q
python -m experiments.phase1d_online_edge.run
```

## Main outputs

```text
results/phase1d/
├── d0_synthetic.json
├── d1_local_stft.csv
├── d1_local_stft.json
├── d2_identifiability.json
├── estimator_selection.json
├── summary.json
├── tracking_traces.json
└── figures/
    ├── D3_online_edge_tracking.png
    ├── D3b_error_by_memory.png
    ├── D3c_memory_conditioning.png
    └── D3d_active_spectrum_failure.png
```

## What to send back for audit

Please return at least:

```text
results/phase1d/summary.json
results/phase1d/estimator_selection.json
results/phase1d/d2_identifiability.json
```

If the run fails, also save:

```bash
python --version
python -m pip freeze
```

and the complete terminal output.
