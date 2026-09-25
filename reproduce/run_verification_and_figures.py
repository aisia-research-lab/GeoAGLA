#!/usr/bin/env python3
"""
Master Verification & Publication Figures Generator.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Executes:
1. Re-generation of publication evidence panels A-D and composite Figure_Main_ABCD (400 DPI).
2. Numerical verification of 20/20 manuscript claims against frozen acceptance gates.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    print("=" * 78)
    print("STEP 1: REPRODUCING PUBLICATION FIGURES (PANELS A - D)")
    print("=" * 78)
    fig_script = ROOT / "scripts" / "verification" / "reproduce_results_and_figures.py"
    subprocess.run([sys.executable, str(fig_script)], cwd=str(ROOT), check=True)

    print("\n" + "=" * 78)
    print("STEP 2: VERIFYING ALL 20 MANUSCRIPT NUMERICAL CLAIMS")
    print("=" * 78)
    audit_script = ROOT / "scripts" / "verification" / "verify_paper_numbers.py"
    subprocess.run([sys.executable, str(audit_script)], cwd=str(ROOT), check=True)

    print("\n>>> All Publication Figures and Manuscript Claims Verified Successfully! <<<")

if __name__ == "__main__":
    main()
