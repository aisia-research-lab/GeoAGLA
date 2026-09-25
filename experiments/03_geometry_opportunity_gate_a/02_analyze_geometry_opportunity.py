#!/usr/bin/env python3
"""Opportunity and Gain Capture Statistical Analysis.
Section 5 (A2, A3) of ICLR 2027 Next Experiment Handoff for Students A & B.
"""
from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import argparse
from pathlib import Path
import sys

# Ensure local scripts folder is in sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common import (
    load_json, dump_json, read_csv, fnum, median, quantile,
    bootstrap_ci, bootstrap_corr_ci
)
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "experiments" else Path(__file__).resolve().parents[1]

def analyze_opportunity(ledger_path: str | Path, out_dir: str | Path, denom_tol: float = 1e-8):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    figs_dir = out / "figures"
    figs_dir.mkdir(parents=True, exist_ok=True)

    rows = read_csv(ledger_path)
    for r in rows:
        for k in [
            "lambda_minus", "lambda_plus", "spectral_width", "transverse_gap",
            "delta_oracle_pred", "delta_oracle_obs", "delta_online_obs", "r_capture",
            "q_online_obs", "q_fgla_obs", "q_oracle_obs", "q_gla_obs"
        ]:
            r[k] = fnum(r.get(k))

    valid = [r for r in rows if r["delta_oracle_obs"] is not None and r["delta_online_obs"] is not None]
    
    # Cases where oracle headroom is above numerical denominator tolerance
    cap_cases = [r for r in valid if r["delta_oracle_obs"] > denom_tol]
    cap = [r["delta_online_obs"] / r["delta_oracle_obs"] for r in cap_cases]

    xo = [r["delta_oracle_obs"] for r in valid]
    yo = [r["delta_online_obs"] for r in valid]
    x_pred = [r["delta_oracle_pred"] for r in rows if r["delta_oracle_pred"] is not None]

    # Correlations
    def calc_corr(x, y, rank=False):
        xa = np.asarray(x, float)
        ya = np.asarray(y, float)
        if len(xa) < 2:
            return None
        if rank:
            xa = np.argsort(np.argsort(xa))
            ya = np.argsort(np.argsort(ya))
        return float(np.corrcoef(xa, ya)[0, 1])

    p_corr = calc_corr(xo, yo, rank=False)
    s_corr = calc_corr(xo, yo, rank=True)
    p_ci = bootstrap_corr_ci(xo, yo, rank=False)
    s_ci = bootstrap_corr_ci(xo, yo, rank=True)

    # Regressions on (xo, yo)
    # 1. Ordinary regression with intercept: y = slope * x + intercept
    poly_fit = np.polyfit(xo, yo, 1) if len(xo) > 2 else [0.0, 0.0]
    ordinary_slope = float(poly_fit[0])
    ordinary_intercept = float(poly_fit[1])

    # 2. Regression through origin: min sum (y - m*x)^2 => m = sum(x*y) / sum(x^2)
    denom_origin = sum(x * x for x in xo)
    origin_slope = float(sum(x * y for x, y in zip(xo, yo)) / denom_origin) if denom_origin > 0 else None

    # Opportunity quantiles & bins
    xo_q25 = quantile(xo, 0.25)
    xo_q50 = quantile(xo, 0.50)
    xo_q75 = quantile(xo, 0.75)

    n_tot = len(xo)
    opp_bins = {
        "negligible_lt_q25": sum(x <= xo_q25 for x in xo) / n_tot if n_tot else 0,
        "small_q25_to_q50": sum(xo_q25 < x <= xo_q50 for x in xo) / n_tot if n_tot else 0,
        "medium_q50_to_q75": sum(xo_q50 < x <= xo_q75 for x in xo) / n_tot if n_tot else 0,
        "large_gt_q75": sum(x > xo_q75 for x in xo) / n_tot if n_tot else 0,
        "thresholds": {"q25": xo_q25, "median": xo_q50, "q75": xo_q75}
    }

    summary = {
        "n_cases_total": len(rows),
        "n_online_valid": len(valid),
        "denom_tol": denom_tol,
        "n_capture_valid": len(cap),
        "n_capture_excluded": len(valid) - len(cap),
        "predicted_oracle_opportunity": {
            "median": median(x_pred),
            "iqr": [quantile(x_pred, 0.25), quantile(x_pred, 0.75)],
            "p10": quantile(x_pred, 0.10),
            "p90": quantile(x_pred, 0.90)
        },
        "observed_oracle_opportunity": {
            "median": median(xo),
            "iqr": [xo_q25, xo_q75],
            "p10": quantile(xo, 0.10),
            "p90": quantile(xo, 0.90),
            "bins": opp_bins
        },
        "observed_online_gain": {
            "median": median(yo),
            "iqr": [quantile(yo, 0.25), quantile(yo, 0.75)],
            "p10": quantile(yo, 0.10),
            "p90": quantile(yo, 0.90)
        },
        "oracle_gain_capture": {
            "median": median(cap),
            "iqr": [quantile(cap, 0.25), quantile(cap, 0.75)],
            "p10": quantile(cap, 0.10),
            "p90": quantile(cap, 0.90),
            "bootstrap95_median": bootstrap_ci(cap),
            "frac_gt_0": sum(v > 0 for v in cap) / len(cap) if cap else None,
            "frac_ge_0p5": sum(v >= 0.5 for v in cap) / len(cap) if cap else None,
            "frac_ge_0p8": sum(v >= 0.8 for v in cap) / len(cap) if cap else None,
            "frac_gt_1": sum(v > 1.0 for v in cap) / len(cap) if cap else None,
            "frac_lt_0": sum(v < 0 for v in cap) / len(cap) if cap else None,
        },
        "correlation": {
            "pearson": p_corr,
            "pearson_bootstrap95_ci": p_ci,
            "spearman": s_corr,
            "spearman_bootstrap95_ci": s_ci,
        },
        "regression": {
            "ordinary_slope": ordinary_slope,
            "ordinary_intercept": ordinary_intercept,
            "through_origin_slope": origin_slope
        }
    }

    dump_json(summary, out / "e6_summary.json")

    # --- PLOTS ---
    # Figure A1a: Delta_oracle vs lambda_+
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=220)
    xx = [r["lambda_plus"] for r in rows if r["lambda_plus"] is not None and r["delta_oracle_obs"] is not None]
    yy = [r["delta_oracle_obs"] for r in rows if r["lambda_plus"] is not None and r["delta_oracle_obs"] is not None]
    ax.scatter(xx, yy, s=30, color="#1f77b4", edgecolors="k", alpha=0.8)
    ax.set_xlabel(r"Upper Transverse Edge $\lambda_+$", fontsize=11)
    ax.set_ylabel(r"Observed Oracle Headroom $\Delta_{\rm oracle}^{\rm obs}$", fontsize=11)
    ax.set_title(r"Figure A1a: Oracle Opportunity vs. $\lambda_+$", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figs_dir / "A1a_oracle_vs_lambda_plus.png")
    plt.close(fig)

    # Figure A1b: Delta_oracle vs 1 - lambda_+
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=220)
    xx = [r["transverse_gap"] for r in rows if r["transverse_gap"] is not None and r["delta_oracle_obs"] is not None]
    ax.scatter(xx, yy, s=30, color="#2ca02c", edgecolors="k", alpha=0.8)
    ax.set_xlabel(r"Transverse Gap $1 - \lambda_+$", fontsize=11)
    ax.set_ylabel(r"Observed Oracle Headroom $\Delta_{\rm oracle}^{\rm obs}$", fontsize=11)
    ax.set_title(r"Figure A1b: Oracle Opportunity vs. Transverse Gap", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figs_dir / "A1b_oracle_vs_gap.png")
    plt.close(fig)

    # Figure A1c: Delta_oracle vs lambda_+ - lambda_-
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=220)
    xx = [r["spectral_width"] for r in rows if r["spectral_width"] is not None and r["delta_oracle_obs"] is not None]
    ax.scatter(xx, yy, s=30, color="#9467bd", edgecolors="k", alpha=0.8)
    ax.set_xlabel(r"Spectral Width $\lambda_+ - \lambda_-$", fontsize=11)
    ax.set_ylabel(r"Observed Oracle Headroom $\Delta_{\rm oracle}^{\rm obs}$", fontsize=11)
    ax.set_title(r"Figure A1c: Oracle Opportunity vs. Spectral Width", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figs_dir / "A1c_oracle_vs_width.png")
    plt.close(fig)

    # Figure A2: Central Experimental Figure — Online Gain vs Available Oracle Gain
    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=220)
    wins = [r for r in valid if (r["delta_online_obs"] or 0) >= 0]
    losses = [r for r in valid if (r["delta_online_obs"] or 0) < 0]

    ax.scatter([r["delta_oracle_obs"] for r in wins], [r["delta_online_obs"] for r in wins],
               s=35, color="#1f77b4", edgecolors="k", label=f"Online Win/Tied (N={len(wins)})", alpha=0.85, zorder=3)
    if losses:
        ax.scatter([r["delta_oracle_obs"] for r in losses], [r["delta_online_obs"] for r in losses],
                   s=45, color="#d62728", marker="x", linewidths=1.8, label=f"Online Loss (N={len(losses)})", zorder=4)

    all_vals = xo + yo
    lo = min(min(all_vals), 0.0) * 1.05
    hi = max(max(all_vals), 0.01) * 1.05
    
    # Identity line y = x and zero-gain line y = 0
    ax.plot([lo, hi], [lo, hi], "k--", lw=1.2, alpha=0.75, label="Identity line $y = x$ (100% capture)")
    ax.axhline(0, color="gray", lw=1.0, linestyle=":", label="Zero gain $y = 0$ (FGLA baseline)")

    # Regression lines
    x_grid = np.linspace(min(xo), max(xo), 100)
    if origin_slope is not None:
        ax.plot(x_grid, origin_slope * x_grid, color="darkorange", lw=1.5,
                label=f"Origin slope = {origin_slope:.2f}")
    
    ax.set_xlabel(r"Available Oracle Gain $\Delta_{\rm oracle}^{\rm obs} = q_{\rm FGLA}^{\rm obs} - q_{\rm Oracle}^{\rm obs}$", fontsize=10)
    ax.set_ylabel(r"Realized Online Gain $\Delta_{\rm online}^{\rm obs} = q_{\rm FGLA}^{\rm obs} - q_{\rm Online}^{\rm obs}$", fontsize=10)
    ax.set_title("Figure A2: Online Gain vs. Available Oracle Gain", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8.5, loc="upper left", frameon=True)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figs_dir / "A2_online_vs_oracle_gain.png")
    plt.close(fig)

    # Figure A3: Raw R_capture vs Delta_oracle^obs
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=220)
    xc = [r["delta_oracle_obs"] for r in cap_cases]
    yc = [r["r_capture"] for r in cap_cases]
    ax.scatter(xc, yc, s=30, color="#ff7f0e", edgecolors="k", alpha=0.85)
    ax.axhline(1.0, color="k", linestyle="--", lw=1.0, label="100% capture")
    ax.axhline(0.5, color="purple", linestyle=":", lw=1.0, label="50% capture")
    ax.axhline(0.0, color="gray", linestyle="-", lw=0.8)
    ax.set_xlabel(r"Available Oracle Gain $\Delta_{\rm oracle}^{\rm obs}$", fontsize=11)
    ax.set_ylabel(r"Raw Capture Ratio $R_{\rm capture}$", fontsize=11)
    ax.set_title("Figure A3: Gain Capture Ratio vs. Oracle Headroom", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figs_dir / "A3_gain_capture_vs_oracle.png")
    plt.close(fig)

    print(f"[OK] Statistical Opportunity Analysis complete. Summary: {out / 'e6_summary.json'}")
    return summary

def main():
    p = argparse.ArgumentParser(description="Analyze E6 geometry opportunity and online gain capture")
    p.add_argument("--ledger", default=str(ROOT / "results" / "e6_geometry_opportunity" / "e6_case_ledger.csv"))
    p.add_argument("--out", default=str(ROOT / "results" / "e6_geometry_opportunity"))
    p.add_argument("--denom-tol", type=float, default=1e-8)
    args = p.parse_args()

    analyze_opportunity(args.ledger, args.out, args.denom_tol)

if __name__ == "__main__":
    main()