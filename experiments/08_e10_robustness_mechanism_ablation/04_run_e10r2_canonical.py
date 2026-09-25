"""
04_run_e10r2_canonical.py — E10-R2 Canonical Final Freeze runner.

Per E10R2_Canonical_Equivalence_Final_Freeze_Guide.md section 0:
this file does NOT reimplement any scientific algorithm. Every computation
is a direct call into the canonical repository code:

  - experiments/05_real_audio_basin_transfer/03_phase2b_real_audio_basin_sweep.py
        load_audio, _window, _init_state, _fixed, _errors, _rate,
        _magnitude_residual, _success, orbit_distance (re-exported as B.*)
  - src/geometry_gla/operators/stft_fft.py            FFTAnalysisOperator
  - src/geometry_gla/algorithms/minimax.py             fgla_opt, oracle_minimax
  - src/geometry_gla/algorithms/online_safe.py         run_online_policy
  - src/geometry_gla/algorithms/online_ablation.py     run_online_ablation

This file's only job is: read the locked population + frozen config, loop
over (file, profile, init, seed, variant), and write the ledger. No formula,
threshold, or hyperparameter is redefined here.
"""
from __future__ import annotations
import sys, json, csv, argparse, importlib.util, hashlib, platform
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

_base = ROOT / "experiments" / "05_real_audio_basin_transfer" / "03_phase2b_real_audio_basin_sweep.py"
_spec = importlib.util.spec_from_file_location("phase2b_frozen", _base)
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.algorithms.online_ablation import run_online_ablation

VARIANTS = ["fgla_oracle", "fixed_1e_oracle", "online_raw", "online_env", "online_fallback", "online_full"]

CANONICAL_ONLINE_KW = (
    "n_iter", "warmup", "block_size", "memory", "margin", "lambda_ceiling",
    "svd_rtol", "cond_max", "alpha_safe", "beta_safe", "gamma_safe", "K_safe", "descent_a",
)


def online_kwargs(C: dict) -> dict:
    return {k: C[k] for k in CANONICAL_ONLINE_KW}


