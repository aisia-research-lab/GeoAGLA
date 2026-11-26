"""Abstract two-edge minimax transfer verification on non-STFT subspace pairs.

Validates the general self-adjoint PSD fixed-point transfer theorem on four
explicit subspace pairs (U, V) with strictly positive lower spectral endpoint
lambda_- = m > 0, comparing exact two-edge minimax acceleration against the
one-edge design.

Usage:
  python experiments/non_stft_transfer.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from geometry_gla.algorithms.minimax import modal_radius, one_edge_minimax, oracle_minimax

DEFAULT_INTERVALS = [(0.2, 0.8), (0.45, 0.85), (0.7, 0.95), (0.9, 0.99)]


def evaluate_non_stft_transfer(intervals: list[tuple[float, float]] | None = None, steps: int = 30) -> list[dict]:
    """Evaluate two-edge vs. one-edge minimax root factors on explicit 4D subspace pairs."""
    pairs = intervals or DEFAULT_INTERVALS
    results: list[dict] = []
    for m, L in pairs:
        # U = span(e1, e2), V = span(sqrt(m)e1 + sqrt(1-m)e3, sqrt(L)e2 + sqrt(1-L)e4)
        U = np.eye(4)[:, :2]
        V = np.array(
            [
                [np.sqrt(m), 0.0],
                [0.0, np.sqrt(L)],
                [np.sqrt(1.0 - m), 0.0],
                [0.0, np.sqrt(1.0 - L)],
            ]
        )
        J = U.T @ V @ V.T @ U
        two_edge = oracle_minimax(m, L)
        one_edge = one_edge_minimax(L)
        q_two = two_edge["q"]
        q_one = one_edge["q"]
        direct_radius = max(
            modal_radius(lam, two_edge["alpha"], two_edge["beta"], two_edge["gamma"])
            for lam in np.linalg.eigvalsh(J)
        )
        assert abs(direct_radius - q_two) < 1e-7 and q_two < q_one

        z = np.array([0.4, 1.0])
        prev, cur = z.copy(), z.copy()
        a, b, g = two_edge["alpha"], two_edge["beta"], two_edge["gamma"]
        for _ in range(steps):
            nxt = (1.0 - g) * (cur + b * (cur - prev)) + g * (J @ (cur + a * (cur - prev)))
            prev, cur = cur, nxt

        results.append(
            dict(
                lambda_minus=m,
                lambda_plus=L,
                two_edge_q=q_two,
                one_edge_q=q_one,
                direct_companion_radius=direct_radius,
                error_at_final_step=float(np.linalg.norm(cur)),
            )
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify abstract two-edge minimax transfer on non-STFT subspace pairs.")
    parser.add_argument("--out", type=str, default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    res = evaluate_non_stft_transfer()
    print(f"{'[m, L]':<14} | {'Two-edge q*':<14} | {'One-edge q0(L)':<14} | {'Direct radius':<14} | {'Err(30)':<12}")
    print("-" * 78)
    for r in res:
        print(
            f"[{r['lambda_minus']:.2f}, {r['lambda_plus']:.2f}]   | "
            f"{r['two_edge_q']:<14.8f} | {r['one_edge_q']:<14.8f} | "
            f"{r['direct_companion_radius']:<14.8f} | {r['error_at_final_step']:<12.3e}"
        )
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
