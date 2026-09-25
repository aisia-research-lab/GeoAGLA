# Phase-1C — Multi-Instance Oracle Geometry & Rate Verification Report v1

## Scope

Phase-1C extends the Phase-1B H1/H2 smoke tests to a deterministic multi-instance STFT grid. It is a theorem-facing diagnostic, not yet the final audio benchmark.

## Frozen experiment grid

- 6 STFT configurations (Gaussian/Hann windows; signal lengths 16, 24, 32; two window/FFT scales)
- 5 seeds per configuration
- 30 H1 geometry cases
- 3 local perturbation magnitudes: `1e-3`, `1e-4`, `1e-5`
- 3 methods per H2 case: GLA, oracle-tuned FGLA, geometry-optimal Oracle
- 270 H2 runs total
- 180 local iterations per H2 run

## Automated tests

```text
6 passed
```

The Phase-1B tests are retained and two Phase-1C grid tests are added.

## H1 — Tangent geometry identity

Result: **STRONG PASS**.

- Maximum relative Jacobian/principal-angle spectral error: `1.0401041157141908e-15`
- Median relative spectral error: `8.154345658883253e-16`
- Every case has exactly one neutral eigenvalue
- H1 gate: `PASS`

Across all 30 STFT instances, the numerical spectrum of the local Griffin–Lim Jacobian matches the squared-cosine principal-angle spectrum at machine precision.

Generated diagnostic:

`results/phase1c/figures/D1_geometry_identity.png`

## H2 — Predicted versus observed local contraction

Result: **PASS**.

Median relative fitted-rate errors:

- GLA: `1.2280913825695168e-08`
- Oracle-tuned FGLA: `0.0055696003753962576` (~0.56%)
- Geometry-optimal Oracle: `0.005967589282080471` (~0.60%)

90th-percentile relative fitted-rate errors:

- GLA: `3.678918692044512e-07`
- Oracle-tuned FGLA: `0.009314192843547134` (~0.93%)
- Geometry-optimal Oracle: `0.012944248251004646` (~1.29%)

The predicted ordering

```text
q_oracle < q_FGLA,opt < q_GLA
```

holds for 100% of matched runs, and the **observed fitted ordering also holds for 100%** of matched runs.

Generated diagnostic:

`results/phase1c/figures/D2_rate_prediction.png`

## Finite-window audit

Phase-1B showed a visible positive fitted-rate bias for accelerated methods. Phase-1C therefore explicitly audits early, middle, late, and adaptive-late fitting windows.

A critical numerical point was confirmed during development: once the accelerated trajectory reaches approximately machine-noise-level orbit errors, including those points in a log-linear tail fit can spuriously push the estimated contraction factor back toward one. Phase-1C therefore fits only within a trustworthy numerical error range (`> 1e-10` in the current small explicit-matrix diagnostics). This is an estimator hygiene rule, not a change to the algorithm or theorem.

After excluding numerical-floor contamination, the median accelerated fitted-rate bias is approximately 0.5–0.6%, and the 90th-percentile Oracle error is about 1.3%.

Generated diagnostic:

`results/phase1c/figures/D2b_finite_window_audit.png`

## Gate decision

```text
H1 = STRONG PASS
H2 = PASS
Predicted ordering fraction = 1.00
Observed ordering fraction = 1.00
PHASE-1C GATE = GREEN
```

No computational evidence from Phase-1C requires reopening G1–G3.

## Reproduction command

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
python reproduce/run_phase1c.py
```

Outputs are written to `results/phase1c/` as JSON, CSV, and PNG files.

## Recommended next scientific stage

Proceed to **Phase-1D — Online Dominant Spectral-Edge Identification Engine v1** only after independently reproducing Phase-1C on the target machine. Phase-1D should keep the Oracle spectrum offline as diagnostic truth and test whether passive secant/Ritz estimates recover the dominant transverse edge without additional projection/STFT pairs.