def run_variant(name, c0, cstar, s, op, lambda_true, C):
    """Dispatch to canonical implementations. lambda_true (oracle edge) is
    passed ONLY to the two oracle variants — never to the online variants
    (no-oracle-leakage, guide section 7)."""
    if name == "fgla_oracle":
        tr, er, q = B._fixed(c0, cstar, s, op, fgla_opt(lambda_true),
                              C["n_iter"], C["rate_tail_fraction"], C["rate_floor"])
        blocks = []
    elif name == "fixed_1e_oracle":
        tr, er, q = B._fixed(c0, cstar, s, op, oracle_minimax(0.0, lambda_true),
                              C["n_iter"], C["rate_tail_fraction"], C["rate_floor"])
        blocks = []
    elif name == "online_full":
        rr = run_online_policy(c0, c0, s, op, policy="dynamic_envelope", **online_kwargs(C))
        tr = rr["trajectory"]; er = B._errors(tr, cstar); q = B._rate(er, C["rate_tail_fraction"], C["rate_floor"]); blocks = rr["blocks"]
    elif name == "online_raw":
        rr = run_online_ablation(c0, c0, s, op, use_envelope=False, use_fallback=False, **online_kwargs(C))
        tr = rr["trajectory"]; er = B._errors(tr, cstar); q = B._rate(er, C["rate_tail_fraction"], C["rate_floor"]); blocks = rr["blocks"]
    elif name == "online_env":
        rr = run_online_ablation(c0, c0, s, op, use_envelope=True, use_fallback=False, **online_kwargs(C))
        tr = rr["trajectory"]; er = B._errors(tr, cstar); q = B._rate(er, C["rate_tail_fraction"], C["rate_floor"]); blocks = rr["blocks"]
    elif name == "online_fallback":
        rr = run_online_ablation(c0, c0, s, op, use_envelope=False, use_fallback=True, **online_kwargs(C))
        tr = rr["trajectory"]; er = B._errors(tr, cstar); q = B._rate(er, C["rate_tail_fraction"], C["rate_floor"]); blocks = rr["blocks"]
    else:
        raise ValueError(name)

    fm = B._magnitude_residual(tr[-1], s)
    succ = B._success(float(B.orbit_distance(c0, cstar)), float(er[-1]), fm, C)  # canonical success (0.10 / 1e-5)
    return tr, er, q, fm, succ, blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio-dir", required=True)
    ap.add_argument("--locked-geometry",
                     default=str(ROOT / "experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv"))
    ap.add_argument("--out", default=str(ROOT / "results/08_e10r2_canonical"))
    ap.add_argument("--seed-mode", choices=["historical_batch2"], default="historical_batch2")
    a = ap.parse_args()

    C = json.loads((ROOT / "configs/phase2b_grid.json").read_text())
    G = pd.read_csv(a.locked_geometry)
    gmap = {(r.file, r.profile): float(r.lambda_plus) for r in G.itertuples()}
    paths = sorted(p for p in Path(a.audio_dir).rglob("*") if p.is_file() and p.suffix.lower() == ".wav")
    pmap = {p.name: p for p in paths}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    # Mandatory log header (guide section 28)
    print("E10-R2 CANONICAL FINAL FREEZE RUN")
    print(f"success_mag_threshold = {C['basin_success']['final_magnitude_residual_max']}")
    print(f"success_orbit_ratio_threshold = {C['basin_success']['final_orbit_ratio_max']}")
    print(f"seed_mode = {a.seed_mode}")
    print(f"locked_cases = {len(G)}")
    print(f"expected_run_keys = {len(G) * 12}")
    print(f"expected_rows = {len(G) * 12 * 6}")
    print("canonical_online_full = run_online_policy(dynamic_envelope)")
    if C['basin_success']['final_magnitude_residual_max'] != 1e-5 or C['basin_success']['final_orbit_ratio_max'] != 0.10:
        print("NO-GO: success threshold does not match canonical 1e-5 / 0.10")
        sys.exit(1)

    rows, events = [], []
    for global_fi, name in enumerate(sorted(set(G.file))):
        if name not in pmap:
            raise FileNotFoundError(name)
        path = pmap[name]
        x, meta = B.load_audio(path, C["target_sample_rate"], C["excerpt_length"])
        fi = global_fi % 2  # historical_batch2 (only supported mode)
        for pi, P in enumerate(C["stft_profiles"]):
            key = (name, P["id"])
            if key not in gmap:
                continue
            win = B._window(P["window"], P["window_length"])
            op = FFTAnalysisOperator(len(x), win, P["hop"], P["n_fft"])
            cstar = op.q_analyze(x); s = np.abs(cstar); xstar = x
            lambda_true = gmap[key]
            for init in C["basin_initializations"]:
                for level in init["levels"]:
                    for seed in C["seeds"]:
                        init_seed = 10000 * fi + 100 * pi + 10 * seed + int(round(1000 * level))
                        c0 = B._init_state(init["kind"], level, init_seed, cstar, s, xstar, op)
                        init_err = float(B.orbit_distance(c0, cstar)); init_mag = B._magnitude_residual(c0, s)
                        run_key = f'{name}|{P["id"]}|{init["kind"]}|{level:g}|{seed}'
                        for v in VARIANTS:
                            tr, er, q, fm, succ, blocks = run_variant(v, c0, cstar, s, op, lambda_true, C)
                            rows.append(dict(
                                run_key=run_key, file=name, profile=P["id"], init_kind=init["kind"],
                                level=float(level), seed=int(seed), init_seed=int(init_seed),
                                seed_mode="historical_batch2", variant=v,
                                lambda_true=lambda_true,  # diagnostic only — never fed to online variants above
                                initial_orbit_error=init_err, initial_magnitude_residual=init_mag,
                                final_orbit_error=float(er[-1]), final_magnitude_residual=fm,
                                success=bool(succ), q_fitted=q, n_blocks=len(blocks),
                            ))
                            for b in blocks:
                                events.append(dict(run_key=run_key, variant=v, lambda_true=lambda_true, **b))

    L = pd.DataFrame(rows)
    expected = len(G) * 12 * 6
    if len(L) != expected:
        print(f"NO-GO: closure cardinality failed: {len(L)} != {expected}")
        sys.exit(1)
    if not (L.groupby("run_key").variant.nunique() == 6).all():
        print("NO-GO: some run_key missing one or more of the 6 variants"); sys.exit(1)
    if L.duplicated(["run_key", "variant"]).sum() != 0:
        print("NO-GO: duplicate (run_key, variant) rows found"); sys.exit(1)

    L.to_csv(out / "e10r2_run_ledger.csv", index=False)
    L.to_json(out / "e10r2_run_ledger.json", orient="records", indent=2)
    pd.DataFrame(events).to_csv(out / "e10r2_event_ledger.csv", index=False)
    print("PASS: rows", len(L), "paired instances", len(L) // 6, "locked geometry cases", len(G))


if __name__ == "__main__":
    main()
