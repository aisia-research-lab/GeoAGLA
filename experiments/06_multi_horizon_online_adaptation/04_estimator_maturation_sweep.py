#!/usr/bin/env python3
"""Estimator Maturation and Horizon Trace Audit (Online Evaluator - Task B1 / E6-D).
Section 7 of ICLR 2027 Next Experiment Handoff for Students A & B.
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
SCRIPTS_DIR = ROOT / "scripts"
for p in (SRC_DIR, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from common import load_json, dump_json, write_csv, read_csv, fnum, quantiles
from geometry_gla.operators.stft import (
    AnalysisOperator, periodic_stft_matrix, gaussian_window, hann_window
)
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.geometry.realify import r2c
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.metrics.phase import orbit_distance


def _parse_config(cfg_str: str) -> dict[str, Any]:
    # e.g. "g16_w8_h4_f8" or "h32_w16_h4_f16"
    parts = cfg_str.split("_")
    w_type = "gaussian" if parts[0].startswith("g") else "hann"
    N = int(parts[0][1:])
    W = int(parts[1][1:])
    hop = int(parts[2][1:])
    n_fft = int(parts[3][1:])
    return {"window": w_type, "N": N, "W": W, "hop": hop, "n_fft": n_fft}


def _build_operator(c: dict[str, Any]) -> AnalysisOperator:
    w = gaussian_window(c["W"]) if c["window"] == "gaussian" else hann_window(c["W"])
    T = periodic_stft_matrix(c["N"], w, c["hop"], c["n_fft"])
    return AnalysisOperator(T)


def compute_maturation_times(
    errors_rel: list[float],
    thresholds: tuple[float, ...] = (0.01, 0.005, 0.001)
) -> dict[str, int | None]:
    """Find first iteration after which envelope relative error stays <= threshold for the rest of tail."""
    n = len(errors_rel)
    res = {}
    for th in thresholds:
        th_key = f"T_edge_{str(th).replace('.', 'p')}"
        t_match = None
        for i in range(n):
            if all(errors_rel[j] <= th for j in range(i, n)):
                t_match = i
                break
        res[th_key] = t_match
    return res


def compute_param_stabilization(
    alphas: list[float],
    gammas: list[float],
    tol: float = 0.01
) -> int | None:
    """First iteration after which parameter variations stay <= tol."""
    n = len(alphas)
    if n < 10:
        return None
    for i in range(10, n):
        tail_a = alphas[i:]
        tail_g = gammas[i:]
        std_a = np.std(tail_a) / max(1e-12, np.mean(np.abs(tail_a)))
        std_g = np.std(tail_g) / max(1e-12, np.mean(np.abs(tail_g)))
        if std_a <= tol and std_g <= tol:
            return i
    return None


def run_maturation_audit(
    ledger_path: str | Path | None = None,
    out_dir: str | Path | None = None,
    n_iter: int = 180,
    warmup: int = 12,
    block_size: int = 8,
):
    out = Path(out_dir or (ROOT / "results" / "e6_maturation"))
    traces_dir = ROOT / "results" / "traces"
    figs_dir = ROOT / "results" / "figures"
    for d in (out, traces_dir, figs_dir):
        d.mkdir(parents=True, exist_ok=True)

    lp = ledger_path or (ROOT / "results" / "e6_geometry_opportunity" / "e6_case_ledger.csv")
    if not Path(lp).exists():
        # Fallback to generating representative cases directly
        print(f"Ledger {lp} not found. Running on predefined representative case grid...")
        cases = [
            {"case_id": "rep_low_opp", "config": "g16_w8_h4_f8", "seed": 0, "epsilon": 0.001, "opp_regime": "low"},
            {"case_id": "rep_med_opp_1", "config": "g32_w16_h4_f16", "seed": 1, "epsilon": 0.001, "opp_regime": "medium"},
            {"case_id": "rep_med_opp_2", "config": "h32_w16_h4_f16", "seed": 2, "epsilon": 0.001, "opp_regime": "medium"},
            {"case_id": "rep_high_opp_1", "config": "g48_w24_h6_f24", "seed": 3, "epsilon": 0.0001, "opp_regime": "high"},
            {"case_id": "rep_high_opp_2", "config": "h48_w24_h6_f24", "seed": 4, "epsilon": 0.0001, "opp_regime": "high"},
            {"case_id": "rep_high_opp_3", "config": "h64_w32_h8_f32", "seed": 5, "epsilon": 0.0001, "opp_regime": "high"},
        ]
    else:
        all_rows = read_csv(lp)
        print(f"Loaded {len(all_rows)} cases from {lp}")
        # Sort by delta_oracle_obs to pick low, medium, high opportunity cases
        valid = [r for r in all_rows if fnum(r.get("delta_oracle_obs")) is not None]
        valid.sort(key=lambda r: float(r["delta_oracle_obs"]))
        
        # Pick 12 representative cases spanning the full opportunity distribution
        indices = np.linspace(0, len(valid) - 1, min(12, len(valid)), dtype=int)
        cases = []
        for rank, idx in enumerate(indices):
            r = valid[idx]
            d_o = float(r["delta_oracle_obs"])
            regime = "low" if rank < len(indices)//3 else ("medium" if rank < 2*len(indices)//3 else "high")
            cases.append({
                "case_id": r["case_id"],
                "config": r["config"],
                "seed": int(r["seed"]),
                "epsilon": float(r["epsilon_or_initialization"]),
                "opp_regime": regime,
                "delta_oracle_obs": d_o,
                "delta_online_obs": fnum(r.get("delta_online_obs")),
                "lambda_plus": fnum(r.get("lambda_plus")),
            })

    print(f"\n--- [TASK B1 / E6-D] Running Estimator Maturation Traces on {len(cases)} cases ---")
    maturation_records = []
    plot_cases = {"low": None, "medium": None, "high": None}

    for idx, c in enumerate(cases, 1):
        cid = c["case_id"]
        cfg = _parse_config(c["config"])
        seed = c["seed"]
        eps = c["epsilon"]
        regime = c["opp_regime"]

        try:
            op = _build_operator(cfg)
        except Exception as e:
            print(f"[{idx}/{len(cases)}] {cid} Operator build failed: {e}")
            continue

        rng = np.random.default_rng(seed)
        N = cfg["N"]
        x = rng.normal(size=N) + 1j * rng.normal(size=N)
        c_star = op.analyze(x)
        minmag = float(np.min(np.abs(c_star)))
        if minmag < 1e-12:
            continue

        spec = transverse_spectrum(c_star, op)
        lp = float(spec["lambda_plus"])
        lm = float(spec["lambda_minus"])

        # Perturbation along slowest transverse mode
        jvals, jvecs = np.linalg.eigh(spec["J"])
        top_idx = np.where(jvals < 1.0 - 1e-8)[0][-1]
        v = r2c(spec["QU"] @ jvecs[:, top_idx])
        v /= np.linalg.norm(v)

        t0 = c_star + eps * v
        t_minus1 = t0.copy()
        s = np.abs(c_star)

        # Run frozen online policy
        online_res = run_online_policy(
            t0, t_minus1, s, op,
            n_iter=n_iter, warmup=warmup, block_size=block_size,
            memory=3, margin=0.0, policy="dynamic_envelope"
        )

        traj = online_res["trajectory"]
        blocks = online_res["blocks"]

        # Reconstruct per-iteration trace
        trace_rows = []
        errors_rel = []
        alphas = []
        gammas = []
        iter_envelope = None
        iter_raw = None
        iter_alpha = 0.0
        iter_beta = 0.0
        iter_gamma = 1.0
        accepted_flag = True

        for k in range(len(traj)):
            # Determine which block k belongs to
            if k < warmup:
                iter_raw = None
                iter_envelope = None
                iter_alpha, iter_beta, iter_gamma = 0.0, 0.0, 1.0
                accepted_flag = True
            else:
                blk_idx = min(len(blocks) - 1, (k - warmup) // block_size)
                blk = blocks[blk_idx]
                iter_raw = blk.get("raw_current")
                iter_envelope = blk.get("edge_state")
                iter_alpha = blk.get("alpha", 0.0)
                iter_beta = blk.get("beta", 0.0)
                iter_gamma = blk.get("gamma", 1.0)
                accepted_flag = bool(blk.get("candidate_accepted", True))

            orb_err = orbit_distance(traj[k], c_star)
            env_val = iter_envelope if iter_envelope is not None else (iter_raw if iter_raw is not None else 0.0)
            rel_err = abs(env_val - lp) / lp if env_val > 0 else 1.0

            errors_rel.append(rel_err)
            alphas.append(iter_alpha)
            gammas.append(iter_gamma)

            trace_rows.append({
                "iteration": k,
                "lambda_hat_raw": iter_raw,
                "lambda_hat_envelope": iter_envelope,
                "lambda_plus_oracle": lp,
                "edge_rel_error": rel_err,
                "alpha": iter_alpha,
                "beta": iter_beta,
                "gamma": iter_gamma,
                "safeguard_accept": accepted_flag,
                "orbit_error": orb_err,
            })

        # Save individual trace
        write_csv(trace_rows, traces_dir / f"{cid}_trace.csv")

        # Compute maturation metrics
        mat_times = compute_maturation_times(errors_rel)
        t_param = compute_param_stabilization(alphas, gammas)

        d_online = c.get("delta_online_obs")
        if d_online is None:
            # Estimate online rate from late trajectory
            e_sub = [r["orbit_error"] for r in trace_rows[int(0.55*n_iter):]]
            p = np.polyfit(np.arange(len(e_sub)), np.log(np.clip(e_sub, 1e-14, None)), 1)
            q_on = float(np.exp(p[0]))
            q_fg = fgla_opt(lp)["q"]
            d_online = q_fg - q_on

        t1pct = mat_times.get("T_edge_0p01")
        t05pct = mat_times.get("T_edge_0p005")
        t01pct = mat_times.get("T_edge_0p001")

        rec = {
            "case_id": cid,
            "config": c["config"],
            "seed": seed,
            "opp_regime": regime,
            "lambda_plus": lp,
            "delta_oracle_obs": c.get("delta_oracle_obs"),
            "delta_online_obs": d_online,
            "T_edge_1pct": t1pct,
            "T_edge_0p5pct": t05pct,
            "T_edge_0p1pct": t01pct,
            "T_param": t_param,
            "maturation_ratio_1pct": (t1pct / n_iter) if t1pct is not None else None,
            "maturation_ratio_0p5pct": (t05pct / n_iter) if t05pct is not None else None,
            "final_edge_rel_error": errors_rel[-1],
        }
        maturation_records.append(rec)

        if plot_cases[regime] is None:
            plot_cases[regime] = {
                "cid": cid, "lp": lp, "trace": trace_rows,
                "t1pct": t1pct, "t05pct": t05pct
            }

        print(f"[{idx}/{len(cases)}] {cid} ({regime} opp): lp={lp:.5f} | T_1%={t1pct} | T_0.5%={t05pct} | T_param={t_param}")

    # Write summary files
    write_csv(maturation_records, out / "maturation_ledger.csv")
    dump_json({
        "n_cases": len(maturation_records),
        "thresholds": ["1%", "0.5%", "0.1%"],
        "records": maturation_records
    }, out / "maturation_summary.json")

    # --------------------------------------------------------------------------
    # Figure B1: Estimator Maturation Traces (Low, Medium, High Opportunity)
    # --------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), sharey=False)
    regime_order = ["low", "medium", "high"]
    for ax, reg in zip(axes, regime_order):
        pc = plot_cases.get(reg)
        if pc is None:
            ax.set_title(f"{reg.capitalize()} Opportunity (No Data)")
            continue
        tr = pc["trace"]
        iters = [r["iteration"] for r in tr]
        raws = [r["lambda_hat_raw"] for r in tr]
        envs = [r["lambda_hat_envelope"] for r in tr]
        lp_val = pc["lp"]

        ax.axhline(lp_val, color="crimson", linestyle="--", linewidth=1.5, label=r"Oracle $\lambda_+$")
        ax.plot(iters, raws, color="deepskyblue", alpha=0.6, linestyle=":", marker=".", markersize=3, label=r"Raw Ritz $\hat{\lambda}$")
        ax.plot(iters, envs, color="navy", linewidth=2.0, label=r"Dynamic Envelope $\lambda_{\rm env}$")

        if pc["t1pct"] is not None:
            ax.axvline(pc["t1pct"], color="darkgreen", linestyle="-.", alpha=0.7, label=f"T_1% ({pc['t1pct']})")
        if pc["t05pct"] is not None:
            ax.axvline(pc["t05pct"], color="purple", linestyle="--", alpha=0.7, label=f"T_0.5% ({pc['t05pct']})")

        ax.set_title(f"{reg.capitalize()} Opportunity ({pc['cid']})", fontsize=11, fontweight="bold")
        ax.set_xlabel("Iteration", fontsize=10)
        ax.set_ylabel(r"Spectral Edge Estimate $\hat{\lambda}_+$", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="lower right", fontsize=8)

    fig.tight_layout()
    fig_b1_path = figs_dir / "Figure_B1_estimator_maturation_traces.png"
    fig.savefig(fig_b1_path, dpi=200)
    plt.close(fig)
    print(f"\n[OK] Saved Figure B1 to {fig_b1_path}")

    # --------------------------------------------------------------------------
    # Figure B2: Online Gain vs Estimator Maturation Ratio
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    valid_pts = [r for r in maturation_records if r["maturation_ratio_1pct"] is not None and r["delta_online_obs"] is not None]
    if valid_pts:
        xs = [r["maturation_ratio_1pct"] for r in valid_pts]
        ys = [r["delta_online_obs"] for r in valid_pts]
        ax.scatter(xs, ys, color="royalblue", edgecolor="black", s=60, alpha=0.85, zorder=3)
        ax.axhline(0, color="gray", linestyle="--", linewidth=1.0)

        # Trendline
        if len(xs) > 2:
            z = np.polyfit(xs, ys, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(xs), max(xs), 50)
            ax.plot(x_line, p(x_line), color="crimson", linestyle="-", linewidth=1.8, label=f"Trend (slope={z[0]:.3f})")
            ax.legend(fontsize=9)

    ax.set_xlabel(r"Estimator Maturation Ratio ($T_{\rm edge, 1\%} / H$)", fontsize=11)
    ax.set_ylabel(r"Observed Online Gain ($\Delta_{\rm online}^{\rm obs} = q_{\rm FGLA} - q_{\rm Online}$)", fontsize=11)
    ax.set_title(r"Figure B2: Online Gain vs. Estimator Maturation Ratio", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig_b2_path = figs_dir / "Figure_B2_online_gain_vs_maturation_ratio.png"
    fig.savefig(fig_b2_path, dpi=200)
    plt.close(fig)
    print(f"[OK] Saved Figure B2 to {fig_b2_path}")

    return maturation_records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Task B1: Estimator Maturation Audit")
    parser.add_argument("--ledger", type=str, default=None, help="Path to E6 case ledger")
    parser.add_argument("--out", type=str, default=None, help="Output directory")
    parser.add_argument("--n-iter", type=int, default=180, help="Iteration horizon")
    args = parser.parse_args()

    run_maturation_audit(ledger_path=args.ledger, out_dir=args.out, n_iter=args.n_iter)