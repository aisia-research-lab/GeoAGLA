"""Matched-budget (projection calls and synchronized wall-clock) benchmark & ablation runner.

Evaluates all 10 methods and ablation variants on the same PyTorch STFT backend:
  Online, NAGLA_H2, FGLA_095, RestartNAG, OneEdgeOracle,
  OnlineNoFallback, OnlineRaw, OnlineGram, GLA, AGLA_tuned.

Usage:
  # Self-contained synthetic smoke benchmark (CPU):
  python experiments/matched_budget_benchmark.py --synthetic --mode calls --device cpu --out outputs/calls_synth.jsonl
  python experiments/matched_budget_benchmark.py --synthetic --mode wall  --device cpu --out outputs/wall_synth.jsonl

  # Full audio benchmark on a local MUSAN directory (CPU or CUDA):
  python experiments/matched_budget_benchmark.py --audio-root /path/to/musan --spectra outputs/spectral_audio.jsonl --mode calls --device cuda:0 --out outputs/calls_audio.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Iterator

import numpy as np
import torch

from experiments.common import (
    ALL_INITS,
    CALL_BUDGETS,
    METHODS,
    STFT_PROFILES,
    WALL_BUDGETS,
    NumpyPeriodicSTFT,
    build_initial_state,
    load_audio_records,
    make_window,
    run_solver,
    sha256_bytes,
)
from geometry_gla.operators.stft_torch import TorchPeriodicSTFT


def extract_budget_rows(result: dict, mode: str, budgets: list[int] | list[float]) -> Iterator[dict]:
    """Select the last fully committed checkpoint within each budget cap."""
    rows = result["rows"]
    field = "calls" if mode == "calls" else "solver_seconds"
    for b in budgets:
        eligible = [r for r in rows if r[field] <= b]
        last = eligible[-1]
        yield dict(
            **last,
            budget=b,
            budget_kind=mode,
            initial_error=result["initial_error"],
            orbit_success=bool(last["orbit"] <= 0.1 * result["initial_error"]),
            mag_success=bool(last["mag"] <= 1e-5),
            status="ok",
        )


def _load_spectra_map(path: str | Path) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("status") == "RESOLVED" and "L" in r:
                out[(r["source_id"], r["profile"])] = float(r["L"])
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Matched-budget projection-call and wall-clock benchmark.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--synthetic", action="store_true", help="Run fast synthetic smoke benchmark.")
    group.add_argument("--audio-root", type=str, help="Path to local MUSAN audio directory.")
    parser.add_argument("--spectra", type=str, default=None, help="JSONL file from spectral_geometry.py (for OneEdgeOracle).")
    parser.add_argument("--mode", choices=["calls", "wall"], required=True, help="Budget accounting mode.")
    parser.add_argument("--device", type=str, default="cpu", help="PyTorch device (e.g., cpu or cuda:0).")
    parser.add_argument("--seeds", type=int, default=1, help="Number of random seeds per initialization.")
    parser.add_argument("--out", type=str, required=True, help="Output JSONL path.")
    args = parser.parse_args()

    torch.set_num_threads(1)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    blocks_path = Path(str(out_path) + ".blocks.jsonl")

    if args.synthetic:
        budgets = [30, 90] if args.mode == "calls" else [0.005, 0.015]
        max_iter = 96 if args.mode == "calls" else 100000
        wall_limit = None if args.mode == "calls" else max(budgets)
        x = np.random.default_rng(17).normal(size=512) + 1j * np.random.default_rng(2).normal(size=512)
        items = [({"source_id": "synthetic_512"}, x)]
        profiles = ["gaussian"]
        inits = ["transverse_0.01"]
        spectra_map = {("synthetic_512", "gaussian"): 0.99}
    else:
        budgets = CALL_BUDGETS if args.mode == "calls" else WALL_BUDGETS
        max_iter = 2884 if args.mode == "calls" else 100000
        wall_limit = None if args.mode == "calls" else max(budgets)
        items = list(load_audio_records(args.audio_root))
        profiles = list(STFT_PROFILES.keys())
        inits = ALL_INITS
        spectra_map = _load_spectra_map(args.spectra) if args.spectra else {}

    total_budget_rows = 0
    with out_path.open("w", encoding="utf-8") as f_out, blocks_path.open("w", encoding="utf-8") as f_blk:
        for meta, sig in items:
            for profile in profiles:
                win, hop, n_fft = make_window(profile)
                no = NumpyPeriodicSTFT(len(sig), win, hop, n_fft)
                op = TorchPeriodicSTFT(len(sig), win, hop, n_fft, device=args.device)
                c_star = no.analyze(sig)
                L_true = spectra_map.get((meta["source_id"], profile))

                # Common FFT warm-up outside timed budget
                op.G(op.tensor(c_star), op.tensor(np.abs(c_star)).real)
                op.synchronize()

                for kind in inits:
                    for seed in range(args.seeds):
                        sk = int(sha256_bytes(f"{meta['source_id']}|{profile}|{kind}|{seed}|REBFINAL".encode())[:8], 16)
                        init_state = build_initial_state(c_star, no, kind, sk)
                        base_key = dict(
                            source_id=meta["source_id"],
                            profile=profile,
                            N=len(sig),
                            init=kind,
                            seed=seed,
                            initial_hash=sha256_bytes(init_state.tobytes()),
                            true_L=L_true,
                        )
                        order = METHODS.copy()
                        random.Random(sk).shuffle(order)

                        for method in order:
                            if method == "OneEdgeOracle" and L_true is None:
                                for b in budgets:
                                    f_out.write(
                                        json.dumps(
                                            dict(**base_key, method=method, budget_kind=args.mode, budget=b, status="skipped", reason="missing_spectrum", success=False)
                                        )
                                        + "\n"
                                    )
                                continue

                            res = run_solver(
                                op,
                                c_star,
                                init_state,
                                method,
                                L=L_true,
                                max_iter=max_iter,
                                wall_limit=wall_limit,
                                record_hashes=(args.mode == "calls"),
                            )
                            assert res["wall_reached"], "Wall-time budget not reached; increase max_iter"
                            for row in extract_budget_rows(res, args.mode, budgets):
                                f_out.write(json.dumps(dict(**base_key, method=method, **row), allow_nan=False) + "\n")
                                total_budget_rows += 1
                            f_blk.write(
                                json.dumps(
                                    dict(
                                        **base_key,
                                        method=method,
                                        mode=args.mode,
                                        initial_error=res["initial_error"],
                                        rows=res["rows"],
                                        blocks=res["blocks"],
                                    ),
                                    allow_nan=False,
                                )
                                + "\n"
                            )
            print(f"Completed {meta['source_id']} ({args.mode} mode)", flush=True)

    print(f"Wrote {total_budget_rows} budget rows to {out_path}")


if __name__ == "__main__":
    main()
