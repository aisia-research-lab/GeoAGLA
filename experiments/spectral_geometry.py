"""Independent principal-sine Gram vs. direct tangent-Jacobian spectral identity verification.

Verifies Theorem 3.1:
  1. The radial direction c* is an exact zero mode (J* c* = 0).
  2. The direct tangent-Jacobian dominant gap (1 - L) matches the smallest
     principal sine squared (sin^2 theta_1) computed via an independent
     normal-measurement Gram operator.

Usage:
  # Self-contained synthetic verification (no external audio required):
  python experiments/spectral_geometry.py --synthetic --out outputs/spectral_synthetic.jsonl

  # Full real-audio verification on a local MUSAN audio directory:
  python experiments/spectral_geometry.py --audio-root /path/to/musan --out outputs/spectral_audio.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

from experiments.common import NumpyPeriodicSTFT, STFT_PROFILES, load_audio_records, make_window


def compute_spectral_geometry(op: NumpyPeriodicSTFT, x: np.ndarray) -> tuple[dict, np.ndarray, np.ndarray]:
    """Compute dominant Jacobian eigenvalue L and independent principal-sine gap."""
    c = op.analyze(x)
    s = np.abs(c)
    assert s.min() > 1e-10 * np.median(s), "Irregular spectrogram coefficients near zero"

    u = c / s
    root = np.sqrt(op.frame_diag)
    n = op.N
    z = x * root
    z = z / np.linalg.norm(z)

    to_real = lambda v: np.r_[v.real, v.imag]
    to_cx = lambda v: v[:n] + 1j * v[n:]
    hor = lambda v: v - z * np.vdot(z, v)

    # Radial zero-mode check: J* c* = P_U P_V c* = 0
    pv_c = c - u * np.real(u.conj() * c)
    radial_residual = float(np.linalg.norm(op.project_range(pv_c)) / np.linalg.norm(c))

    # Direct tangent-Jacobian compression vs. independent normal-measurement Gram B*B
    def j_action(v: np.ndarray) -> np.ndarray:
        w = op.analyze(v / root)
        return op.adjoint(w - u * np.real(u.conj() * w)) / root

    def normal_map(v: np.ndarray) -> np.ndarray:
        return np.real(u.conj() * op.analyze(v / root))

    def normal_adj(w: np.ndarray) -> np.ndarray:
        return op.adjoint(u * w) / root

    def aj_matvec(a: np.ndarray) -> np.ndarray:
        return to_real(hor(j_action(hor(to_cx(a)))))

    def gram_matvec(a: np.ndarray) -> np.ndarray:
        v = to_cx(a)
        h = hor(v)
        return to_real(hor(normal_adj(normal_map(h))) + (v - h))

    J_op = LinearOperator((2 * n, 2 * n), matvec=aj_matvec, dtype=float)
    B_op = LinearOperator((2 * n, 2 * n), matvec=gram_matvec, dtype=float)

    ev, vec = eigsh(J_op, k=2, which="LA", tol=1e-11, maxiter=30000, v0=np.random.default_rng(529).normal(size=2 * n))
    L = float(ev[-1])
    v_dom = hor(to_cx(vec[:, -1]))
    v_dom /= np.linalg.norm(v_dom)

    es, vs = eigsh(B_op, k=2, which="SA", tol=1e-11, maxiter=30000, v0=np.random.default_rng(192).normal(size=2 * n))
    angle_gap = float(es[0])
    w_min = vs[:, 0]

    # Verify adjoint identity in the real inner product
    rg = np.random.default_rng(72)
    p = hor(rg.normal(size=n) + 1j * rg.normal(size=n))
    y = rg.normal(size=len(c))
    adj_res = float(abs(np.dot(normal_map(p), y) - np.vdot(p, normal_adj(y)).real) / max(1.0, np.linalg.norm(p) * np.linalg.norm(y)))

    info = dict(
        L=L,
        angle_gap=angle_gap,
        angle_L=1.0 - angle_gap,
        gap=1.0 - L,
        gap_relative_discrepancy=abs(angle_gap - (1.0 - L)) / (1.0 - L),
        radial_zero_residual=radial_residual,
        jacobian_residual=float(np.linalg.norm(j_action(v_dom) - L * v_dom)),
        normal_gram_residual=float(np.linalg.norm(gram_matvec(w_min) - angle_gap * w_min)),
        adjoint_residual=adj_res,
        phase_overlap=float(abs(np.vdot(z, to_cx(w_min)))),
        min_rel_coeff=float(s.min() / np.median(s)),
    )
    assert 0.0 < angle_gap < 1.0 and 0.5 - 1e-9 <= L < 1.0
    assert max(info["jacobian_residual"], info["normal_gram_residual"], adj_res) < 1e-7
    assert info["phase_overlap"] < 1e-6

    dom_vec = op.analyze(v_dom / root) * np.linalg.norm(c)
    return info, dom_vec, c


def save_gap_figure(rows: list[dict], out_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = [1.0 - r["L"] for r in rows]
    y = [1.0 - r["angle_L"] for r in rows]
    mn, mx = min(x + y), max(x + y)
    fig, ax = plt.subplots(figsize=(5.0, 4.5), layout="constrained")
    ax.loglog([mn, mx], [mn, mx], "--", color="gray", label="Identity")
    ax.loglog(x, y, "o", label="Measured numerical gaps")
    ax.set_xlabel("Direct Jacobian gap $(1 - L)$")
    ax.set_ylabel("Principal-sine Gram gap $(\\sin^2\\theta_1)$")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.savefig(out_dir / "gap_identity.png", dpi=220)
    fig.savefig(out_dir / "gap_identity.svg")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify principal-sine Gram vs. direct tangent-Jacobian spectral identity.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--synthetic", action="store_true", help="Run on synthetic complex STFT signals.")
    group.add_argument("--audio-root", type=str, help="Path to local MUSAN audio directory.")
    parser.add_argument("--out", type=str, required=True, help="Output JSONL path.")
    parser.add_argument("--plot", action="store_true", help="Save log-log gap identity figure next to output.")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict] = []

    with out_path.open("w", encoding="utf-8") as f:
        if args.synthetic:
            for seed in (6, 19, 30):
                rng = np.random.default_rng(seed)
                x = rng.normal(size=64) + 1j * rng.normal(size=64)
                w = np.exp(-0.5 * ((np.arange(16) - 7.5) / (16.0 / 6.0)) ** 2)
                op = NumpyPeriodicSTFT(64, w, hop=4, n_fft=16)
                info, _, _ = compute_spectral_geometry(op, x)
                rec = dict(source_id=f"synthetic_seed_{seed}", profile="gaussian_16_4", status="RESOLVED", **info)
                f.write(json.dumps(rec, allow_nan=False) + "\n")
                summary_rows.append(rec)
        else:
            for meta, sig in load_audio_records(args.audio_root):
                for profile in STFT_PROFILES:
                    op = NumpyPeriodicSTFT(len(sig), *make_window(profile))
                    info, _, _ = compute_spectral_geometry(op, sig)
                    rec = dict(source_id=meta["source_id"], profile=profile, status="RESOLVED", **info)
                    f.write(json.dumps(rec, allow_nan=False) + "\n")
                    summary_rows.append(rec)

    csv_path = out_path.with_suffix(".csv")
    with csv_path.open("w", encoding="utf-8", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    if args.plot and summary_rows:
        save_gap_figure(summary_rows, out_path.parent)

    max_disc = max(r["gap_relative_discrepancy"] for r in summary_rows)
    max_rad = max(r["radial_zero_residual"] for r in summary_rows)
    print(f"Resolved {len(summary_rows)} geometries | max gap discrepancy = {max_disc:.3e} | max radial residual = {max_rad:.3e}")


if __name__ == "__main__":
    main()
