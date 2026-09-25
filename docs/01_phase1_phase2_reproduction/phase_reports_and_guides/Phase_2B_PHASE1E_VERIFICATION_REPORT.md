# Phase-1E — Safeguarded Online-λ+ Acceleration Engine v1
## Verification Report

## Status

**Gate: YELLOW**

Phase-1E v1 validates the proof-compatible checkpoint architecture and the intended
estimator-independent safety mechanism, but the frozen H4 performance gate is not
met yet. The correct scientific interpretation is therefore: **safeguard core passes;
parameter-synthesis/performance layer requires one repair cycle before GREEN.**

## Frozen mechanism

The online method uses the Phase-1D passive Ritz estimator with memory `p=3`.
At each checkpoint it synthesizes a conservative lower-edge-zero design

\[
[0,\bar\lambda_{+,k}],\qquad
\bar\lambda_{+,k}=\operatorname{clip}(\widehat\lambda_{+,k}+\Delta,0,1-10^{-8}),
\]

and uses the closed-form minimax parameters with `beta=0`.

Safety does **not** come from the estimator. Candidate blocks are checked with the
fixed, candidate-parameter-independent checkpoint merit

\[
\Phi_s(t,t^-)=\tfrac12 d_{C_2}^2(t)+\tfrac{K_s}{2}\|t-t^-\|^2,
\]

with the v1 freeze

- `alpha_safe = 0`,
- `K_safe = 0.25`,
- `descent_a = 1e-4`.

The primary checkpoint test is

\[
\Phi_s(X_{k+1})+aD_k^2\le \Phi_s(X_k),
\]

where

\[
D_k^2=\sum_{j\in\text{block}}\|t_j-t_{j-1}\|^2.
\]

If an aggressive block fails, it is rolled back and replaced by a safe GLA block.
Rejected candidate secant information is discarded.

## Automated verification

The complete reproduction command reports:

```text
12 passed
```

The test suite includes the previous geometry/minimax/Ritz tests plus new
Phase-1E tests for the fixed merit, local safe-GLA decrease, and hostile estimator
perturbation.

## Main experiment grid

The current grid contains:

- 4 controlled STFT configurations;
- 3 seeds;
- 2 local perturbation levels;
- block sizes `K in {2,4,8}`;
- margins `Delta in {0,0.001,0.003}`.

Total safeguarded online runs:

\[
4\times3\times2\times3\times3=216.
\]

## Selected v1 setting

The automatic selection rule chooses

```text
block_size = 8
margin     = 0.001
```

with:

- fraction beating Oracle-tuned FGLA: **0.6667**;
- mean late rejection fraction: **0.0333**;
- mean overall rejection fraction: **0.0179**;
- median online/FGLA fitted-rate ratio: **0.9968**;
- P90 online/FGLA fitted-rate ratio: **1.0355**;
- safe-fallback E1 failures: **0**.

## Gate audit

### E1 — fixed-merit safe fallback

**PASS.** No fallback block violated the frozen E1 checkpoint inequality in the
main sweep.

### H5 — eventual safeguard inactivity

**PASS under the frozen diagnostic gate.** Mean late rejection fraction is about
3.3%, below the 5% diagnostic threshold.

This is empirical support for eventual inactivity; it is not itself the final
mathematical proof.

### Hostile estimator test

**PASS.** The selected safeguard was also tested after deliberately perturbing the
estimated edge by biases

```text
-0.05, -0.02, +0.05
```

across the controlled cases. The committed trajectories still reduced the orbit
error and the safe fallback continued to satisfy E1.

This supports the intended design principle:

> Estimation controls performance; the checkpoint controls safety.

### E2 relative-error diagnostic

For the selected setting the maximum observed diagnostic ratio

\[
\frac{\|\nabla \Phi_s(X_{k+1})\|}{D_k+D_{k-1}}
\]

was approximately

\[
0.156.
\]

This is encouraging evidence for a bounded relative-error constant on the tested
local regime. It must not yet be promoted to a theorem without the corresponding
uniform analytic argument.

### H4 — online acceleration versus Oracle-tuned FGLA

**FAIL under the frozen 70% gate.** The selected online method beats FGLA-opt on
16/24 controlled cases (66.7%), narrowly below the required 70% threshold.

The median rate ratio is below one, so the online method is slightly faster in the
median, but its P90 ratio exceeds one. The failure is concentrated in a small set
of configurations/seeds and cannot be hidden by aggregate averages.

## Scientific conclusion

Phase-1E v1 establishes a useful separation:

\[
\boxed{\text{safeguard architecture works empirically}}
\]

but

\[
\boxed{\text{online parameter synthesis is not yet robustly performance-optimal}.}
\]

Therefore the correct decision is

\[
\boxed{\textbf{PHASE-1E v1 = YELLOW}.}
\]

Do **not** claim H4 or the complete Phase-1E chain as GREEN from this package.

## Recommended next action

Before any realistic audio benchmark, run a narrow repair stage:

**Phase-1E-R — Online Parameter-Synthesis & Rate-Fitting Repair v1**

Its goals should be:

1. audit the H4 failures by configuration and perturbation;
2. replace the fixed additive margin with a geometry-scaled or confidence-aware
   synthesis rule;
3. separate genuine slowdowns from finite-window/numerical-floor rate fitting;
4. re-run the same frozen H4/H5 gates without changing the safeguard acceptance
   rule.

The checkpoint mechanism should remain frozen during that repair so that only the
performance layer changes.
