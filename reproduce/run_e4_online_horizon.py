#!/usr/bin/env python3
"""
Experiment E4: Online Dynamics, Safeguarding & Finite-Horizon Adaptation.
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Evaluates:
- Online adaptive Chebyshev acceleration with passive Rayleigh-Ritz tracking.
- Safeguarded monotonic fallback mechanism preventing divergence.
- Multi-horizon rate realization across H in {30, 60, 120, 200, 360}.
- Canonical C1 capture ratio audit and long-horizon failure taxonomy.

Flags:
    --safeguard: Run safeguarded acceleration verification (Phase 1E).
    --audit:     Run canonical C1 capture ratio audit across horizons.
    --patch:     Run final 29-case long-horizon audit (H in {360, 720, 1440}).
    --all:       Run all E4 sub-experiments sequentially.
    Default:     Run Phase 1E-R repair and horizon policy runner.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "experiments" / "06_multi_horizon_online_adaptation"

def run_step(script_name: str, desc: str, extra_args=None):
    print("\n" + "=" * 78)
    print(f"E4 SUB-EXPERIMENT: {desc}")
    print("=" * 78)
    cmd = [sys.executable, str(EXP_DIR / script_name)] + (extra_args or [])
    subprocess.run(cmd, cwd=str(ROOT), check=True)

def main():
    parser = argparse.ArgumentParser(description="Run Experiment E4 (Online Dynamics & Horizon Adaptation)")
    parser.add_argument("--safeguard", action="store_true", help="Run Phase 1E safeguarded acceleration")
    parser.add_argument("--audit", action="store_true", help="Run canonical C1 capture ratio audit")
    parser.add_argument("--patch", action="store_true", help="Run 29-case long-horizon audit")
    parser.add_argument("--all", action="store_true", help="Run all E4 sub-experiments")
    args, unknown = parser.parse_known_args()

    print("=" * 78)
    print("EXPERIMENT E4: ONLINE DYNAMICS & FINITE-HORIZON ADAPTATION")
    print("=" * 78)

    if args.all:
        run_step("02_phase1e_safeguarded_acceleration.py", "Phase 1E Safeguarded Acceleration")
        run_step("03_phase1er_repair_and_horizon_policy.py", "Phase 1E-R Repair and Horizon Policy")
        run_step("07_c1_canonical_capture_ratio_audit.py", "Canonical C1 Capture Ratio Audit")
        run_step("11_final_patch_horizon_audit.py", "Long-Horizon Failure Audit")
    elif args.safeguard:
        run_step("02_phase1e_safeguarded_acceleration.py", "Phase 1E Safeguarded Acceleration", unknown)
    elif args.audit:
        run_step("07_c1_canonical_capture_ratio_audit.py", "Canonical C1 Capture Ratio Audit", unknown)
    elif args.patch:
        run_step("11_final_patch_horizon_audit.py", "Long-Horizon Failure Audit", unknown)
    else:
        run_step("03_phase1er_repair_and_horizon_policy.py", "Phase 1E-R Repair and Horizon Policy", unknown)

    print("\n>>> Experiment E4 completed successfully! <<<")

if __name__ == "__main__":
    main()
