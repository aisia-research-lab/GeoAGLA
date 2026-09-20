#!/usr/bin/env python3
"""
run_full_pipeline.py
====================
Automated end-to-end execution pipeline for the complete GeoAGLA experimental suite:
1. Environment verification via unit tests (`run_tests.py`).
2. Environment provenance recording (Python version, pip freeze).
3. Phase 1D: Passive Ritz dominant-edge estimation.
4. Phase 1E-R: Online rate realization & horizon policy.
5. Phase 2A: Signal-scale transfer on synthetic signals.
6. Phase 2B: Real-audio transfer on audio dataset (checkpointed batch runner).
7. Phase 1C: Controlled multi-STFT grid sweep verification.
8. Output integrity verification and optional zip bundle generation.

Usage:
    # Run full pipeline on audio samples:
    python scripts/runners/run_full_pipeline.py \
        --audio-dir data/audio_samples \
        --out-dir results/pipeline_runs \
        --run-pilot --batch-size 2

    # Run only Phase 2B real audio transfer:
    python scripts/runners/run_full_pipeline.py \
        --audio-dir data/audio_samples \
        --out-dir results/pipeline_runs \
        --skip-phase1-phase2a
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def run_cmd(cmd: list[str], cwd: Path, desc: str) -> subprocess.CompletedProcess:
    print(f"\n[{desc}] $ {' '.join(cmd)}", flush=True)
    t0 = time.time()
    res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    elapsed = time.time() - t0
    if res.returncode != 0:
        print(f"!!! ERROR at step [{desc}] (after {elapsed:.1f}s) !!!")
        print("--- STDOUT ---\n", res.stdout[-3000:])
        print("--- STDERR ---\n", res.stderr[-3000:])
        raise RuntimeError(f"Step [{desc}] failed with exit code {res.returncode}")
    print(f"[{desc}] Completed in {elapsed:.1f}s.")
    return res


def main():
    parser = argparse.ArgumentParser(
        description="Automated end-to-end execution pipeline for all experimental phases."
    )
    parser.add_argument("--audio-dir", required=True, help="Directory containing .wav audio files.")
    parser.add_argument("--out-dir", default="results/pipeline_runs", help="Output root directory for pipeline results.")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size for Phase 2B audio processing.")
    parser.add_argument("--max-files", type=int, default=None, help="Maximum number of files for Phase 2B (None: run all).")
    parser.add_argument("--run-pilot", action="store_true", help="Run 4-file pilot to measure execution time before full run.")
    parser.add_argument("--skip-phase1-phase2a", action="store_true", help="Skip non-audio phases (Phase 1D, 1E-R, 2A).")
    parser.add_argument("--no-phase1c", action="store_true", help="Skip Phase 1C verification.")
    parser.add_argument("--zip-bundle", action="store_true", help="Automatically compress all results into a zip bundle.")
    args = parser.parse_args()

    out_root = Path(args.out_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    logs_dir = out_root / "terminal_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("         GEOAGLA -- FULL AUTOMATED EXECUTION PIPELINE            ")
    print("=================================================================")
    print(f"Repository root: {str(_repo_root)}")
    print(f"Output root:     {str(out_root)}")
    print(f"Audio directory: {str(args.audio_dir)}")

    # 1. Verify environment
    print("\n--- STEP 1: VERIFYING ENVIRONMENT VIA UNIT TESTS ---")
    run_cmd([sys.executable, "run_tests.py"], _repo_root, "Unit Tests")

    # 2. Record environment
    env_txt = f"Python: {sys.version}\n\n=== PIP FREEZE ===\n"
    res_pip = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    env_txt += res_pip.stdout
    (out_root / "environment_info.txt").write_text(env_txt, encoding="utf-8")
    print(f"Environment log written to: {out_root / 'environment_info.txt'}")

    # 3. Phase 1D
    if not args.skip_phase1_phase2a:
        print("\n--- STEP 2: RUNNING PHASE 1D (Ritz Dominant-Edge Tracking) ---")
        run_cmd(
            [sys.executable, "experiments/06_multi_horizon_online_adaptation/01_phase1d_online_edge_tracking.py"],
            _repo_root,
            "Phase 1D",
        )
        src_1d = _repo_root / "results/01_phase1_reproduction/phase1d"
        if src_1d.exists():
            shutil.copytree(src_1d, out_root / "phase1d", dirs_exist_ok=True)

        # 4. Phase 1E-R
        print("\n--- STEP 3: RUNNING PHASE 1E-R (Rate Realization & Horizon Policy) ---")
        run_cmd(
            [sys.executable, "experiments/06_multi_horizon_online_adaptation/03_phase1er_repair_and_horizon_policy.py"],
            _repo_root,
            "Phase 1E-R",
        )
        src_1er = _repo_root / "results/01_phase1_reproduction/phase1er"
        if src_1er.exists():
            shutil.copytree(src_1er, out_root / "phase1er", dirs_exist_ok=True)

        # 5. Phase 2A
        print("\n--- STEP 4: RUNNING PHASE 2A (Synthetic Signal-Scale Transfer) ---")
        run_cmd(
            [sys.executable, "experiments/05_real_audio_basin_transfer/01_phase2a_synthetic_transfer.py"],
            _repo_root,
            "Phase 2A",
        )
        src_2a = _repo_root / "results/02_phase2_transfer/phase2a"
        if src_2a.exists():
            shutil.copytree(src_2a, out_root / "phase2a", dirs_exist_ok=True)
    else:
        print("\n--- SKIPPING PHASES 1D, 1E-R, 2A (--skip-phase1-phase2a set) ---")

    # 6. Phase 2B Checkpointed
    print("\n--- STEP 5: RUNNING PHASE 2B (Real-Audio Basin Transfer) ---")
    p2b_out = out_root / "phase2b_results"

    if args.run_pilot:
        print("\n[Pilot] Running 4-file pilot to measure execution time...")
        pilot_out = out_root / "phase2b_pilot"
        run_cmd(
            [
                sys.executable,
                "experiments/05_real_audio_basin_transfer/05_run_phase2b_checkpointed.py",
                "--audio-dir", str(args.audio_dir),
                "--max-files", "4",
                "--batch-size", str(args.batch_size),
                "--out", str(pilot_out),
            ],
            _repo_root,
            "Phase 2B Pilot",
        )

    p2b_cmd = [
        sys.executable,
        "experiments/05_real_audio_basin_transfer/05_run_phase2b_checkpointed.py",
        "--audio-dir", str(args.audio_dir),
        "--batch-size", str(args.batch_size),
        "--out", str(p2b_out),
    ]
    if args.max_files is not None:
        p2b_cmd.extend(["--max-files", str(args.max_files)])
    run_cmd(p2b_cmd, _repo_root, "Phase 2B Full")

    # 7. Phase 1C Verification
    if not args.no_phase1c:
        print("\n--- STEP 6: RUNNING PHASE 1C (Controlled Multi-STFT Grid Sweep) ---")
        res_1c = run_cmd(
            [sys.executable, "experiments/02_controlled_local_rates/01_controlled_multi_stft_grid_sweep.py"],
            _repo_root,
            "Phase 1C Verification",
        )
        (logs_dir / "phase1c_verification_log.txt").write_text(
            f"STDOUT:\n{res_1c.stdout}\n\nSTDERR:\n{res_1c.stderr}", encoding="utf-8"
        )
        src_1c = _repo_root / "results/01_phase1_reproduction/phase1c"
        if src_1c.exists():
            shutil.copytree(src_1c, out_root / "phase1c", dirs_exist_ok=True)

    # 8. Verify outputs
    print("\n--- STEP 7: VERIFYING OUTPUT ARTIFACTS ---")
    expected_items = [
        "environment_info.txt",
        "phase2b_results/summary.json",
    ]
    if not args.skip_phase1_phase2a:
        expected_items.extend([
            "phase1d/summary.json",
            "phase1er/summary.json",
            "phase2a/summary.json",
        ])
    if not args.no_phase1c:
        expected_items.append("phase1c/summary.json")

    all_ok = True
    for item in expected_items:
        p = out_root / item
        if p.exists():
            print(f"  [OK]       {item}")
        else:
            print(f"  [MISSING]  {item}")
            all_ok = False

    # 9. Zip bundle
    if args.zip_bundle:
        zip_path = out_root.parent / f"{out_root.name}_bundle.zip"
        print(f"\n--- STEP 8: COMPRESSING RESULTS ARCHIVE: {zip_path} ---")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(out_root.rglob("*")):
                if f.is_file() and "_audio_batch_" not in str(f):
                    zf.write(f, arcname=out_root.name / f.relative_to(out_root))
        print(f"Results archive created: {zip_path}")

    print("\n=================================================================")
    if all_ok:
        print("          PIPELINE COMPLETED SUCCESSFULLY (100% OK)              ")
    else:
        print("          PIPELINE COMPLETED WITH WARNINGS (CHECK LOGS)          ")
    print("=================================================================")


if __name__ == "__main__":
    main()
