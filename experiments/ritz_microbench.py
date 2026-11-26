"""Isolated runtime microbenchmark for passive Rayleigh-Ritz SVD vs. STFT projections.

Usage:
  python experiments/ritz_microbench.py
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from experiments.common import NumpyPeriodicSTFT, STFT_PROFILES, make_window
from geometry_gla.estimators.ritz import ritz_largest


def run_microbench(signal_length: int = 4096, profile: str = "hann", memory: int = 3, repeats: int = 100) -> dict:
    """Measure per-step STFT projection cost and isolated Rayleigh-Ritz SVD cost."""
    rng = np.random.default_rng(7)
    win, hop, n_fft = make_window(profile)
    op = NumpyPeriodicSTFT(signal_length, win, hop, n_fft)
    x = rng.normal(size=signal_length)
    c = op.analyze(x)
    s = np.abs(c)

    # Warm-up
    for _ in range(5):
        c = op.G(c, s)

    # Time GLA projections
    t0 = time.perf_counter()
    for _ in range(repeats):
        c = op.G(c, s)
    gla_ms = 1000.0 * (time.perf_counter() - t0) / repeats

    # Prepare secants and time Rayleigh-Ritz SVD
    sec_s = [rng.normal(size=len(c)) + 1j * rng.normal(size=len(c)) for _ in range(memory)]
    sec_y = [rng.normal(size=len(c)) + 1j * rng.normal(size=len(c)) for _ in range(memory)]
    ritz_largest(sec_s, sec_y)  # warm-up

    t1 = time.perf_counter()
    for _ in range(repeats):
        ritz_largest(sec_s, sec_y)
    ritz_ms = 1000.0 * (time.perf_counter() - t1) / repeats

    amortized_k8_ms = ritz_ms / 8.0
    return dict(
        signal_length=signal_length,
        profile=profile,
        coeff_dim=len(c),
        memory=memory,
        gla_step_ms=gla_ms,
        ritz_update_ms=ritz_ms,
        amortized_per_iter_k8_ms=amortized_k8_ms,
        relative_amortized_overhead_pct=100.0 * amortized_k8_ms / gla_ms,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Microbenchmark isolated Rayleigh-Ritz SVD vs. STFT projections.")
    parser.add_argument("--signal-length", type=int, default=4096)
    parser.add_argument("--repeats", type=int, default=50)
    parser.add_argument("--out", type=str, default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    results = [run_microbench(args.signal_length, p, repeats=args.repeats) for p in STFT_PROFILES]
    for r in results:
        print(
            f"[{r['profile']:8s}] M={r['coeff_dim']:6d} | GLA={r['gla_step_ms']:.3f} ms | "
            f"Ritz(p={r['memory']})={r['ritz_update_ms']:.3f} ms | "
            f"Amortized(K=8)={r['amortized_per_iter_k8_ms']:.3f} ms ({r['relative_amortized_overhead_pct']:.1f}%)"
        )
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
