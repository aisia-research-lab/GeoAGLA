from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import matplotlib.pyplot as plt

from geometry_gla.operators.stft import (
    AnalysisOperator, periodic_stft_matrix, gaussian_window, hann_window,
)
from geometry_gla.geometry.jacobian import jacobian_matrix_on_range
from geometry_gla.geometry.principal_angles import principal_angle_spectrum
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.geometry.realify import r2c
from geometry_gla.algorithms.minimax import oracle_minimax, fgla_opt
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.metrics.phase import orbit_distance


def _window(kind: str, length: int) -> np.ndarray:
    if kind == "gaussian":
        return gaussian_window(length)
    if kind == "hann":
        return hann_window(length)
    raise ValueError(f"unknown window {kind}")


def _make_case(cfg: dict[str, Any], seed: int, near_zero_tol: float):
    rng = np.random.default_rng(seed)
    T = periodic_stft_matrix(
        cfg["signal_length"], _window(cfg["window"], cfg["window_length"]),
        cfg["hop"], cfg["n_fft"],
    )
    op = AnalysisOperator(T)
    # Complex signals match the complex-Hilbert-space local theory directly.
    x = rng.normal(size=cfg["signal_length"]) + 1j * rng.normal(size=cfg["signal_length"])
    c = op.analyze(x)
    minmag = float(np.min(np.abs(c)))
    if minmag <= near_zero_tol:
        raise RuntimeError(f"near-zero STFT coefficient {minmag:.3e}")
    return op, c, minmag


def _fit_window(errors: np.ndarray, lo: int, hi: int, floor: float = 1e-10):
    hi = min(hi, len(errors))
    idx = np.arange(lo, hi)
    idx = idx[np.isfinite(errors[idx]) & (errors[idx] > floor)]
    if idx.size < 6:
        return None
    slope, intercept = np.polyfit(idx.astype(float), np.log(errors[idx]), 1)
    return {"q": float(np.exp(slope)), "n": int(idx.size), "lo": int(idx[0]), "hi": int(idx[-1]),
            "slope": float(slope), "intercept": float(intercept)}


def _adaptive_late_fit(errors: np.ndarray, floor: float = 1e-10):
    idx = np.where(np.isfinite(errors) & (errors > floor))[0]
    idx = idx[idx >= 4]
    if idx.size < 8:
        return None
    # Later 45% of all trustworthy points. This deliberately retains enough
    # samples for critically damped n*q^n transients while moving toward the tail.
    start = int(0.55 * idx.size)
    sel = idx[start:]
    if sel.size < 8:
        sel = idx[-8:]
    slope, intercept = np.polyfit(sel.astype(float), np.log(errors[sel]), 1)
    return {"q": float(np.exp(slope)), "n": int(sel.size), "lo": int(sel[0]), "hi": int(sel[-1]),
            "slope": float(slope), "intercept": float(intercept)}


