#!/usr/bin/env python3
"""
05_run_phase2b_checkpointed.py
==============================
Phase-2B Real-Audio Basin Transfer runner with checkpoint and resume mechanism
per independent audio batch.

Purpose:
- Chunks audio files into small batches (default: 2 files/batch).
- Each batch writes results to `_batch_NN/` immediately upon completion.
- Automatically skips completed batches with `summary.json`, supporting seamless resumption
  upon interruption (e.g. Kaggle/Colab 12h timeout, power loss).
- Supports `--time-budget-sec`: safely stops before deadline to guarantee clean exit (exit 0)
  and preserve results.
- Automatically merges all batches into summary, manifest, CSV, and figures
  using standard Phase-2B formulas.

Usage:
    # Run 4 files, 2 files/batch:
    python experiments/05_real_audio_basin_transfer/05_run_phase2b_checkpointed.py \\
        --audio-dir data/audio_samples --max-files 4 --batch-size 2 \\
        --out results/05_real_audio_basin_transfer/checkpointed_run

    # Run on cloud with 10-hour time budget:
    python experiments/05_real_audio_basin_transfer/05_run_phase2b_checkpointed.py \\
        --audio-dir /path/to/musan_subset --batch-size 2 --time-budget-sec 36000 \\
        --out results/phase2b_checkpointed
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_repo_root / "src") not in sys.path:
    sys.path.insert(0, str(_repo_root / "src"))

# Import run from sibling sweep module
import importlib.util
_sweep_path = Path(__file__).resolve().parent / "03_phase2b_real_audio_basin_sweep.py"
_spec = importlib.util.spec_from_file_location("phase2b_sweep", _sweep_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
run_phase2b_batch = _mod.run


def discover_wav_files(audio_dir: Path | str, max_files: Optional[int] = None) -> List[Path]:
    """Discover and sort .wav files deterministically."""
    paths = sorted(
        p for p in Path(audio_dir).rglob("*")
        if p.is_file() and p.suffix.lower() == ".wav"
    )
    if max_files is not None:
        paths = paths[: int(max_files)]
    return paths


def chunk(paths: List[Path], batch_size: int) -> List[List[Path]]:
    """Chunk file list into batches."""
    return [paths[i:i + batch_size] for i in range(0, len(paths), batch_size)]


def run_batches(
    paths: List[Path],
    config_path: str,
    out_root: Path,
    batch_size: int,
    deadline: Optional[float] = None,
) -> Tuple[List[Path], bool]:
    """
    Run each batch through the underlying sweep runner.
    Supports skipping completed batches and deadline enforcement.
    """
    batches = chunk(paths, batch_size)
    batch_out_dirs: List[Path] = []
    stopped_early = False

    for i, batch_files in enumerate(batches):
        batch_out = out_root / f"_batch_{i:02d}"
        marker = batch_out / "summary.json"

        # Skip if batch already completed
        if marker.exists():
            batch_out_dirs.append(batch_out)
            print(f"[batch {i+1}/{len(batches)}] Already completed in previous session — skipping ({marker}).", flush=True)
            continue

        # Check deadline budget
        if deadline is not None and time.time() >= deadline:
            remaining = len(batches) - i
            print(f"\n!!! TIME BUDGET EXCEEDED — safely stopping before batch {i+1}/{len(batches)}.")
            print(f"!!! Remaining: {remaining} batches — will resume in next session.", flush=True)
            stopped_early = True
            break

        # Prepare batch audio directory
        batch_audio_dir = out_root / f"_audio_batch_{i:02d}"
        if batch_audio_dir.exists():
            shutil.rmtree(batch_audio_dir)
        batch_audio_dir.mkdir(parents=True, exist_ok=True)
        for f in batch_files:
            shutil.copy2(f, batch_audio_dir / f.name)

        names = ", ".join(f.name for f in batch_files)
        print(f"[batch {i+1}/{len(batches)}] Running ({names}) ...", flush=True)
        t0 = time.time()
        run_phase2b_batch(
            str(batch_audio_dir),
            config_path,
            str(batch_out),
            max_files=len(batch_files),
        )
        print(f"[batch {i+1}/{len(batches)}] Done in {time.time()-t0:.1f}s. Wrote: {marker}", flush=True)
        batch_out_dirs.append(batch_out)

    return batch_out_dirs, stopped_early


def _load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def merge(batch_out_dirs: List[Path], config_path: str, out_root: Path):
    """
    Merge results across all completed batches.
    Preserves standard Phase-2B gating, metrics, and figure generation.
    """
    C = json.loads(Path(config_path).read_text(encoding="utf-8"))
    manifest, geometry, basin = [], [], []

    for bd in batch_out_dirs:
        manifest.extend(_load(bd / "audio_manifest.json", []))
        geometry.extend(_load(bd / "geometry_results.json", []))
        basin.extend(_load(bd / "basin_results.json", []))

    out = out_root
    (out / "figures").mkdir(parents=True, exist_ok=True)
    (out / "audio_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "geometry_results.json").write_text(json.dumps(geometry, indent=2, allow_nan=True), encoding="utf-8")
    (out / "basin_results.json").write_text(json.dumps(basin, indent=2, allow_nan=True), encoding="utf-8")

    for name, rows in [("geometry_results.csv", geometry), ("basin_results.csv", basin)]:
        if rows:
            with (out / name).open("w", newline="", encoding="utf-8") as f:
                fields = sorted(set().union(*(r.keys() for r in rows)))
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                w.writerows(rows)

    gok = [r for r in geometry if r.get("status") == "OK"]
    if not gok:
        summary = {
            "phase2b_gate": "RED",
            "reason": "no regular real-audio geometry cases",
            "n_files": len(manifest),
        }
        (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return summary

    paired = [r for r in basin if r["success_online"] and r["success_fgla"] and r["q_ratio_online_fgla"] is not None]
    small = [
        r for r in basin
        if (r["init_kind"] == "transverse" and r["level"] <= 0.01)
        or (r["init_kind"] == "phase_jitter" and r["level"] <= 0.15)
    ]
    ratios = np.asarray([r["q_ratio_online_fgla"] for r in paired], float) if paired else np.asarray([])
    edges = np.asarray([r["final_edge_rel_error"] for r in basin if r["final_edge_rel_error"] is not None], float)
    G = C["gates"]

    geom_max = float(np.max([r["geometry_rel_error"] for r in gok]))
    edge_med = float(np.median(edges)) if edges.size else float("inf")
    small_succ = float(np.mean([r["success_online"] for r in small])) if small else 0.0
    on_succ = float(np.mean([r["success_online"] for r in basin])) if basin else 0.0
    fg_succ = float(np.mean([r["success_fgla"] for r in basin])) if basin else 0.0
    beat = float(np.mean([r["beats_fgla"] for r in paired])) if paired else 0.0
    medratio = float(np.median(ratios)) if ratios.size else float("inf")
    late = float(np.mean([r["late_reject_fraction"] for r in basin])) if basin else 1.0
    e1 = int(sum(r["fallback_e1_failures"] for r in basin))

    passes = {
        "G2B_A_real_audio_geometry_pass": bool(geom_max <= G["geometry_relative_error_max"]),
        "G2B_B_active_edge_tracking_pass": bool(edge_med <= G["edge_relative_error_median_max"]),
        "G2B_C_small_basin_pass": bool(small_succ >= G["small_basin_success_fraction_min"]),
        "G2B_D_basin_nonshrink_pass": bool(on_succ + G["online_basin_deficit_vs_fgla_max"] >= fg_succ),
        "G2B_E_paired_rate_pass": bool(
            len(paired) > 0
            and beat >= G["paired_success_online_beat_fraction_min"]
            and medratio < G["paired_success_median_q_ratio_max"]
        ),
        "G2B_F_safeguard_pass": bool(
            late <= G["late_reject_fraction_mean_max"]
            and e1 <= G["fallback_e1_failures_max"]
        ),
    }

    summary = {
        "profile": C["profile"],
        "n_files": len(manifest),
        "n_geometry_cases": len(gok),
        "n_basin_runs": len(basin),
        "n_paired_success_runs": len(paired),
        "max_geometry_relative_error": geom_max,
        "median_final_edge_relative_error": edge_med,
        "small_basin_online_success_fraction": small_succ,
        "overall_online_success_fraction": on_succ,
        "overall_fgla_success_fraction": fg_succ,
        "paired_success_online_beat_fraction": beat,
        "paired_success_median_q_ratio": medratio,
        "paired_success_p90_q_ratio": float(np.percentile(ratios, 90)) if ratios.size else None,
        "mean_late_reject_fraction": late,
        "fallback_e1_failures": e1,
        "near_phase_degenerate_fraction": float(np.mean([r["lambda_plus"] >= 0.9999 for r in gok])),
        **passes,
    }
    summary["phase2b_gate"] = "GREEN" if all(passes.values()) else "YELLOW"
    summary["merged_from_batches"] = len(batch_out_dirs)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=True), encoding="utf-8")

    # Initialization summary
    groups = []
    for kind in sorted(set(r["init_kind"] for r in basin)):
        for level in sorted(set(r["level"] for r in basin if r["init_kind"] == kind)):
            z = [r for r in basin if r["init_kind"] == kind and r["level"] == level]
            pair = [r for r in z if r["success_online"] and r["success_fgla"] and r["q_ratio_online_fgla"] is not None]
            groups.append({
                "init_kind": kind,
                "level": level,
                "n": len(z),
                "online_success_fraction": float(np.mean([r["success_online"] for r in z])),
                "fgla_success_fraction": float(np.mean([r["success_fgla"] for r in z])),
                "paired_beat_fraction": float(np.mean([r["beats_fgla"] for r in pair])) if pair else None,
                "paired_median_q_ratio": float(np.median([r["q_ratio_online_fgla"] for r in pair])) if pair else None,
            })
    (out / "initialization_summary.json").write_text(json.dumps(groups, indent=2, allow_nan=True), encoding="utf-8")

    # Figures
    labels = [f"{r['file']}\n{r['profile']}" for r in gok]
    x = np.arange(len(gok))
    fig, ax = plt.subplots(figsize=(max(8, 1.1 * len(gok)), 4.8))
    ax.bar(x, [r["geometry_rel_error"] for r in gok])
    ax.axhline(G["geometry_relative_error_max"], linestyle="--")
    ax.set_yscale("log")
    ax.set_xticks(x, labels, rotation=35, ha="right")
    ax.set_ylabel("relative error")
    ax.set_title("2B-D1 — Real-audio tangent geometry transfer (merged batches)")
    fig.tight_layout()
    fig.savefig(out / "figures" / "2B_D1_real_audio_geometry.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for kind in sorted(set(g["init_kind"] for g in groups)):
        z = [g for g in groups if g["init_kind"] == kind]
        ax.plot([g["level"] for g in z], [g["online_success_fraction"] for g in z], marker="o", label=f"{kind} online")
        ax.plot([g["level"] for g in z], [g["fgla_success_fraction"] for g in z], marker="x", label=f"{kind} FGLA")
    ax.set_xscale("log")
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("initialization level")
    ax.set_ylabel("basin success fraction")
    ax.set_title("2B-D2 — Real-audio basin profile (merged batches)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "figures" / "2B_D2_basin_profile.png", dpi=180)
    plt.close(fig)

    if paired:
        fig, ax = plt.subplots(figsize=(7.5, 4.8))
        ax.hist([r["q_ratio_online_fgla"] for r in paired], bins=min(12, max(4, len(paired) // 2)))
        ax.axvline(1.0, linestyle="--")
        ax.set_xlabel("q_online / q_FGLA")
        ax.set_ylabel("count")
        ax.set_title("2B-D3 — Paired-success local rate transfer (merged batches)")
        fig.tight_layout()
        fig.savefig(out / "figures" / "2B_D3_rate_ratio.png", dpi=180)
        plt.close(fig)

    print(f"\nSuccessfully merged {len(batch_out_dirs)} batch -> {out}")
    print(json.dumps(summary, indent=2))
    return summary


def main():
    ap = argparse.ArgumentParser(
        description="Phase-2B real-audio runner with checkpoint/resume per audio batch and deadline control."
    )
    ap.add_argument("--audio-dir", required=True, help="Path to directory containing .wav audio files.")
    ap.add_argument("--config", default="configs/phase2b_grid.json", help="Configuration JSON file (default: configs/phase2a_grid.json).")
    ap.add_argument("--out", default="results/05_real_audio_basin_transfer/checkpointed", help="Output directory for results.")
    ap.add_argument("--max-files", type=int, default=None, help="Maximum number of audio files to process.")
    ap.add_argument("--batch-size", type=int, default=2, help="Batch size (number of audio files per batch, default: 2).")
    ap.add_argument("--time-budget-sec", type=float, default=None, help="Maximum runtime budget in seconds (stops safely before deadline).")
    args = ap.parse_args()

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    all_paths = discover_wav_files(Path(args.audio_dir), args.max_files)
    if not all_paths:
        raise FileNotFoundError(f"No .wav files found in {args.audio_dir}")
    n_batches = ((len(all_paths) - 1) // args.batch_size) + 1
    print(f"Found {len(all_paths)} WAV files -> chunked into {n_batches} batches (batch-size={args.batch_size}).")

    deadline = (time.time() + args.time_budget_sec) if args.time_budget_sec else None
    batch_out_dirs, stopped_early = run_batches(all_paths, args.config, out_root, args.batch_size, deadline=deadline)

    # Merge all completed batches
    if batch_out_dirs:
        merge(batch_out_dirs, args.config, out_root)
    else:
        print("No completed batches found to merge.")


if __name__ == "__main__":
    main()
