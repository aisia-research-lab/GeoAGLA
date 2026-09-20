# Reproduce Package: One-Command Reproduction Scripts

The `reproduce/` package provides one-command execution runners for each experimental phase of the GeoAGLA project. These scripts ensure 100% compatibility across execution environments (Local Workstation, Compute Server, Kaggle, and Google Colab).

---

## Runner Catalog

| Script | Phase | Description | Output Directory |
| :--- | :--- | :--- | :--- |
| `run_phase1b.py` | Phase 1B | Unit tests + S0 (Linear modal dynamics) + H1 (Geometry-spectral correspondence) + H2 (Oracle rate prediction). | `results/phase1b/` |
| `run_phase1c.py` | Phase 1C | Multi-STFT grid sweep across 202 audio configurations. | `results/01_phase1_reproduction/phase1c/` |
| `run_phase1d.py` | Phase 1D | Online Ritz dominant-edge tracking & error milestone verification. | `results/01_phase1_reproduction/phase1d/` |
| `run_phase1e.py` | Phase 1E | Safeguarded online acceleration (running envelope & GLA fallback). | `results/01_phase1_reproduction/phase1e/` |
| `run_phase1er.py` | Phase 1E-R | Horizon policy analysis and switching dynamics. | `results/01_phase1_reproduction/phase1er/` |
| `run_phase2a.py` | Phase 2A | Synthetic signal-scale transfer across dimensions. | `results/02_phase2_transfer/phase2a/` |
| `run_phase2a_real_audio.py` | Phase 2A (Audio) | Real audio waveform transfer (`.wav`). | `results/phase2a_real_audio/` |
| `run_phase2b.py` | Phase 2B | Full real-audio basin sweep. | `results/phase2b/` |
| `run_phase2b_smoke.py` | Phase 2B (Smoke) | Fast smoke test on 2 synthetic signals (~15s, no external audio required). | `results/02_phase2_transfer/phase2b_smoke/` |
| `run_phase2b_checkpointed.py` | Phase 2B (Batch) | Resumable batch runner with checkpointing and deadline control. | `results/05_real_audio_basin_transfer/checkpointed/` |

---

## Usage Instructions

### 1. Execute from Repository Root:
```bash
# Run Phase 1B:
python -m reproduce.run_phase1b

# Run Phase 1C:
python -m reproduce.run_phase1c

# Run Phase 1D:
python -m reproduce.run_phase1d

# Run Phase 1E-R:
python -m reproduce.run_phase1er

# Run Phase 2A:
python -m reproduce.run_phase2a

# Run Phase 2B Smoke Test (fast ~15s, self-contained):
python -m reproduce.run_phase2b_smoke

# Run Phase 2B Checkpointed on Audio Corpus:
python -m reproduce.run_phase2b_checkpointed --audio-dir data/audio_samples --batch-size 2
```

### 2. Direct Script Invocation:
```bash
python reproduce/run_phase1b.py
python reproduce/run_phase2b_smoke.py
```
