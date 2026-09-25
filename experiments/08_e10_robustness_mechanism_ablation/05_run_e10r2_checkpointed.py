"""
05_run_e10r2_checkpointed.py
=============================
DECLARED MODIFICATION — new file, does NOT edit 04_run_e10r2_canonical.py.

Checkpoint/resume wrapper around the E10-R2 canonical closure runner, for
Kaggle sessions (~12h wall-clock limit) or any machine where a single
~17-18h sequential run risks interruption.

Reused UNCHANGED from 04_run_e10r2_canonical.py (imported as a module):
run_variant(), VARIANTS, online_kwargs(), and everything that module itself
imports from the canonical repository (B.*, FFTAnalysisOperator, fgla_opt,
oracle_minimax, run_online_policy, run_online_ablation). No scientific
computation, threshold, or formula is touched here.

NEW in this file (must be declared per guide section 26-27, same as the
E10-R checkpoint wrapper): only the outer control flow — batching the fixed,
sorted file list by file index, writing each finished batch to disk
immediately, a manifest for resume, and a merge+validate step that produces
the SAME output files/schema as 04_run_e10r2_canonical.py
(e10r2_run_ledger.csv/json, e10r2_event_ledger.csv), plus the same
mandatory log header and hard cardinality gates.

global_fi (used for seed_mode=historical_batch2) is computed from the FIXED
global position in the 395-case sorted file list, independent of how files
are split into batches — so results are equivalent to a single-shot run of
04_run_e10r2_canonical.py on the full population.

Usage (first session):
    python experiments/08_e10_robustness_mechanism_ablation/05_run_e10r2_checkpointed.py \
        --audio-dir /path/to/MUSAN_ODD_202 \
        --locked-geometry experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv \
        --out results/08_e10r2_canonical_ckpt \
        --seed-mode historical_batch2 \
        --batch-size 4 \
        --time-budget-sec 34200   # 9.5h safety margin under Kaggle's ~12h

Usage (resume — same --out, or a copy of the previous session's checkpoint
directory carried over as a new Kaggle "Add Input" dataset): rerun the
identical command. Already-completed batches are skipped automatically.
"""
from __future__ import annotations
import sys, json, csv, argparse, importlib.util, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

_e10r2_path = Path(__file__).resolve().parent / "04_run_e10r2_canonical.py"
_spec = importlib.util.spec_from_file_location("e10r2_canonical_original", _e10r2_path)
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)  # also runs its own canonical imports (E.B, etc.)

VARIANTS = E.VARIANTS
run_variant = E.run_variant
B = E.B
FFTAnalysisOperator = E.FFTAnalysisOperator


def batch_id_str(i: int) -> str:
    return f"batch_{i:04d}"


def load_manifest(ckpt_dir: Path) -> dict:
    mf = ckpt_dir / "_manifest.json"
    if mf.exists():
        return json.loads(mf.read_text())
    return {"completed_batches": [], "batch_size": None, "seed_mode": None}


def save_manifest(ckpt_dir: Path, manifest: dict) -> None:
    (ckpt_dir / "_manifest.json").write_text(json.dumps(manifest, indent=2))


def write_batch_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    fields = sorted(set().union(*(r.keys() for r in rows)))
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def process_one_file(name, global_fi, pmap, gmap, C):
    """Reproduces EXACTLY the per-file inner loop body of
    04_run_e10r2_canonical.py's main(), for a single file."""
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
    return rows, events


