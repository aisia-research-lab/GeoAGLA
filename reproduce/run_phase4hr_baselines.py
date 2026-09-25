#!/usr/bin/env python3
"""
Reproduce Phase 4H-R: Contemporary Baseline Closure (NAGLA & Standard AGLA).
Executes all validation gates, baseline pairing, and statistical audits in sequence:
  1. 01_freeze_baseline_parameters.py (Gate B0: Protocol pre-registration)
  2. 02_validate_baseline_gates.py (Gates B1-B4: Determinism, Equivalence, Init alignment, No retuning)
  3. 03_run_phase4hr_baselines.py (5-method paired ledger generation across 4,752 instances)
  4. 04_analyze_and_report.py (Gate B5: Success recomputation, cluster-bootstrap CIs, audit report)
"""
from __future__ import annotations
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "experiments" / "09_phase4hr_contemporary_baselines"

STEPS = [
    ("Gate B0: Parameter Pre-Registration", EXP_DIR / "01_freeze_baseline_parameters.py"),
    ("Gates B1-B4: Baseline Technical Gate Validation", EXP_DIR / "02_validate_baseline_gates.py"),
    ("Step 3: 5-Method Paired Baseline Execution", EXP_DIR / "03_run_phase4hr_baselines.py"),
    ("Step 4: Statistical Analysis, Cluster Bootstrap & Audit", EXP_DIR / "04_analyze_and_report.py"),
]

def main():
    print("=" * 78)
    print("PHASE 4H-R: CONTEMPORARY BASELINE CLOSURE PIPELINE")
    print("ICLR 2027: Geometry Determines Acceleration in Phase Retrieval")
    print("=" * 78)

    t0_master = time.time()
    for i, (name, script) in enumerate(STEPS, start=1):
        print(f"\n[{i}/{len(STEPS)}] Running {name} ({script.name})...")
        t0 = time.time()
        res = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
        dur = time.time() - t0
        if res.returncode != 0:
            print(f"\n[FAIL] Step {i} failed with exit code {res.returncode}")
            sys.exit(res.returncode)
        print(f"[PASS] Step {i} completed in {dur:.2f}s")

    total_dur = time.time() - t0_master
    print("\n" + "=" * 78)
    print(f"PHASE 4H-R PIPELINE COMPLETED SUCCESSFULLY IN {total_dur:.2f}s")
    print(f"Audit Report:  {EXP_DIR / 'audit' / 'PHASE4HR_BASELINE_AUDIT.md'}")
    print(f"Claim Firewall: {EXP_DIR / 'audit' / 'CLAIM_FIREWALL.md'}")
    print("=" * 78)

if __name__ == "__main__":
    main()