def _rate_audit(errors: list[float], n_iter: int):
    e = np.asarray(errors, dtype=float)
    windows = {}
    for label, lo, hi in [
        ("early", 10, min(50, n_iter + 1)),
        ("middle", max(20, n_iter // 3), min(2 * n_iter // 3, n_iter + 1)),
        ("late", max(30, 2 * n_iter // 3), n_iter + 1),
    ]:
        windows[label] = _fit_window(e, lo, hi)
    windows["adaptive_late"] = _adaptive_late_fit(e)
    return windows


def run(config_path: str, out_dir: str):
    config = json.loads(Path(config_path).read_text())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)

    h1_rows = []
    h1_points_x, h1_points_y = [], []
    h2_rows = []
    rate_audits = []

    total_cases = len(config["configs"]) * len(config["seeds"])
    completed = 0
    for cfg in config["configs"]:
        for seed in config["seeds"]:
            op, c_star, minmag = _make_case(cfg, seed, config["near_zero_tol"])

            # H1: two independent routes to the same spectrum.
            J, _ = jacobian_matrix_on_range(c_star, op)
            vals = np.sort(np.linalg.eigvalsh(J))
            geom, _ = principal_angle_spectrum(op.T, c_star)
            if vals.size != geom.size:
                raise RuntimeError("Jacobian/principal-angle spectrum dimension mismatch")
            rel = float(np.linalg.norm(vals - geom) / (np.linalg.norm(vals) + 1e-15))
            sym = float(np.linalg.norm(J - J.T))
            neutral = int(np.sum(vals >= 1 - config["phase_tol"]))
            h1_rows.append({
                "config": cfg["id"], "seed": seed, "dimension": int(vals.size),
                "min_abs_coeff": minmag, "relative_spectral_error": rel,
                "symmetry_error": sym, "neutral_count": neutral,
                "lambda_min_all": float(vals[0]), "lambda_max_all": float(vals[-1]),
            })
            h1_points_x.extend(geom.tolist())
            h1_points_y.extend(vals.tolist())

            # H2: regular-case oracle spectrum and local perturbations.
            spec = transverse_spectrum(c_star, op, phase_tol=config["phase_tol"])
            if spec["neutral_count"] != 1:
                # Preserve it in H1; skip H2 because the theorem assumes regularity modulo phase.
                completed += 1
                print(f"[{completed}/{total_cases}] {cfg['id']} seed={seed}: nonregular; H2 skipped")
                continue
            lm_raw, lp_raw = spec["lambda_minus"], spec["lambda_plus"]
            # Numerical eigensolvers can return O(1e-16) negative values for a PSD operator.
            lm = max(0.0, float(lm_raw))
            lp = min(1.0 - 1e-14, float(lp_raw))
            if not (lm < lp):
                raise RuntimeError(f"degenerate transverse interval [{lm_raw}, {lp_raw}]")
            prm_o = oracle_minimax(lm, lp)
            prm_f = fgla_opt(lp)

            # Perturb in the slowest transverse eigenmode to make the limiting factor observable.
            jvals, jvecs = np.linalg.eigh(spec["J"])
            transverse_idx = np.where(jvals < 1 - config["phase_tol"])[0]
            top_idx = transverse_idx[-1]
            v = r2c(spec["QU"] @ jvecs[:, top_idx])
            v = v / np.linalg.norm(v)

            methods = {
                "gla": {"alpha": 0.0, "beta": 0.0, "gamma": 1.0, "q": lp},
                "fgla_opt": prm_f,
                "oracle": prm_o,
            }
            s = np.abs(c_star)
            for eps in config["perturbations"]:
                t0 = c_star + eps * v
                for name, prm in methods.items():
                    traj = run_agla_state(t0, t0.copy(), s, op, prm["alpha"], prm["beta"], prm["gamma"], config["n_iter"])
                    errors = [orbit_distance(z, c_star) for z in traj]
                    audit = _rate_audit(errors, config["n_iter"])
                    fit = audit["adaptive_late"]
                    qobs = float(fit["q"]) if fit is not None else float("nan")
                    qpred = float(prm["q"])
                    relerr = float(abs(qobs - qpred) / max(qpred, 1e-15)) if np.isfinite(qobs) else float("nan")
                    h2_rows.append({
                        "config": cfg["id"], "seed": seed, "epsilon": eps, "method": name,
                        "lambda_minus": lm, "lambda_plus": lp, "q_pred": qpred, "q_obs": qobs,
                        "abs_error": float(abs(qobs - qpred)) if np.isfinite(qobs) else float("nan"),
                        "rel_error": relerr, "final_error": float(errors[-1]),
                        "fit_lo": fit["lo"] if fit else None, "fit_hi": fit["hi"] if fit else None,
                        "fit_n": fit["n"] if fit else 0,
                    })
                    rate_audits.append({
                        "config": cfg["id"], "seed": seed, "epsilon": eps, "method": name,
                        "q_pred": qpred, "windows": audit,
                    })
            completed += 1
            print(f"[{completed}/{total_cases}] {cfg['id']} seed={seed}: H1/H2 done")

    # Save machine-readable raw results.
    (out / "h1_multi.json").write_text(json.dumps(h1_rows, indent=2))
    (out / "h2_multi.json").write_text(json.dumps(h2_rows, indent=2, allow_nan=True))
    (out / "finite_window_audit.json").write_text(json.dumps(rate_audits, indent=2, allow_nan=True))

    def write_csv(path: Path, rows: list[dict[str, Any]]):
        if not rows:
            return
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    write_csv(out / "h1_multi.csv", h1_rows)
    write_csv(out / "h2_multi.csv", h2_rows)

    # Figure D1: all eigenvalues from both independent computations.
    fig = plt.figure(figsize=(6.5, 6.0))
    ax = fig.add_subplot(111)
    ax.scatter(h1_points_x, h1_points_y, s=10, alpha=0.45)
    ax.plot([0, 1], [0, 1], linewidth=1.2)
    ax.set_xlabel(r"$\cos^2\theta_j$ from principal angles")
    ax.set_ylabel(r"$\lambda_j(DG(c^\star))$")
    ax.set_title("D1 — Tangent geometry identity across STFT instances")
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
    fig.tight_layout(); fig.savefig(out / "figures" / "D1_geometry_identity.png", dpi=180); plt.close(fig)

    # Figure D2: predicted vs observed contraction, one marker cloud per method.
    fig = plt.figure(figsize=(6.5, 6.0))
    ax = fig.add_subplot(111)
    for method, marker in [("gla", "o"), ("fgla_opt", "s"), ("oracle", "^")]:
        rr = [r for r in h2_rows if r["method"] == method and np.isfinite(r["q_obs"])]
        ax.scatter([r["q_pred"] for r in rr], [r["q_obs"] for r in rr], s=22, alpha=0.6, marker=marker, label=method)
    ax.plot([0, 1], [0, 1], linewidth=1.2)
    ax.set_xlabel("Predicted local contraction factor")
    ax.set_ylabel("Observed fitted contraction factor")
    ax.set_title("D2 — Predicted versus observed local contraction")
    ax.set_xlim(0, 1.02); ax.set_ylim(0, 1.02); ax.legend()
    fig.tight_layout(); fig.savefig(out / "figures" / "D2_rate_prediction.png", dpi=180); plt.close(fig)

    # Figure D2b: finite-window bias relative to predicted rate.
    fig = plt.figure(figsize=(7.0, 4.8))
    ax = fig.add_subplot(111)
    labels = ["early", "middle", "late", "adaptive_late"]
    for method, marker in [("fgla_opt", "s"), ("oracle", "^")]:
        med = []
        for label in labels:
            vals_rel = []
            for r in rate_audits:
                if r["method"] != method:
                    continue
                f = r["windows"].get(label)
                if f is not None:
                    vals_rel.append((f["q"] - r["q_pred"]) / max(r["q_pred"], 1e-15))
            med.append(float(np.median(vals_rel)) if vals_rel else np.nan)
        ax.plot(np.arange(len(labels)), med, marker=marker, label=method)
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xticks(np.arange(len(labels)), labels)
    ax.set_ylabel("Median relative fitted-rate bias")
    ax.set_title("D2b — Finite-window contraction-rate audit")
    ax.legend(); fig.tight_layout(); fig.savefig(out / "figures" / "D2b_finite_window_audit.png", dpi=180); plt.close(fig)

    # Aggregate gates.
    h1_err = np.array([r["relative_spectral_error"] for r in h1_rows])
    regular_cases = {(r["config"], r["seed"]) for r in h2_rows}
    def meth(method):
        return [r for r in h2_rows if r["method"] == method and np.isfinite(r["q_obs"])]
    summary = {
        "n_h1_cases": len(h1_rows),
        "n_regular_h2_cases": len(regular_cases),
        "n_h2_runs": len(h2_rows),
        "h1_max_relative_spectral_error": float(np.max(h1_err)),
        "h1_median_relative_spectral_error": float(np.median(h1_err)),
        "h1_all_single_neutral": bool(all(r["neutral_count"] == 1 for r in h1_rows)),
        "h1_pass": bool(np.max(h1_err) <= config["h1_relative_error_tol"] and all(r["neutral_count"] == 1 for r in h1_rows)),
    }
    for method in ["gla", "fgla_opt", "oracle"]:
        rr = meth(method)
        rels = np.array([r["rel_error"] for r in rr], dtype=float)
        summary[f"{method}_median_relative_rate_error"] = float(np.nanmedian(rels)) if rels.size else None
        summary[f"{method}_p90_relative_rate_error"] = float(np.nanpercentile(rels, 90)) if rels.size else None

    # Ordering is checked within identical (config, seed, eps) triples.
    groups = {}
    for r in h2_rows:
        key = (r["config"], r["seed"], r["epsilon"])
        groups.setdefault(key, {})[r["method"]] = r
    order_flags = []
    pred_order_flags = []
    for g in groups.values():
        if set(g) >= {"gla", "fgla_opt", "oracle"}:
            qo, qf, qg = g["oracle"]["q_obs"], g["fgla_opt"]["q_obs"], g["gla"]["q_obs"]
            if np.isfinite(qo) and np.isfinite(qf) and np.isfinite(qg):
                order_flags.append(qo < qf < qg)
            pred_order_flags.append(g["oracle"]["q_pred"] < g["fgla_opt"]["q_pred"] < g["gla"]["q_pred"])
    summary["observed_ordering_fraction"] = float(np.mean(order_flags)) if order_flags else None
    summary["predicted_ordering_fraction"] = float(np.mean(pred_order_flags)) if pred_order_flags else None
    summary["h2_ordering_pass"] = bool(order_flags and np.mean(order_flags) >= 0.90)
    summary["phase1c_gate"] = "GREEN" if summary["h1_pass"] and summary["h2_ordering_pass"] else "REVIEW"
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== Phase-1C summary ===")
    print(json.dumps(summary, indent=2))
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/phase1c_grid.json")
    p.add_argument("--out", default="results/phase1c")
    a = p.parse_args()
    run(a.config, a.out)


if __name__ == "__main__":
    main()