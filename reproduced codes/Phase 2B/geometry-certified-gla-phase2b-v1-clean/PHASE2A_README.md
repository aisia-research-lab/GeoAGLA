# Phase-2A — Realistic STFT/Audio Geometry Transfer Gate v1

## Purpose

Phase-2A tests whether the Phase-1 geometry/acceleration mechanism survives the jump from tiny explicit-matrix diagnostics to matrix-free, signal-scale STFT operators.

The default deterministic gate uses four license-free audio-like signal families at `N=256, 512, 512, 1024`. It is intentionally reproducible and dataset-independent. A separate optional WAV extension is included for user-supplied real audio. **Publication claims about real audio remain pending until that extension is run.**

## Frozen algorithm

- passive Ritz memory: `p = 3`
- block length: `K = 8`
- synthesis margin: `Delta = 0`
- adaptation policy: `dynamic_envelope`
- safe fallback: GLA (`alpha=beta=0, gamma=1`)
- checkpoint merit parameters: `K_safe=0.25`, `descent_a=1e-4`

These are inherited from the independently reproduced Phase-1E-R gate. They are not retuned in Phase-2A.

## New signal-scale geometry engine

`FFTAnalysisOperator` implements a matrix-free periodic STFT. Because the full FFT is used per frame, the frame operator `T^*T` is diagonal. This gives inexpensive canonical least-squares synthesis and the isometric range map

`Q = T (T^*T)^(-1/2)`.

At a regular feasible point `c*`, the local signal-coordinate Jacobian is applied as

`J = Q^* P_V Q`,

where `P_V` is the tangent projection to the magnitude torus. The dominant transverse edge is computed by Lanczos/eigsh without forming the coefficient-space Jacobian matrix.

## Gates

- **G2A Geometry transfer:** independent factorized power check matches matrix-free eigsh dominant transverse edge with max relative error <= 0.5%.
- **G2B Active-edge tracking:** median final passive Ritz edge error <= 2%.
- **G2C Online-rate transfer:** Online-lambda+ beats FGLA-opt in >= 70% of controlled signal-scale cases and has median q-ratio < 1.
- **G2D Safeguard transfer:** mean late rejection <= 5% and zero fallback E1 failures.

The default package reports a **controlled signal-scale gate** and a separate **real-audio gate**. Do not collapse the two.
