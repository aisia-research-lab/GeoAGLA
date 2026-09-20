from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))

def main():
    print("=== Phase-1C: Unit tests ===")
    subprocess.run([sys.executable, "run_tests.py"], check=True, cwd=str(ROOT))
    print("\n=== Phase-1C: Multi-STFT grid sweep ===")
    subprocess.run([
        sys.executable, "-m", "experiments.02_controlled_local_rates.01_controlled_multi_stft_grid_sweep",
        "--config", "configs/phase1c_grid.json",
        "--out", "results/01_phase1_reproduction/phase1c"
    ], check=True, cwd=str(ROOT))
    print("\nPhase-1C complete. See results/01_phase1_reproduction/phase1c/summary.json")

if __name__ == "__main__":
    main()
