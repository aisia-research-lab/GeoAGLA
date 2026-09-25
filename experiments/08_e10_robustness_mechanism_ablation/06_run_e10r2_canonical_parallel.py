"""
06_run_e10r2_canonical_parallel.py
====================================
DECLARED MODIFICATION — new file, does NOT edit 04_run_e10r2_canonical.py
or 05_run_e10r2_checkpointed.py.

Adds two things on top of the checkpoint wrapper's per-file granularity:

1. PARALLELISM: files are processed by a pool of worker PROCESSES
   (default 6). Each file is an independent unit (fixed global_fi,
   independent audio/STFT/trajectory computation) so results are byte-
   identical to a sequential run — this is pure speed-up, not a change of
   method. Verified: process_one_file() below is the exact same function
   body as in 05_run_e10r2_checkpointed.py, calling the same canonical
   run_variant()/VARIANTS from 04_run_e10r2_canonical.py.

2. REAL-TIME PROGRESS LOG: unlike 05's batch-level logging (silent until
   an entire batch of files finishes), this script writes ONE line to
   BOTH stdout and a log file the instant each individual file finishes —
   with elapsed time, files done / total, average time/file, and an ETA.
   This is what fixes the "log looks frozen" problem seen on Kaggle: run
   this script and `Get-Content -Wait logs\\progress.log` (or `tail -f` on
   Linux/Mac) in a second window to watch it live.

Checkpointing is per FILE (finer-grained than 05's per-BATCH), so an
interrupted run resumes from the exact file it left off at, not from the
start of a whole batch.

Usage:
    python experiments/08_e10_robustness_mechanism_ablation/06_run_e10r2_canonical_parallel.py \
        --audio-dir D:\\path\\to\\MUSAN_ODD_202 \
        --locked-geometry experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv \
        --out results/08_e10r2_canonical_parallel \
        --seed-mode historical_batch2 \
        --workers 6

Resume: rerun the identical command with the same --out. Already-completed
files are skipped; only remaining files are (re)submitted to the pool.
"""
from __future__ import annotations
import sys, json, csv, argparse, importlib.util, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

_e10r2_path = Path(__file__).resolve().parent / "04_run_e10r2_canonical.py"


