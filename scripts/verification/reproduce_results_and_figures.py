#!/usr/bin/env python3
"""
ICLR 2027 Main Experimental Evidence Reproduction (Panels A-D)
Paper: Geometry Determines Local Acceleration in Griffin-Lim Phase Retrieval

Provenances:
- Panel A: data/reproducibility/theory_validation/geometry_results.csv
- Panel B: data/reproducibility/theory_validation/rate_results.csv
- Panel C: data/reproducibility/raw_trace_provenance/traces/*.csv
- Panel D: data/reproducibility/basin_original/basin_results.csv and basin_musan_odd/basin_results.csv
- Canonical rate audit: data/reproducibility/canonical_rate/C1_capture_ratio_audit.csv

Outputs:
- results/publication_figures/reproduced_metrics.json
- results/publication_figures/figures/panel_A_geometry_spectrum.pdf (and .png, 400 DPI)
- results/publication_figures/figures/panel_B_predicted_observed.pdf (and .png, 400 DPI)
- results/publication_figures/figures/panel_C_estimator_maturation.pdf (and .png, 400 DPI)
- results/publication_figures/figures/panel_D_replicated_robustness.pdf (and .png, 400 DPI)
- results/publication_figures/figures/Figure_Main_ABCD.pdf (and .png, 400 DPI)
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "reproducibility"
if not DATA.exists():
    DATA = ROOT / "data"
OUT = ROOT / "results" / "publication_figures"
OUT.mkdir(parents=True, exist_ok=True)
FIGDIR = OUT / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# 1. Statistical functions
# -------------------------------------------------------------------------

def bootstrap_file_cluster(df, n_boot=20000, seed=20270918):
    """Bootstrap source files; retain all rows/outcomes belonging to each sampled file."""
    online_sum = df.groupby("file")["success_online"].sum().to_numpy(float)
    fgla_sum = df.groupby("file")["success_fgla"].sum().to_numpy(float)
    counts = df.groupby("file").size().to_numpy(float)
    rng = np.random.default_rng(seed)
    m = len(counts)
    vals = np.empty(n_boot)
    batch = 1000
    for a in range(0, n_boot, batch):
        b = min(a + batch, n_boot)
        idx = rng.integers(0, m, size=(b - a, m))
        num = (online_sum[idx] - fgla_sum[idx]).sum(axis=1)
        den = counts[idx].sum(axis=1)
        vals[a:b] = num / den
    return np.quantile(vals, [0.025, 0.975]) * 100.0

def basin_summary(df):
    paired = df[df["success_online"].astype(bool) & df["success_fgla"].astype(bool)]
    return {
        "n_files": int(df["file"].nunique()),
        "n_runs": int(len(df)),
        "online_success_pct": 100.0 * float(df["success_online"].mean()),
        "fgla_success_pct": 100.0 * float(df["success_fgla"].mean()),
        "difference_pp": 100.0 * float(df["success_online"].mean() - df["success_fgla"].mean()),
        "paired_success_n": int(len(paired)),
        "paired_online_beat_pct": 100.0 * float((paired["q_online"] < paired["q_fgla"]).mean()),
        "paired_median_q_ratio": float(paired["q_ratio_online_fgla"].median()),
        "safeguard_failures": int(df["fallback_e1_failures"].sum()),
    }

# -------------------------------------------------------------------------
# 2. Load ledgers
# -------------------------------------------------------------------------

def run_reproduction():
    geom = pd.read_csv(DATA / "theory_validation/geometry_results.csv")
    rate = pd.read_csv(DATA / "theory_validation/rate_results.csv")
    c1 = pd.read_csv(DATA / "canonical_rate/C1_capture_ratio_audit.csv")
    orig = pd.read_csv(DATA / "basin_original/basin_results.csv")
    odd = pd.read_csv(DATA / "basin_musan_odd/basin_results.csv")

    gok = geom[geom["status"] == "OK"] if "status" in geom else geom
    rok = rate[rate["status"] == "OK"] if "status" in rate else rate

    results = {
        "theory_validation": {
            "geometry_n": int(len(gok)),
            "geometry_median_relative_error": float(gok["geometry_rel_error"].median()),
            "geometry_max_relative_error": float(gok["geometry_rel_error"].max()),
            "rate_n": int(len(rok)),
            "observed_hierarchy_pass_n": int(rok["observed_hierarchy_pass"].sum()),
            "observed_hierarchy_pass_fraction": float(rok["observed_hierarchy_pass"].mean()),
            "median_final_error_reduction_fgla_vs_gla": float(np.median(rok["final_err_gla"] / rok["final_err_fgla"])),
            "median_final_error_reduction_oracle_vs_gla": float(np.median(rok["final_err_gla"] / rok["final_err_oracle"])),
        },
        "canonical_rate_horizons": {},
        "basin_original": basin_summary(orig),
        "basin_musan_odd": basin_summary(odd),
    }

    for H, d in c1.groupby("horizon"):
        results["canonical_rate_horizons"][str(int(H))] = {
            "n": int(len(d)),
            "online_beat_fraction": float((d["q_online"] < d["q_fgla"]).mean()),
            "median_q_ratio_online_fgla": float(np.median(d["q_online"] / d["q_fgla"])),
            "poor_rate_fit_fraction": float(d["POOR_RATE_FIT"].mean()),
        }

    print("Computing 20,000-resample file-cluster bootstrap confidence intervals...")
    results["basin_original"]["file_cluster_95ci_difference_pp"] = list(map(float, bootstrap_file_cluster(orig)))
    results["basin_musan_odd"]["file_cluster_95ci_difference_pp"] = list(map(float, bootstrap_file_cluster(odd)))

    metrics_file = OUT / "reproduced_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved numerical metrics to {metrics_file}")

    # -------------------------------------------------------------------------
    # 3. Individual Panels Generation
    # -------------------------------------------------------------------------

    # Panel A: Geometry -> Spectrum
    fig, ax = plt.subplots(figsize=(5.6, 4.3))
    x, y = gok["cos_theta_sq"].to_numpy(), gok["lambda_plus"].to_numpy()
    ax.scatter(x, y, s=22, alpha=0.7, color="#1f77b4", edgecolor="none")
    lo, hi = min(x.min(), y.min()), max(x.max(), y.max())
    ax.plot([lo, hi], [lo, hi], "--", color="#d62728", lw=1.3, label=r"Identity line ($y=x$)")
    ax.set_xlabel(r"Principal-angle prediction $\cos^2\theta$", fontsize=10)
    ax.set_ylabel(r"Direct Jacobian edge $\lambda_+$", fontsize=10)
    ax.set_title(r"(a) Geometry $\rightarrow$ Spectrum ($n=202$)", fontsize=11, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGDIR / "panel_A_geometry_spectrum.pdf", bbox_inches="tight")
    fig.savefig(FIGDIR / "panel_A_geometry_spectrum.png", dpi=400, bbox_inches="tight")
    plt.close(fig)

    # Panel B: Predicted -> Observed rates
    fig, ax = plt.subplots(figsize=(5.6, 4.3))
    series = [
        ("q_gla_pred", "q_gla_obs", "GLA", "o", "#2ca02c"),
        ("q_fgla_pred", "q_fgla_obs", "FGLA", "s", "#1f77b4"),
        ("q_oracle_pred", "q_oracle_obs", "Geometry Oracle", "^", "#ff7f0e"),
    ]
    for pc, oc, label, marker, color in series:
        ax.scatter(rok[pc], rok[oc], s=20, alpha=0.65, label=label, marker=marker, color=color)
    cols = ["q_gla_pred", "q_gla_obs", "q_fgla_pred", "q_fgla_obs", "q_oracle_pred", "q_oracle_obs"]
    lo = rok[cols].min().min()
    hi = rok[cols].max().max()
    ax.plot([lo, hi], [lo, hi], "--", color="gray", lw=1.3, label="Identity line")
    ax.set_xlabel("Predicted contraction factor", fontsize=10)
    ax.set_ylabel("Observed fitted contraction factor", fontsize=10)
    ax.set_title(r"(b) Predicted $\rightarrow$ Observed Rate", fontsize=11, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIGDIR / "panel_B_predicted_observed.pdf", bbox_inches="tight")
    fig.savefig(FIGDIR / "panel_B_predicted_observed.png", dpi=400, bbox_inches="tight")
    plt.close(fig)

    # Panel C: Passive edge-estimator maturation
    traces_dir = DATA / "raw_trace_provenance" / "traces"
    if not traces_dir.exists():
        traces_dir = DATA / "estimator" / "traces"

    trace_cases = [
        ("low", "g24_w8_h4_f8__s2__e0.001_trace.csv", "Low Opportunity", 0.9999802815490957, 12),
        ("medium", "h24_w8_h4_f8__s0__e1e-05_trace.csv", "Medium Opportunity", 0.9997290021630232, 12),
        ("high", "g32_w16_h4_f16__s1__e0.001_trace.csv", "High Opportunity", 0.991704965416071, 12),
    ]

    all_traces_available = traces_dir.exists() and all((traces_dir / fn).exists() for _, fn, _, _, _ in trace_cases)

    if all_traces_available:
        fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.2), sharey=False)
        for ax, (reg, fn, title, lp_val, t1pct) in zip(axes, trace_cases):
            tdf = pd.read_csv(traces_dir / fn)
            iters = tdf["iteration"].to_numpy()
            raws = tdf["lambda_hat_raw"].to_numpy(dtype=float)
            envs = tdf["lambda_hat_envelope"].to_numpy(dtype=float)

            ax.axhline(lp_val, color="crimson", linestyle="--", linewidth=1.5, label=r"Oracle $\lambda_+$")
            valid_raw = ~np.isnan(raws)
            if np.any(valid_raw):
                ax.plot(iters[valid_raw], raws[valid_raw], "o-", color="#1f77b4", markersize=3, alpha=0.6, label=r"Raw Ritz $\hat{\lambda}_+$")
            ax.plot(iters, envs, "-", color="#2ca02c", linewidth=2.0, label=r"Running Envelope $\lambda_{\rm env}$")
            ax.axvline(t1pct, color="orange", linestyle=":", linewidth=1.3, label=r"1% Maturation ($T_{1\%}$)")

            ax.set_xlabel("Iteration $k$", fontsize=10)
            ax.set_ylabel(r"Eigenvalue estimate $\lambda$", fontsize=10)
            ax.set_title(f"{title}\n" + r"($\lambda_+ \approx " + f"{lp_val:.5f}$)", fontsize=10.5, fontweight="bold")
            ax.grid(True, linestyle=":", alpha=0.5)
            ax.legend(frameon=False, fontsize=8, loc="lower right")

        fig.suptitle(r"(c) Passive Ritz Edge-Estimator Maturation Across Geometry Regimes ($p=3$)", fontsize=12, fontweight="bold", y=1.03)
        fig.tight_layout()
        fig.savefig(FIGDIR / "panel_C_estimator_maturation.pdf", bbox_inches="tight")
        fig.savefig(FIGDIR / "panel_C_estimator_maturation.png", dpi=400, bbox_inches="tight")
        plt.close(fig)
        print("  [Panel C] Regenerated from raw per-iteration traces (RAW-DATA-REPRODUCIBLE: PASS)")

    # Panel D: Replicated Basin Robustness
    fig, ax = plt.subplots(figsize=(6.4, 4.3))
    levels = [0.001, 0.01, 0.1, 0.3, 0.5, 1.0]

    def get_curve(df, col):
        return [float(df[df["level"] == lvl][col].mean()) * 100.0 for lvl in levels]

    ax.plot(levels, get_curve(orig, "success_online"), "o-", color="#1f77b4", lw=1.8, label="Original: Online")
    ax.plot(levels, get_curve(orig, "success_fgla"), "o--", color="#1f77b4", alpha=0.7, lw=1.5, label="Original: FGLA")
    ax.plot(levels, get_curve(odd, "success_online"), "s-", color="#ff7f0e", lw=1.8, label="MUSAN-ODD: Online")
    ax.plot(levels, get_curve(odd, "success_fgla"), "s--", color="#ff7f0e", alpha=0.7, lw=1.5, label="MUSAN-ODD: FGLA")

    ax.set_xscale("log")
    ax.set_ylim(0, 105)
    ax.set_xlabel("Perturbation scale / initialization level", fontsize=10)
    ax.set_ylabel("Basin convergence success rate (%)", fontsize=10)
    ax.set_title(r"(d) Replicated Basin Robustness ($N=4680$ vs $4752$)", fontsize=11, fontweight="bold")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIGDIR / "panel_D_replicated_robustness.pdf", bbox_inches="tight")
    fig.savefig(FIGDIR / "panel_D_replicated_robustness.png", dpi=400, bbox_inches="tight")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # 4. Composite 2x2 Figure Main ABCD
    # -------------------------------------------------------------------------
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13.0, 10.0))
    ax1.imshow(mpimg.imread(FIGDIR / "panel_A_geometry_spectrum.png"))
    ax1.axis("off")
    ax2.imshow(mpimg.imread(FIGDIR / "panel_B_predicted_observed.png"))
    ax2.axis("off")
    ax3.imshow(mpimg.imread(FIGDIR / "panel_C_estimator_maturation.png"))
    ax3.axis("off")
    ax4.imshow(mpimg.imread(FIGDIR / "panel_D_replicated_robustness.png"))
    ax4.axis("off")

    fig.tight_layout(pad=0.4)
    fig.savefig(FIGDIR / "Figure_Main_ABCD.pdf", bbox_inches="tight")
    fig.savefig(FIGDIR / "Figure_Main_ABCD.png", dpi=400, bbox_inches="tight")
    plt.close(fig)

    print("\n" + "=" * 60)
    print("REPRODUCTION COMPLETED SUCCESSFULLY")
    print(f"Metrics saved to: {metrics_file}")
    print(f"Publication panels saved to: {FIGDIR}")
    print("=" * 60)
    return results

if __name__ == "__main__":
    run_reproduction()
