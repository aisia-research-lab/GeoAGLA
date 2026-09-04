# Phase-1B Smoke Report

Execution date: 2026-09-04
Environment: CPU-only Python environment in the ChatGPT build container.

## Unit tests

`4 passed`.

The tests cover:
- orthogonal range projector consistency;
- Jacobian/principal-angle spectral identity;
- spectral minimax endpoint equioscillation;
- oracle minimax contraction strictly below optimal FGLA on representative intervals.

## H1 smoke result

Controlled periodic Gaussian-window STFT case:
- relative Jacobian-vs-principal-angle spectral error: `8.77e-16`;
- symmetry error after numerical representation: `0.0`;
- neutral eigenvalue count: `1`;
- real range dimension: `32`.

This passes the Phase-1A H1 tolerance by a wide margin.

## H2 smoke result

Controlled feasible STFT case:
- transverse `lambda_plus = 0.9984540016546004`;
- GLA predicted/observed: `0.9984540 / 0.9984541`;
- oracle-optimal FGLA predicted/observed: `0.9606808 / 0.9726906`;
- Oracle geometry method predicted/observed: `0.9451619 / 0.9581719`.

The finite-window observed rates preserve the predicted ordering:

`Oracle geometry < oracle-optimal FGLA < GLA`.

The small positive bias for the critically damped accelerated methods is expected
from finite-window fitting (double-root dynamics include a polynomial prefactor).
The exact modal-radius identities are separately asserted in the unit tests.

## S0 note

The S0 JSON includes finite-window log-fit estimates, which are intentionally
not used as exact theorem assertions. Exact worst-case modal radii are verified
by `tests/test_minimax.py` at numerical precision.
