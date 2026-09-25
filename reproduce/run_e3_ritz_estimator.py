#!/usr/bin/env python3
"""
Experiment E3: Passive Rayleigh-Ritz Dominant-Edge Estimation.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Tracks the dominant eigenvalue lambda_+ online along the algorithmic trajectory
using passive Rayleigh-Ritz Krylov projections (memory depths p in {1, 3, 5})
without active subspace perturbations.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_SCRIPT = ROOT / "experiments" / "06_multi_horizon_online_adaptation" / "01_phase1d_online_edge_tracking.py"

def main():
    print("=" * 78)
    print("EXPERIMENT E3: PASSIVE RAYLEIGH-RITZ DOMINANT-EDGE ESTIMATION")
    print("=" * 78)
    cmd = [sys.executable, str(EXP_SCRIPT)] + sys.argv[1:]
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    print("\n>>> Experiment E3 completed successfully! <<<")

if __name__ == "__main__":
    main()
