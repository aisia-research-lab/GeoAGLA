from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))

def main():
    print("=== Phase-1D: Unit tests ===")
    subprocess.run([sys.executable, "run_tests.py"], check=True, cwd=str(ROOT))
    print("\n=== Phase-1D: Online dominant-edge diagnostics ===")
    subprocess.run([
        sys.executable, "-m", "experiments.06_multi_horizon_online_adaptation.01_phase1d_online_edge_tracking"
    ], check=True, cwd=str(ROOT))
    print("\nPhase-1D complete. See results/01_phase1_reproduction/phase1d/summary.json")

if __name__ == "__main__":
    main()
