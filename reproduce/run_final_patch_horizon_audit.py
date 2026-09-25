#!/usr/bin/env python3
"""
Reproduce Final Real-Audio Patch & 29-Case Horizon Audit.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_SCRIPT = ROOT / "experiments" / "06_multi_horizon_online_adaptation" / "11_final_patch_horizon_audit.py"

def main():
    print("=" * 78)
    print("RUNNING FINAL REAL-AUDIO PATCH & 29-CASE HORIZON AUDIT")
    print("=" * 78)
    cmd = [sys.executable, str(EXP_SCRIPT)] + sys.argv[1:]
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    print("\n>>> Final Real-Audio Patch & Horizon Audit Reproduced Successfully! <<<")

if __name__ == "__main__":
    main()
