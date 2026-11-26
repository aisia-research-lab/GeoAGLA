"""Aggregate raw matched-budget ledgers into summary tables, paired bootstrap CIs, and diagnostics.

Usage:
  python experiments/benchmark_analysis.py --raw outputs/calls_audio.jsonl --mode calls --out outputs/calls_summary
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from experiments.common import CALL_BUDGETS, METHODS, WALL_BUDGETS


def _population_of(init_kind: str) -> str:
    if init_kind == "random_phase":
        return "random"
    if init_kind == "signal_noise_0.1":
        return "signal_noise"
    return "standard"


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze raw matched-budget JSONL ledgers.")
    parser.add_argument("--raw", nargs="+", required=True, help="One or more raw JSONL files from matched_budget_benchmark.py.")
    parser.add_argument("--mode", choices=["calls", "wall"], required=True, help="Budget mode.")
    parser.add_argument("--out", type=str, required=True, help="Output directory for CSV tables.")
    parser.add_argument("--bootstrap-resamples", type=int, default=10000, help="Number of cluster bootstrap resamples.")
    args = parser.parse_args()

    dest = Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    mode = args.mode

    rows: dict[tuple, dict] = {}
    traces: dict[tuple, dict] = {}
    observed_budgets = set()
    observed_files = set()

    for fn in args.raw:
        with Path(fn).open("r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                assert r["budget_kind"] == mode
                key = (r["source_id"], r["profile"], r["init"], r["seed"], r["budget"], r["method"])
                assert key not in rows, f"Duplicate record: {key}"
                rows[key] = r
                observed_budgets.add(r["budget"])
                observed_files.add(r["source_id"])
                if r["status"] == "ok":
                    assert r["success"] == (r["orbit"] <= 0.1 * r["initial_error"] and r["mag"] <= 1e-5)
                    cap_val = r["calls"] if mode == "calls" else r["solver_seconds"]
                    assert cap_val <= r["budget"]

        blk_path = Path(str(fn) + ".blocks.jsonl")
        if blk_path.exists():
            with blk_path.open("r", encoding="utf-8") as bf:
                for line in bf:
                    tr = json.loads(line)
                    tkey = (tr["source_id"], tr["profile"], tr["init"], tr["seed"], tr["method"])
                    traces[tkey] = tr

    budgets = sorted(observed_budgets) if observed_budgets else (CALL_BUDGETS if mode == "calls" else WALL_BUDGETS)
    files = sorted(observed_files)
    rng = np.random.default_rng(2026)

    summary_rows: list[dict] = []
    paired_rows: list[dict] = []

    for b in budgets:
        for pop in ("standard", "signal_noise", "random"):
            keys = sorted({k[:4] for k in rows if k[4] == b and _population_of(k[2]) == pop})
            if not keys:
                continue
            n = len(keys)
            for m in METHODS:
                subset = [rows[k + (b, m)] for k in keys if (k + (b, m)) in rows]
                valid = [r for r in subset if r["status"] == "ok"]
                summary_rows.append(
                    dict(
                        budget=b,
                        population=pop,
                        method=m,
                        n=n,
                        success=sum(int(r["success"]) for r in subset),
                        failures=n - len(valid),
                        median_orbit=float(np.median([r["orbit"] for r in valid])) if valid else "",
                        median_mag=float(np.median([r["mag"] for r in valid])) if valid else "",
                        median_calls=float(np.median([r["calls"] for r in valid])) if valid else "",
                        median_solver_seconds=float(np.median([r["solver_seconds"] for r in valid])) if valid else "",
                    )
                )
            for m in METHODS[1:]:
                paired_keys = [k for k in keys if (k + (b, "Online")) in rows and (k + (b, m)) in rows]
                if not paired_keys:
                    continue
                dif = np.array([int(rows[k + (b, "Online")]["success"]) - int(rows[k + (b, m)]["success"]) for k in paired_keys])
                present_files = sorted({k[0] for k in paired_keys})
                cluster_means = np.array([dif[[k[0] == fl for k in paired_keys]].mean() for fl in present_files])
                boot_idx = rng.integers(0, len(present_files), (args.bootstrap_resamples, len(present_files)))
                ci = np.quantile(cluster_means[boot_idx].mean(axis=1), [0.025, 0.975])
                paired_rows.append(
                    dict(
                        budget=b,
                        population=pop,
                        comparison=f"Online minus {m}",
                        n=len(paired_keys),
                        delta_pp=float(100.0 * dif.mean()),
                        rescues=int(np.sum(dif == 1)),
                        losses=int(np.sum(dif == -1)),
                        ci_low=float(100.0 * ci[0]),
                        ci_high=float(100.0 * ci[1]),
                        clusters=len(present_files),
                    )
                )

    for fname, data in (("summary.csv", summary_rows), ("paired.csv", paired_rows)):
        if data:
            with (dest / fname).open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                writer.writeheader()
                writer.writerows(data)

    mech_rows: list[dict] = []
    for key, tr in traces.items():
        if not tr.get("blocks"):
            continue
        for subset_name, blocks in (
            ("all", tr["blocks"]),
            ("late", [b for b in tr["blocks"] if b["iteration"] >= 360]),
            ("local_proxy", [b for b in tr["blocks"] if b.get("orbit_proxy")]),
        ):
            if not blocks:
                continue
            eligible = [b for b in blocks if b.get("in_tolerance") is not None]
            mech_rows.append(
                dict(
                    source_id=key[0],
                    profile=key[1],
                    init=key[2],
                    seed=key[3],
                    method=key[4],
                    subset=subset_name,
                    blocks=len(blocks),
                    fallbacks=sum(int(b["fallback"]) for b in blocks),
                    safe_GLA=sum(int(b["committed_GLA"]) for b in blocks),
                    estimates=len(eligible),
                    inside_tolerance=sum(int(b["in_tolerance"]) for b in eligible),
                    exact_slack_failures=sum(int(b["committed"]["slack"] < 0) for b in blocks),
                    tolerant_failures=sum(int(not b["committed"]["accepted"]) for b in blocks),
                )
            )
    if mech_rows:
        with (dest / "mechanism.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(mech_rows[0].keys()))
            writer.writeheader()
            writer.writerows(mech_rows)

    report = dict(status="PASS", records=len(rows), traces=len(traces), clusters=len(files))
    (dest / "analysis_summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
