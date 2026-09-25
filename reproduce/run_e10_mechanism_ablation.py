#!/usr/bin/env python3
"""
Experiment E10: Robustness Mechanism Ablation Suite.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Decomposes and audits the 6 architectural mechanisms of GeoAGLA:
1. Passive Ritz dominant-edge tracking.
2. Dynamic running envelope damping.
3. Rayleigh quotient safeguard fallback.
4. Block update memory cadence.
5. Monotonic orbit merit monitoring.
6. Identity preservation on neutral modes.

Modes:
    --locked:    Run locked-seed historical equivalence check (E10-R).
    --canonical: Run canonical 202-file baseline test (E10-R2).
    --archive:   Run complete forensic bitwise archive verification (E10-R2F).
    Default:     Run 6-variant robustness mechanism ablation suite (E10).
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "experiments" / "08_e10_robustness_mechanism_ablation"

def main():
    parser = argparse.ArgumentParser(description="Run Experiment E10 (Robustness Mechanism Ablation)")
    parser.add_argument("--locked", action="store_true", help="Run E10-R locked evaluation")
    parser.add_argument("--canonical", action="store_true", help="Run E10-R2 canonical evaluation")
    parser.add_argument("--archive", action="store_true", help="Run E10-R2F forensic closure archive")
    args, unknown = parser.parse_known_args()

    print("=" * 78)
    print("EXPERIMENT E10: ROBUSTNESS MECHANISM ABLATION SUITE")
    print("=" * 78)

    if args.locked:
        script = EXP_DIR / "03_run_e10r_locked.py"
    elif args.canonical:
        script = EXP_DIR / "04_run_e10r2_canonical.py"
    elif args.archive:
        script = EXP_DIR / "11_e10r2f_final_archive.py"
    else:
        script = EXP_DIR / "01_run_e10_ablation.py"

    cmd = [sys.executable, str(script)] + unknown
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    print("\n>>> Experiment E10 completed successfully! <<<")

if __name__ == "__main__":
    main()
