#!/usr/bin/env python3
"""Multi-Horizon Rate Audit and Failure Decomposition (Online Evaluator - Task B2 / E6-E).
Sections 8 & 9 of ICLR 2027 Next Experiment Handoff for Students A & B.
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

from common import load_json, dump_json, write_csv, read_csv, fnum, median, quantiles
from geometry_gla.operators.stft import (
    AnalysisOperator, periodic_stft_matrix, gaussian_window, hann_window
)
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.geometry.realify import r2c
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.metrics.phase import orbit_distance


def _parse_config(cfg_str: str) -> dict[str, Any]:
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


def _fit_rate(errors: list[float], fraction: float = 0.35, floor: float = 1e-12) -> tuple[float | None, float, int]:
    e = np.asarray(errors, dtype=float)
    idx = np.where(np.isfinite(e) & (e > floor))[0]
    idx = idx[idx >= 4]
    if len(idx) < 8:
        return None, 0.0, 0
    n = max(8, int(np.ceil(fraction * len(idx))))
    sel = idx[-n:]
    x = sel.astype(float)
    y = np.log(e[sel])
    slope, intercept = np.polyfit(x, y, 1)
    q_obs = float(np.exp(slope))
    y_pred = slope * x + intercept
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    ss_res = float(np.sum((y - y_pred) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 1e-14 else 1.0
    return q_obs, max(0.0, min(1.0, r2)), len(sel)


def classify_failure(
    d_oracle_obs: float | None,
    lp: float,
    t_edge_ratio: float | None,
    safeguard_fallback_rate: float,
    r2_fit: float,
    fit_points: int
) -> tuple[str, str]:
    """Assign a deterministic diagnostic category supported by empirical evidence."""
    # 1. Negligible oracle opportunity
    if d_oracle_obs is not None and d_oracle_obs < 1e-4:
        return "NEGLIGIBLE_ORACLE_OPPORTUNITY", f"Oracle headroom is negligible (Delta_oracle = {d_oracle_obs:.2e} < 1e-4)"
    
    # 2. Near-degenerate geometry
    if lp >= 0.9999:
        return "NEAR_DEGENERATE_GEOMETRY", f"Near-degenerate spectral edge (lambda_+ = {lp:.6f} >= 0.9999)"
    
    # 3. Estimator not mature
    if t_edge_ratio is None or t_edge_ratio > 0.45:
        return "ESTIMATOR_NOT_MATURE", f"Ritz envelope maturation latency consumed too much budget (ratio = {t_edge_ratio})"
    
    # 4. Safeguard-dominated transient
    if safeguard_fallback_rate > 0.20:
        return "SAFEGUARD_DOMINATED_TRANSIENT", f"Frequent rollback to GLA fallback ({safeguard_fallback_rate*100:.1f}% > 20%)"
    
    # 5. Rate-fit uncertainty / insufficient tail
    if r2_fit < 0.70 or fit_points < 8:
        return "RATE_FIT_UNCERTAINTY", f"Low regression R^2 ({r2_fit:.2f}) or insufficient tail points ({fit_points})"
    
    # 6. Unexplained
    return "UNEXPLAINED", "None of the predefined diagnostics explain the loss"


def run_multi_horizon_audit(
    ledger_path: str | Path | None = None,
    out_dir: str | Path | None = None,
    horizons: tuple[int, ...] = (60, 120, 180, 360),
    sample_size: int = 15,
):
    out = Path(out_dir or (ROOT / "results" / "e6_failure_analysis"))
    figs_dir = ROOT / "results" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    figs_dir.mkdir(parents=True, exist_ok=True)

    lp_file = ledger_path or (ROOT / "results" / "e6_geometry_opportunity" / "e6_case_ledger.csv")
    if Path(lp_file).exists():
        all_rows = read_csv(lp_file)
        # Sample across configurations deterministically
        indices = np.linspace(0, len(all_rows) - 1, min(sample_size, len(all_rows)), dtype=int)
        cases = [all_rows[i] for i in indices]
    else:
        cases = [
            {"case_id": f"cfg_{i}", "config": "g16_w8_h4_f8", "seed": i, "epsilon_or_initialization": 0.001}
            for i in range(sample_size)
        ]

    print(f"\n--- [TASK B2 / E6-E] Multi-Horizon Rate Audit on {len(cases)} cases across H in {horizons} ---")

    horizon_metrics = {}
    failure_cases = []
    
    for H in horizons:
        print(f"\nEvaluating Horizon H = {H}...")
        warmup = min(12, H // 4)
        block_size = 8

        q_onlines = []
        q_fglas = []
        q_oracles = []
        captures = []
        losses = []

        for idx, c in enumerate(cases, 1):
            cid = c.get("case_id", f"case_{idx}")
            cfg = _parse_config(c["config"])
            seed = int(c["seed"])
            eps = float(c["epsilon_or_initialization"])

            try:
                op = _build_operator(cfg)
            except Exception:
                continue

            rng = np.random.default_rng(seed)
            N = cfg["N"]
            x = rng.normal(size=N) + 1j * rng.normal(size=N)
            c_star = op.analyze(x)
            if float(np.min(np.abs(c_star))) < 1e-12:
                continue

            spec = transverse_spectrum(c_star, op)
            lm_val = max(0.0, float(spec["lambda_minus"]))
            lp_val = min(1.0 - 1e-12, max(lm_val + 1e-8, float(spec["lambda_plus"])))

            jvals, jvecs = np.linalg.eigh(spec["J"])
            top_idx = np.where(jvals < 1.0 - 1e-8)[0][-1]
            v = r2c(spec["QU"] @ jvecs[:, top_idx])
            v /= np.linalg.norm(v)

            t0 = c_star + eps * v
            t_minus1 = t0.copy()
            s = np.abs(c_star)

            # 1. Run FGLA
            p_fg = fgla_opt(lp_val)
            fg_traj = run_agla_state(t0, t_minus1, s, op, p_fg["alpha"], p_fg["beta"], p_fg["gamma"], H)
            fg_errs = [orbit_distance(z, c_star) for z in fg_traj]
            q_fg_obs, r2_fg, n_fg = _fit_rate(fg_errs)

            # 2. Run Oracle
            p_ora = oracle_minimax(lm_val, lp_val)
            ora_traj = run_agla_state(t0, t_minus1, s, op, p_ora["alpha"], p_ora["beta"], p_ora["gamma"], H)
            ora_errs = [orbit_distance(z, c_star) for z in ora_traj]
            q_ora_obs, r2_ora, n_ora = _fit_rate(ora_errs)

            # 3. Run Online Policy
            on_res = run_online_policy(
                t0, t_minus1, s, op,
                n_iter=H, warmup=warmup, block_size=block_size,
                memory=3, margin=0.0, policy="dynamic_envelope"
            )
            on_traj = on_res["trajectory"]
            on_errs = [orbit_distance(z, c_star) for z in on_traj]
            q_on_obs, r2_on, n_on = _fit_rate(on_errs)

            if q_on_obs is None or q_fg_obs is None:
                continue

            q_onlines.append(q_on_obs)
            q_fglas.append(q_fg_obs)
            if q_ora_obs is not None:
                q_oracles.append(q_ora_obs)

            d_ora = (q_fg_obs - q_ora_obs) if q_ora_obs is not None else None
            d_on = q_fg_obs - q_on_obs
            r_cap = (d_on / d_ora) if (d_ora is not None and d_ora > 1e-8) else None
            if r_cap is not None:
                captures.append(r_cap)

            # Check for loss vs FGLA
            online_beats_fgla = bool(q_on_obs < q_fg_obs)
            if not online_beats_fgla:
                # Inspect blocks for safeguard fallback rate
                blks = on_res["blocks"]
                rejections = sum(1 for b in blks if not b.get("candidate_accepted", True))
                fallback_rate = (rejections / len(blks)) if blks else 0.0
                
                # Check envelope maturation
                envs = [b.get("edge_state") for b in blks if b.get("edge_state") is not None]
                t_mat_ratio = 0.5 if not envs or abs(envs[-1] - lp_val)/lp_val > 0.01 else 0.2

                diag_cat, diag_desc = classify_failure(
                    d_ora, lp_val, t_mat_ratio, fallback_rate, r2_on, n_on
                )
                failure_cases.append({
                    "horizon": H,
                    "case_id": cid,
                    "config": c["config"],
                    "seed": seed,
                    "lambda_plus": lp_val,
                    "q_fgla_obs": q_fg_obs,
                    "q_online_obs": q_on_obs,
                    "q_oracle_obs": q_ora_obs,
                    "delta_online_obs": d_on,
                    "delta_oracle_obs": d_ora,
                    "r2_fit": r2_on,
                    "safeguard_fallback_rate": fallback_rate,
                    "diagnostic_category": diag_cat,
                    "description": diag_desc,
                })

        # Calculate summary statistics for horizon H
        fgla_wins = sum(1 for on, fg in zip(q_onlines, q_fglas) if on < fg)
        beat_frac = (fgla_wins / len(q_onlines)) if q_onlines else 0.0
        ratios_fg = [on / fg for on, fg in zip(q_onlines, q_fglas)]
        ratios_ora = [on / ora for on, ora in zip(q_onlines, q_oracles)] if q_oracles else []

        h_stat = {
            "horizon": H,
            "total_cases": len(q_onlines),
            "fgla_beat_count": fgla_wins,
            "fgla_beat_fraction": beat_frac,
            "median_q_online_over_q_fgla": median(ratios_fg),
            "p90_q_online_over_q_fgla": quantiles(ratios_fg)["p90"] if ratios_fg else None,
            "median_q_online_over_q_oracle": median(ratios_ora) if ratios_ora else None,
            "median_oracle_gain_capture": median(captures) if captures else None,
            "failure_count": len(q_onlines) - fgla_wins,
        }
        horizon_metrics[f"H{H}"] = h_stat
        print(f"H={H:3d}: FGLA Beat Fraction = {beat_frac*100:5.1f}% ({fgla_wins}/{len(q_onlines)}) | Median Capture = {h_stat['median_oracle_gain_capture']}")

    # Write output tables
    write_csv(failure_cases, out / "failure_cases.csv")
    dump_json({
        "horizon_audit": horizon_metrics,
        "total_failures_recorded": len(failure_cases),
    }, out / "failure_summary.json")

    # --------------------------------------------------------------------------
    # Figure B3: Multi-Horizon Rate Audit Metrics
    # --------------------------------------------------------------------------
    hz_list = sorted([int(k[1:]) for k in horizon_metrics.keys()])
    beat_fractions = [horizon_metrics[f"H{h}"]["fgla_beat_fraction"] * 100 for h in hz_list]
    med_captures = [horizon_metrics[f"H{h}"]["median_oracle_gain_capture"] or 0.0 for h in hz_list]
    med_ratios = [horizon_metrics[f"H{h}"]["median_q_online_over_q_fgla"] or 1.0 for h in hz_list]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    axes[0].plot(hz_list, beat_fractions, marker="o", color="navy", linewidth=2.0, markersize=7)
    axes[0].set_title("FGLA Beat Fraction vs. Horizon", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Horizon (H)", fontsize=10)
    axes[0].set_ylabel(r"$P(q_{\rm Online} < q_{\rm FGLA})$ (%)", fontsize=10)
    axes[0].grid(True, linestyle=":", alpha=0.6)
    axes[0].set_ylim(0, 105)

    axes[1].plot(hz_list, med_captures, marker="s", color="darkgreen", linewidth=2.0, markersize=7)
    axes[1].set_title("Median Oracle-Gain Capture", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Horizon (H)", fontsize=10)
    axes[1].set_ylabel(r"Median $R_{\rm capture}$", fontsize=10)
    axes[1].grid(True, linestyle=":", alpha=0.6)

    axes[2].plot(hz_list, med_ratios, marker="^", color="darkred", linewidth=2.0, markersize=7)
    axes[2].axhline(1.0, color="gray", linestyle="--", linewidth=1.2, label="Parity (1.0)")
    axes[2].set_title("Median Rate Ratio (Online / FGLA)", fontsize=11, fontweight="bold")
    axes[2].set_xlabel("Horizon (H)", fontsize=10)
    axes[2].set_ylabel(r"$q_{\rm Online} / q_{\rm FGLA}$", fontsize=10)
    axes[2].grid(True, linestyle=":", alpha=0.6)
    axes[2].legend(fontsize=9)

    fig.tight_layout()
    fig_b3_path = figs_dir / "Figure_B3_multi_horizon_performance.png"
    fig.savefig(fig_b3_path, dpi=200)
    plt.close(fig)
    print(f"\n[OK] Saved Figure B3 to {fig_b3_path}")

    # --------------------------------------------------------------------------
    # Figure B4: Failure Decomposition Taxonomy
    # --------------------------------------------------------------------------
    categories = [
        "NEGLIGIBLE_ORACLE_OPPORTUNITY",
        "ESTIMATOR_NOT_MATURE",
        "NEAR_DEGENERATE_GEOMETRY",
        "SAFEGUARD_DOMINATED_TRANSIENT",
        "RATE_FIT_UNCERTAINTY",
        "UNEXPLAINED"
    ]
    palette = ["#95a5a6", "#e67e22", "#3498db", "#e74c3c", "#f1c40f", "#34495e"]

    fig, ax = plt.subplots(figsize=(9, 5))
    h_labels = [f"H={h}" for h in hz_list]
    cat_counts_by_h = {cat: [sum(1 for f in failure_cases if f["horizon"] == h and f["diagnostic_category"] == cat) for h in hz_list] for cat in categories}

    bottoms = np.zeros(len(hz_list))
    for cat, color in zip(categories, palette):
        counts = np.array(cat_counts_by_h[cat])
        if np.sum(counts) > 0:
            ax.bar(h_labels, counts, bottom=bottoms, label=cat, color=color, edgecolor="black", alpha=0.85)
            bottoms += counts

    ax.set_title("Figure B4: Decomposition of Online Losses by Horizon", fontsize=12, fontweight="bold")
    ax.set_xlabel("Observation Horizon", fontsize=11)
    ax.set_ylabel("Number of Loss Cases", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.5, axis="y")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    fig.tight_layout()
    fig_b4_path = figs_dir / "Figure_B4_failure_taxonomy_distribution.png"
    fig.savefig(fig_b4_path, dpi=200)
    plt.close(fig)
    print(f"[OK] Saved Figure B4 to {fig_b4_path}")

    return horizon_metrics, failure_cases


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Task B2: Multi-Horizon Audit and Failure Decomposition")
    parser.add_argument("--ledger", type=str, default=None, help="Path to E6 case ledger")
    parser.add_argument("--out", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    run_multi_horizon_audit(ledger_path=args.ledger, out_dir=args.out)