#!/usr/bin/env python3
"""
Reproduce Final Scientific Freeze Reconciliation Pipeline.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_SCRIPT = ROOT / "experiments" / "06_multi_horizon_online_adaptation" / "12_final_freeze_reconciliation.py"

def main():
    print("=" * 78)
    print("RUNNING FINAL SCIENTIFIC FREEZE RECONCILIATION PIPELINE")
    print("=" * 78)
    cmd = [sys.executable, str(EXP_SCRIPT)] + sys.argv[1:]
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    print("\n>>> Final Freeze Reconciliation Completed Successfully! <<<")

if __name__ == "__main__":
    main()
