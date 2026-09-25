#!/usr/bin/env python3
"""Freeze deterministic held-out geometry grid specification and write SHA-256 checksum.
Section 6 (A3) of ICLR 2027 Next Experiment Handoff for Students A & B.
"""
from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import argparse
import random
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common import load_json, dump_json, sha256_file

ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "experiments" else Path(__file__).resolve().parents[1]


def freeze_heldout_grid(spec_path: str | Path, out_path: str | Path, sha_path: str | Path | None = None):
    spec_file = Path(spec_path)
    out_file = Path(out_path)
    spec = load_json(spec_file)

    seed = int(spec.get("seed", 20270911))
    n_cases = int(spec.get("n_cases", 36))
    dimensions = spec["dimensions"]
    window_lengths = spec["window_lengths"]
    hops = spec["hops"]
    windows = spec["windows"]
    case_seeds = spec["case_seeds"]
    epsilons = spec["epsilons"]

    rng = random.Random(seed)
    cases = []
    for i in range(n_cases):
        N = rng.choice(dimensions)
        valid_w = [w for w in window_lengths if w <= N]
        W = rng.choice(valid_w)
        valid_h = [h for h in hops if h <= W]
        hop = rng.choice(valid_h)
        window = rng.choice(windows)
        case_seed = rng.choice(case_seeds)
        eps = rng.choice(epsilons)
        cases.append({
            "case_id": f"H{i:03d}",
            "N": N,
            "window": window,
            "W": W,
            "hop": hop,
            "n_fft": W,
            "seed": case_seed,
            "epsilon": eps,
        })

    manifest = {
        "schema_version": 1,
        "frozen": True,
        "seed": seed,
        "n_cases": len(cases),
        "cases": cases,
        "note": spec.get("note", "Held-out geometry manifest frozen before method evaluation."),
    }

    out_file.parent.mkdir(parents=True, exist_ok=True)
    dump_json(manifest, out_file)
    digest = sha256_file(out_file)

    if sha_path is not None:
        sha_file = Path(sha_path)
        sha_file.parent.mkdir(parents=True, exist_ok=True)
        sha_file.write_text(f"{digest}  {out_file.name}\n")

    # Also keep e6_heldout_geometry.json in sync
    alias_path = out_file.parent / "e6_heldout_geometry.json"
    dump_json(manifest, alias_path)

    print(f"[OK] Frozen {len(cases)} held-out cases to {out_file}")
    print(f"     SHA256: {digest}")
    return manifest, digest


def main():
    parser = argparse.ArgumentParser(description="Freeze held-out geometry grid")
    parser.add_argument("--spec", default=str(ROOT / "configs" / "heldout_grid_spec.json"))
    parser.add_argument("--out", default=str(ROOT / "configs" / "e6_heldout_manifest_frozen.json"))
    parser.add_argument("--sha", default=str(ROOT / "configs" / "heldout_manifest.sha256"))
    args = parser.parse_args()

    freeze_heldout_grid(args.spec, args.out, args.sha)


if __name__ == "__main__":
    main()