def merge_and_validate(ckpt_dir: Path, out_dir: Path, G: pd.DataFrame, expected_rows: int) -> None:
    batch_dirs = sorted(ckpt_dir.glob("batch_*"))
    all_rows, all_events = [], []
    for bd in batch_dirs:
        rc = bd / "rows.csv"
        ec = bd / "events.csv"
        if rc.exists() and rc.stat().st_size > 0:
            all_rows.append(pd.read_csv(rc))
        if ec.exists() and ec.stat().st_size > 0:
            all_events.append(pd.read_csv(ec))
    L = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    Ev = pd.concat(all_events, ignore_index=True) if all_events else pd.DataFrame()

    if len(L) != expected_rows:
        raise RuntimeError(
            f"closure cardinality failed: {len(L)} != {expected_rows} "
            f"(not all batches complete yet — resume the same command)"
        )
    if L.run_key.nunique() != expected_rows // 6:
        raise RuntimeError(f"run_key count mismatch: {L.run_key.nunique()} != {expected_rows // 6}")
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
    ap.add_argument("--out", default=str(ROOT / "results/08_e10r2_canonical_ckpt"))
    ap.add_argument("--seed-mode", choices=["historical_batch2"], default="historical_batch2")
    ap.add_argument("--batch-size", type=int, default=4, help="files per checkpoint batch")
    ap.add_argument("--time-budget-sec", type=float, default=None)
    ap.add_argument("--merge-only", action="store_true")
    a = ap.parse_args()

    C = json.loads((ROOT / "configs/phase2b_grid.json").read_text())

    # Mandatory log header (guide section 28) — checked BEFORE any batch runs.
    print("E10-R2 CANONICAL FINAL FREEZE RUN (checkpointed)")
    print(f"success_mag_threshold = {C['basin_success']['final_magnitude_residual_max']}")
    print(f"success_orbit_ratio_threshold = {C['basin_success']['final_orbit_ratio_max']}")
    print(f"seed_mode = {a.seed_mode}")
    print("canonical_online_full = run_online_policy(dynamic_envelope)")
    if C['basin_success']['final_magnitude_residual_max'] != 1e-5 or C['basin_success']['final_orbit_ratio_max'] != 0.10:
        print("NO-GO: success threshold does not match canonical 1e-5 / 0.10")
        sys.exit(1)

    G = pd.read_csv(a.locked_geometry)
    gmap = {(r.file, r.profile): float(r.lambda_plus) for r in G.itertuples()}
    expected_rows = len(G) * 12 * 6
    print(f"locked_cases = {len(G)}")
    print(f"expected_run_keys = {len(G) * 12}")
    print(f"expected_rows = {expected_rows}")

    paths = sorted(p for p in Path(a.audio_dir).rglob("*") if p.is_file() and p.suffix.lower() == ".wav")
    pmap = {p.name: p for p in paths}

    files_sorted = sorted(set(G.file))  # FIXED order — identical to 04_run_e10r2_canonical.py
    n_files = len(files_sorted)
    n_batches = (n_files + a.batch_size - 1) // a.batch_size

    ckpt_dir = Path(a.out) / "_batches"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    out_dir = Path(a.out)

    manifest = load_manifest(ckpt_dir)
    if manifest["batch_size"] not in (None, a.batch_size):
        raise RuntimeError(
            f"--batch-size changed between sessions ({manifest['batch_size']} -> {a.batch_size}); "
            f"resume must use the same batch size as the first session for this checkpoint dir."
        )
    manifest["batch_size"] = a.batch_size
    manifest["seed_mode"] = a.seed_mode
    completed = set(manifest["completed_batches"])

    if not a.merge_only:
        t_start = time.time()
        for b in range(n_batches):
            bname = batch_id_str(b)
            if bname in completed:
                continue
            lo, hi = b * a.batch_size, min((b + 1) * a.batch_size, n_files)
            bdir = ckpt_dir / bname
            bdir.mkdir(parents=True, exist_ok=True)
            rows, events = [], []
            for global_fi in range(lo, hi):
                name = files_sorted[global_fi]
                r, e = process_one_file(name, global_fi, pmap, gmap, C)
                rows.extend(r)
                events.extend(e)
            write_batch_csv(bdir / "rows.csv", rows)
            write_batch_csv(bdir / "events.csv", events)
            completed.add(bname)
            manifest["completed_batches"] = sorted(completed)
            save_manifest(ckpt_dir, manifest)
            print(f"[checkpoint] {bname} done ({len(completed)}/{n_batches} batches, "
                  f"files {lo}:{hi}, {len(rows)} rows)")

            if a.time_budget_sec is not None and (time.time() - t_start) > a.time_budget_sec:
                remaining = n_batches - len(completed)
                print(f"[checkpoint] time budget reached — {remaining} batch(es) remaining. "
                      f"Resume by rerunning the identical command with the same --out.")
                return

    if len(completed) < n_batches:
        print(f"[checkpoint] {len(completed)}/{n_batches} batches complete — "
              f"NOT YET CLOSED. Resume by rerunning the identical command with the same --out.")
        return

    merge_and_validate(ckpt_dir, out_dir, G, expected_rows)


if __name__ == "__main__":
    main()
