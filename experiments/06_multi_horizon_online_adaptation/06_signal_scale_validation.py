#!/usr/bin/env python3
"""Held-Out Signal-Scale Validation (Online Evaluator - Task B3 / E7-A).
Section 10 of ICLR 2027 Next Experiment Handoff for Students A & B.
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

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
SCRIPTS_DIR = ROOT / "scripts"
for p in (SRC_DIR, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from common import load_json, dump_json, write_csv, median, quantiles
from geometry_gla.operators.stft import (
    AnalysisOperator, periodic_stft_matrix, gaussian_window, hann_window
)
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.metrics.phase import orbit_distance
from geometry_gla.signals import make_signal


def run_signal_scale_validation(
    out_dir: str | Path | None = None,
    n_iter: int = 180,
    tolerances: tuple[float, ...] = (1e-2, 1e-3, 1e-4, 1e-6),
):
    out = Path(out_dir or (ROOT / "results" / "e7_signal_scale"))
    out.mkdir(parents=True, exist_ok=True)

    signal_kinds = ["harmonic", "chirp", "speech_like", "transient"]
    configs = [
        {"N": 256, "W": 64, "hop": 16, "n_fft": 64, "window": "hann"},
        {"N": 256, "W": 64, "hop": 8, "n_fft": 64, "window": "gaussian"},
        {"N": 512, "W": 128, "hop": 32, "n_fft": 128, "window": "hann"},
    ]
    seeds = [42, 123]

    print(f"\n--- [TASK B3 / E7-A] Held-Out Signal-Scale Validation on {len(signal_kinds)} signal types ---")
    print(f"Pre-frozen tolerances: {tolerances}")

    ledger_rows = []
    case_idx = 0

    for kind in signal_kinds:
        for cfg in configs:
            for seed in seeds:
                case_idx += 1
                cid = f"{kind}_N{cfg['N']}_w{cfg['W']}_h{cfg['hop']}_s{seed}"

                # 1. Build operator
                w = hann_window(cfg["W"]) if cfg["window"] == "hann" else gaussian_window(cfg["W"])
                T = periodic_stft_matrix(cfg["N"], w, cfg["hop"], cfg["n_fft"])
                op = AnalysisOperator(T)

                # 2. Synthesize deterministic signal
                x = make_signal(kind, cfg["N"], seed=seed)
                c_star = op.analyze(x.astype(np.complex128))
                s = np.abs(c_star)

                # 3. Transverse spectrum
                try:
                    spec = transverse_spectrum(c_star, op)
                    lm = max(0.0, float(spec["lambda_minus"]))
                    lp = min(1.0 - 1e-12, max(lm + 1e-8, float(spec["lambda_plus"])))
                except Exception:
                    lp = 0.999
                    lm = 0.0

                # Deterministic random phase initialization
                rng = np.random.default_rng(seed + 999)
                init_phase = np.exp(1j * rng.uniform(-np.pi, np.pi, size=c_star.shape))
                t0 = s * init_phase
                t_minus1 = t0.copy()

                # Method 1: GLA
                gla_traj = run_agla_state(t0, t_minus1, s, op, 0.0, 0.0, 1.0, n_iter)
                e_gla = [orbit_distance(z, c_star) for z in gla_traj]

                # Method 2: FGLA (optimal constant)
                p_fg = fgla_opt(lp)
                fg_traj = run_agla_state(t0, t_minus1, s, op, p_fg["alpha"], p_fg["beta"], p_fg["gamma"], n_iter)
                e_fg = [orbit_distance(z, c_star) for z in fg_traj]

                # Method 3: Oracle Minimax
                p_ora = oracle_minimax(lm, lp)
                ora_traj = run_agla_state(t0, t_minus1, s, op, p_ora["alpha"], p_ora["beta"], p_ora["gamma"], n_iter)
                e_ora = [orbit_distance(z, c_star) for z in ora_traj]

                # Method 4: Frozen Online (dynamic envelope)
                on_res = run_online_policy(
                    t0, t_minus1, s, op,
                    n_iter=n_iter, warmup=12, block_size=8,
                    memory=3, margin=0.0, policy="dynamic_envelope"
                )
                e_on = [orbit_distance(z, c_star) for z in on_res["trajectory"]]

                # Compute iterations to tolerance T_m(tau)
                t_gla_dict = {}
                t_fg_dict = {}
                t_ora_dict = {}
                t_on_dict = {}
                s_iter_dict = {}

                for tau in tolerances:
                    tau_str = f"tau_{str(tau).replace('.', 'p')}"
                    
                    # T_m(tau) = min {n: e_n <= tau}
                    idx_gla = next((n for n, err in enumerate(e_gla) if err <= tau), None)
                    idx_fg = next((n for n, err in enumerate(e_fg) if err <= tau), None)
                    idx_ora = next((n for n, err in enumerate(e_ora) if err <= tau), None)
                    idx_on = next((n for n, err in enumerate(e_on) if err <= tau), None)

                    t_gla_dict[f"T_gla_{tau_str}"] = idx_gla
                    t_fg_dict[f"T_fgla_{tau_str}"] = idx_fg
                    t_ora_dict[f"T_oracle_{tau_str}"] = idx_ora
                    t_on_dict[f"T_online_{tau_str}"] = idx_on

                    # Paired iteration saving: (T_FGLA - T_Online) / T_FGLA
                    if idx_fg is not None and idx_on is not None and idx_fg > 0:
                        s_iter = (idx_fg - idx_on) / idx_fg
                    else:
                        s_iter = None
                    s_iter_dict[f"S_iter_{tau_str}"] = s_iter

                # Safeguard stats
                blks = on_res["blocks"]
                rejections = sum(1 for b in blks if not b.get("candidate_accepted", True))
                fallback_rate = (rejections / len(blks)) if blks else 0.0

                row = {
                    "case_id": cid,
                    "signal_kind": kind,
                    "N": cfg["N"],
                    "W": cfg["W"],
                    "hop": cfg["hop"],
                    "seed": seed,
                    "lambda_plus": lp,
                    "lambda_minus": lm,
                    "final_err_gla": e_gla[-1],
                    "final_err_fgla": e_fg[-1],
                    "final_err_oracle": e_ora[-1],
                    "final_err_online": e_on[-1],
                    "safeguard_fallback_rate": fallback_rate,
                }
                row.update(t_gla_dict)
                row.update(t_fg_dict)
                row.update(t_ora_dict)
                row.update(t_on_dict)
                row.update(s_iter_dict)

                ledger_rows.append(row)
                t_fg_1e2 = t_fg_dict.get("T_fgla_tau_0p01")
                t_on_1e2 = t_on_dict.get("T_online_tau_0p01")
                print(f"[{case_idx:2d}/24] {kind:11s} (N={cfg['N']}, s={seed}): T_fgla(1e-2)={t_fg_1e2} | T_online(1e-2)={t_on_1e2} | Online Final Err={e_on[-1]:.2e}")

    # Summary by signal kind
    kind_summaries = {}
    for kind in signal_kinds:
        k_rows = [r for r in ledger_rows if r["signal_kind"] == kind]
        s_iter_0p01 = [r["S_iter_tau_0p01"] for r in k_rows if r.get("S_iter_tau_0p01") is not None]
        s_iter_0p001 = [r["S_iter_tau_0p001"] for r in k_rows if r.get("S_iter_tau_0p001") is not None]
        kind_summaries[kind] = {
            "n_cases": len(k_rows),
            "median_final_err_gla": median([r["final_err_gla"] for r in k_rows]),
            "median_final_err_fgla": median([r["final_err_fgla"] for r in k_rows]),
            "median_final_err_online": median([r["final_err_online"] for r in k_rows]),
            "median_saving_tau_1e2": median(s_iter_0p01) if s_iter_0p01 else None,
            "median_saving_tau_1e3": median(s_iter_0p001) if s_iter_0p001 else None,
            "mean_safeguard_fallback_rate": float(np.mean([r["safeguard_fallback_rate"] for r in k_rows])),
        }

    # Save ledger and summary
    write_csv(ledger_rows, out / "signal_scale_ledger.csv")
    dump_json({
        "total_cases": len(ledger_rows),
        "signal_kinds": signal_kinds,
        "tolerances": list(tolerances),
        "stratified_by_kind": kind_summaries,
    }, out / "signal_scale_summary.json")

    print(f"\n[OK] Signal-scale validation complete. Saved to {out / 'signal_scale_ledger.csv'}")
    return ledger_rows, kind_summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Task B3: Signal-Scale Validation")
    parser.add_argument("--out", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    run_signal_scale_validation(out_dir=args.out)