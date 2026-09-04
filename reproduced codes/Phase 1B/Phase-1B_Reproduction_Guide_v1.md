# Phase-1B — Reproducible Oracle Geometry Engine v1
## Installation, Smoke-Test, and Reproduction Guide

This guide records the instructions for running the **Phase-1B — Reproducible Oracle Geometry Engine v1** package.

## 1. Current status

The packaged implementation has been smoke-tested with:

- **4/4 unit tests passing**
- **H1 geometry smoke test passing**
- **H2 oracle-rate smoke test passing**

For H1, the numerical discrepancy between the Jacobian spectrum and the squared-cosine principal-angle spectrum was approximately

$$8.77\times 10^{-16}.$$

The test also detected exactly one neutral eigenvalue associated with global phase.

For H2, the representative observed contraction ordering was

$$q_{\mathrm{Oracle}} < q_{\mathrm{FGLA,opt}} < q_{\mathrm{GLA}},$$

with smoke-test values

$$0.9582 < 0.9727 < 0.99845.$$

Finite-window fitted accelerated rates can be slightly above the theoretical asymptotic rate because of finite-window effects and the polynomial prefactor associated with repeated/critically damped roots. Exact modal spectral-radius identities are tested separately by the unit tests.

## 2. Setup on macOS/Linux

After extracting `geometry-certified-gla-phase1b-v1.zip`:

```bash
cd geometry-certified-gla-phase1b
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

## 3. Run the complete Phase-1B reproduction

```bash
python reproduce/run_phase1b.py
```

The pipeline executes:

1. Unit tests
2. S0 synthetic modal verification
3. H1 tangent-geometry verification
4. H2 oracle-rate verification

The unit-test stage should report:

```text
4 passed
```

## 4. Run individual components

```bash
pytest -q
python -m experiments.s0_linear.run
python -m experiments.h1_geometry.run
python -m experiments.h2_oracle_rate.run
```

## 5. Output files

Results are written to:

```text
results/phase1b/s0_results.json
results/phase1b/h1_results.json
results/phase1b/h2_results.json
```

Retain these raw outputs rather than manually copying numerical results.

## 6. What the engine implements

The current codebase contains:

- periodic STFT operator;
- orthogonal projection onto the STFT range;
- magnitude projection;
- analytic tangent derivative;
- realification of complex subspaces;
- local Griffin–Lim Jacobian;
- principal-angle computation;
- transverse-spectrum extraction;
- exact geometry-optimal $q^\star(\lambda_-,\lambda_+)$;
- optimal FGLA baseline;
- AGLA state recurrence;
- global-phase alignment;
- contraction-rate estimation.

## 7. Reproducibility design

The repository is intended to evolve into the public code release accompanying the IEEE TSP manuscript. It already includes deterministic seeds, automated `pytest` assertions, raw JSON outputs, README documentation, a smoke-test report, MIT license, and `CITATION.cff`.

The final reproducibility principle is:

> Every manuscript figure and table should be generated from code and machine-readable experiment outputs, without manually edited numerical results.

## 8. H1 interpretation

At a regular feasible point,

$$J_\star=DG(c^\star)|_U=P_UP_V|_U,$$

where $V=T_{C_2}(c^\star)$. The predicted transverse eigenvalues are

$$\lambda_j=\cos^2\theta_j.$$

The global-phase direction is treated separately because it gives the expected neutral eigenvalue

$$\lambda_{\mathrm{phase}}=1.$$

## 9. H2 interpretation

For a transverse spectral interval

$$[\lambda_-,\lambda_+]\subset[0,1),$$

the Oracle geometry method uses the theoretically derived minimax parameters and predicts $q^\star(\lambda_-,\lambda_+)$.

The principal diagnostic ordering is

$$q_{\mathrm{Oracle}}<q_{\mathrm{FGLA,opt}}<q_{\mathrm{GLA}}.$$

Phase-1B is a smoke-test package; it is not yet the multi-instance statistical validation required for the final manuscript.

## 10. Recommended first run

```bash
cd geometry-certified-gla-phase1b
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pytest -q
python reproduce/run_phase1b.py
```

If an error occurs, save the full terminal output together with:

```bash
python --version
python -m pip freeze
```

This helps distinguish environment/dependency problems from numerical or implementation issues.

## 11. Next stage after successful reproduction

The next planned package is:

**Phase-1C — Multi-Instance Oracle Geometry & Rate Verification Engine v1**

It will extend H1/H2 to a grid of STFT configurations, multiple seeds and feasible instances, automatically generate the geometry-identity and rate-prediction figures, and create aggregate machine-readable experiment ledgers.

Only after H1/H2 survive this multi-instance verification should the project proceed to Online-$\lambda_+$ estimation and safeguard experiments.

---

**Project:** Geometry-Certified Acceleration of Griffin–Lim Phase Retrieval  
**Package:** Phase-1B — Reproducible Oracle Geometry Engine v1  
**Status:** S0/H1/H2 smoke-tested; ready for independent reproduction.
