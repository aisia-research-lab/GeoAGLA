from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))

def run_module(module):
    print(f"\n=== {module} ===")
    subprocess.run([sys.executable, "-m", module], check=True, cwd=str(ROOT))

def main():
    print("=== Phase-1B: Unit tests ===")
    subprocess.run([sys.executable, "run_tests.py"], check=True, cwd=str(ROOT))
    run_module("experiments.01_linear_modal_dynamics.01_s0_linear_modal_dynamics")
    run_module("experiments.01_linear_modal_dynamics.02_h1_geometry_spectral_correspondence")
    run_module("experiments.01_linear_modal_dynamics.03_h2_oracle_rate_prediction")
    print("\nPhase-1B reproduction complete. See results/phase1b/")

if __name__ == "__main__":
    main()
