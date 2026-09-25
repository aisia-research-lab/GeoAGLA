#!/usr/bin/env python3
"""
Experiment E1: Geometry-Spectrum Correspondence.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Verifies the mathematical identity between STFT tangent subspace principal angles
and the spectrum of the phase retrieval Jacobian:
    lambda_pm = (1 pm cos theta) / 2
Evaluates synthetic test cases across Hann and Gaussian windows.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_SCRIPT = ROOT / "experiments" / "01_linear_modal_dynamics" / "02_h1_geometry_spectral_correspondence.py"

def main():
    print("=" * 78)
    print("EXPERIMENT E1: GEOMETRY-SPECTRUM CORRESPONDENCE (H1)")
    print("=" * 78)
    cmd = [sys.executable, str(EXP_SCRIPT)] + sys.argv[1:]
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    print("\n>>> Experiment E1 completed successfully! <<<")

if __name__ == "__main__":
    main()
