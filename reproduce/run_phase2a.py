from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))

def main():
    print("=== Phase-2A: Controlled synthetic signal-scale transfer ===")
    subprocess.run([
        sys.executable, "-m", "experiments.05_real_audio_basin_transfer.01_phase2a_synthetic_transfer"
    ], check=True, cwd=str(ROOT))
    print("\nPhase-2A complete. See results/02_phase2_transfer/phase2a/summary.json")

if __name__ == "__main__":
    main()
