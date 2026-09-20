#!/usr/bin/env python3
"""Build canonical E6 case ledger from frozen H2 rate data and Online horizon audit data.
Section 4 (A1) of ICLR 2027 Next Experiment Handoff for Students A & B.
"""
from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import argparse
from pathlib import Path
import sys

# Ensure local scripts folder is in sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common import load_json, dump_json, write_csv, fnum

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_H2_PATHS = [
    ROOT / "data" / "frozen" / "h2_multi.json",
    ROOT.parent / "Phase 1 Runs" / "results" / "phase1c" / "h2_multi.json",
    ROOT.parent / "phase1_runs_from_kaggle" / "phase1c" / "h2_multi.json",
    ROOT.parent / "[2026_09_11] - ICLR experiment" / "handoff_final" / "phase1c" / "h2_multi.json",
]

DEFAULT_HZ_PATHS = [
    ROOT / "data" / "frozen" / "horizon_audit.json",
    ROOT.parent / "Phase 1 Runs" / "results" / "phase1er" / "horizon_audit.json",
    ROOT.parent / "[2026_09_11] - ICLR experiment" / "handoff_final" / "phase1er" / "horizon_audit.json",
]

def find_file(explicit: str | None, candidates: list[Path]) -> Path:
    if explicit and Path(explicit).exists():
        return Path(explicit)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"Could not locate required file. Tried explicit='{explicit}' and:\n" + "\n".join(str(p) for p in candidates))

def build_ledger(h2_path: str | Path, horizon_path: str | Path, out_dir: str | Path, horizon_val: int | None = None, denom_tol: float = 1e-8):
    h2_file = Path(h2_path)
    hz_file = Path(horizon_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Loading H2 data: {h2_file}")
    h2 = load_json(h2_file)
    print(f"Loading Horizon data: {hz_file}")
    hz = load_json(hz_file)
    hzrows = hz["rows"] if isinstance(hz, dict) and "rows" in hz else hz

    # Determine matched observation horizon
    controlled_horizons = [int(r.get("fit_hi", 0)) for r in h2 if r.get("fit_hi") is not None]
    H = horizon_val or (max(controlled_horizons) if controlled_horizons else 180)
    print(f"Using canonical observation horizon H = {H}")

    on = {(r["config"], int(r["seed"]), float(r["epsilon"])): r for r in hzrows if int(r["n_iter"]) == H}
    
    base = {}
    for r in h2:
        k = (r["config"], int(r["seed"]), float(r["epsilon"]))
        base.setdefault(k, {})[r["method"]] = r

    rows = []
    for k, m in sorted(base.items()):
        if not {"gla", "fgla_opt", "oracle"} <= set(m):
            continue
        g, f, o = m["gla"], m["fgla_opt"], m["oracle"]
        z = on.get(k, {})
        
        lp = float(g["lambda_plus"])
        lm = float(g["lambda_minus"])
        width = lp - lm
        gap = 1.0 - lp
        
        q_gla_pred = float(g["q_pred"])
        q_fgla_pred = float(f["q_pred"])
        q_oracle_pred = float(o["q_pred"])
        
        q_gla_obs = float(g["q_obs"]) if fnum(g.get("q_obs")) is not None else None
        q_fgla_obs = float(f["q_obs"]) if fnum(f.get("q_obs")) is not None else None
        q_oracle_obs = float(o["q_obs"]) if fnum(o.get("q_obs")) is not None else None
        
        q_online_obs = fnum(z.get("q_online"))
        q_fgla_online_hz = fnum(z.get("q_fgla"))
        
        d_oracle_pred = q_fgla_pred - q_oracle_pred
        d_oracle_obs = (q_fgla_obs - q_oracle_obs) if (q_fgla_obs is not None and q_oracle_obs is not None) else None
        d_online_obs = (q_fgla_obs - q_online_obs) if (q_fgla_obs is not None and q_online_obs is not None) else None
        
        # Oracle gain capture ratio
        r_capture = None
        r_capture_clipped = None
        if d_online_obs is not None and d_oracle_obs is not None:
            if d_oracle_obs > denom_tol:
                r_capture = d_online_obs / d_oracle_obs
                r_capture_clipped = min(1.0, max(0.0, r_capture))

        fit_window_str = f"{o.get('fit_lo')}-{o.get('fit_hi')}" if o.get("fit_lo") is not None else "adaptive_late"

        rows.append({
            "case_id": f"{k[0]}__s{k[1]}__e{k[2]:g}",
            "config": k[0],
            "seed": k[1],
            "epsilon_or_initialization": k[2],
            "lambda_minus": lm,
            "lambda_plus": lp,
            "spectral_width": width,
            "transverse_gap": gap,
            "q_gla_pred": q_gla_pred,
            "q_fgla_pred": q_fgla_pred,
            "q_oracle_pred": q_oracle_pred,
            "q_gla_obs": q_gla_obs,
            "q_fgla_obs": q_fgla_obs,
            "q_oracle_obs": q_oracle_obs,
            "q_online_obs": q_online_obs,
            "q_fgla_online_horizon": q_fgla_online_hz,
            "edge_estimate_final": z.get("final_edge"),
            "edge_rel_error_final": z.get("final_edge_rel_error"),
            "online_beats_fgla": z.get("beats"),
            "delta_oracle_pred": d_oracle_pred,
            "delta_oracle_obs": d_oracle_obs,
            "delta_online_obs": d_online_obs,
            "r_capture": r_capture,
            "r_capture_clipped": r_capture_clipped,
            "fit_window": fit_window_str,
            "fit_lo": o.get("fit_lo"),
            "fit_hi": o.get("fit_hi"),
            "horizon": H,
        })

    csv_path = out / "e6_case_ledger.csv"
    json_path = out / "e6_case_ledger.json"
    write_csv(rows, csv_path)
    dump_json(rows, json_path)
    print(f"[OK] Successfully built canonical E6 ledger: {len(rows)} cases saved to {csv_path}")
    return rows

def main():
    p = argparse.ArgumentParser(description="Build canonical E6 ledger from frozen H2 & horizon results")
    p.add_argument("--h2", default=None, help="Path to h2_multi.json")
    p.add_argument("--horizon", default=None, help="Path to horizon_audit.json")
    p.add_argument("--out", default=str(ROOT / "results" / "e6_geometry_opportunity"), help="Output directory")
    p.add_argument("--horizon-value", type=int, default=None, help="Matched observation horizon")
    p.add_argument("--denom-tol", type=float, default=1e-8, help="Denominator tolerance for R_capture")
    args = p.parse_args()

    h2_file = find_file(args.h2, DEFAULT_H2_PATHS)
    hz_file = find_file(args.horizon, DEFAULT_HZ_PATHS)
    build_ledger(h2_file, hz_file, args.out, args.horizon_value, args.denom_tol)

if __name__ == "__main__":
    main()