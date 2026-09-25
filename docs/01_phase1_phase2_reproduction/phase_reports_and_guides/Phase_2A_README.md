# Geometry-Certified Acceleration of Griffin–Lim Phase Retrieval

This repository snapshot contains the reproducible research engines through:

**Phase-2A — Realistic STFT/Audio Geometry Transfer Gate v1**

Current controlled chain:

`Phase-1B GREEN -> Phase-1C GREEN -> Phase-1D YELLOW-GREEN -> Phase-1E YELLOW -> Phase-1E-R GREEN -> Phase-2A controlled GREEN`

Phase-2A adds a matrix-free signal-scale STFT operator, dominant transverse spectral-edge computation, factorized tangent-geometry verification, inherited passive Ritz tracking (`p=3`), inherited safeguarded dynamic-envelope online acceleration (`K=8`, `Delta=0`), and an optional user-supplied WAV extension.

Start with:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pytest -q
python reproduce/run_phase2a.py
```

See `Phase-2A_Reproduction_Guide_v1.md` and `PHASE2A_VERIFICATION_REPORT.md`.
