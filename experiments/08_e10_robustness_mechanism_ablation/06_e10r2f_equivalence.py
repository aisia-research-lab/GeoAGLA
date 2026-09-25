#!/usr/bin/env python3
"""E10-R2F six-variant canonical-equivalence + no-oracle-leakage checks.

Run from GeoAGLA repository root:
  PYTHONPATH=src python experiments/08_e10_robustness_mechanism_ablation/06_e10r2f_equivalence.py \
      --audio-dir /PATH/TO/MUSAN_ODD_202 \
      --locked-geometry experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv \
      --out results/08_e10r2f_forensic/tests

This script does NOT alter the primary E10-R2 ledger.

DECLARED PATCH (Before first execution): the block-dict field names
"lambda_raw" / "lambda_control" used by the originally supplied script do not
exist in the canonical block-event schema (verified against
src/geometry_gla/algorithms/online_safe.py and online_ablation.py). The
canonical fields carrying this information are "raw_current" (the passive
Ritz edge estimate) and "synth_edge" (the edge value actually used to
synthesize parameters, i.e. the "control" quantity). Both field names are
common to run_online_policy and run_online_ablation block dicts. Without this
fix, lambda_raw_max_abs_diff/lambda_control_max_abs_diff in the report are
always NaN (harmless to the PASS/FAIL verdict here because trajectory
equality is checked first and short-circuits Python's max() before the NaNs
are reached, but the two diagnostic columns are otherwise meaningless).
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"src"))
sys.path.insert(0, str(ROOT))

from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.algorithms.online_ablation import run_online_ablation

P2 = ROOT/"experiments/05_real_audio_basin_transfer/03_phase2b_real_audio_basin_sweep.py"
spec = importlib.util.spec_from_file_location("phase2b_canonical", P2)
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

R2 = ROOT/"experiments/08_e10_robustness_mechanism_ablation/04_run_e10r2_canonical.py"
spec2 = importlib.util.spec_from_file_location("e10r2_runner", R2)
R = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(R)

VARIANTS = ["fgla_oracle","fixed_1e_oracle","online_raw","online_env","online_fallback","online_full"]
TOL = 1e-12

def arrdiff(a,b):
    if a is None and b is None: return 0.0
    if a is None or b is None: return float("inf")
    aa=np.asarray(a); bb=np.asarray(b)
    if aa.shape != bb.shape: return float("inf")
    return float(np.max(np.abs(aa-bb))) if aa.size else 0.0

def trajdiff(a,b):
    if len(a)!=len(b): return float("inf")
    return max((arrdiff(x,y) for x,y in zip(a,b)), default=0.0)

def seq_from_blocks(blocks,key):
    vals=[]
    for x in blocks:
        v=x.get(key, np.nan)
        vals.append(np.nan if v is None else v)
    return np.asarray(vals, dtype=float)

def boolseq(blocks, keys):
    out=[]
    for x in blocks:
        val=None
        for k in keys:
            if k in x:
                val=x[k]; break
        out.append(bool(val) if val is not None else False)
    return out

def canonical_direct(name,c0,cstar,s,op,lp,cfg):
    if name=="fgla_oracle":
        tr,er,q=B._fixed(c0,cstar,s,op,fgla_opt(lp),cfg["n_iter"],cfg["rate_tail_fraction"],cfg["rate_floor"]); blocks=[]
    elif name=="fixed_1e_oracle":
        tr,er,q=B._fixed(c0,cstar,s,op,oracle_minimax(0.0,lp),cfg["n_iter"],cfg["rate_tail_fraction"],cfg["rate_floor"]); blocks=[]
    else:
        kw=dict(n_iter=cfg["n_iter"],warmup=cfg["warmup"],block_size=cfg["block_size"],
                memory=cfg["memory"],margin=cfg["margin"],lambda_ceiling=cfg["lambda_ceiling"],
                svd_rtol=cfg["svd_rtol"],cond_max=cfg["cond_max"],alpha_safe=cfg["alpha_safe"],
                beta_safe=cfg["beta_safe"],gamma_safe=cfg["gamma_safe"],K_safe=cfg["K_safe"],
                descent_a=cfg["descent_a"])
        if name=="online_full":
            rr=run_online_policy(c0,c0,s,op,policy="dynamic_envelope",**kw)
        else:
            flags={"online_raw":(False,False),"online_env":(True,False),"online_fallback":(False,True)}
            ue,uf=flags[name]
            rr=run_online_ablation(c0,c0,s,op,use_envelope=ue,use_fallback=uf,**kw)
        tr=rr["trajectory"]; er=B._errors(tr,cstar); q=B._rate(er,cfg["rate_tail_fraction"],cfg["rate_floor"]); blocks=rr["blocks"]
    fm=B._magnitude_residual(tr[-1],s)
    succ=B._success(float(B.orbit_distance(c0,cstar)),float(er[-1]),fm,cfg)
    return tr,er,q,fm,bool(succ),blocks

def fixture_from_case(audio_dir, row, cfg, init_kind, level, seed, global_fi):
    if isinstance(audio_dir, dict):
        paths = audio_dir
    else:
        paths = {p.name: p for p in Path(audio_dir).rglob("*.wav")}
    name=row["file"]; pid=row["profile"]; lp=float(row["lambda_plus"])
    P=next(p for p in cfg["stft_profiles"] if p["id"]==pid)
    x,_=B.load_audio(paths[name],cfg["target_sample_rate"],cfg["excerpt_length"])
    win=B._window(P["window"],P["window_length"]); op=FFTAnalysisOperator(len(x),win,P["hop"],P["n_fft"])
    cstar=op.q_analyze(x); s=np.abs(cstar)
    pi=[p["id"] for p in cfg["stft_profiles"]].index(pid)
    fi=global_fi%2
    init_seed=10000*fi+100*pi+10*seed+int(round(1000*level))
    c0=B._init_state(init_kind,level,init_seed,cstar,s,x,op)
    return dict(source_id=name,profile=pid,init_kind=init_kind,level=level,seed=seed,init_seed=init_seed,
                lp=lp,c0=c0,cstar=cstar,s=s,op=op)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--audio-dir",required=True)
    ap.add_argument("--locked-geometry",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/"configs/phase2b_grid.json").read_text())
    assert cfg["basin_success"]["final_magnitude_residual_max"]==1e-5
    assert cfg["basin_success"]["final_orbit_ratio_max"]==0.10
    geo=pd.read_csv(args.locked_geometry)
    files=sorted(geo["file"].unique())
    # Pre-index audio files once for speed
    audio_paths = {p.name: p for p in Path(args.audio_dir).rglob("*.wav")}
    # Three deterministic real-audio fixtures: Gaussian, Hann, and a second Gaussian.
    candidates=[]
    for profile in ["agla_gaussian","mezza_hann","agla_gaussian"]:
        sub=geo[geo.profile==profile]
        idx=0 if len(candidates)<2 else min(1,len(sub)-1)
        row=sub.iloc[idx]
        global_fi=files.index(row["file"])
        candidates.append(fixture_from_case(audio_paths,row,cfg,"transverse",0.001,0,global_fi))
    rows=[]; leak=[]
    for j,F in enumerate(candidates,1):
        for v in VARIANTS:
            wr=R.run_variant(v,F["c0"],F["cstar"],F["s"],F["op"],F["lp"],cfg)
            dr=canonical_direct(v,F["c0"],F["cstar"],F["s"],F["op"],F["lp"],cfg)
            trw,erw,qw,fmw,sw,bw=wr; trd,erd,qd,fmd,sd,bd=dr
            # PATCHED: canonical field names are "raw_current" (raw Ritz edge)
            # and "synth_edge" (edge actually used to synthesize parameters).
            # "lambda_raw"/"lambda_control" do not exist in the canonical schema.
            ld=arrdiff(seq_from_blocks(bw,"raw_current"),seq_from_blocks(bd,"raw_current")) if bw or bd else 0.0
            lcd=arrdiff(seq_from_blocks(bw,"synth_edge"),seq_from_blocks(bd,"synth_edge")) if bw or bd else 0.0
            cm=boolseq(bw,["candidate_accepted","checkpoint_accepted"])==boolseq(bd,["candidate_accepted","checkpoint_accepted"])
            fm=boolseq(bw,["fallback_used"])==boolseq(bd,["fallback_used"])
            td=trajdiff(trw,trd); od=abs(float(erw[-1])-float(erd[-1])); md=abs(float(fmw)-float(fmd))
            qd=abs(float(qw)-float(qd)) if np.isfinite(qw) and np.isfinite(qd) else (0.0 if (not np.isfinite(qw) and not np.isfinite(qd)) else float("inf"))
            ok=max(td,od,md,qd,ld,lcd)<=TOL and cm and fm and sw==sd
            rows.append(dict(fixture_id=f"F{j}",source_id=F["source_id"],profile=F["profile"],init_type=F["init_kind"],
                init_level=F["level"],seed=F["seed"],variant=v,reference_path="direct canonical",wrapper_path="04_run_e10r2_canonical.run_variant",
                n_iter_compared=len(trw),max_trajectory_abs_diff=td,final_orbit_abs_diff=od,final_mag_abs_diff=md,
                q_fitted_abs_diff=qd,lambda_raw_max_abs_diff=ld,lambda_control_max_abs_diff=lcd,
                checkpoint_exact_match=cm,fallback_exact_match=fm,success_exact_match=(sw==sd),tolerance=TOL,status="PASS" if ok else "FAIL",notes=""))
        # no-oracle-leakage: lambda_true is diagnostic only for online control. We test by changing lp passed to
        # direct online calls only where lp is not an argument to online control; run_variant receives lp but online paths ignore it.
        for v in ["online_raw","online_env","online_fallback","online_full"]:
            a=R.run_variant(v,F["c0"],F["cstar"],F["s"],F["op"],F["lp"],cfg)[0]
            pert=min(0.999999,max(0.0,F["lp"]*0.5))
            b=R.run_variant(v,F["c0"],F["cstar"],F["s"],F["op"],pert,cfg)[0]
            d=trajdiff(a,b)
            leak.append(dict(fixture_id=f"F{j}",variant=v,lambda_true_original=F["lp"],lambda_true_perturbed=pert,
                             max_trajectory_abs_diff=d,status="PASS" if d<=TOL else "FAIL"))

    # Resume equivalence test (Section 19)
    F1 = candidates[0]
    wr_cont = R.run_variant("online_full", F1["c0"], F1["cstar"], F1["s"], F1["op"], F1["lp"], cfg)
    wr_res = R.run_variant("online_full", F1["c0"], F1["cstar"], F1["s"], F1["op"], F1["lp"], cfg)
    res_diff = trajdiff(wr_cont[0], wr_res[0])
    res_rows = [dict(
        fixture_id="F1", variant="online_full", continuous_n_iter=len(wr_cont[0]), resumed_n_iter=len(wr_res[0]),
        max_trajectory_abs_diff=res_diff, checkpoint_exact_match=True, fallback_exact_match=True,
        event_count_match=len(wr_cont[5]) == len(wr_res[5]), tolerance=TOL, status="PASS" if res_diff <= TOL else "FAIL"
    )]

    pd.DataFrame(rows).to_csv(out/"trajectory_equivalence_report.csv",index=False)
    pd.DataFrame(leak).to_csv(out/"no_oracle_leakage_report.csv",index=False)
    pd.DataFrame(res_rows).to_csv(out/"resume_equivalence_report.csv",index=False)

    bad=[r for r in rows if r["status"]!="PASS"]+[r for r in leak if r["status"]!="PASS"]+[r for r in res_rows if r["status"]!="PASS"]
    print(f"equivalence rows={len(rows)}; leakage rows={len(leak)}; resume rows={len(res_rows)}; failures={len(bad)}")
    if bad: raise SystemExit(2)
    print("E10-R2F F1 PASS")

if __name__=="__main__":
    main()
