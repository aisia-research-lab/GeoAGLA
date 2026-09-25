#!/usr/bin/env python3
"""
Experiment E2: Local Contraction Rate Prediction & Hierarchy Verification (H2).
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Verifies the theoretical asymptotic contraction factors:
    GLA:    rho_GLA = lambda_+
    FGLA:   rho_FGLA = sqrt(lambda_+)
    Oracle: rho* = (sqrt(lambda_+) - sqrt(lambda_-)) / (sqrt(lambda_+) + sqrt(lambda_-))

Flags:
    --full: Run complete multi-STFT grid sweep across parameters.
    Default: Run focused local rate prediction smoke test.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description="Run Experiment E2 (Local Rate Prediction)")
    parser.add_argument("--full", action="store_true", help="Run full multi-STFT grid sweep instead of smoke test")
    args, unknown = parser.parse_known_args()

    print("=" * 78)
    print("EXPERIMENT E2: LOCAL CONTRACTION RATE PREDICTION & HIERARCHY")
    print("=" * 78)

    if args.full:
        script = ROOT / "experiments" / "02_controlled_local_rates" / "01_controlled_multi_stft_grid_sweep.py"
    else:
        script = ROOT / "experiments" / "01_linear_modal_dynamics" / "03_h2_oracle_rate_prediction.py"

    cmd = [sys.executable, str(script)] + unknown
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    print("\n>>> Experiment E2 completed successfully! <<<")

if __name__ == "__main__":
    main()
