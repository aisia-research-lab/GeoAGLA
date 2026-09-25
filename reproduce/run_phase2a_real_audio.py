from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))

def main():
    p = argparse.ArgumentParser(description="Phase-2A real audio WAV transfer")
    p.add_argument("--audio-dir", required=True, help="Path to audio directory")
    p.add_argument("--max-files", type=int, default=4)
    p.add_argument("--N", type=int, default=2048)
    p.add_argument("--n-iter", type=int, default=360)
    args = p.parse_args()

    cmd = [
        sys.executable, "-m", "experiments.05_real_audio_basin_transfer.02_phase2a_wav_transfer",
        "--audio-dir", str(args.audio_dir),
        "--max-files", str(args.max_files),
        "--N", str(args.N),
        "--n-iter", str(args.n_iter),
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT))

if __name__ == "__main__":
    main()
