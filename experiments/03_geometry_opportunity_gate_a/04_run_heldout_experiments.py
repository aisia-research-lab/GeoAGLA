#!/usr/bin/env python3
"""Run controlled held-out geometry generalization experiments.
Section 6 (A3 / E6-C) of ICLR 2027 Next Experiment Handoff for Students A & B.
"""
from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import argparse
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

# Ensure src is in sys.path
ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "experiments" else Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
SCRIPTS_DIR = ROOT / "scripts"
for p in (SRC_DIR, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from common import load_json, dump_json, write_csv, quantiles, fnum
from geometry_gla.operators.stft import (
    AnalysisOperator, periodic_stft_matrix, gaussian_window, hann_window
)
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.geometry.realify import r2c
from geometry_gla.algorithms.minimax import oracle_minimax, fgla_opt
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.metrics.phase import orbit_distance


def _window(kind: str, length: int) -> np.ndarray:
    if kind == "gaussian":
        return gaussian_window(length)
    if kind == "hann":
        return hann_window(length)
    raise ValueError(f"Unknown window kind: {kind}")


def _adaptive_late_fit(errors: list[float] | np.ndarray, floor: float = 1e-10) -> dict[str, Any] | None:
    e = np.asarray(errors, dtype=float)
    idx = np.where(np.isfinite(e) & (e > floor))[0]
    idx = idx[idx >= 4]
    if idx.size < 8:
        return None
    start = int(0.55 * idx.size)
    sel = idx[start:]
    if sel.size < 8:
        sel = idx[-8:]
    slope, intercept = np.polyfit(sel.astype(float), np.log(e[sel]), 1)
    q = float(np.exp(slope))
    return {
        "q": q,
        "n": int(sel.size),
        "lo": int(sel[0]),
        "hi": int(sel[-1]),
        "slope": float(slope),
        "intercept": float(intercept),
    }


def run_heldout_suite(
    manifest_path: str | Path,
    out_dir: str | Path,
    n_iter: int = 180,
    near_zero_tol: float = 1e-10,
    phase_tol: float = 1e-8,
):
    manifest_file = Path(manifest_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    manifest = load_json(manifest_file)
    cases = manifest.get("cases", [])
    print(f"Executing held-out experiment suite on {len(cases)} cases (n_iter={n_iter})...")

    start_time = time.time()
    rows = []
    skipped = []

    for i, c in enumerate(cases, 1):
        cid = c["case_id"]
        N = int(c["N"])
        W = int(c["W"])
        hop = int(c["hop"])
        n_fft = int(c["n_fft"])
        window_name = c["window"]
        seed = int(c["seed"])
        eps = float(c["epsilon"])

        # 1. Build AnalysisOperator
        try:
            w = _window(window_name, W)
            T = periodic_stft_matrix(N, w, hop, n_fft)
            op = AnalysisOperator(T)
        except Exception as ex:
            print(f"[{i}/{len(cases)}] {cid} Operator build failed: {ex}")
            skipped.append({"case_id": cid, "reason": f"operator_error: {ex}"})
            continue

        # 2. Synthesize complex signal and target spectrogram
        rng = np.random.default_rng(seed)
        x = rng.normal(size=N) + 1j * rng.normal(size=N)
        c_star = op.analyze(x)
        minmag = float(np.min(np.abs(c_star)))
        if minmag <= near_zero_tol:
            print(f"[{i}/{len(cases)}] {cid} Near-zero coefficient minmag={minmag:.2e} <= {near_zero_tol}")
            skipped.append({"case_id": cid, "reason": "near_zero_coefficient", "minmag": minmag})
            continue

        # 3. Transverse spectrum
        try:
            spec = transverse_spectrum(c_star, op, phase_tol=phase_tol)
        except Exception as ex:
            print(f"[{i}/{len(cases)}] {cid} Transverse spectrum failed: {ex}")
            skipped.append({"case_id": cid, "reason": f"spectrum_error: {ex}"})
            continue

        if spec["neutral_count"] != 1:
            print(f"[{i}/{len(cases)}] {cid} Non-regular: neutral_count={spec['neutral_count']} != 1")
            skipped.append({"case_id": cid, "reason": "non_regular_neutral_modes", "neutral_count": spec["neutral_count"]})
            continue

        lm_raw, lp_raw = spec["lambda_minus"], spec["lambda_plus"]
        lm = max(0.0, float(lm_raw))
        lp = min(1.0 - 1e-14, float(lp_raw))
        if not (lm < lp):
            print(f"[{i}/{len(cases)}] {cid} Degenerate transverse interval [{lm_raw}, {lp_raw}]")
            skipped.append({"case_id": cid, "reason": "degenerate_interval", "lm": lm_raw, "lp": lp_raw})
            continue

        spectral_width = lp - lm
        transverse_gap = 1.0 - lp

        # 4. Find slowest transverse eigenvector for perturbation
        jvals, jvecs = np.linalg.eigh(spec["J"])
        transverse_idx = np.where(jvals < 1 - phase_tol)[0]
        top_idx = transverse_idx[-1]
        v = r2c(spec["QU"] @ jvecs[:, top_idx])
        v = v / np.linalg.norm(v)

        t0 = c_star + eps * v
        t_minus1 = t0.copy()
        s = np.abs(c_star)

        # 5. Method parameterizations
        prm_fgla = fgla_opt(lp)
        prm_oracle = oracle_minimax(lm, lp)
        prm_conservative = oracle_minimax(0.0, lp)

        methods_config = {
            "gla": {"alpha": 0.0, "beta": 0.0, "gamma": 1.0, "q_pred": lp},
            "fgla_opt": {"alpha": prm_fgla["alpha"], "beta": prm_fgla["beta"], "gamma": prm_fgla["gamma"], "q_pred": prm_fgla["q"]},
            "oracle_minimax": {"alpha": prm_oracle["alpha"], "beta": prm_oracle["beta"], "gamma": prm_oracle["gamma"], "q_pred": prm_oracle["q"]},
            "oracle_conservative": {"alpha": prm_conservative["alpha"], "beta": prm_conservative["beta"], "gamma": prm_conservative["gamma"], "q_pred": prm_conservative["q"]},
        }

        # 6. Run fixed methods
        fits = {}
        for mname, prm in methods_config.items():
            traj = run_agla_state(t0, t_minus1, s, op, prm["alpha"], prm["beta"], prm["gamma"], n_iter)
            errs = [orbit_distance(z, c_star) for z in traj]
            fits[mname] = _adaptive_late_fit(errs)

        # 7. Run Online method (frozen dynamic_envelope, p=3, K=8, margin=0.0)
        try:
            on_res = run_online_policy(
                t0, t_minus1, s, op,
                n_iter=n_iter,
                warmup=12,
                block_size=8,
                memory=3,
                margin=0.0,
                policy="dynamic_envelope",
            )
            on_errs = [orbit_distance(z, c_star) for z in on_res["trajectory"]]
            fits["online"] = _adaptive_late_fit(on_errs)
            
            # Extract final edge estimate from online history/logs
            last_blocks = on_res.get("blocks", [])
            last_estimate = None
            if last_blocks:
                last_estimate = last_blocks[-1].get("raw_estimate")
            edge_est_final = float(last_estimate) if last_estimate is not None else None
            edge_rel_err = abs(edge_est_final - lp) / max(lp, 1e-12) if edge_est_final is not None else None
        except Exception as ex:
            print(f"[{i}/{len(cases)}] {cid} Online execution error: {ex}")
            fits["online"] = None
            edge_est_final = None
            edge_rel_err = None

        # 8. Extract observed contraction rates
        q_gla_obs = fits["gla"]["q"] if fits["gla"] is not None else None
        q_fgla_obs = fits["fgla_opt"]["q"] if fits["fgla_opt"] is not None else None
        q_oracle_obs = fits["oracle_minimax"]["q"] if fits["oracle_minimax"] is not None else None
        q_conservative_obs = fits["oracle_conservative"]["q"] if fits["oracle_conservative"] is not None else None
        q_online_obs = fits["online"]["q"] if fits["online"] is not None else None

        q_gla_pred = float(methods_config["gla"]["q_pred"])
        q_fgla_pred = float(methods_config["fgla_opt"]["q_pred"])
        q_oracle_pred = float(methods_config["oracle_minimax"]["q_pred"])
        q_conservative_pred = float(methods_config["oracle_conservative"]["q_pred"])

        d_oracle_obs = (q_fgla_obs - q_oracle_obs) if (q_fgla_obs is not None and q_oracle_obs is not None) else None
        d_online_obs = (q_fgla_obs - q_online_obs) if (q_fgla_obs is not None and q_online_obs is not None) else None
        d_conservative_obs = (q_fgla_obs - q_conservative_obs) if (q_fgla_obs is not None and q_conservative_obs is not None) else None

        r_capture = None
        r_capture_clipped = None
        if d_online_obs is not None and d_oracle_obs is not None and d_oracle_obs > 1e-8:
            r_capture = d_online_obs / d_oracle_obs
            r_capture_clipped = min(1.0, max(0.0, r_capture))

        online_beats_fgla = bool(d_online_obs > 0.0) if d_online_obs is not None else False

        row = {
            "case_id": cid,
            "N": N,
            "window": window_name,
            "W": W,
            "hop": hop,
            "n_fft": n_fft,
            "seed": seed,
            "epsilon": eps,
            "lambda_minus": lm,
            "lambda_plus": lp,
            "spectral_width": spectral_width,
            "transverse_gap": transverse_gap,
            "q_gla_pred": q_gla_pred,
            "q_fgla_pred": q_fgla_pred,
            "q_oracle_pred": q_oracle_pred,
            "q_conservative_pred": q_conservative_pred,
            "q_gla_obs": q_gla_obs,
            "q_fgla_obs": q_fgla_obs,
            "q_oracle_obs": q_oracle_obs,
            "q_conservative_obs": q_conservative_obs,
            "q_online_obs": q_online_obs,
            "delta_oracle_pred": q_fgla_pred - q_oracle_pred,
            "delta_oracle_obs": d_oracle_obs,
            "delta_online_obs": d_online_obs,
            "delta_conservative_obs": d_conservative_obs,
            "r_capture": r_capture,
            "r_capture_clipped": r_capture_clipped,
            "online_beats_fgla": online_beats_fgla,
            "edge_estimate_final": edge_est_final,
            "edge_rel_error_final": edge_rel_err,
            "fit_window": "adaptive_late",
            "horizon": n_iter,
        }
        rows.append(row)
        print(f"[{i}/{len(cases)}] {cid} N={N} W={W} hop={hop} | lp={lp:.4f} | q_fgla={q_fgla_obs:.4f} q_ora={q_oracle_obs:.4f} q_on={q_online_obs:.4f} | beats={online_beats_fgla}")

    elapsed = time.time() - start_time
    print(f"\nHeld-out suite completed in {elapsed:.2f}s: {len(rows)} valid, {len(skipped)} skipped.")

    # Write held-out ledger
    ledger_csv = out / "e6_heldout_ledger.csv"
    ledger_json = out / "e6_heldout_ledger.json"
    write_csv(rows, ledger_csv)
    dump_json({"schema_version": 1, "n_cases": len(rows), "cases": rows, "skipped": skipped}, ledger_json)

    # Compute summary statistics
    d_oras = [r["delta_oracle_obs"] for r in rows if r["delta_oracle_obs"] is not None]
    d_ons = [r["delta_online_obs"] for r in rows if r["delta_online_obs"] is not None]
    rcaps = [r["r_capture"] for r in rows if r["r_capture"] is not None]

    summary = {
        "n_cases_total": len(cases),
        "n_cases_valid": len(rows),
        "n_cases_skipped": len(skipped),
        "oracle_opportunity": {
            "median": float(np.median(d_oras)) if d_oras else None,
            "iqr": float(np.percentile(d_oras, 75) - np.percentile(d_oras, 25)) if d_oras else None,
            "quantiles": quantiles(d_oras) if d_oras else None,
        },
        "online_gain": {
            "median": float(np.median(d_ons)) if d_ons else None,
            "iqr": float(np.percentile(d_ons, 75) - np.percentile(d_ons, 25)) if d_ons else None,
            "quantiles": quantiles(d_ons) if d_ons else None,
            "frac_positive_gain": float(np.mean([x > 0 for x in d_ons])) if d_ons else None,
            "win_rate_vs_fgla": float(np.mean([r["online_beats_fgla"] for r in rows])) if rows else None,
        },
        "capture": {
            "median": float(np.median(rcaps)) if rcaps else None,
            "iqr": float(np.percentile(rcaps, 75) - np.percentile(rcaps, 25)) if rcaps else None,
            "quantiles": quantiles(rcaps) if rcaps else None,
            "frac_ge_0": float(np.mean([x >= 0.0 for x in rcaps])) if rcaps else None,
            "frac_ge_0p5": float(np.mean([x >= 0.5 for x in rcaps])) if rcaps else None,
            "frac_ge_0p8": float(np.mean([x >= 0.8 for x in rcaps])) if rcaps else None,
            "frac_gt_1": float(np.mean([x > 1.0 for x in rcaps])) if rcaps else None,
            "frac_lt_0": float(np.mean([x < 0.0 for x in rcaps])) if rcaps else None,
        },
        "skipped_cases": skipped,
    }

    summary_json = out / "e6_heldout_summary.json"
    dump_json(summary, summary_json)
    print(f"[OK] Held-out ledger and summary written to {out}")
    return rows, summary


def main():
    parser = argparse.ArgumentParser(description="Run controlled held-out geometry generalization")
    parser.add_argument("--manifest", default=str(ROOT / "configs" / "e6_heldout_manifest_frozen.json"))
    parser.add_argument("--out", default=str(ROOT / "results" / "e6_geometry_opportunity"))
    parser.add_argument("--n-iter", type=int, default=180)
    args = parser.parse_args()

    run_heldout_suite(args.manifest, args.out, n_iter=args.n_iter)


if __name__ == "__main__":
    main()