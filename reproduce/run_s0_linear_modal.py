#!/usr/bin/env python3
"""
Experiment S0: Linear Modal Dynamics Smoke Test.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Validates the fundamental 2-mode scalar recurrence and confirms that the
asymptotic error contraction rate matches the spectral radius: rho = lambda_+.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_SCRIPT = ROOT / "experiments" / "01_linear_modal_dynamics" / "01_s0_linear_modal_dynamics.py"

def main():
    print("=" * 78)
    print("EXPERIMENT S0: LINEAR MODAL DYNAMICS SMOKE TEST")
    print("=" * 78)
    cmd = [sys.executable, str(EXP_SCRIPT)] + sys.argv[1:]
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    print("\n>>> Experiment S0 completed successfully! <<<")

if __name__ == "__main__":
    main()
