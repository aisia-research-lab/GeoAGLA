#!/usr/bin/env python3
"""
Experiment E7: Computational Cost Microbenchmarking & Profiling.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Benchmarks:
1. Isolated passive Rayleigh-Ritz eigensolver execution timing and amortized per-iteration overhead.
2. Comparative runtime profiling against STFT/iSTFT projections and GLA/FGLA iterations.
3. Runtime provenance and computational complexity scaling.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "experiments" / "07_computational_cost_microbench"

def main():
    parser = argparse.ArgumentParser(description="Run Experiment E7 (Computational Cost Microbenchmark)")
    parser.add_argument("--profiling", action="store_true", help="Run full runtime provenance profiling")
    parser.add_argument("--crosscheck", action="store_true", help="Run computational cost cross-check")
    parser.add_argument("--all", action="store_true", help="Run all E7 microbenchmarks")
    args, unknown = parser.parse_known_args()

    print("=" * 78)
    print("EXPERIMENT E7: COMPUTATIONAL COST MICROBENCHMARKING")
    print("=" * 78)

    if args.all:
        subprocess.run([sys.executable, str(EXP_DIR / "03_isolated_ritz_microbench.py")], cwd=str(ROOT), check=True)
        subprocess.run([sys.executable, str(EXP_DIR / "01_computational_cost_and_crosscheck.py")], cwd=str(ROOT), check=True)
        subprocess.run([sys.executable, str(EXP_DIR / "02_runtime_provenance_and_profiling.py")], cwd=str(ROOT), check=True)
    elif args.profiling:
        subprocess.run([sys.executable, str(EXP_DIR / "02_runtime_provenance_and_profiling.py")] + unknown, cwd=str(ROOT), check=True)
    elif args.crosscheck:
        subprocess.run([sys.executable, str(EXP_DIR / "01_computational_cost_and_crosscheck.py")] + unknown, cwd=str(ROOT), check=True)
    else:
        # Default: run isolated ritz microbenchmark
        subprocess.run([sys.executable, str(EXP_DIR / "03_isolated_ritz_microbench.py")] + unknown, cwd=str(ROOT), check=True)

    print("\n>>> Experiment E7 completed successfully! <<<")

if __name__ == "__main__":
    main()
