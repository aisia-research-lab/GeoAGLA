# E10R2_CANONICAL_IMPORT_AUDIT.md

Audit performed by static source inspection of the delivered
`GeoAGLA_E10R_Closure_v1_1` package plus the new
`04_run_e10r2_canonical.py` / `tests/test_e10r2_equivalence.py`.
All 18 equivalence tests (Gates B, C, D, E, no-oracle-leakage) were executed
and PASSED — see `pytest.log`. This document records the import-identity
findings (Gate A); it does not itself replace the test run.

| component | canonical source file | imported symbol | wrapper used? | local reimplementation? | PASS/FAIL |
|---|---|---|---|---|---|
| STFT operator | `src/geometry_gla/operators/stft_fft.py` | `FFTAnalysisOperator` | direct import | NO | PASS |
| FGLA parameter synthesis | `src/geometry_gla/algorithms/minimax.py` | `fgla_opt` | direct import | NO | PASS |
| One-edge oracle parameter synthesis | `src/geometry_gla/algorithms/minimax.py` | `oracle_minimax` | direct import | NO | PASS |
| Online policy (`online_full`) | `src/geometry_gla/algorithms/online_safe.py` | `run_online_policy` | direct import, called with `policy="dynamic_envelope"` exactly as guide sec. 6/11 requires | NO | PASS |
| Online ablation (`online_raw`/`online_env`/`online_fallback`) | `src/geometry_gla/algorithms/online_ablation.py` | `run_online_ablation` | direct import; this module itself only composes canonical primitives (`_align_pair`, `_edge_from_history`, `_one_step`, `_run_block` from `online_safe.py`, `checkpoint_accept` from `safeguards/checkpoint.py`, `oracle_minimax` from `minimax.py`) — no independent math | thin wrapper only, no new algorithm | PASS |
| Ritz estimator | `src/geometry_gla/estimators/ritz.py` | `ritz_largest` (used internally by `online_safe._edge_from_history`, not called directly by the E10-R2 runner) | not imported by runner — reached only via canonical `online_safe`/`online_ablation` | NO | PASS |
| Checkpoint / rollback | `src/geometry_gla/safeguards/checkpoint.py` | `checkpoint_accept`, `restricted_merit_gradient_norm` (reached via `online_safe`/`online_ablation`) | not imported by runner directly | NO | PASS |
| Audio loading, STFT window, orbit distance, magnitude residual, success rule, fixed-parameter rollout | `experiments/05_real_audio_basin_transfer/03_phase2b_real_audio_basin_sweep.py` (loaded as module `B` via `importlib`) | `load_audio`, `_window`, `_init_state`, `_fixed`, `_errors`, `_rate`, `_magnitude_residual`, `_success`, `orbit_distance` | direct call through `B.*` | NO | PASS |
| Success threshold | `configs/phase2b_grid.json` → `basin_success` | `final_orbit_ratio_max=0.10`, `final_magnitude_residual_max=1e-5` | read directly, also asserted at runtime in `04_run_e10r2_canonical.py` (`NO-GO` if it drifts) | NO | PASS |

## No hardcoded `1e-3` found

`grep` of `04_run_e10r2_canonical.py` and the canonical modules above for
`1e-3` / `0.001` found no occurrence tied to the success criterion. The only
`1e-3`-scale constants in the repository are unrelated numerical tolerances
(`phase_tol`, `svd_rtol` family), not the basin-success magnitude threshold.

## Scope note

This audit covers the code as delivered in this package as of this session.
It does not certify that a *different*, previously executed E10-R
standalone build (referenced in the guide's motivation section) was
free of drift — only that the canonical repository code and the new
E10-R2 runner built from it are equivalent, as proven by the 18 passing
equivalence tests.
