# Phase-1E-R — Online Rate-Realization Failure Decomposition & Repair v1

## Decision

**GREEN on the controlled Phase-1 grid.** The Phase-1E H4 miss is reproduced as a finite-horizon / estimator-maturation effect rather than a safeguard failure or a failure of the oracle spectral design.

## What was changed

The Phase-1E safeguard is frozen. This repair stage does **not** loosen E1, change the safe fallback, or tune the gate after seeing results. It decomposes the performance loss by changing only the parameter-update policy and the observation horizon.

The primary repaired policy is still passive `dynamic_envelope`, with memory `p=3`, block size `K=8`, and **zero additive margin**. No extra projection/STFT pair is used.

## Local reference run

- Tests: **13/13 passed**.
- Failure-decomposition runs: **192** = 24 regular cases × 8 policies.
- Selected practical policy: `dynamic_envelope`.
- H4 beat fraction at 240 iterations: **0.75**.
- Median `q_online/q_FGLA`: **0.997684**.
- P90 `q_online/q_FGLA`: **1.002835**.
- Mean late rejection fraction: **0.0**.
- Safe-fallback E1 failures: **0**.
- Median final active-edge relative error: **3.93e-6**.

The frozen-oracle control has median `q_online/q_oracle_fixed = 1.000507`, showing that the block/checkpoint implementation itself realizes the fixed oracle rate to about 0.05% median accuracy.

## Failure decomposition

Early freezing is harmful: `freeze_first` and `freeze_calibrated` beat FGLA in 0/24 cases, with median final edge errors about 5.25% and 2.07%, respectively. Thresholded and EMA updates also lag because they retain stale edge estimates. Continued passive updating is therefore required during the local transient.

The dynamic raw and dynamic envelope policies both beat FGLA in 18/24 cases at 240 iterations. The envelope is retained because it is the Phase-1E-compatible monotone edge state and is slightly better on the aggregate selection rule.

## Horizon audit

For the same `dynamic_envelope`, `K=8`, margin=0 policy:

| Horizon | Beat fraction | Median q ratio | P90 q ratio |
|---:|---:|---:|---:|
| 120 | 0.3333 | 1.00509 | 1.01659 |
| 180 | 0.5000 | 0.99889 | 1.00563 |
| 240 | 0.7500 | 0.99768 | 1.00284 |
| 360 | 1.0000 | 0.99424 | 0.99853 |

This directly explains the Phase-1E laptop result: at 180 iterations the zero-margin policy has a 50% beat fraction, matching the earlier observation. By 240 it crosses the pre-frozen 70% H4 gate, and by 360 all 24 controlled cases beat FGLA-opt.

## Scientific interpretation

The repaired conclusion is **not** “a larger margin fixes H4.” It is:

> Accurate passive edge identification needs enough residence time to mature and the accelerated recurrence needs enough post-identification iterations to realize its asymptotic spectral advantage.

Thus the observed Phase-1E failure is a rate-realization delay. The safeguard remains independent of the estimator and does not need to be weakened.

## Frozen recommendation for Phase-1F / S2

Use `p=3`, `K=8`, zero additive margin, dynamic running-envelope edge synthesis, and the unchanged fixed-merit checkpoint safeguard. Report both fixed-budget performance and a geometry-maturation diagnostic; do not claim uniform finite-horizon superiority.

The theorem-facing claim remains asymptotic/local: under active-edge consistency and eventual safeguard inactivity, the online method approaches the geometry-designed local regime. Finite-budget audio performance must be measured separately.
