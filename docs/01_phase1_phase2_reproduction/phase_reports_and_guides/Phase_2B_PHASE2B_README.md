# Phase-2B — Real-Audio Basin & Geometry Validation v1

## Scientific purpose

Phase-2B is the first gate that uses **user-supplied recorded WAV audio**. It does not retune the Phase-1E-R method. The frozen online accelerator remains

- Ritz memory `p = 3`;
- checkpoint block size `K = 8`;
- spectral margin `Delta = 0`;
- `dynamic_envelope` edge policy;
- safe fallback = GLA checkpoint block.

The gate asks whether the Phase-1 geometry story transfers from deterministic audio-like signals to actual recordings, and whether the online method preserves a useful local basin while the safeguard remains quiet.

## What is audited

For every regular audio excerpt and STFT profile, the engine records the dominant transverse edge `lambda_plus`, the gap `1-lambda_plus`, an independent power/principal-angle check, near-zero coefficient statistics, passive Ritz edge error, Online/FGLA/Oracle local rates, checkpoint rejections, and E1 fallback failures.

Two controlled initialization families are used:

1. **Transverse coefficient perturbations** with levels `1e-3, 1e-2, 5e-2`.
2. **Magnitude-preserving phase jitter before range projection** with standard-deviation levels `0.05, 0.15, 0.30` radians.

Each is repeated for two frozen random seeds. These are local/basin diagnostics; Phase-2B does not yet claim recovery from arbitrary random or zero phase.

## Frozen STFT profiles

- `agla_gaussian`: Gaussian window 256, hop 32, FFT 256.
- `mezza_hann`: Hann window 512, hop 128, FFT 512 at 16 kHz (32 ms / 8 ms).

Audio is converted to mono, resampled to 16 kHz, mean-centered, and a deterministic maximum-RMS 4096-sample excerpt is selected. The excerpt is norm-normalized. Original WAV files are never modified.

## Gate definitions

- **G2B-A Geometry:** maximum independent geometry relative error <= `3e-3`.
- **G2B-B Active edge:** median final Ritz relative edge error <= `1e-2`.
- **G2B-C Small basin:** Online succeeds on >= `60%` of the smaller perturbation cases.
- **G2B-D Basin non-shrink:** Online success fraction may trail FGLA by at most `5 percentage points`.
- **G2B-E Paired-success rate:** among runs where both Online and FGLA return to the reference orbit, Online beats FGLA in >= `60%` and median rate ratio is < 1.
- **G2B-F Safeguard:** mean late rejection <= `10%` and safe-fallback E1 failures = 0.

`GREEN` requires all six. Gates are intentionally not modified after results are seen.

## Why real WAV files are not bundled

The repository does not redistribute third-party recordings. This avoids hidden licensing assumptions and forces publication experiments to carry an explicit dataset manifest. A deterministic generated-WAV smoke test is included only to test code paths; it is **not** evidence for the real-audio scientific gate.
