"""Exact-rational certificate for the switching counterexample (Proposition 7, Section IX).

Every claim in the proof is checked with fractions.Fraction, so no floating-point
rounding enters the verdict:
  * r = 68371/100000 < q_F(9/10) = 1 - sqrt(1/10);
  * strict radius-r Jury inequalities for u1, u2 at both endpoints lambda in {0, L},
    with the smallest positive slack above 6/10^6; radial (u) and phase (d_u) roots below r;
  * the stated rational bounds on tr P and det P for P = M_L(u2)^8 M_L(u1)^8;
  * x^2 - (tr P) x + det P < 0 at x = -(685/1000)^16, inside the stated interval;
  * 0.685 > q_F(L), so rho(P)^(1/16) > q_F(L).
Floating-point values (switched and frozen factors) are reported for reference only.

Usage:
  python -m experiments.verify_switching_certificate --out outputs/switching_certificate.json
"""
from __future__ import annotations

import argparse
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np

L = F(9, 10)
U1, U2 = F(5812, 10000), F(6837, 10000)
R_UPPER = F(68371, 100000)
R_LOWER = F(685, 1000)


def companion(lam: F, u: F) -> list[list[F]]:
    """Modal companion matrix M_lambda(u) of the one-edge design (Section IV-A)."""
    d = u * (1 + u) / (3 - u)
    return [[-u + (1 + u + d) * lam, -d * lam], [F(1), F(0)]]


def matmul(A: list[list[F]], B: list[list[F]]) -> list[list[F]]:
    return [[sum(A[i][k] * B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def matpow(A: list[list[F]], n: int) -> list[list[F]]:
    out = [[F(1), F(0)], [F(0), F(1)]]
    for _ in range(n):
        out = matmul(out, A)
    return out


def below_qF(r: F) -> bool:
    """r < q_F(L) = 1 - sqrt(1 - L)  <=>  (1 - r)^2 > 1 - L (for r < 1)."""
    return (1 - r) ** 2 > 1 - L


def certificate() -> dict:
    assert below_qF(R_UPPER), "r must lie below q_F(L)"
    slacks = []
    for u in (U1, U2):
        d = u * (1 + u) / (3 - u)
        assert u < R_UPPER and d < R_UPPER, "radial and phase roots must lie below r"
        for lam in (F(0), L):
            M = companion(lam, u)
            A, C = M[0][0], -M[0][1]
            s = [R_UPPER**2 - abs(C), R_UPPER**2 - R_UPPER * A + C, R_UPPER**2 + R_UPPER * A + C]
            assert all(x > 0 for x in s), f"strict Jury inequality fails at u={u}, lambda={lam}"
            slacks += s
    assert min(slacks) > F(6, 10**6)

    P = matmul(matpow(companion(L, U2), 8), matpow(companion(L, U1), 8))
    tr = P[0][0] + P[1][1]
    det = P[0][0] * P[1][1] - P[0][1] * P[1][0]
    assert F(-2579561, 10**9) < tr < F(-2579560, 10**9)
    assert F(299408, 10**12) < det < F(299409, 10**12)

    x = -(R_LOWER**16)
    value = x * x - tr * x + det
    assert F(-2403, 10**10) < value < F(-2402, 10**10) and value < 0
    assert not below_qF(R_LOWER) and (1 - R_LOWER) ** 2 < 1 - L, "0.685 must exceed q_F(L)"

    def rho(M: list[list[F]]) -> float:
        return float(np.max(np.abs(np.linalg.eigvals(np.array(M, dtype=float)))))

    frozen = [max(float(u), float(u * (1 + u) / (3 - u)), rho(companion(L, u))) for u in (U1, U2)]
    return {
        "status": "PASS",
        "L": str(L),
        "u1": str(U1),
        "u2": str(U2),
        "r_upper": str(R_UPPER),
        "min_jury_slack": float(min(slacks)),
        "trace_P": float(tr),
        "det_P": float(det),
        "x": float(x),
        "char_poly_at_x": float(value),
        "certified_switched_rate_lower_bound": float(R_LOWER),
        "q_F": 1.0 - float(np.sqrt(0.1)),
        "numerical_switched_rate": rho(P) ** (1.0 / 16.0),
        "numerical_frozen_rates": frozen,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Exact-rational check of the switching counterexample.")
    parser.add_argument("--out", type=str, default=None, help="Optional JSON output path.")
    args = parser.parse_args()
    result = certificate()
    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
