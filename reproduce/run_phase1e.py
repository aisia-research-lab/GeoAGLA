from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))

def main():
    print("=== Phase-1E: Unit tests ===")
    subprocess.run([sys.executable, "run_tests.py"], check=True, cwd=str(ROOT))
    print("\n=== Phase-1E: Safeguarded online acceleration ===")
    subprocess.run([
        sys.executable, "-m", "experiments.06_multi_horizon_online_adaptation.02_phase1e_safeguarded_acceleration"
    ], check=True, cwd=str(ROOT))
    print("\nPhase-1E complete. See results/01_phase1_reproduction/phase1e/summary.json")

if __name__ == "__main__":
    main()
