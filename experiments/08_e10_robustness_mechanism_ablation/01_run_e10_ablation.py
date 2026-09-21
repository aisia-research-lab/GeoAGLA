#!/usr/bin/env python3
"""01_run_e10_ablation.py
======================
Experiment 10: Online Robustness Mechanism Ablation.

Evaluates six paired algorithm variants on identical problem and initialization instances
from the canonical Phase-2B real-audio population:
1. `fgla_oracle`: Optimal fixed-momentum FGLA with known true lambda+.
2. `fixed_1e_oracle`: Fixed one-edge minimax design oracle_minimax(0.0, lambda+).
3. `online_raw`: Passive Ritz estimation without envelope or checkpoint rollback.
4. `online_env`: Passive Ritz with running-max envelope, without rollback.
5. `online_fallback`: Passive Ritz with checkpoint rollback, without running-max envelope.
6. `online_full`: Full canonical Online policy (dynamic_envelope + checkpoint rollback).

Usage:
    python experiments/08_e10_robustness_mechanism_ablation/01_run_e10_ablation.py \\
        --audio-dir /path/to/wavs \\
        --out results/08_e10_robustness_mechanism_ablation \\
        --max-files 2
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

# Import Phase-2B baseline components dynamically to avoid directory name import syntax issues
base_path = ROOT / "experiments" / "05_real_audio_basin_transfer" / "03_phase2b_real_audio_basin_sweep.py"
spec = importlib.util.spec_from_file_location("phase2b_frozen", base_path)
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.geometry.matrixfree import top_transverse_spectrum
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.algorithms.online_ablation import run_online_ablation

VARIANTS = ["fgla_oracle", "fixed_1e_oracle", "online_raw", "online_env", "online_fallback", "online_full"]


def _run_variant(name: str, c0: np.ndarray, cstar: np.ndarray, s: np.ndarray, op: FFTAnalysisOperator, lp: float, C: dict):
    if name == "fgla_oracle":
        tr, er, q = B._fixed(c0, cstar, s, op, fgla_opt(lp), C["n_iter"], C["rate_tail_fraction"], C["rate_floor"])
        blocks = []
    elif name == "fixed_1e_oracle":
        tr, er, q = B._fixed(c0, cstar, s, op, oracle_minimax(0.0, lp), C["n_iter"], C["rate_tail_fraction"], C["rate_floor"])
        blocks = []
    else:
        kw = dict(
            n_iter=C["n_iter"],
            warmup=C["warmup"],
            block_size=C["block_size"],
            memory=C["memory"],
            margin=C["margin"],
            lambda_ceiling=C["lambda_ceiling"],
            svd_rtol=C["svd_rtol"],
            cond_max=C["cond_max"],
            alpha_safe=C["alpha_safe"],
            beta_safe=C["beta_safe"],
            gamma_safe=C["gamma_safe"],
            K_safe=C["K_safe"],
            descent_a=C["descent_a"],
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
        q = B._rate(er, C["rate_tail_fraction"], C["rate_floor"])
        blocks = rr["blocks"]

    fm = B._magnitude_residual(tr[-1], s)
    success = B._success(float(B.orbit_distance(c0, cstar)), float(er[-1]), fm, C)
    return tr, er, q, fm, success, blocks


def run_e10_ablation(audio_dir: str | Path, out_dir: str | Path, config_path: str | Path | None = None, max_files: int | None = None):
    audio_dir = Path(audio_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if config_path is None:
        config_path = ROOT / "configs" / "phase2b_grid.json"
    C = json.loads(Path(config_path).read_text(encoding="utf-8"))

    paths = sorted([p for p in audio_dir.rglob("*.wav") if p.is_file()])
    if max_files:
        paths = paths[:max_files]

    if not paths:
        raise FileNotFoundError(f"No WAV files found in {audio_dir}")

    print("=" * 70)
    print(f"Starting E10 Mechanism Ablation across {len(paths)} audio files")
    print(f"Output directory: {out_dir}")
    print(f"Variants: {', '.join(VARIANTS)}")
    print("=" * 70)

    rows = []
    events = []

    for fi, path in enumerate(paths):
        x, meta = B.load_audio(path, C["target_sample_rate"], C["excerpt_length"])
        xstar = x

        for pi, P in enumerate(C["stft_profiles"]):
            try:
                win = B._window(P["window"], P["window_length"])
                op = FFTAnalysisOperator(len(xstar), win, P["hop"], P["n_fft"])
                cstar = op.analyze(xstar)
                s = np.abs(cstar)
                nz = B._near_zero_stats(cstar, C["near_zero_thresholds"])
                if nz["min_abs_coeff"] <= C["exact_zero_relative_tol"] * nz["median_abs_coeff"]:
                    print(f"[SKIP_IRREGULAR] {path.name} {P['id']}: near-zero coefficient violation")
                    continue
                sp = top_transverse_spectrum(cstar, op, k=C["eig_k"], phase_tol=C["phase_tol"], eig_tol=C["eig_tol"])
                lp = float(sp["lambda_plus"])
            except Exception as exc:
                print(f"[SKIP_ERROR] {path.name} {P['id']}: {repr(exc)}")
                continue

            print(f"[PROCESS] File {fi+1}/{len(paths)}: {path.name} | Profile: {P['id']} | lambda+: {lp:.6f}")

            for init in C["basin_initializations"]:
                for level in init["levels"]:
                    for seed in C["seeds"]:
                        init_seed = 10000 * fi + 100 * pi + 10 * seed + int(round(1000 * level))
                        c0 = B._init_state(init["kind"], level, init_seed, cstar, s, xstar, op)
                        init_err = float(B.orbit_distance(c0, cstar))
                        init_mag = B._magnitude_residual(c0, s)
                        run_key = f"{path.name}|{P['id']}|{init['kind']}|{level:g}|{seed}"

                        for v in VARIANTS:
                            tr, er, q, fm, succ, blocks = _run_variant(v, c0, cstar, s, op, lp, C)
                            n_reject = int(sum(not b.get("candidate_accepted", b.get("checkpoint_accepted", True)) for b in blocks))
                            if v == "online_full":
                                n_fb = int(sum(bool(b.get("fallback_used", False)) or (not b.get("candidate_accepted", True)) for b in blocks))
                            else:
                                n_fb = int(sum(bool(b.get("fallback_used", False)) for b in blocks))

                            rows.append(
                                dict(
                                    run_key=run_key,
                                    file=path.name,
                                    profile=P["id"],
                                    init_kind=init["kind"],
                                    level=float(level),
                                    seed=int(seed),
                                    init_seed=int(init_seed),
                                    variant=v,
                                    lambda_plus=lp,
                                    initial_orbit_error=init_err,
                                    initial_magnitude_residual=init_mag,
                                    final_orbit_error=float(er[-1]),
                                    final_magnitude_residual=fm,
                                    success=bool(succ),
                                    q_fitted=q,
                                    n_blocks=len(blocks),
                                    n_checkpoint_reject=n_reject,
                                    n_fallback=n_fb,
                                )
                            )
                            for b in blocks:
                                events.append(dict(run_key=run_key, variant=v, lambda_plus=lp, **b))

    def write_csv(p: Path, data: list):
        if not data:
            return
        fields = sorted(set().union(*(r.keys() for r in data)))
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(data)

    write_csv(out_dir / "e10_run_ledger.csv", rows)
    write_csv(out_dir / "e10_event_ledger.csv", events)
    (out_dir / "e10_run_ledger.json").write_text(json.dumps(rows, indent=2, allow_nan=True), encoding="utf-8")

    paired_cases = len(rows) // len(VARIANTS) if VARIANTS else 0
    print(f"\n[DONE] Successfully wrote {len(rows)} method rows ({paired_cases} paired cases) to {out_dir}")
    return rows, events


def main():
    parser = argparse.ArgumentParser(description="Run E10 Robustness Mechanism Ablation across real-audio cases")
    parser.add_argument("--audio-dir", required=True, help="Directory containing .wav audio files")
    parser.add_argument("--out", default=str(ROOT / "results" / "08_e10_robustness_mechanism_ablation"), help="Output directory")
    parser.add_argument("--config", default=None, help="Path to grid configuration JSON (default: configs/phase2b_grid.json)")
    parser.add_argument("--max-files", type=int, default=None, help="Maximum number of audio files to process (default: all)")
    args = parser.parse_args()

    run_e10_ablation(args.audio_dir, args.out, args.config, args.max_files)


if __name__ == "__main__":
    main()
