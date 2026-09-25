#!/usr/bin/env python3
"""
Experiment E6: Geometry-Opportunity Gate A & Held-Out Generalization Suite.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Executes full Gate A verification pipeline:
1. Canonical 90-case geometry opportunity ledger generation.
2. Oracle headroom and geometry opportunity gap analysis.
3. 36-case controlled held-out STFT geometry grid sweep.
4. Validation against Gate A criteria (Delta_oracle, error reduction).
5. Generation of publication summary tables.
6. Gate A scientific audit report generation.
7. Targeted neutral mode exactness audit.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "experiments" / "03_geometry_opportunity_gate_a"

SCRIPTS = [
    ("01_build_e6_ledger.py", "1. Build Canonical 90-Case Geometry Opportunity Ledger"),
    ("02_analyze_geometry_opportunity.py", "2. Analyze Geometry Opportunity Gap & Headroom"),
    ("03_freeze_heldout_grid.py", "3. Freeze 36-Case Held-Out Geometry Grid"),
    ("04_run_heldout_experiments.py", "4. Run Held-Out Geometry Experiments"),
    ("05_validate_results.py", "5. Validate Against Gate A Acceptance Criteria"),
    ("06_make_tables.py", "6. Generate Publication Summary Tables"),
    ("07_generate_gate_a_report.py", "7. Generate Gate A Scientific Audit Report"),
    ("08_run_neutral_mode_audit.py", "8. Run Neutral Mode Exactness Audit"),
]

def main():
    parser = argparse.ArgumentParser(description="Run Experiment E6 (Gate A & Held-Out Suite)")
    parser.add_argument("--step", type=int, default=None, help="Run specific step number (1-8)")
    args, unknown = parser.parse_known_args()

    print("=" * 78)
    print("EXPERIMENT E6: GEOMETRY-OPPORTUNITY GATE A & HELDOUT SUITE")
    print("=" * 78)

    if args.step is not None:
        idx = args.step - 1
        if 0 <= idx < len(SCRIPTS):
            script_file, desc = SCRIPTS[idx]
            print(f"\n--- Running Step {args.step}: {desc} ---")
            subprocess.run([sys.executable, str(EXP_DIR / script_file)] + unknown, cwd=str(ROOT), check=True)
        else:
            print(f"Error: Step {args.step} out of range (1-{len(SCRIPTS)})")
            sys.exit(1)
    else:
        for i, (script_file, desc) in enumerate(SCRIPTS, start=1):
            print(f"\n--- Step {i}/{len(SCRIPTS)}: {desc} ---")
            subprocess.run([sys.executable, str(EXP_DIR / script_file)], cwd=str(ROOT), check=True)

    print("\n>>> Experiment E6 completed successfully! <<<")

if __name__ == "__main__":
    main()
