"""
09_e10r2f_event_repair_parallel.py
====================================
DECLARED MODIFICATION — new file, does NOT edit 07_e10r2f_event_repair.py.

Parallel + real-time-log version of the online-only event reconstruction
runner (Gate F2). Reuses UNCHANGED from 07_e10r2f_event_repair.py:
online_run(), save_checkpoint(), load_checkpoint(), ONLINE, TOL — imported
as a module, not copy-pasted. Only the outer control flow is new:

1. PARALLELISM: files processed by a pool of worker PROCESSES (default 6).
   Each file is an independent unit (fixed global_fi, independent audio/
   STFT/trajectory computation per file), so results are byte-identical to
   a sequential run — pure speed-up, not a change of method.

2. SAME CHECKPOINT FORMAT AS 07: uses the identical
   <out>/checkpoint/{run_rows_checkpoint.csv, event_rows_checkpoint.csv,
   progress.json} schema (via 07's own save_checkpoint/load_checkpoint
   functions). This means: if 07_e10r2f_event_repair.py was already run
   sequentially and interrupted (or is still running) against a given
   --out directory, pointing this script at the SAME --out will pick up
   exactly where it left off — no reprocessing, no data loss. Do not run
   07 and 09 against the same --out at the same time; stop 07 first
   (Ctrl+C), then run 09 with the same --out to continue in parallel.

3. REAL-TIME PROGRESS LOG: writes one line to BOTH stdout (flush=True,
   avoids the buffering problem seen when 07's output is piped through
   Tee-Object) and a dedicated log file the instant each file finishes.

Usage:
    python experiments/08_e10_robustness_mechanism_ablation/09_e10r2f_event_repair_parallel.py \
        --audio-dir D:\\path\\to\\MUSAN_ODD_202 \
        --locked-geometry experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv \
        --primary-ledger results/08_e10r2f_forensic/primary/e10r2_run_ledger.csv \
        --out results/08_e10r2f_forensic \
        --workers 6

Resume: rerun the identical command with the same --out (whether the prior
session used 07 sequentially, or this script). Already-completed files are
skipped automatically.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time, platform
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

_repair_path = Path(__file__).resolve().parent / "07_e10r2f_event_repair.py"


def _load_repair_module():
    spec = importlib.util.spec_from_file_location("e10r2f_event_repair_original", _repair_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def process_one_file(name, global_fi, wavs, gmap, cfg):
    """Per-file body identical to 07's main() inner loop, reusing 07's
    online_run(). Reloads the module fresh in each worker process (required
    for ProcessPoolExecutor on Windows, which spawns new interpreters)."""
    M = _load_repair_module()
    B = M.B
    from geometry_gla.operators.stft_fft import FFTAnalysisOperator
    online_run = M.online_run
    ONLINE = M.ONLINE

    rows, events = [], []
    x, _ = B.load_audio(wavs[name], cfg["target_sample_rate"], cfg["excerpt_length"])
    fi = global_fi % 2
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
                            n_fallback=int(sum(bool(b.get("fallback_used", not b.get("candidate_accepted", True) if v in ["online_fallback", "online_full"] else False)) for b in blocks)),
                        ))
                        for bi, b in enumerate(blocks):
                            cand_acc = bool(b.get("candidate_accepted", b.get("checkpoint_accepted", True)))
                            fb = bool(b.get("fallback_used", (not cand_acc) if v in ["online_fallback", "online_full"] else False))
                            ev = dict(
                                run_key=run_key, source_id=name, file=name, profile=P["id"],
                                init_type=init["kind"], init_kind=init["kind"], init_level=float(level), level=float(level),
                                seed=int(seed), variant=v, block_index=bi, lambda_plus=lp,
                                iteration_start=b.get("start_iter", 0), iteration_end=b.get("end_iter", 0),
                                lambda_raw=b.get("raw_current", np.nan), lambda_control=b.get("synth_edge", np.nan),
                                checkpoint_evaluated=True, checkpoint_accepted=cand_acc, checkpoint_rejected=not cand_acc,
                                fallback_used=fb
                            )
                            ev.update(b)
                            ev["source_id"] = name; ev["file"] = name
                            ev["init_type"] = init["kind"]; ev["init_level"] = float(level)
                            ev["iteration_start"] = b.get("start_iter", 0); ev["iteration_end"] = b.get("end_iter", 0)
                            ev["lambda_raw"] = b.get("raw_current", np.nan); ev["lambda_control"] = b.get("synth_edge", np.nan)
                            ev["checkpoint_evaluated"] = True; ev["checkpoint_accepted"] = cand_acc; ev["checkpoint_rejected"] = not cand_acc
                            ev["fallback_used"] = fb
                            events.append(ev)
    return name, rows, events


def log(msg: str, log_fh) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    log_fh.write(line + "\n")
    log_fh.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio-dir", required=True)
    ap.add_argument("--locked-geometry", required=True)
    ap.add_argument("--primary-ledger", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    progress_log = out / "logs" / "f2_progress.log"
    log_fh = open(progress_log, "a")

    M = _load_repair_module()
    B = M.B
    TOL = M.TOL
    save_checkpoint = M.save_checkpoint
    load_checkpoint = M.load_checkpoint

    cfg = json.loads((ROOT / "configs/phase2b_grid.json").read_text())
    if cfg["basin_success"]["final_magnitude_residual_max"] != 1e-5 or cfg["basin_success"]["final_orbit_ratio_max"] != 0.10:
        log("NO-GO: success threshold does not match canonical 1e-5 / 0.10", log_fh)
        sys.exit(1)

    geo = pd.read_csv(args.locked_geometry)
    gmap = {(r.file, r.profile): float(r.lambda_plus) for r in geo.itertuples()}
    primary = pd.read_csv(args.primary_ledger)
    if len(primary) != 28440:
        log(f"NO-GO: primary ledger has {len(primary)} rows, expected 28440", log_fh)
        sys.exit(1)
    pidx = primary.set_index(["run_key", "variant"])

    wavs = {p.name: p for p in Path(args.audio_dir).rglob("*.wav")}
    files = sorted(geo.file.unique())
    n_files = len(files)
    cp = out / "checkpoint"

    log(f"E10-R2F FORENSIC ONLINE EVENT RERUN (parallel, workers={args.workers})", log_fh)
    log(f"python={sys.version.splitlines()[0]}  platform={platform.platform()}", log_fh)
    log("success_mag_threshold = 1e-5  success_orbit_ratio_threshold = 0.10  seed_mode = historical_batch2", log_fh)
    log("locked_cases = 395  expected_online_rows = 18960  expected_event_rows = 834240", log_fh)

    rows, events, done = load_checkpoint(cp)
    log(f"Resuming: {len(done)}/{n_files} files already done (from checkpoint), "
        f"{n_files - len(done)} remaining. rows so far={len(rows)} events so far={len(events)}", log_fh)

    pending = [(gi, name) for gi, name in enumerate(files) if name not in done]

    if pending:
        t_start = time.time()
        n_done_this_session = 0
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            it = iter(pending)
            futures = {}
            for _ in range(min(args.workers, len(pending))):
                gi, name = next(it)
                futures[ex.submit(process_one_file, name, gi, wavs, gmap, cfg)] = name

            while futures:
                completed, _ = wait(futures, return_when=FIRST_COMPLETED)
                for fut in completed:
                    fname = futures.pop(fut)
                    try:
                        name, frows, fevents = fut.result()
                    except Exception as exc:
                        log(f"NO-GO: worker exception on file={fname}: {exc!r}", log_fh)
                        raise

                    rows.extend(frows)
                    events.extend(fevents)
                    done.add(name)
                    save_checkpoint(cp, rows, events, done)

                    n_done_this_session += 1
                    elapsed = time.time() - t_start
                    avg = elapsed / n_done_this_session
                    remaining = n_files - len(done)
                    eta_sec = avg * remaining / max(1, args.workers)
                    log(
                        f"file done: {name} | rows+={len(frows)} events+={len(fevents)} | "
                        f"progress {len(done)}/{n_files} | elapsed {elapsed/60:.1f}min | "
                        f"avg {avg:.1f}s/file | ETA ~{eta_sec/60:.1f}min remaining",
                        log_fh,
                    )
                    try:
                        gi2, name2 = next(it)
                        futures[ex.submit(process_one_file, name2, gi2, wavs, gmap, cfg)] = name2
                    except StopIteration:
                        pass
    else:
        log("All files already completed — skipping straight to validation/merge.", log_fh)

    rdf = pd.DataFrame(rows); edf = pd.DataFrame(events)
    log(f"All files processed — validating: rows={len(rdf)} events={len(edf)}", log_fh)

    if len(rdf) != 18960:
        log(f"NO-GO: online rows {len(rdf)} != 18960", log_fh); raise RuntimeError(f"online rows {len(rdf)} != 18960")
    if len(edf) != 834240:
        log(f"NO-GO: event rows {len(edf)} != 834240", log_fh); raise RuntimeError(f"event rows {len(edf)} != 834240")
    if rdf.duplicated(["run_key", "variant"]).any():
        log("NO-GO: duplicate online run keys", log_fh); raise RuntimeError("duplicate online run keys")
    if edf.duplicated(["run_key", "variant", "block_index"]).any():
        log("NO-GO: duplicate event keys", log_fh); raise RuntimeError("duplicate event keys")
    counts = edf.groupby(["run_key", "variant"]).size()
    if counts.min() != 44 or counts.max() != 44:
        log(f"NO-GO: events/run not exactly 44: min={counts.min()} max={counts.max()}", log_fh)
        raise RuntimeError(f"events/run not exactly 44: min={counts.min()} max={counts.max()}")

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
        q1 = float(r.q_fitted); q2 = float(p.q_fitted)
        qd = abs(q1 - q2) if np.isfinite(q1) and np.isfinite(q2) else (0.0 if (not np.isfinite(q1) and not np.isfinite(q2)) else float("inf"))
        ok = max(od, md, qd) <= TOL and sm
        comp.append(dict(run_key=r.run_key, variant=r.variant, primary_final_orbit=p.final_orbit_error, rerun_final_orbit=r.final_orbit_error,
            orbit_abs_diff=od, primary_final_mag=p.final_magnitude_residual, rerun_final_mag=r.final_magnitude_residual, mag_abs_diff=md,
            q_fitted_abs_diff=qd, primary_success=bool(p.success), rerun_success=bool(r.success), success_match=sm, status="PASS" if ok else "FAIL"))
    cdf = pd.DataFrame(comp)
    cdf.to_csv(out / "forensic_rerun/rerun_primary_equivalence.csv", index=False)

    n_fail = int((cdf.status != "PASS").sum())
    summary = {"expected_event_rows": 834240, "observed_event_rows": len(edf), "duplicate_event_keys": 0, "online_runs": len(rdf),
        "expected_events_per_run": 44, "min_events_per_run": int(counts.min()), "max_events_per_run": int(counts.max()),
        "rerun_primary_failures": n_fail, "status": "PASS" if n_fail == 0 else "FAIL"}
    (out / "audit/event_integrity_summary.json").write_text(json.dumps(summary, indent=2))

    # Also write the same full_run.log completion block that 07 produces, so
    # downstream deliverable packaging is identical regardless of which
    # runner (07 sequential or 09 parallel) actually finished the job.
    with (out / "logs/full_run.log").open("a") as f:
        f.write("E10-R2F FORENSIC ONLINE EVENT RERUN (parallel)\n")
        f.write("success_mag_threshold = 1e-5\nseed_mode = historical_batch2\n")
        f.write("locked_cases = 395\nexpected_online_rows = 18960\nexpected_event_rows = 834240\n")
        f.write(f"python={sys.version}\nplatform={platform.platform()}\n")
        f.write(f"online_forensic_rows = {len(rdf)}\nevent_rows = {len(edf)}\nrerun_primary_failures = {n_fail}\n")
        f.write(f"end={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        if n_fail == 0:
            f.write("E10-R2F COMPLETED\n")

    log_fh.close()
    if n_fail > 0:
        raise SystemExit("Rerun differs from primary ledger; STOP, do not overwrite primary.")
    print("E10-R2F F2 PASS: 18,960 online rows; 834,240 events; primary equivalence PASS")


if __name__ == "__main__":
    main()
