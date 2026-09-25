# Phase-2B Reproduction Guide v1

## 1. Install

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pytest -q
```

Expected package test status for v1: **17 passed**.

## 2. Prepare real WAV audio

Create a local folder containing 4–6 ordinary PCM WAV recordings. Diverse speech/music/transient content is preferred. Files may be in nested subfolders; `.wav` and `.WAV` are both discovered.

No labels are required. Do not manually crop or normalize files for the engine.

## 3. Preflight on two files

```bash
python reproduce/run_phase2b.py \
  --audio-dir "/absolute/path/to/wavs" \
  --max-files 2 \
  --out results/phase2b_preflight
```

Inspect `results/phase2b_preflight/summary.json`. If every geometry case is skipped as irregular, use different non-silent recordings rather than relaxing the regularity tolerance.

## 4. Frozen Phase-2B run

```bash
python reproduce/run_phase2b.py \
  --audio-dir "/absolute/path/to/wavs" \
  --max-files 6 \
  --out results/phase2b
```

Do **not** edit `configs/phase2b_grid.json` before the independent gate is audited.

## 5. Files to send for scientific audit

Please send:

```text
results/phase2b/summary.json
results/phase2b/audio_manifest.json
results/phase2b/geometry_results.json
results/phase2b/basin_results.json
results/phase2b/initialization_summary.json
```

The most important result is `summary.json`, but the other four are required to diagnose any YELLOW gate without parameter fishing.

## 6. Mechanical smoke test only

```bash
python reproduce/run_phase2b_smoke.py
```

This generates temporary artificial WAV files to verify decoding, STFT, geometry, initialization, safeguard, and result-writing paths. Its scientific gate status must be ignored.

## 7. Outputs

The engine creates JSON/CSV ledgers plus figures:

- `2B_D1_real_audio_geometry.png`
- `2B_D2_basin_profile.png`
- `2B_D3_rate_ratio.png` when paired-success runs exist
- `2B_D4_trajectories.png`

## 8. Interpretation rule

A real-audio `GREEN` is a transfer validation, not yet the final publication benchmark. It authorizes the next full benchmark stage; it does not establish global recovery from arbitrary initialization or uniform finite-budget superiority.
