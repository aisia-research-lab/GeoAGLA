# Phase-1D — Online Dominant Spectral-Edge Identification Engine v1
## Verification Report

## Gate objective

Phase-1D tests H3:

\[
\widehat\lambda_{+,n}\to\lambda_+
\]

from passive trajectory data, without adding another Griffin–Lim map / STFT-projection pair per iteration.

For GLA,

\[
s_n=c_n-c_{n-1},\qquad y_n=G(c_n)-G(c_{n-1})=c_{n+1}-c_n=s_{n+1},
\]

so the secant-image pair is already contained in the trajectory.

## Executed checks

- Full repository test suite: **9/9 tests passed**.
- D0 synthetic exact-operator tests.
- D1 controlled local STFT tests on 6 STFT configurations, 3 seeds, 2 perturbation scales, and memories \(p\in\{1,3,5\}\).
- D2 exact hidden-mode non-identifiability construction.
- Automatic estimator selection and diagnostic figures.

## D0 — Synthetic estimator validation

Maximum absolute dominant-edge error:

\[
1.17\times 10^{-13}.
\]

**Decision: PASS.** The secant/Ritz implementation reproduces the active dominant eigenvalue to numerical precision in exact linear tests.

## D1 — Local STFT passive identification

There are 108 estimator rows:

\[
6\ \text{STFT configs}\times 3\ \text{seeds}\times 2\ \text{perturbations}\times 3\ \text{memories}.
\]

Aggregate tail errors:

| Memory | Median relative error | 90th percentile relative error | Median under-estimation fraction |
|---:|---:|---:|---:|
| 1 | 0.594% | 0.978% | 100% |
| **3** | **0.233%** | **0.487%** | **100%** |
| 5 | 0.461% | 1.065% | 10.9% |

The frozen selection rule picks

\[
\boxed{p=3}
\]

because it has the lowest 90th-percentile tail error.

For \(p=3\):

\[
\operatorname{median}\frac{|\widehat\lambda_+-\lambda_+|}{\lambda_+}
=2.33\times10^{-3},
\]

and

\[
P_{90}=4.87\times10^{-3}.
\]

Both are far inside the frozen 5% median and 10% P90 gates.

**Decision: STRONG PASS for trajectory-active dominant-edge estimation.**

## Direction of estimator bias

For the selected \(p=3\) estimator, the median tail under-estimation fraction is 1.0. Thus the raw estimator typically approaches the dominant edge from below on these controlled GLA trajectories.

This is scientifically important:

\[
\boxed{\widehat\lambda_+\text{ is not a certified upper bound.}}
\]

It must not be used by itself as a stability certificate for aggressive online parameter synthesis.

## D2 — Exact passive non-identifiability boundary

Two PSD self-adjoint operators were constructed that agree on the entire excited 3D subspace but have different hidden full spectral edges:

\[
\lambda_+(J_A)=0.90,\qquad \lambda_+(J_B)=0.99.
\]

The passive trajectories are exactly identical:

\[
\max_n\|x_n^A-x_n^B\|=0,
\]

and both passive Ritz estimators return

\[
\widehat\lambda_+=0.80,
\]

which is the active-subspace edge.

Therefore finite passive data cannot certify an unexcited full-spectrum edge. This computational construction matches the theoretical non-identifiability statement and prevents overclaiming H3.

## Frozen interpretation

Phase-1D supports the following statement:

> A small-memory passive secant/Ritz estimator can accurately identify the trajectory-active dominant spectral edge in regular local STFT phase-retrieval trajectories, with negligible operator cost. It does not certify unseen spectral modes or provide a deterministic outer spectral bound.

It does **not** support the statement that the complete transverse spectrum can be passively recovered.

## Gate decision

\[
\boxed{\textbf{PHASE-1D = YELLOW-GREEN}}
\]

Reason:

- estimator implementation: GREEN;
- controlled active-edge accuracy: STRONG GREEN;
- no-extra-projection requirement: GREEN;
- full-spectrum certification: impossible from finite passive data;
- raw estimate as safety bound: RED / prohibited;
- implication for Phase-1E: use conservative margin/envelope plus independent safeguard.

## Phase-1E handoff

The next engine should freeze \(p=3\) as the default online estimator and synthesize parameters from a conservative quantity such as

\[
\overline\lambda_{+,n}=\min\{1-\epsilon,\widehat\lambda_{+,n}+\Delta_n\},
\]

while treating \(\Delta_n\) as a performance margin rather than a proof certificate. Global safety must come from the fixed-merit checkpoint safeguard, not from the Ritz estimate.
