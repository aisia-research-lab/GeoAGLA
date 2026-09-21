#!/usr/bin/env python3
"""03_run_e10r_locked.py
======================
Experiment E10-R: Final Mechanism Attribution & Reproducibility Closure.

Executes the frozen 6-variant ablation across the locked 395-case STFT geometry
population on the 202-file audio benchmark, guaranteeing:
1. Exact locked geometry cases (395 valid pairs, no runtime re-filtering).
2. Historical Kaggle batch2 seed convention (`--seed-mode historical_batch2`).
3. Six-way paired evaluation (4,740 paired problem instances, 28,440 method rows).
4. Periodic checkpointing and structured event logging.

Variants evaluated:
- `fgla_oracle`: Optimal fixed momentum using asymptotic eigenvalue lambda_+.
- `fixed_1e_oracle`: Minimax oracle on the single-edge interval [0, lambda_+].
- `online_raw`: Pure online Rayleigh quotient estimation without envelope or fallback.
- `online_env`: Online estimation with dynamic stability envelope enabled.
- `online_fallback`: Online estimation with conservative GLA fallback enabled.
- `online_full`: Canonical GeoAGLA combining online adaptation, envelope, and fallback.

Usage:
    python experiments/08_e10_robustness_mechanism_ablation/03_run_e10r_locked.py \
        --audio-dir data/audio_benchmark \
        --out results/08_e10r_locked \
        --seed-mode historical_batch2
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

# Dynamically import canonical Phase-2B helper routines
_phase2b_path = ROOT / "experiments" / "05_real_audio_basin_transfer" / "03_phase2b_real_audio_basin_sweep.py"
_spec = importlib.util.spec_from_file_location("phase2b_frozen", _phase2b_path)
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.algorithms.online_ablation import run_online_ablation

VARIANTS = [
    "fgla_oracle",
    "fixed_1e_oracle",
    "online_raw",
    "online_env",
    "online_fallback",
    "online_full",
]


def run_variant(
    name: str,
    c0: np.ndarray,
    cstar: np.ndarray,
    s: np.ndarray,
    op: FFTAnalysisOperator,
    lp: float,
    cfg: Dict[str, Any],
) -> Tuple[List[np.ndarray], List[float], float, float, bool, List[Dict[str, Any]]]:
    """Run a single method variant for n_iter iterations."""
    if name == "fgla_oracle":
        tr, er, q = B._fixed(
            c0, cstar, s, op, fgla_opt(lp),
            cfg["n_iter"], cfg["rate_tail_fraction"], cfg["rate_floor"]
        )
        blocks: List[Dict[str, Any]] = []
    elif name == "fixed_1e_oracle":
        tr, er, q = B._fixed(
            c0, cstar, s, op, oracle_minimax(0.0, lp),
            cfg["n_iter"], cfg["rate_tail_fraction"], cfg["rate_floor"]
        )
        blocks = []
    else:
        kw = dict(
            n_iter=cfg["n_iter"],
            warmup=cfg["warmup"],
            block_size=cfg["block_size"],
            memory=cfg["memory"],
            margin=cfg["margin"],
            lambda_ceiling=cfg["lambda_ceiling"],
            svd_rtol=cfg["svd_rtol"],
            cond_max=cfg["cond_max"],
            alpha_safe=cfg["alpha_safe"],
            beta_safe=cfg["beta_safe"],
            gamma_safe=cfg["gamma_safe"],
            K_safe=cfg["K_safe"],
            descent_a=cfg["descent_a"],
        )
        if name == "online_full":
            rr = run_online_policy(c0, c0, s, op, policy="dynamic_envelope", **kw)
        elif name == "online_raw":
            rr = run_online_ablation(c0, c0, s, op, use_envelope=False, use_fallback=False, **kw)
        elif name == "online_env":
            rr = run_online_ablation(c0, c0, s, op, use_envelope=True, use_fallback=False, **kw)
        elif name == "online_fallback":
            rr = run_online_ablation(c0, c0, s, op, use_envelope=False, use_fallback=True, **kw)
        else:
            raise ValueError(f"Unknown variant: {name}")

        tr = rr["trajectory"]
        er = B._errors(tr, cstar)
        q = B._rate(er, cfg["rate_tail_fraction"], cfg["rate_floor"])
        blocks = rr["blocks"]

    fm = B._magnitude_residual(tr[-1], s)
    succ = B._success(float(B.orbit_distance(c0, cstar)), float(er[-1]), fm, cfg)
    return tr, er, q, fm, succ, blocks


def execute_e10r(
    audio_dir: Path,
    out_dir: Path,
    seed_mode: str = "historical_batch2",
    checkpoint_interval: int = 10,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Execute the locked 395-case E10-R closure experiment."""
    cfg_path = ROOT / "configs" / "phase2b_grid.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    locked_csv = ROOT / "experiments" / "08_e10_robustness_mechanism_ablation" / "frozen" / "e10r_locked_geometry_395.csv"
    if not locked_csv.exists():
        raise FileNotFoundError(f"Locked geometry file not found: {locked_csv}")

    geo_df = pd.read_csv(locked_csv)
    gmap = {(r.file, r.profile): float(r.lambda_plus) for r in geo_df.itertuples()}

    paths = sorted(p for p in audio_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".wav")
    pmap = {p.name: p for p in paths}

    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = out_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    unique_files = sorted(set(geo_df["file"]))
    print(f"Starting E10-R Locked Closure across {len(unique_files)} files ({len(geo_df)} locked geometry cases)...")
    print(f"Seed mode: {seed_mode}")
    print(f"Expected cardinality: 395 cases x 12 inits x 6 variants = 28,440 method rows.")

    rows: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    t_start = time.time()

    for global_fi, name in enumerate(unique_files):
        if name not in pmap:
            raise FileNotFoundError(f"Required locked audio file missing from audio directory: {name}")
        path = pmap[name]
        x, meta = B.load_audio(path, cfg["target_sample_rate"], cfg["excerpt_length"])

        # Historical Kaggle jobs processed sorted files in consecutive batches of two and reset fi inside each batch
        fi = (global_fi % 2) if seed_mode == "historical_batch2" else global_fi

        for pi, P in enumerate(cfg["stft_profiles"]):
            key = (name, P["id"])
            if key not in gmap:
                continue

            win = B._window(P["window"], P["window_length"])
            op = FFTAnalysisOperator(len(x), win, P["hop"], P["n_fft"])
            cstar = op.q_analyze(x)
            s = np.abs(cstar)
            xstar = x
            lp = gmap[key]

            for init in cfg["basin_initializations"]:
                for level in init["levels"]:
                    for seed in cfg["seeds"]:
                        init_seed = 10000 * fi + 100 * pi + 10 * seed + int(round(1000 * level))
                        c0 = B._init_state(init["kind"], level, init_seed, cstar, s, xstar, op)
                        init_err = float(B.orbit_distance(c0, cstar))
                        init_mag = B._magnitude_residual(c0, s)
                        run_key = f"{name}|{P['id']}|{init['kind']}|{level:g}|{seed}"

                        for v in VARIANTS:
                            tr, er, q, fm, succ, blocks = run_variant(v, c0, cstar, s, op, lp, cfg)
                            n_rej = int(sum(not b.get("candidate_accepted", b.get("checkpoint_accepted", True)) for b in blocks))
                            n_fb = int(sum(bool(b.get("fallback_used", False)) for b in blocks))

                            row = dict(
                                run_key=run_key,
                                file=name,
                                profile=P["id"],
                                init_kind=init["kind"],
                                level=float(level),
                                seed=int(seed),
                                init_seed=int(init_seed),
                                seed_mode=seed_mode,
                                variant=v,
                                lambda_plus=lp,
                                initial_orbit_error=init_err,
                                initial_magnitude_residual=init_mag,
                                final_orbit_error=float(er[-1]),
                                final_magnitude_residual=fm,
                                success=bool(succ),
                                q_fitted=q,
                                n_blocks=len(blocks),
                                n_checkpoint_reject=n_rej,
                                n_fallback=n_fb,
                            )
                            rows.append(row)

                            for b in blocks:
                                events.append(dict(run_key=run_key, variant=v, lambda_plus=lp, **b))

        if (global_fi + 1) % 5 == 0 or (global_fi + 1) == len(unique_files):
            elapsed = time.time() - t_start
            print(f"[{global_fi+1:3d}/{len(unique_files):3d}] Elapsed: {elapsed:.1f}s | Rows: {len(rows):5d}/28440")

        # Periodic checkpoint
        if (global_fi + 1) % checkpoint_interval == 0:
            pd.DataFrame(rows).to_csv(checkpoint_dir / "e10r_checkpoint_latest.csv", index=False)

    def write_csv(p: Path, data: List[Dict[str, Any]]) -> None:
        if not data:
            p.write_text("run_key,variant,block\n", encoding="utf-8")
            return
        fields = sorted(set().union(*(r.keys() for r in data)))
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(data)

    write_csv(out_dir / "e10r_run_ledger.csv", rows)
    write_csv(out_dir / "e10r_event_ledger.csv", events)
    (out_dir / "e10r_run_ledger.json").write_text(json.dumps(rows, indent=2, allow_nan=True), encoding="utf-8")

    expected_rows = 395 * 12 * 6
    if len(rows) != expected_rows:
        raise RuntimeError(f"Hard closure cardinality failed: {len(rows)} != {expected_rows}")

    print(f"PASS: rows {len(rows)} paired instances {len(rows)//6} locked geometry cases {len(geo_df)}")
    return rows, events


def main() -> None:
    ap = argparse.ArgumentParser(description="E10-R Locked Closure Runner")
    ap.add_argument("--audio-dir", required=True, help="Directory containing audio WAV benchmark files")
    ap.add_argument("--out", default=str(ROOT / "results" / "08_e10r_locked"), help="Output directory")
    ap.add_argument("--seed-mode", choices=["historical_batch2", "global"], default="historical_batch2", help="Seed generation mode")
    ap.add_argument("--checkpoint-interval", type=int, default=10, help="Files per checkpoint save")
    args = ap.parse_args()

    execute_e10r(
        audio_dir=Path(args.audio_dir),
        out_dir=Path(args.out),
        seed_mode=args.seed_mode,
        checkpoint_interval=args.checkpoint_interval,
    )


if __name__ == "__main__":
    main()
