# Phase-2A Verification Report v1

## Reference execution

Environment: Python/NumPy/SciPy/Matplotlib, matrix-free periodic STFT, deterministic procedural audio-like signals.

Unit/integration tests:

- **15 passed**

Reference command:

```bash
python reproduce/run_phase2a.py
```

## Controlled signal-scale results

Four regular cases completed with no skips:

- harmonic, `N=256`, Hann 128, hop 16, FFT 128
- chirp, `N=512`, Hann 128, hop 16, FFT 128
- speech-like, `N=512`, Gaussian 256, hop 32, FFT 256
- transient, `N=1024`, Hann 256, hop 32, FFT 256

Summary:

| Diagnostic | Reference result | Gate |
|---|---:|---:|
| max geometry relative error | `8.7796e-4` | <= `5e-3` |
| median final active-edge relative error | `3.3920e-6` | <= `2e-2` |
| Online beat fraction vs FGLA-opt | `0.75` | >= `0.70` |
| median `q_online/q_FGLA` | `0.99465` | < `1` |
| P90 `q_online/q_FGLA` | `1.00132` | diagnostic |
| mean late reject fraction | `0.0` | <= `0.05` |
| fallback E1 failures | `0` | `0` |

Hence:

- G2A geometry transfer: **PASS**
- G2B active-edge tracking: **PASS**
- G2C online-rate transfer: **PASS**
- G2D safeguard transfer: **PASS**
- **Phase-2A controlled signal-scale gate: GREEN**

## Horizon audit

The same trajectories were evaluated at frozen prefix horizons:

| Horizon | beat fraction | median `q_online/q_FGLA` | P90 |
|---:|---:|---:|---:|
| 120 | 0.50 | 0.99868 | 1.00550 |
| 240 | 0.75 | 0.99312 | 0.99834 |
| 360 | 0.75 | 0.99465 | 1.00132 |

This continues the Phase-1E-R observation that rate realization is horizon-dependent. It does **not** justify a claim of uniform finite-horizon superiority.

## Real-audio status

**PENDING.** The default package deliberately does not download or bundle external audio datasets. Use the optional command below on user-supplied WAV files before making publication claims about real recorded audio:

```bash
python reproduce/run_phase2a_real_audio.py --audio-dir /path/to/wavs
```

The controlled result should therefore be described as *signal-scale geometry transfer*, not yet as a complete real-audio validation.

## Reproducibility repair

The Phase-1E-R import defect has been repaired. `reproduce/run_phase2a.py` bootstraps both the repository root and `src/`, so the documented command works without manually setting `PYTHONPATH`.
