# Phase-2B Verification Report v1

## Build status

**Engine status: READY FOR INDEPENDENT REAL-AUDIO EXECUTION.**

The repository was extended from the independently reproduced Phase-2A package. Phase-1E-R parameters were frozen without retuning. The direct reproduction launcher prepends the repository root and `src/` internally, so no manual `PYTHONPATH` workaround is required.

## Local software verification

- Unit/integration tests: **17 passed**.
- Mechanical generated-WAV smoke path: completed end-to-end.
- Smoke output is intentionally excluded from scientific gate interpretation because generated signals are not recorded audio and the shortened smoke configuration is not the frozen Phase-2B configuration.

## New Phase-2B components

- `configs/phase2b_grid.json`
- `experiments/phase2b_real_audio/run.py`
- `reproduce/run_phase2b.py`
- `reproduce/run_phase2b_smoke.py`
- `tests/test_phase2b_audio.py`
- `PHASE2B_README.md`
- `Phase-2B_Reproduction_Guide_v1.md`

## Frozen scientific design

Real audio is resampled to 16 kHz and evaluated under two STFT profiles (AGLA-style Gaussian and Mezza-style Hann). For each regular file/profile pair, the engine audits local tangent geometry and then maps two basin families: transverse coefficient perturbations and phase-jitter/range-projection perturbations. Online, oracle-FGLA, and Oracle-[0,lambda+] use the same initial state.

The primary Phase-2B output is not just a rate table. It tests a causal chain:

`real recording -> regular local geometry -> passive edge identification -> geometry-synthesized acceleration -> basin preservation -> checkpoint safety`.

## Gate status

**Real-audio gate: PENDING.**

No third-party recording is silently bundled or substituted. Phase-2B becomes scientifically auditable only after the user executes the frozen engine on real WAV recordings and returns the machine-readable ledgers.
