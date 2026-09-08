# Phase-2A Reproduction Guide v1

## 1. Create environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## 2. Run tests

```bash
pytest -q
```

Expected package reference: `15 passed`.

## 3. Run the deterministic Phase-2A controlled gate

```bash
python reproduce/run_phase2a.py
```

No `PYTHONPATH` workaround is required in this release.

Expected outputs:

```text
results/phase2a/summary.json
results/phase2a/case_results.json
results/phase2a/case_results.csv
results/phase2a/horizon_audit.json
results/phase2a/horizon_summary.json
results/phase2a/figures/2A_D1_geometry_transfer.png
results/phase2a/figures/2A_D2_edge_tracking.png
results/phase2a/figures/2A_D3_horizon_transfer.png
results/phase2a/figures/2A_D4_online_trajectories.png
```

Please send back at least:

```text
results/phase2a/summary.json
results/phase2a/case_results.json
results/phase2a/horizon_summary.json
```

for independent audit.

## 4. Optional real-WAV extension

Put ordinary PCM WAV files in a folder and run:

```bash
python reproduce/run_phase2a_real_audio.py --audio-dir /path/to/wavs
```

Default behavior:

- at most 4 WAV files;
- middle excerpt of `N=2048` samples;
- Hann 256, hop 32, FFT 256;
- 360 iterations;
- same frozen `p=3`, `K=8`, `Delta=0`, dynamic-envelope policy.

Options:

```bash
python reproduce/run_phase2a_real_audio.py \
  --audio-dir /path/to/wavs \
  --max-files 6 \
  --N 2048 \
  --n-iter 360
```

Outputs go to:

```text
results/phase2a_real_audio/wav_results.json
results/phase2a_real_audio/summary.json
```

The WAV extension is a transfer diagnostic, not yet the full publication benchmark.

## 5. Scientific interpretation

A GREEN controlled gate means the Phase-1 mechanism survives matrix-free signal-scale STFT computation. It does **not** by itself establish performance on EBU/TIMIT or a full realistic audio benchmark. That requires the real-audio extension and then the publication-scale benchmark gate.
