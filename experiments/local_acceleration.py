"""Controlled local oracle acceleration and spectral mismatch sensitivity sweep.

Validates:
  - Theorem 4.1: One-edge minimax AGLA strictly outperforms optimal FGLA on
    dominant-mode perturbations while GLA eliminates radial perturbations immediately.
  - Theorem 4.2: Exact stationary mismatch rate R(L, q0(ell)) and strict
    improvement interval across gap ratios and boundary endpoints.

Usage:
  python experiments/local_acceleration.py --synthetic --out outputs/local_synthetic.jsonl
  python experiments/local_acceleration.py --audio-root /path/to/musan --out outputs/local_audio.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterator

import numpy as np

from experiments.common import NumpyPeriodicSTFT, STFT_PROFILES, load_audio_records, make_window
from experiments.spectral_geometry import compute_spectral_geometry
from geometry_gla.algorithms.minimax import (
    fgla_opt,
    mismatch_acceleration_interval,
    mismatch_radius,
    one_edge_minimax,
)

GAP_RATIOS = [0.25, 0.5, 0.75, 1.0, 1.10, 1.125, 1.25, 1.5, 2.0]
CHECKPOINTS = (1, 2, 10, 30, 90, 180, 360, 720, 1440)


def run_mismatch_sweep(
    op: NumpyPeriodicSTFT,
    c_star: np.ndarray,
    dom_vec: np.ndarray,
    L: float,
    horizon: int = 1440,
    scale: float = 1e-6,
) -> Iterator[dict]:
    """Run controlled dominant-mode and radial trajectories across mismatch ratios."""
    s = np.abs(c_star)
    R = float(np.linalg.norm(c_star))
    lo, hi = mismatch_acceleration_interval(L)
    configs: list[tuple[str, float | None]] = (
        [(f"gap_ratio_{z}", 1.0 - z * (1.0 - L)) for z in GAP_RATIOS]
        + [("lower_boundary", lo), ("upper_boundary", hi), ("FGLA_oracle", None), ("GLA", -1.0)]
    )

    save_set = set(CHECKPOINTS) | {horizon}
    for direction, pert_vec, lam in (("upper", dom_vec, L), ("radial", c_star, 0.0)):
        for name, ell in configs:
            if ell is None:
                par = fgla_opt(L)
                a, b, g, pred = par["alpha"], par["beta"], par["gamma"], par["q"]
                cls = "baseline"
            elif ell < 0.0:
                a, b, g, pred = 0.0, 0.0, 1.0, L
                cls = "baseline"
            else:
                par = one_edge_minimax(ell)
                a, b, g = par["alpha"], par["beta"], par["gamma"]
                pred = mismatch_radius(L, ell)
                cls = "boundary" if "boundary" in name else ("strict_advantage" if lo < ell < hi else "no_strict_advantage")

            t = c_star + scale * pert_vec
            tp = t.copy()
            lin = np.array([1.0, 1.0], dtype=float)
            A = (1.0 - g) * (1.0 + b) + g * lam * (1.0 + a)
            C = (1.0 - g) * b + g * lam * a
            M = np.array([[A, -C], [1.0, 0.0]], dtype=float)

            for step in range(1, horizon + 1):
                tn = (1.0 - g) * (t + b * (t - tp)) + g * op.G(t + a * (t - tp), s)
                tp, t = t, tn
                lin = M @ lin
                if step in save_set:
                    ph = np.vdot(c_star, t + tp)
                    ph = ph / abs(ph) if abs(ph) > 0.0 else 1.0
                    measured = float(np.hypot(np.linalg.norm(t - ph * c_star), np.linalg.norm(tp - ph * c_star)) / (np.sqrt(2.0) * R))
                    predicted = float(scale * np.linalg.norm(lin) / np.sqrt(2.0))
                    orbit_err = float(np.linalg.norm(t - c_star * np.exp(1j * np.angle(np.vdot(c_star, t)))) / R)
                    yield dict(
                        method=name,
                        direction=direction,
                        scale=scale,
                        iteration=step,
                        ell=None if (ell is None or ell < 0.0) else float(ell),
                        L=L,
                        gap_ratio=None if (ell is None or ell < 0.0) else float((1.0 - ell) / (1.0 - L)),
                        ell_min=lo,
                        ell_max=hi,
                        classification=cls,
                        predicted_worst_rate=float(pred),
                        predicted_state=predicted,
                        measured_state=measured,
                        orbit_error=orbit_err,
                        mag_residual=float(np.linalg.norm(np.abs(t) - s) / R),
                        relative_error=None if predicted < 1e-12 else float(abs(measured - predicted) / predicted),
                        floor=bool(predicted < 1e-12 or measured < 1e-12),
                    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Controlled local acceleration and mismatch sweep.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--synthetic", action="store_true", help="Run on synthetic STFT geometries.")
    group.add_argument("--audio-root", type=str, help="Path to local MUSAN audio directory.")
    parser.add_argument("--out", type=str, required=True, help="Output JSONL path.")
    parser.add_argument("--horizon", type=int, default=1440, help="Maximum iterations.")
    parser.add_argument("--scale", type=float, default=1e-6, help="Initial perturbation norm scale.")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total_rows = 0
    max_rel_err = 0.0

    with out_path.open("w", encoding="utf-8") as f:
        if args.synthetic:
            horizon = min(args.horizon, 180)
            for seed in (6, 19, 30):
                rng = np.random.default_rng(seed)
                x = rng.normal(size=64) + 1j * rng.normal(size=64)
                w = np.exp(-0.5 * ((np.arange(16) - 7.5) / (16.0 / 6.0)) ** 2)
                op = NumpyPeriodicSTFT(64, w, hop=4, n_fft=16)
                info, dom_vec, c_star = compute_spectral_geometry(op, x)
                for row in run_mismatch_sweep(op, c_star, dom_vec, info["L"], horizon=horizon, scale=args.scale):
                    row.update(source_id=f"synthetic_seed_{seed}", profile="gaussian_16_4")
                    f.write(json.dumps(row, allow_nan=False) + "\n")
                    total_rows += 1
                    if row["relative_error"] is not None and not row["floor"]:
                        max_rel_err = max(max_rel_err, row["relative_error"])
        else:
            for meta, sig in load_audio_records(args.audio_root):
                for profile in STFT_PROFILES:
                    op = NumpyPeriodicSTFT(len(sig), *make_window(profile))
                    info, dom_vec, c_star = compute_spectral_geometry(op, sig)
                    for row in run_mismatch_sweep(op, c_star, dom_vec, info["L"], horizon=args.horizon, scale=args.scale):
                        row.update(source_id=meta["source_id"], profile=profile)
                        f.write(json.dumps(row, allow_nan=False) + "\n")
                        total_rows += 1
                        if row["relative_error"] is not None and not row["floor"]:
                            max_rel_err = max(max_rel_err, row["relative_error"])

    print(f"Wrote {total_rows} local/mismatch checkpoint rows to {out_path} | max non-floor relative error = {max_rel_err:.3e}")


if __name__ == "__main__":
    main()
