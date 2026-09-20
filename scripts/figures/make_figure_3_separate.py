"""Script to generate the 3 separate plots of Figure 3 at 400 DPI.

This script creates 3 standalone subfigures (both PNG at 400 DPI and PDF)
corresponding to the 3 panels of Figure 3:
  - Figure 3(a): Low Opportunity
  - Figure 3(b): Medium Opportunity
  - Figure 3(c): High Opportunity

Outputs are saved into:
  ICLR2027_Figure_Scripts/figure_3/
"""
from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# -----------------------------------------------------------------------------
# Directory paths
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT_DIR / "results" / "figures" / "publication_m4"

# -----------------------------------------------------------------------------
# Case configurations for the 3 subplots
# -----------------------------------------------------------------------------
CASES = [
    {
        "id": "3a",
        "regime": "Low",
        "cid": "g24_w8_h4_f8__s2__e0.001",
        "trace_file": "g24_w8_h4_f8__s2__e0.001_trace.csv",
        "lp": 0.9999802815490957,
        "delta_oracle": 0.001231,
        "t1pct": 12,
        "t05pct": 12,
    },
    {
        "id": "3b",
        "regime": "Medium",
        "cid": "h24_w8_h4_f8__s0__e1e-05",
        "trace_file": "h24_w8_h4_f8__s0__e1e-05_trace.csv",
        "lp": 0.9997290021630232,
        "delta_oracle": 0.006239,
        "t1pct": 12,
        "t05pct": 12,
    },
    {
        "id": "3c",
        "regime": "High",
        "cid": "g32_w16_h4_f16__s1__e0.001",
        "trace_file": "g32_w16_h4_f16__s1__e0.001_trace.csv",
        "lp": 0.991704965416071,
        "delta_oracle": 0.032287,
        "t1pct": 12,
        "t05pct": 12,
    },
]

# Candidate search directories for the trace CSV files
TRACE_SEARCH_DIRS = [
    OUT_DIR / "traces",
    BASE_DIR / "traces",
    ROOT_DIR / "results" / "06_multi_horizon_online_adaptation" / "traces",
    ROOT_DIR / "results" / "traces",
]


def find_trace(fname: str) -> Path | None:
    for d in TRACE_SEARCH_DIRS:
        cand = d / fname
        if cand.exists():
            return cand
    return None


def plot_single_panel(case: dict, trace_path: Path, dpi: int = 400):
    df = pd.read_csv(trace_path)
    iters = df["iteration"].to_numpy()
    raws = df["lambda_hat_raw"].to_numpy()
    envs = df["lambda_hat_envelope"].to_numpy()

    fig, ax = plt.subplots(figsize=(5.6, 4.2))

    # Reference Oracle line
    ax.axhline(
        case["lp"],
        color="crimson",
        linestyle="--",
        linewidth=1.6,
        label=r"Oracle $\lambda_+$",
    )
    # Raw passive Ritz eigenvalues
    ax.plot(
        iters,
        raws,
        color="deepskyblue",
        alpha=0.65,
        linestyle=":",
        marker=".",
        markersize=3.5,
        label=r"Raw Ritz $\hat{\lambda}$",
    )
    # Dynamic monotone envelope
    ax.plot(
        iters,
        envs,
        color="navy",
        linewidth=2.2,
        label=r"Dynamic Envelope $\lambda_{\rm env}$",
    )

    # Maturation vertical threshold lines
    if case["t1pct"] is not None:
        ax.axvline(
            case["t1pct"],
            color="darkgreen",
            linestyle="-.",
            alpha=0.75,
            linewidth=1.3,
            label=f"$T_{{1\\%}}$ ({case['t1pct']})",
        )
    if case["t05pct"] is not None:
        ax.axvline(
            case["t05pct"],
            color="purple",
            linestyle="--",
            alpha=0.75,
            linewidth=1.3,
            label=f"$T_{{0.5\\%}}$ ({case['t05pct']})",
        )

    ax.set_title(
        rf"{case['regime']} Opportunity ($\Delta = {case['delta_oracle']:.4f}$)" + f"\n[{case['cid']}]",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlabel("Iteration", fontsize=10)
    ax.set_ylabel(r"Spectral Edge Estimate $\hat{\lambda}_+$", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)

    fig.tight_layout()

    out_name = f"Figure_{case['id']}_{case['regime'].lower()}_opportunity"
    fig.savefig(OUT_DIR / f"{out_name}.png", dpi=dpi, bbox_inches="tight")
    fig.savefig(OUT_DIR / f"{out_name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Generated {out_name}.png (DPI={dpi}) and .pdf")


def crop_existing_figure_3(dpi: int = 400):
    candidates = [
        BASE_DIR / "publication_figures" / "Figure_3_estimator_maturation.png",
        BASE_DIR / "Online Evaluator_Final_Freeze_Candidate_v1" / "figures" / "Figure_B1_estimator_maturation_traces.png",
    ]
    src_img = next((p for p in candidates if p.exists()), None)
    if src_img is None:
        print("[INFO] Composite Figure 3 image not found for cropping.")
        return

    with Image.open(src_img) as im:
        w, h = im.size
        col_w = w / 3.0
        crops = [
            ("3a_low", 0, 0, int(col_w), h),
            ("3b_medium", int(col_w), 0, int(2 * col_w), h),
            ("3c_high", int(2 * col_w), 0, w, h),
        ]
        for name, left, top, right, bottom in crops:
            panel = im.crop((left, top, right, bottom))
            png_out = OUT_DIR / f"Figure_{name}_cropped.png"
            pdf_out = OUT_DIR / f"Figure_{name}_cropped.pdf"
            panel.save(png_out, dpi=(dpi, dpi))
            panel.convert("RGB").save(pdf_out, "PDF", resolution=float(dpi))
            print(f"[OK] Cropped {png_out.name} (DPI={dpi}) and .pdf")


def main():
    print("=" * 65)
    print(f"Generating 3 Separate Subfigures for Figure 3 (DPI = 400)")
    print(f"Output folder: {OUT_DIR.resolve()}")
    print("=" * 65)

    # 1. Generate crisp vector & 400 DPI plots from underlying trace data
    for case in CASES:
        trace_path = find_trace(case["trace_file"])
        if trace_path is not None:
            plot_single_panel(case, trace_path, dpi=400)
        else:
            print(f"[WARNING] Trace file {case['trace_file']} not found.")

    # 2. Also generate precision cropped versions directly from composite image
    print("\n--- Generating precision cropped panels from composite Figure 3 ---")
    crop_existing_figure_3(dpi=400)

    print("\n[SUCCESS] All 3 separate figures have been created in:")
    print(f"  {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