def _load_canonical():
    spec = importlib.util.spec_from_file_location("e10r2_canonical_original", _e10r2_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def process_one_file(name, global_fi, pmap, gmap, C):
    """Identical body to 05_run_e10r2_checkpointed.py's process_one_file —
    imports the canonical module fresh in each worker process (required for
    ProcessPoolExecutor on Windows, which spawns fresh interpreters)."""
    E = _load_canonical()
    B = E.B
    FFTAnalysisOperator = E.FFTAnalysisOperator
    run_variant = E.run_variant
    VARIANTS = E.VARIANTS

    rows, events = [], []
    if name not in pmap:
        raise FileNotFoundError(name)
    path = pmap[name]
    x, meta = B.load_audio(path, C["target_sample_rate"], C["excerpt_length"])
    fi = global_fi % 2  # seed-mode historical_batch2 (only supported mode)
    for pi, P in enumerate(C["stft_profiles"]):
        key = (name, P["id"])
        if key not in gmap:
            continue
        win = B._window(P["window"], P["window_length"])
        op = FFTAnalysisOperator(len(x), win, P["hop"], P["n_fft"])
        cstar = op.q_analyze(x)
        s = np.abs(cstar)
        xstar = x
        lambda_true = gmap[key]
        for init in C["basin_initializations"]:
            for level in init["levels"]:
                for seed in C["seeds"]:
                    init_seed = 10000 * fi + 100 * pi + 10 * seed + int(round(1000 * level))
                    c0 = B._init_state(init["kind"], level, init_seed, cstar, s, xstar, op)
                    init_err = float(B.orbit_distance(c0, cstar))
                    init_mag = B._magnitude_residual(c0, s)
                    run_key = f'{name}|{P["id"]}|{init["kind"]}|{level:g}|{seed}'
                    for v in VARIANTS:
                        tr, er, q, fm, succ, blocks = run_variant(v, c0, cstar, s, op, lambda_true, C)
                        rows.append(dict(
                            run_key=run_key, file=name, profile=P["id"], init_kind=init["kind"],
                            level=float(level), seed=int(seed), init_seed=int(init_seed),
                            seed_mode="historical_batch2", variant=v, lambda_true=lambda_true,
                            initial_orbit_error=init_err, initial_magnitude_residual=init_mag,
                            final_orbit_error=float(er[-1]), final_magnitude_residual=fm,
                            success=bool(succ), q_fitted=q, n_blocks=len(blocks),
                        ))
                        for b in blocks:
                            events.append(dict(run_key=run_key, variant=v, lambda_true=lambda_true, **b))
    return name, global_fi, rows, events


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    fields = sorted(set().union(*(r.keys() for r in rows)))
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def log(msg: str, log_fh) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    log_fh.write(line + "\n")
    log_fh.flush()


def capture_reproducibility_manifest(out_dir: Path, logs_dir: Path, args_dict: dict) -> dict:
    """Records everything needed to reproduce this run later: exact command,
    environment, and SHA256 of every canonical file actually used. Written
    BEFORE any computation starts, so it survives even a crash on file 1."""
    import platform, subprocess, hashlib

    manifest = {
        "run_type": "E10-R2 canonical, parallel checkpointed",
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "args": args_dict,
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count_logical": __import__("os").cpu_count(),
    }

    try:
        freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                                 capture_output=True, text=True, timeout=60).stdout
        (logs_dir / "e10r2_pip_freeze.txt").write_text(freeze)
        manifest["pip_freeze_file"] = "logs/e10r2_pip_freeze.txt"
    except Exception as exc:
        manifest["pip_freeze_error"] = repr(exc)

    hash_files = {
        "04_run_e10r2_canonical.py": ROOT / "experiments/08_e10_robustness_mechanism_ablation/04_run_e10r2_canonical.py",
        "06_run_e10r2_canonical_parallel.py": Path(__file__).resolve(),
        "phase2b_grid.json": ROOT / "configs/phase2b_grid.json",
        "e10r_locked_geometry_395.csv": Path(args_dict["locked_geometry"]),
        "online_safe.py": ROOT / "src/geometry_gla/algorithms/online_safe.py",
        "minimax.py": ROOT / "src/geometry_gla/algorithms/minimax.py",
        "ritz.py": ROOT / "src/geometry_gla/estimators/ritz.py",
        "checkpoint.py": ROOT / "src/geometry_gla/safeguards/checkpoint.py",
        "03_phase2b_real_audio_basin_sweep.py": ROOT / "experiments/05_real_audio_basin_transfer/03_phase2b_real_audio_basin_sweep.py",
    }
    sha = {}
    for label, p in hash_files.items():
        p = Path(p)
        sha[label] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "MISSING"
    manifest["sha256"] = sha
    (logs_dir / "e10r2_SHA256SUMS.txt").write_text(
        "\n".join(f"{h}  {label}" for label, h in sha.items()) + "\n"
    )

    # Freeze a copy of the config/population actually used, in case the
    # live files are edited later — this is the exact grid this run used.
    frozen_dir = out_dir / "_frozen_inputs"
    frozen_dir.mkdir(parents=True, exist_ok=True)
    import shutil as _shutil
    _shutil.copy(ROOT / "configs/phase2b_grid.json", frozen_dir / "phase2b_grid.json")
    _shutil.copy(args_dict["locked_geometry"], frozen_dir / "e10r_locked_geometry_395.csv")
    manifest["frozen_inputs_dir"] = str(frozen_dir)

    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def load_manifest(ckpt_dir: Path) -> dict:
    mf = ckpt_dir / "_manifest.json"
    if mf.exists():
        return json.loads(mf.read_text())
    return {"completed_files": []}


def save_manifest(ckpt_dir: Path, manifest: dict) -> None:
    (ckpt_dir / "_manifest.json").write_text(json.dumps(manifest, indent=2))


def safe_name(name: str) -> str:
    return name.replace("/", "_").replace("\\", "_").replace(".", "_")


