
import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

#!/usr/bin/env python3
"""Isolated Microbenchmark for Passive Ritz 3x3 Eigensolver Overhead.
Directly measures the isolated solve time of the generalized Ritz eigensolver
and calculates the amortized overhead over K=8 iteration blocks.
"""
import time
import numpy as np
import sys
from pathlib import Path

# Ensure src is in sys.path
ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from geometry_gla.estimators.ritz import ritz_largest

def benchmark_isolated_ritz(p=3, n_trials=1000, K=8, coeff_dim=2048):
    rng = np.random.default_rng(2027)
    secants = [rng.normal(size=coeff_dim) + 1j * rng.normal(size=coeff_dim) for _ in range(p + 1)]
    images = [rng.normal(size=coeff_dim) + 1j * rng.normal(size=coeff_dim) for _ in range(p + 1)]

    # Warmup
    for _ in range(50):
        _ = ritz_largest(secants, images)

    # Timing loop
    t0 = time.perf_counter()
    for _ in range(n_trials):
        _ = ritz_largest(secants, images)
    total_time = time.perf_counter() - t0

    time_per_update_ms = (total_time / n_trials) * 1000.0
    amortized_overhead_ms = time_per_update_ms / K

    print("=" * 65)
    print("ISOLATED PASSIVE RITZ EIGENSOLVER MICROBENCHMARK")
    print("=" * 65)
    print(f"Memory dimension (p):            {p} (yielding {p}x{p} generalized eigenproblem)")
    print(f"Block update interval (K):       {K} iterations")
    print(f"Number of timing trials:         {n_trials}")
    print(f"Execution time per update:       {time_per_update_ms:.4f} ms/update")
    print(f"Amortized cost per iteration:    {amortized_overhead_ms:.4f} ms/iteration")
    print(f"Relative overhead (vs ~1.69 ms): {amortized_overhead_ms / 1.691 * 100:.2f}%")
    print("=" * 65)

if __name__ == "__main__":
    benchmark_isolated_ritz()