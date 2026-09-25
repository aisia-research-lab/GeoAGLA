#!/usr/bin/env python3
"""
Experiment E5: Real-Audio Basin Transfer & Robustness across MUSAN Recordings.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Evaluates:
- STFT-FFT isometric operator equivalence (Phase 2A).
- Real-audio single/multi-file pilot verification.
- Large-scale basin of attraction sweep across perturbation levels and initializations (Phase 2B).
- Checkpointed multi-batch runner with auto-resume and deadline control.

Flags:
    --stft-fft:      Run STFT-FFT operator isometric equivalence verification.
    --pilot:         Run fast real-audio pilot on sample audio files (Default).
    --sweep:         Run Phase 2B basin sweep on specified --audio-dir.
    --checkpointed:  Run checkpointed multi-batch runner with auto-resume.
    --audio-dir:     Path to audio files (default: data/audio_samples).
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "experiments" / "05_real_audio_basin_transfer"

def main():
    parser = argparse.ArgumentParser(description="Run Experiment E5 (Real-Audio Basin Transfer)")
    parser.add_argument("--stft-fft", action="store_true", help="Run STFT-FFT isometric equivalence test")
    parser.add_argument("--pilot", action="store_true", help="Run fast real-audio pilot")
    parser.add_argument("--sweep", action="store_true", help="Run Phase 2B real-audio basin sweep")
    parser.add_argument("--checkpointed", action="store_true", help="Run checkpointed multi-batch runner")
    parser.add_argument("--audio-dir", type=str, default="data/audio_samples", help="Path to audio directory")
    args, unknown = parser.parse_known_args()

    print("=" * 78)
    print("EXPERIMENT E5: REAL-AUDIO BASIN TRANSFER & INITIALIZATION ROBUSTNESS")
    print("=" * 78)

    if args.stft_fft:
        script = EXP_DIR / "01_phase2a_synthetic_transfer.py"
        cmd = [sys.executable, str(script)] + unknown
    elif args.sweep:
        script = EXP_DIR / "03_phase2b_real_audio_basin_sweep.py"
        cmd = [sys.executable, str(script), "--audio-dir", args.audio_dir] + unknown
    elif args.checkpointed:
        script = EXP_DIR / "05_run_phase2b_checkpointed.py"
        cmd = [sys.executable, str(script), "--audio-dir", args.audio_dir] + unknown
    else:
        # Default: run pilot test
        script = EXP_DIR / "02_phase2a_wav_transfer.py"
        cmd = [sys.executable, str(script)] + unknown

    subprocess.run(cmd, cwd=str(ROOT), check=True)
    print("\n>>> Experiment E5 completed successfully! <<<")

if __name__ == "__main__":
    main()
