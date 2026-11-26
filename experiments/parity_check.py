"""Trajectory and checkpoint-decision parity check: NumPy reference vs. PyTorch backend.

Verifies that the PyTorch direct-SVD solver matches the NumPy reference
implementation (`geometry_gla.algorithms.online_safe.run_online_policy`) across
16 test cases (2 signals x 2 STFT profiles x 4 initialization regimes).

Usage:
  python experiments/parity_check.py --device cpu
  python experiments/parity_check.py --device cuda:0 --audio-root /path/to/musan --out outputs/parity_gpu.json
"""
from __future__ import annotations

import argparse
import json
from itertools import islice
from pathlib import Path

import numpy as np

from experiments.common import (
    STFT_PROFILES,
    NumpyPeriodicSTFT,
    build_initial_state,
    load_audio_records,
    make_window,
    run_solver,
)
from geometry_gla.algorithms.agla import run_agla_state, run_nagla_state
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.operators.stft_torch import TorchPeriodicSTFT

PARITY_INITS = ["transverse_0.001", "transverse_0.01", "phase_jitter_0.15", "random_phase"]


def check_one_case(x: np.ndarray, profile: str, init_kind: str, device: str, horizon: int = 84) -> dict:
    """Compare NumPy reference and PyTorch trajectories on one problem instance."""
    win, hop, n_fft = make_window(profile)
    no = NumpyPeriodicSTFT(len(x), win, hop, n_fft)
    to = TorchPeriodicSTFT(len(x), win, hop, n_fft, device=device)
    c_star = no.analyze(x)
    t0 = build_initial_state(c_star, no, init_kind, seed=9)
    no.projections = 0

    ref = run_online_policy(t0, t0, np.abs(c_star), no, n_iter=horizon)
    actual = run_solver(to, c_star, t0, "Online", max_iter=horizon, record_trace=True)

    R = float(np.linalg.norm(c_star))
    err = np.linalg.norm(np.asarray(actual["trajectory"]) - ref["trajectory"], axis=1) / R
    events, ref_blocks = actual["blocks"], ref["blocks"]
    assert len(events) == len(ref_blocks)

    mismatch_blocks: list[int] = []
    max_edge_diff = 0.0
    for rb, ab in zip(ref_blocks, events):
        if rb["synth_edge"] is not None and ab["synth_edge"] is not None:
            max_edge_diff = max(max_edge_diff, abs(rb["synth_edge"] - ab["synth_edge"]))
        if (
            (rb["synth_edge"] is None) != (ab["synth_edge"] is None)
            or rb["candidate_accepted"] != ab["candidate"]["accepted"]
            or rb["fallback_e1_pass"] != ab["committed"]["accepted"]
        ):
            mismatch_blocks.append(rb["block"])

    nref = run_nagla_state(t0, np.abs(c_star), no, horizon, H=2)
    nact = run_solver(to, c_star, t0, "NAGLA_H2", max_iter=horizon, record_trace=True)
    nagla_err = float(np.max(np.linalg.norm(nref - np.asarray(nact["trajectory"]), axis=1) / R))

    fref = run_agla_state(t0, np.abs(c_star), no, horizon, alpha=0.95, beta=0.0, gamma=1.0)
    fact = run_solver(to, c_star, t0, "FGLA_095", max_iter=horizon, record_trace=True)
    fgla_err = float(np.max(np.linalg.norm(fref - np.asarray(fact["trajectory"]), axis=1) / R))

    ref_calls = 12 + sum(
        (b["end_iter"] - b["start_iter"]) * (1 + int(not b["candidate_accepted"])) + 1 for b in ref_blocks
    )
    actual_calls = actual["rows"][-1]["calls"]
    max_state_err = float(np.max(err))
    passed = bool(
        max_state_err < 1e-7
        and not mismatch_blocks
        and max_edge_diff < 1e-6
        and ref_calls == actual_calls
        and max(nagla_err, fgla_err) < 1e-10
    )
    return dict(
        profile=profile,
        init=init_kind,
        max_state_error=max_state_err,
        max_synth_difference=max_edge_diff,
        decision_mismatch_blocks=mismatch_blocks,
        reference_calls=ref_calls,
        actual_calls=actual_calls,
        nagla_error=nagla_err,
        fgla_error=fgla_err,
        passed=passed,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify trajectory parity between NumPy reference and PyTorch backend.")
    parser.add_argument("--device", type=str, default="cpu", help="Target PyTorch device (cpu or cuda:0).")
    parser.add_argument("--audio-root", type=str, default=None, help="Optional MUSAN directory (uses synthetic signals if omitted).")
    parser.add_argument("--horizon", type=int, default=84, help="Number of iterations per parity case.")
    parser.add_argument("--out", type=str, default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    if args.audio_root:
        signals = [sig for _, sig in islice(load_audio_records(args.audio_root), 2)]
    else:
        signals = [
            np.random.default_rng(i).normal(size=512) + 1j * np.random.default_rng(i + 20).normal(size=512)
            for i in range(2)
        ]

    cases = []
    for sig in signals:
        for profile in STFT_PROFILES:
            for kind in PARITY_INITS:
                res = check_one_case(sig, profile, kind, args.device, horizon=args.horizon)
                cases.append(res)
                status_tag = "PASS" if res["passed"] else "FAIL"
                print(
                    f"[{status_tag}] {profile:8s} | {kind:18s} | "
                    f"max_state_err={res['max_state_error']:.2e} | calls={res['actual_calls']}"
                )

    summary = dict(
        device=args.device,
        synthetic=(args.audio_root is None),
        horizon=args.horizon,
        passed=sum(c["passed"] for c in cases),
        total=len(cases),
        status="PASS" if all(c["passed"] for c in cases) else "FAIL",
        cases=cases,
    )
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    assert summary["status"] == "PASS", "Parity check failed"
    print(f"Parity check PASSED ({summary['passed']}/{summary['total']} cases on {args.device}).")


if __name__ == "__main__":
    main()
