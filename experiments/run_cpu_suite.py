"""One-command self-contained CPU reproduction and verification suite.

Runs every experimental module on synthetic data (requiring no external audio
download) into a temporary directory (or --out directory) to verify end-to-end
executability on any workstation.

Usage:
  python experiments/run_cpu_suite.py
  python experiments/run_cpu_suite.py --out outputs/cpu_suite
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(label: str, args: list[str], env: dict[str, str]) -> float:
    print(f"\n>>> {label}")
    t0 = time.time()
    proc = subprocess.run([sys.executable, "-m", *args], cwd=str(REPO_ROOT), env=env)
    dur = time.time() - t0
    if proc.returncode != 0:
        raise SystemExit(f"[FAIL] {label} failed with exit code {proc.returncode}")
    print(f"[PASS] {label} ({dur:.2f}s)")
    return dur


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all self-contained CPU experiments end-to-end.")
    parser.add_argument("--out", type=str, default=None, help="Directory to store generated outputs (uses temp dir if omitted).")
    args = parser.parse_args()

    env = os.environ.copy()
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["OMP_NUM_THREADS"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + str(REPO_ROOT) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )

    t_start = time.time()
    ctx = tempfile.TemporaryDirectory() if args.out is None else None
    out_dir = Path(ctx.name) if ctx is not None else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        _run("1/6 Reference vs. PyTorch parity check (16 cases)", ["experiments.parity_check", "--device", "cpu", "--out", str(out_dir / "parity.json")], env)
        _run("2/6 Non-STFT two-edge minimax transfer", ["experiments.non_stft_transfer", "--out", str(out_dir / "transfer.json")], env)
        _run("3/6 Spectral geometry identity (synthetic)", ["experiments.spectral_geometry", "--synthetic", "--plot", "--out", str(out_dir / "spectral.jsonl")], env)
        _run("4/6 Controlled local acceleration & mismatch sweep (synthetic)", ["experiments.local_acceleration", "--synthetic", "--out", str(out_dir / "local.jsonl")], env)
        _run("5/6 Matched-budget calls & wall benchmark + analysis (synthetic)", ["experiments.matched_budget_benchmark", "--synthetic", "--mode", "calls", "--device", "cpu", "--out", str(out_dir / "calls.jsonl")], env)
        _run("5b/6 Matched-budget analysis", ["experiments.benchmark_analysis", "--raw", str(out_dir / "calls.jsonl"), "--mode", "calls", "--out", str(out_dir / "calls_summary")], env)
        _run("5c/6 Independent raw-ledger audit", ["experiments.audit_ledger", "--raw", str(out_dir / "calls.jsonl"), "--mode", "calls", "--out", str(out_dir / "calls_audit.json")], env)
        _run("6/6 Rayleigh-Ritz SVD microbenchmark", ["experiments.ritz_microbench", "--repeats", "20", "--out", str(out_dir / "microbench.json")], env)
        _run("7/7 Exact-rational switching certificate (Proposition 7)", ["experiments.verify_switching_certificate", "--out", str(out_dir / "switching_certificate.json")], env)
    finally:
        if ctx is not None:
            ctx.cleanup()

    print(f"\nAll self-contained CPU experiments PASSED in {time.time() - t_start:.2f}s.")


if __name__ == "__main__":
    main()