def merge_and_validate(ckpt_dir: Path, out_dir: Path, G: pd.DataFrame, expected_rows: int) -> None:
    all_rows, all_events = [], []
    for f in ckpt_dir.glob("file_*.rows.csv"):
        if f.stat().st_size > 0:
            all_rows.append(pd.read_csv(f))
    for f in ckpt_dir.glob("file_*.events.csv"):
        if f.stat().st_size > 0:
            all_events.append(pd.read_csv(f))
    L = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    Ev = pd.concat(all_events, ignore_index=True) if all_events else pd.DataFrame()

    if len(L) != expected_rows:
        raise RuntimeError(f"closure cardinality failed: {len(L)} != {expected_rows} — resume the same command.")
    if not (L.groupby("run_key").variant.nunique() == 6).all():
        raise RuntimeError("some run_key missing one or more of the 6 variants")
    if L.duplicated(["run_key", "variant"]).sum() != 0:
        raise RuntimeError("duplicate (run_key, variant) rows found")
    pairs = set(zip(L.file, L.profile))
    if pairs != set(zip(G.file, G.profile)):
        raise RuntimeError("ledger (file, profile) pairs do not match frozen locked population")

    out_dir.mkdir(parents=True, exist_ok=True)
    L.to_csv(out_dir / "e10r2_run_ledger.csv", index=False)
    L.to_json(out_dir / "e10r2_run_ledger.json", orient="records", indent=2)
    if len(Ev):
        Ev.to_csv(out_dir / "e10r2_event_ledger.csv", index=False)
    else:
        (out_dir / "e10r2_event_ledger.csv").write_text("")
    print("PASS: rows", len(L), "paired instances", len(L) // 6, "locked geometry cases", len(G))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio-dir", required=True)
    ap.add_argument("--locked-geometry",
                     default=str(ROOT / "experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv"))
    ap.add_argument("--out", default=str(ROOT / "results/08_e10r2_canonical_parallel"))
    ap.add_argument("--seed-mode", choices=["historical_batch2"], default="historical_batch2")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()

    out_dir = Path(a.out)
    ckpt_dir = out_dir / "_files"
    logs_dir = ROOT / "logs"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_fh = open(logs_dir / "e10r2_progress.log", "a")

    run_manifest = capture_reproducibility_manifest(out_dir, logs_dir, vars(a))

    E = _load_canonical()
    C = json.loads((ROOT / "configs/phase2b_grid.json").read_text())

    log("E10-R2 CANONICAL FINAL FREEZE RUN (parallel, workers=%d)" % a.workers, log_fh)
    log(f"reproducibility manifest written to {out_dir / 'run_manifest.json'}", log_fh)
    log(f"SHA256SUMS written to {logs_dir / 'e10r2_SHA256SUMS.txt'}", log_fh)
    log(f"success_mag_threshold = {C['basin_success']['final_magnitude_residual_max']}", log_fh)
    log(f"success_orbit_ratio_threshold = {C['basin_success']['final_orbit_ratio_max']}", log_fh)
    if C['basin_success']['final_magnitude_residual_max'] != 1e-5 or C['basin_success']['final_orbit_ratio_max'] != 0.10:
        log("NO-GO: success threshold does not match canonical 1e-5 / 0.10", log_fh)
        sys.exit(1)

    G = pd.read_csv(a.locked_geometry)
    gmap = {(r.file, r.profile): float(r.lambda_plus) for r in G.itertuples()}
    expected_rows = len(G) * 12 * 6
    log(f"locked_cases={len(G)} expected_run_keys={len(G)*12} expected_rows={expected_rows}", log_fh)

    paths = sorted(p for p in Path(a.audio_dir).rglob("*") if p.is_file() and p.suffix.lower() == ".wav")
    pmap = {p.name: p for p in paths}
    missing = sorted(set(G.file) - set(pmap))
    if missing:
        log(f"NO-GO: missing {len(missing)} audio files: {missing}", log_fh)
        sys.exit(1)

    files_sorted = sorted(set(G.file))  # FIXED order — identical to 04/05
    n_files = len(files_sorted)

    manifest = load_manifest(ckpt_dir)
    completed = set(manifest["completed_files"])
    pending = [(gi, name) for gi, name in enumerate(files_sorted) if name not in completed]

    if not pending:
        log(f"All {n_files} files already completed — skipping straight to merge.", log_fh)
    else:
        log(f"Resuming: {len(completed)}/{n_files} files already done, {len(pending)} remaining.", log_fh)

        t_start = time.time()
        n_done_this_session = 0
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            it = iter(pending)
            futures = {}
            for _ in range(min(a.workers, len(pending))):
                gi, name = next(it)
                futures[ex.submit(process_one_file, name, gi, pmap, gmap, C)] = name

            while futures:
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                for fut in done:
                    fname = futures.pop(fut)
                    try:
                        name, gi, rows, events = fut.result()
                    except Exception as exc:
                        log(f"NO-GO: worker exception on file={fname}: {exc!r}", log_fh)
                        raise

                    write_csv(ckpt_dir / f"file_{safe_name(name)}.rows.csv", rows)
                    write_csv(ckpt_dir / f"file_{safe_name(name)}.events.csv", events)
                    completed.add(name)
                    manifest["completed_files"] = sorted(completed)
                    save_manifest(ckpt_dir, manifest)

                    n_done_this_session += 1
                    elapsed = time.time() - t_start
                    avg = elapsed / n_done_this_session
                    remaining_files = n_files - len(completed)
                    eta_sec = avg * remaining_files / max(1, a.workers)  # rough, accounts for parallelism
                    log(
                        f"file done: {name} | rows={len(rows)} | "
                        f"progress {len(completed)}/{n_files} | "
                        f"elapsed {elapsed/60:.1f}min | avg {avg:.1f}s/file | "
                        f"ETA ~{eta_sec/60:.1f}min remaining",
                        log_fh,
                    )

                    try:
                        gi2, name2 = next(it)
                        futures[ex.submit(process_one_file, name2, gi2, pmap, gmap, C)] = name2
                    except StopIteration:
                        pass

    log("All files processed — merging and validating...", log_fh)
    status = "UNKNOWN"
    try:
        merge_and_validate(ckpt_dir, out_dir, G, expected_rows)
        log("CLOSED.", log_fh)
        status = "CLOSED"
    except RuntimeError as e:
        log(f"NOT YET CLOSED: {e}", log_fh)
        status = "NOT_CLOSED"
        raise
    finally:
        run_manifest["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        run_manifest["status"] = status
        run_manifest["files_completed_this_and_prior_sessions"] = len(completed)
        run_manifest["files_total"] = n_files
        (out_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2))
        log_fh.close()


if __name__ == "__main__":
    main()
