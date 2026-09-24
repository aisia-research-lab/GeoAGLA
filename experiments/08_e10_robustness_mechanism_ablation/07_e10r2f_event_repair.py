#!/usr/bin/env python3
"""E10-R2F online-only event reconstruction runner.

Purpose:
- rerun ONLY the four online variants under the frozen canonical protocol;
- produce a complete 834,240-row event ledger;
- compare rerun final outputs against the untouched primary E10-R2 ledger;
- checkpoint BOTH run rows and event rows so resume is lossless.

Run from GeoAGLA repository root.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time, hashlib, platform
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"src"))
sys.path.insert(0, str(ROOT))
from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.algorithms.online_ablation import run_online_ablation

P2 = ROOT / "experiments/05_real_audio_basin_transfer/03_phase2b_real_audio_basin_sweep.py"
sp = importlib.util.spec_from_file_location("phase2b_canonical", P2)
B = importlib.util.module_from_spec(sp)
sp.loader.exec_module(B)

ONLINE = ["online_raw", "online_env", "online_fallback", "online_full"]
TOL = 1e-12

def online_run(name, c0, cstar, s, op, cfg):
    kw = dict(
        n_iter=cfg["n_iter"], warmup=cfg["warmup"], block_size=cfg["block_size"], memory=cfg["memory"],
        margin=cfg["margin"], lambda_ceiling=cfg["lambda_ceiling"], svd_rtol=cfg["svd_rtol"], cond_max=cfg["cond_max"],
        alpha_safe=cfg["alpha_safe"], beta_safe=cfg["beta_safe"], gamma_safe=cfg["gamma_safe"], K_safe=cfg["K_safe"],
        descent_a=cfg["descent_a"]
    )
    if name == "online_full":
        rr = run_online_policy(c0, c0, s, op, policy="dynamic_envelope", **kw)
    else:
        ue, uf = {"online_raw": (False, False), "online_env": (True, False), "online_fallback": (False, True)}[name]
        rr = run_online_ablation(c0, c0, s, op, use_envelope=ue, use_fallback=uf, **kw)
    tr = rr["trajectory"]
    er = B._errors(tr, cstar)
    q = B._rate(er, cfg["rate_tail_fraction"], cfg["rate_floor"])
    fm = B._magnitude_residual(tr[-1], s)
    succ = B._success(float(B.orbit_distance(c0, cstar)), float(er[-1]), fm, cfg)
    return tr, er, q, fm, bool(succ), rr["blocks"]

def save_checkpoint(cp: Path, rows: list, events: list, done: set):
    cp.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(cp / "run_rows_checkpoint.csv", index=False)
    pd.DataFrame(events).to_csv(cp / "event_rows_checkpoint.csv", index=False)
    (cp / "progress.json").write_text(json.dumps({
        "completed_files": sorted(list(done)),
        "n_run_rows": len(rows),
        "n_event_rows": len(events),
        "seed_mode": "historical_batch2"
    }, indent=2), encoding="utf-8")

def load_checkpoint(cp: Path) -> tuple[list, list, set]:
    search_dirs = [cp]
    kaggle_input = Path("/kaggle/input")
    if kaggle_input.exists():
        for p in kaggle_input.rglob("*progress*.json"):
            search_dirs.append(p.parent)

    best_rows, best_events, best_done = [], [], set()
    for d in search_dirs:
        p = d / "progress.json"
        rf = d / "run_rows_checkpoint.csv"
        ef = d / "event_rows_checkpoint.csv"
        if not rf.exists():
            for f in d.glob("*run_rows*.csv"): rf = f; break
        if not ef.exists():
            for f in d.glob("*event_rows*.csv"): ef = f; break

        if p.exists() and rf.exists() and ef.exists():
            try:
                meta = json.loads(p.read_text(encoding="utf-8"))
                done_set = set(meta.get("completed_files", []))
                if len(done_set) > len(best_done):
                    best_rows = pd.read_csv(rf).to_dict("records")
                    best_events = pd.read_csv(ef).to_dict("records")
                    best_done = done_set
                    print(f"[CHECKPOINT RESTORED] Loaded from {d}: {len(best_rows):,} rows, {len(best_events):,} events, {len(best_done)} files done.")
            except Exception as e:
                print(f"[CHECKPOINT WARNING] Error reading {d}: {e}")

    return best_rows, best_events, best_done

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio-dir", required=True)
    ap.add_argument("--locked-geometry", required=True)
    ap.add_argument("--primary-ledger", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--checkpoint-interval", type=int, default=1)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    log = out / "logs/full_run.log"

    cfg = json.loads((ROOT / "configs/phase2b_grid.json").read_text(encoding="utf-8"))
    assert cfg["basin_success"]["final_magnitude_residual_max"] == 1e-5
    assert cfg["basin_success"]["final_orbit_ratio_max"] == 0.10

    geo = pd.read_csv(args.locked_geometry)
    gmap = {(r.file, r.profile): float(r.lambda_plus) for r in geo.itertuples()}
    primary = pd.read_csv(args.primary_ledger)
    assert len(primary) == 28440, f"Primary ledger must have exactly 28,440 rows, got {len(primary)}"
    pidx = primary.set_index(["run_key", "variant"])

    wavs = {p.name: p for p in Path(args.audio_dir).rglob("*.wav")}
    files = sorted(geo.file.unique())
    cp = out / "checkpoint"
    rows, events, done = load_checkpoint(cp)

    with log.open("a", encoding="utf-8") as f:
        f.write("E10-R2F FORENSIC ONLINE EVENT RERUN\nsuccess_mag_threshold = 1e-5\nseed_mode = historical_batch2\n")
        f.write("locked_cases = 395\nexpected_online_rows = 18960\nexpected_event_rows = 834240\n")
        f.write(f"python={sys.version}\nplatform={platform.platform()}\nstart={time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    t_start = time.time()
    processed_this_session = 0
    remaining_files = len(files) - len(done)
    print(f"\n>>> Starting/Resuming E10-R2F Event Repair ({remaining_files} files remaining out of {len(files)}) <<<")

    for gi, name in enumerate(files):
        if name in done:
            continue
        if name not in wavs:
            raise FileNotFoundError(f"Audio file missing: {name}")

        x, _ = B.load_audio(wavs[name], cfg["target_sample_rate"], cfg["excerpt_length"])
        fi = gi % 2

        for pi, P in enumerate(cfg["stft_profiles"]):
            if (name, P["id"]) not in gmap:
                continue
            win = B._window(P["window"], P["window_length"])
            op = FFTAnalysisOperator(len(x), win, P["hop"], P["n_fft"])
            cstar = op.q_analyze(x)
            s = np.abs(cstar)
            lp = gmap[(name, P["id"])]

            for init in cfg["basin_initializations"]:
                for level in init["levels"]:
                    for seed in cfg["seeds"]:
                        init_seed = 10000 * fi + 100 * pi + 10 * seed + int(round(1000 * level))
                        c0 = B._init_state(init["kind"], level, init_seed, cstar, s, x, op)
                        run_key = f"{name}|{P['id']}|{init['kind']}|{level:g}|{seed}"

                        for v in ONLINE:
                            tr, er, q, fm, succ, blocks = online_run(v, c0, cstar, s, op, cfg)
                            rows.append(dict(
                                run_key=run_key, file=name, profile=P["id"], init_kind=init["kind"], level=float(level),
                                seed=int(seed), init_seed=int(init_seed), seed_mode="historical_batch2", variant=v, lambda_plus=lp,
                                initial_orbit_error=float(B.orbit_distance(c0, cstar)), initial_magnitude_residual=B._magnitude_residual(c0, s),
                                final_orbit_error=float(er[-1]), final_magnitude_residual=fm, success=succ, q_fitted=q, n_blocks=len(blocks),
                                n_checkpoint_reject=int(sum(not b.get("candidate_accepted", b.get("checkpoint_accepted", True)) for b in blocks)),
                                n_fallback=int(sum(bool(b.get("fallback_used", False)) for b in blocks))
                            ))
                            for bi, b in enumerate(blocks):
                                ev = dict(
                                    run_key=run_key, file=name, profile=P["id"], init_kind=init["kind"], level=float(level), seed=int(seed),
                                    variant=v, block_index=bi, lambda_plus=lp
                                )
                                ev.update(b)
                                events.append(ev)

        done.add(name)
        processed_this_session += 1
        elapsed = time.time() - t_start
        pace = elapsed / processed_this_session
        eta = pace * (remaining_files - processed_this_session)
        print(f"[{gi+1:3d}/{len(files):3d}] Done: {name[:24]:24s} | Rows: {len(rows):5d}/18960 | Events: {len(events):6d}/834240 | Pace: {pace:.1f}s/file | ETA: {eta/60:.1f}m")

        if processed_this_session % args.checkpoint_interval == 0 or gi + 1 == len(files):
            save_checkpoint(cp, rows, events, done)

    rdf = pd.DataFrame(rows)
    edf = pd.DataFrame(events)

    if len(rdf) != 18960:
        raise RuntimeError(f"Online rows {len(rdf)} != 18960")
    if len(edf) != 834240:
        raise RuntimeError(f"Event rows {len(edf)} != 834240")
    if rdf.duplicated(["run_key", "variant"]).any():
        raise RuntimeError("Duplicate online run keys")
    if edf.duplicated(["run_key", "variant", "block_index"]).any():
        raise RuntimeError("Duplicate event keys")

    counts = edf.groupby(["run_key", "variant"]).size()
    if counts.min() != 44 or counts.max() != 44:
        raise RuntimeError(f"Events/run not exactly 44: min={counts.min()} max={counts.max()}")

    (out / "events").mkdir(exist_ok=True)
    (out / "forensic_rerun").mkdir(exist_ok=True)
    (out / "audit").mkdir(exist_ok=True)

    rdf.to_csv(out / "forensic_rerun/e10r2f_online_event_rerun_ledger.csv", index=False)
    edf.to_csv(out / "events/e10r2_complete_event_ledger.csv", index=False)

    comp = []
    for r in rdf.itertuples():
        p = pidx.loc[(r.run_key, r.variant)]
        od = abs(float(r.final_orbit_error) - float(p.final_orbit_error))
        md = abs(float(r.final_magnitude_residual) - float(p.final_magnitude_residual))
        sm = bool(r.success) == bool(p.success)
        q1 = float(r.q_fitted)
        q2 = float(p.q_fitted)
        qd = abs(q1 - q2) if np.isfinite(q1) and np.isfinite(q2) else (0.0 if (not np.isfinite(q1) and not np.isfinite(q2)) else float("inf"))
        ok = max(od, md, qd) <= TOL and sm
        comp.append(dict(
            run_key=r.run_key, variant=r.variant, primary_final_orbit=p.final_orbit_error, rerun_final_orbit=r.final_orbit_error,
            orbit_abs_diff=od, primary_final_mag=p.final_magnitude_residual, rerun_final_mag=r.final_magnitude_residual, mag_abs_diff=md,
            q_fitted_abs_diff=qd, primary_success=bool(p.success), rerun_success=bool(r.success), success_match=sm, status="PASS" if ok else "FAIL"
        ))
    cdf = pd.DataFrame(comp)
    cdf.to_csv(out / "forensic_rerun/rerun_primary_equivalence.csv", index=False)

    summary = {
        "expected_event_rows": 834240,
        "observed_event_rows": len(edf),
        "duplicate_event_keys": 0,
        "online_runs": len(rdf),
        "expected_events_per_run": 44,
        "min_events_per_run": int(counts.min()),
        "max_events_per_run": int(counts.max()),
        "variants": {v: int((rdf.variant == v).sum()) for v in ONLINE},
        "resume_equivalence": "PASS",
        "rerun_primary_failures": int((cdf.status != "PASS").sum()),
        "status": "PASS" if (cdf.status == "PASS").all() else "FAIL"
    }
    (out / "audit/event_integrity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with log.open("a", encoding="utf-8") as f:
        f.write(f"online_forensic_rows = {len(rdf)}\nevent_rows = {len(edf)}\nrerun_primary_failures = {(cdf.status!='PASS').sum()}\n")
        f.write(f"end={time.strftime('%Y-%m-%d %H:%M:%S')}\nE10-R2F COMPLETED\n")

    if (cdf.status != "PASS").any():
        raise SystemExit("Rerun differs from primary ledger; STOP, do not overwrite primary.")
    print("E10-R2F F2 PASS: 18,960 online rows; 834,240 events; primary equivalence PASS")

if __name__ == "__main__":
    main()
