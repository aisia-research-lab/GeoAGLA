# Phase-1D — Online Dominant Spectral-Edge Identification Engine v1

## Scientific question

Can the dominant local spectral edge be estimated passively from an already-computed Griffin–Lim trajectory, without an extra STFT/projection pair?

For a GLA trajectory `c[n+1] = G(c[n])`, define the secant

` s[n] = c[n] - c[n-1] `.

Then the secant image required by a local Ritz estimator is already present:

` y[n] = G(c[n]) - G(c[n-1]) = c[n+1] - c[n] = s[n+1]. `

Thus the estimator adds only small linear-algebra overhead.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
python reproduce/run_phase1d.py
```

Individual run:

```bash
pytest -q
python -m experiments.phase1d_online_edge.run
```

## Outputs

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

## Interpretation rule

A passive Ritz estimate is an **active-subspace estimate**, not a certified outer bound for the full transverse spectrum. The package includes an exact hidden-mode counterexample in which two operators generate identical passive trajectories but have different unexcited full spectral edges. Therefore raw `lambda_hat_plus` must not be treated as a safety certificate in the subsequent online accelerator; Phase-1E must use a safety margin and/or the global safeguard.
