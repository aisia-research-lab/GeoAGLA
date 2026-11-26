"""Independent raw verification of matched-budget ledgers.

Checks, for the files written by matched_budget_benchmark.py (and their .blocks.jsonl traces):
  * no duplicate keys and a complete grid: every start key has every budget and every method;
  * all methods on a start key share the same initial-state hash (paired starts);
  * success arithmetic: success == (orbit <= 0.1 e0 and mag <= 1e-5);
  * exact budget selection: each budget row is the last fully committed checkpoint within its cap;
  * projection accounting: per checkpoint, calls grow by K for ordinary steps and by
    K(1 + fallback) + 1 for Online blocks, with the fallback rule matching the descent test;
  * monotone traces that reach the largest cap.
Optionally --expected-keys N also checks the number of start keys (192 per seed in the manuscript).

Usage:
  python -m experiments.audit_ledger --raw outputs/calls_audio.jsonl --mode calls --expected-keys 192
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.common import METHODS


def audit(raw_files: list[str], mode: str, expected_keys: int | None = None) -> dict:
    field = "calls" if mode == "calls" else "solver_seconds"
    rows: dict[tuple, dict] = {}
    traces: dict[tuple, dict] = {}
    for fn in raw_files:
        with Path(fn).open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                assert r["budget_kind"] == mode, f"wrong budget kind in {fn}"
                k = (r["source_id"], r["profile"], r["init"], r["seed"], r["budget"], r["method"])
                assert k not in rows, f"duplicate record {k}"
                rows[k] = r
        with Path(fn + ".blocks.jsonl").open(encoding="utf-8") as f:
            for line in f:
                t = json.loads(line)
                k = (t["source_id"], t["profile"], t["init"], t["seed"], t["method"])
                assert k not in traces, f"duplicate trace {k}"
                traces[k] = t

    starts = sorted({k[:4] for k in rows})
    budgets = sorted({k[4] for k in rows})
    if expected_keys is not None:
        assert len(starts) == expected_keys, f"{len(starts)} start keys, expected {expected_keys}"
    missing = [s + (b, m) for s in starts for b in budgets for m in METHODS if s + (b, m) not in rows]
    assert not missing, f"{len(missing)} missing records, e.g. {missing[:3]}"

    for s in starts:
        hashes = {rows[s + (budgets[0], m)]["initial_hash"] for m in METHODS}
        assert len(hashes) == 1, f"unpaired initial states at {s}"

    skipped = 0
    for k, r in rows.items():
        if r["status"] != "ok":
            skipped += 1
            continue
        assert r["success"] == (r["orbit"] <= 0.1 * r["initial_error"] and r["mag"] <= 1e-5), f"success arithmetic {k}"
        assert r[field] <= r["budget"], f"budget exceeded {k}"
        tr = traces[k[:4] + (k[5],)]
        last = [x for x in tr["rows"] if x[field] <= r["budget"]][-1]
        assert all(r[c] == last[c] for c in ("iteration", "calls", "orbit", "mag", "success")), f"budget selection {k}"

    for k, tr in traces.items():
        rr = tr["rows"]
        assert rr[0]["calls"] == 0 and rr[0]["iteration"] == 0, f"trace start {k}"
        assert rr[-1][field] >= max(budgets), f"trace does not reach the largest cap {k}"
        online = k[4].startswith("Online")
        blocks = {b["iteration"]: b for b in tr["blocks"]}
        assert len(blocks) == len(tr["blocks"]), f"duplicate block {k}"
        for x, y in zip(rr, rr[1:]):
            assert y["calls"] > x["calls"] and y["iteration"] > x["iteration"], f"non-monotone trace {k}"
            assert y["solver_seconds"] >= x["solver_seconds"], f"non-monotone time {k}"
            K = y["iteration"] - x["iteration"]
            b = blocks.get(y["iteration"])
            assert (b is not None) == (online and x["iteration"] >= 12), f"block log mismatch {k}"
            if b is None:
                assert y["calls"] - x["calls"] == K, f"call accounting {k}"
                continue
            c = b["candidate"]
            accept = c["phi_end"] + 1e-4 * c["D2"] <= c["phi_start"] + 1e-14 * max(1.0, abs(c["phi_start"]))
            assert b["K"] == K and c["accepted"] == accept, f"descent test {k}"
            assert b["fallback"] == (not c["accepted"] and k[4] != "OnlineNoFallback"), f"fallback rule {k}"
            assert b["diagnostic_G"] == 1 and y["calls"] - x["calls"] == K * (1 + int(b["fallback"])) + 1, f"Online call accounting {k}"

    return {
        "status": "PASS",
        "mode": mode,
        "records": len(rows),
        "skipped_records": skipped,
        "start_keys": len(starts),
        "budgets": budgets,
        "traces": len(traces),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Independent audit of raw matched-budget ledgers.")
    parser.add_argument("--raw", nargs="+", required=True, help="Raw JSONL ledgers (each with a .blocks.jsonl companion).")
    parser.add_argument("--mode", choices=["calls", "wall"], required=True)
    parser.add_argument("--expected-keys", type=int, default=None, help="Required number of start keys.")
    parser.add_argument("--out", type=str, default=None, help="Optional JSON report path.")
    args = parser.parse_args()
    report = audit(args.raw, args.mode, args.expected_keys)
    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
