from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))

def main():
    print("=== Phase-1E-R: Horizon policy and repair ===")
    subprocess.run([
        sys.executable, "-m", "experiments.06_multi_horizon_online_adaptation.03_phase1er_repair_and_horizon_policy"
    ], check=True, cwd=str(ROOT))
    subprocess.run([
        sys.executable, "-m", "experiments.06_multi_horizon_online_adaptation.horizon"
    ], check=True, cwd=str(ROOT))
    print("\nPhase-1E-R complete. See results/01_phase1_reproduction/phase1er/summary.json")

if __name__ == "__main__":
    main()
