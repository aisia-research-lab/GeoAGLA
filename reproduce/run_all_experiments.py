#!/usr/bin/env python3
"""
Master End-to-End Experiment Reproducer (S0, E1-E7, E10).
ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

Runs the complete experimental suite in sequence:
  1. Experiment S0:  Linear modal dynamics smoke test
  2. Experiment E1:  Geometry-spectrum correspondence (Hann & Gaussian)
  3. Experiment E2:  Local contraction rate prediction & hierarchy
  4. Experiment E3:  Passive Rayleigh-Ritz dominant-edge estimation
  5. Experiment E4:  Online dynamics, safeguarding & finite-horizon adaptation
  6. Experiment E5:  Real-audio basin transfer (STFT-FFT equivalence & pilot)
  7. Experiment E6:  Geometry-opportunity Gate A ledger & analysis
  8. Experiment E7:  Computational cost microbenchmarking
  9. Experiment E10: Robustness mechanism ablation & forensic archive
 10. Publication:    Figures panels A-D and 20/20 numerical manuscript claims audit
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXPERIMENTS = [
    ("Experiment S0", "run_s0_linear_modal.py", "Linear modal dynamics smoke test"),
    ("Experiment E1", "run_e1_geometry_spectrum.py", "Geometry-spectrum correspondence"),
    ("Experiment E2", "run_e2_oracle_rates.py", "Local contraction rate prediction"),
    ("Experiment E3", "run_e3_ritz_estimator.py", "Passive Rayleigh-Ritz edge tracking"),
    ("Experiment E4", "run_e4_online_horizon.py", "Online dynamics & horizon adaptation"),
    ("Experiment E5", "run_e5_real_audio_basin.py", "Real-audio basin transfer (STFT-FFT equivalence & pilot)", ["--stft-fft"]),
    ("Experiment E6", "run_e6_gate_a_heldout.py", "Geometry-opportunity Gate A ledger & analysis", ["--step", "1"]),
    ("Experiment E7", "run_e7_microbench.py", "Computational cost microbenchmarking"),
    ("Experiment E10", "run_e10_mechanism_ablation.py", "Robustness mechanism ablation & forensic archive", ["--archive"]),
    ("Phase 4H-R", "run_phase4hr_baselines.py", "Contemporary baseline closure (NAGLA & Standard AGLA)"),
    ("Publication & Audit", "run_verification_and_figures.py", "Publication Figures Panels A-D & 20/20 numerical audit"),
]


def main():
    parser = argparse.ArgumentParser(description="Run all GeoAGLA experiments end-to-end")
    parser.add_argument("--stop-on-failure", action="store_true", default=True, help="Stop execution on first failure")
    args = parser.parse_args()

    t0_master = time.time()
    print("=" * 80)
    print("GEOAGLA ICLR 2027: COMPLETE EXPERIMENTAL SUITE EXECUTION")
    print(f"Total stages: {len(EXPERIMENTS)}")
    print("=" * 80)

    results = []
    for i, item in enumerate(EXPERIMENTS, start=1):
        name = item[0]
        script_file = item[1]
        desc = item[2]
        extra_args = item[3] if len(item) > 3 else []

        script_path = ROOT / "reproduce" / script_file
        print(f"\n[{i}/{len(EXPERIMENTS)}] Starting {name}: {desc}...")
        t0 = time.time()
        cmd = [sys.executable, str(script_path)] + extra_args
        res = subprocess.run(cmd, cwd=str(ROOT))
        dur = time.time() - t0

        if res.returncode == 0:
            print(f"[{i}/{len(EXPERIMENTS)}] [PASS] {name} completed in {dur:.2f}s")
            results.append((name, "PASS", dur))
        else:
            print(f"[{i}/{len(EXPERIMENTS)}] [FAIL] {name} failed with exit code {res.returncode}")
            results.append((name, "FAIL", dur))
            if args.stop_on_failure:
                print("\nExecution stopped due to failure.")
                sys.exit(res.returncode)

    total_dur = time.time() - t0_master
    print("\n" + "=" * 80)
    print("ALL EXPERIMENTAL STAGES SUMMARY")
    print("=" * 80)
    for name, status, dur in results:
        print(f"  [{status}] {name:<22} ({dur:.2f}s)")
    print(f"\nTotal elapsed time: {total_dur:.2f}s")
    print("=" * 80)

if __name__ == "__main__":
    main()
