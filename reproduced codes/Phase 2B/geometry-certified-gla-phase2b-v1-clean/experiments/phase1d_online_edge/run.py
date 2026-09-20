from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from geometry_gla.operators.stft import AnalysisOperator, periodic_stft_matrix, gaussian_window, hann_window
from geometry_gla.operators.projections import griffin_lim_map
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.geometry.realify import r2c
from geometry_gla.estimators.ritz import ritz_largest, estimate_edge_series
from geometry_gla.metrics.phase import align_global_phase


def _window(kind, length):
    return gaussian_window(length) if kind == "gaussian" else hann_window(length)


def _case(cfg, seed, near_zero_tol):
    rng=np.random.default_rng(seed)
    T=periodic_stft_matrix(cfg["signal_length"], _window(cfg["window"],cfg["window_length"]), cfg["hop"], cfg["n_fft"])
    op=AnalysisOperator(T)
    x=rng.normal(size=cfg["signal_length"]) + 1j*rng.normal(size=cfg["signal_length"])
    c=op.analyze(x)
    if np.min(np.abs(c)) <= near_zero_tol: raise RuntimeError("near-zero coefficient")
    return op,c,rng


def _gla_trajectory(c0, s, op, n_iter, c_star):
    # Align every stored point to the same orbit representative. The map itself
    # is phase equivariant, and this removes neutral phase drift from secants.
    out=[]; c=np.asarray(c0,dtype=np.complex128)
    for _ in range(n_iter+1):
        out.append(align_global_phase(c, c_star))
        c=griffin_lim_map(c,s,op)
    return np.asarray(out)


def _tail_stats(series, lambda_plus, tail_fraction):
    ok=[r for r in series if r["accepted"] and np.isfinite(r["estimate"])]
    if not ok: return {"n_valid":0,"tail_n":0,"median_rel_error":None,"median_signed_error":None,"under_fraction":None,"last_estimate":None}
    k=max(5,int(np.ceil(tail_fraction*len(ok))))
    tail=ok[-k:]
    est=np.asarray([r["estimate"] for r in tail])
    rel=np.abs(est-lambda_plus)/max(lambda_plus,1e-15)
    return {"n_valid":len(ok),"tail_n":len(tail),"median_rel_error":float(np.median(rel)),
            "median_signed_error":float(np.median(est-lambda_plus)),
            "under_fraction":float(np.mean(est<lambda_plus)),"last_estimate":float(ok[-1]["estimate"]),
            "median_condition":float(np.median([r["condition"] for r in tail]))}


def _d0_synthetic():
    rows=[]
    specs=[[0.15,0.35,0.6,0.82],[0.1,0.4,0.75,0.93],[0.2,0.5,0.85,0.97]]
    for sid,eigs in enumerate(specs):
        J=np.diag(eigs); rng=np.random.default_rng(100+sid); x=rng.normal(size=len(eigs)); tr=[x.copy()]
        for _ in range(120): x=J@x; tr.append(x.copy())
        tr=np.asarray(tr,dtype=np.complex128)
        for p in [1,3,5]:
            ser=estimate_edge_series(tr,p,cond_max=1e12)
            ok=[z for z in ser if z["accepted"]]
            est=ok[-1]["estimate"]
            rows.append({"case":sid,"memory":p,"lambda_plus":max(eigs),"estimate":est,
                         "abs_error":abs(est-max(eigs)),"n_valid":len(ok)})
    return rows


def _d2_identifiability():
    # J_A and J_B agree on the 3D active subspace, but differ on an unexcited
    # fourth direction. The passive trajectory is therefore exactly identical.
    active=np.diag([0.25,0.55,0.8])
    JA=np.diag([0.25,0.55,0.8,0.90]); JB=np.diag([0.25,0.55,0.8,0.99])
    x=np.array([1.0,-0.4,0.8,0.0]); ta=[x.copy()]; tb=[x.copy()]
    xa=x.copy(); xb=x.copy()
    for _ in range(80): xa=JA@xa; xb=JB@xb; ta.append(xa.copy()); tb.append(xb.copy())
    ta=np.asarray(ta,dtype=np.complex128); tb=np.asarray(tb,dtype=np.complex128)
    maxdiff=float(np.max(np.abs(ta-tb)))
    ea=estimate_edge_series(ta,3,cond_max=1e12); eb=estimate_edge_series(tb,3,cond_max=1e12)
    va=[r for r in ea if r["accepted"]]; vb=[r for r in eb if r["accepted"]]
    return {"trajectory_max_difference":maxdiff,"estimate_A":float(va[-1]["estimate"]),
            "estimate_B":float(vb[-1]["estimate"]),"active_edge":0.8,
            "full_lambda_plus_A":0.90,"full_lambda_plus_B":0.99,
            "conclusion":"passive data identify the active edge, not an unexcited full-spectrum edge"}


def run(config_path="configs/phase1d_grid.json", out_dir="results/phase1d"):
    cfgall=json.loads(Path(config_path).read_text()); out=Path(out_dir); (out/"figures").mkdir(parents=True,exist_ok=True)
    d0=_d0_synthetic(); (out/"d0_synthetic.json").write_text(json.dumps(d0,indent=2))
    d2=_d2_identifiability(); (out/"d2_identifiability.json").write_text(json.dumps(d2,indent=2))
    rows=[]; traces=[]; case_count=0
    for cfg in cfgall["configs"]:
      for seed in cfgall["seeds"]:
        op,cstar,rng=_case(cfg,seed,cfgall["near_zero_tol"]); spec=transverse_spectrum(cstar,op,cfgall["phase_tol"])
        if spec["neutral_count"]!=1: continue
        vals,jvecs=np.linalg.eigh(spec["J"]); idx=np.where(vals<1-cfgall["phase_tol"])[0]; lp=float(vals[idx[-1]])
        # Random transverse excitation. Remove the phase vector component using the range-coordinate representation.
        coeff=rng.normal(size=spec["J"].shape[0]); phase_idx=np.argmax(vals); coeff[phase_idx]=0.0
        v=r2c(spec["QU"]@coeff); v/=np.linalg.norm(v)
        for eps in cfgall["perturbations"]:
          tr=_gla_trajectory(cstar+eps*v,np.abs(cstar),op,cfgall["n_iter"],cstar)
          for p in cfgall["memories"]:
            ser=estimate_edge_series(tr,p,svd_rtol=cfgall["svd_rtol"],cond_max=cfgall["cond_max"])
            st=_tail_stats(ser,lp,cfgall["tail_fraction"])
            row={"config":cfg["id"],"seed":seed,"epsilon":eps,"memory":p,"lambda_plus":lp,**st}
            rows.append(row)
            if cfg["id"] in {"h16_w8_h4_f8","g32_w16_h4_f16"} and seed==0 and eps==cfgall["perturbations"][0]:
                traces.append({"config":cfg["id"],"memory":p,"lambda_plus":lp,"series":ser})
          case_count+=1; print(f"Phase-1D case {case_count}: {cfg['id']} seed={seed} eps={eps}")
    (out/"d1_local_stft.json").write_text(json.dumps(rows,indent=2,allow_nan=True))
    with (out/"d1_local_stft.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    (out/"tracking_traces.json").write_text(json.dumps(traces,indent=2,allow_nan=True))

    # Aggregate estimator selection.
    per_mem={}
    for p in cfgall["memories"]:
        rr=[r for r in rows if r["memory"]==p and r["median_rel_error"] is not None]
        errs=np.array([r["median_rel_error"] for r in rr]); unders=np.array([r["under_fraction"] for r in rr])
        per_mem[str(p)]={"n":len(rr),"median_rel_error":float(np.median(errs)),"p90_rel_error":float(np.percentile(errs,90)),
                         "median_under_fraction":float(np.median(unders)),
                         "median_valid_updates":float(np.median([r["n_valid"] for r in rr]))}
    # Selection prioritizes p90 error, then conditioning/availability.
    best=min(cfgall["memories"],key=lambda p:(per_mem[str(p)]["p90_rel_error"],-per_mem[str(p)]["median_valid_updates"]))
    sel={"per_memory":per_mem,"selected_memory":best,
         "selection_rule":"minimum p90 tail relative error; ties favor more valid updates",
         "raw_estimate_is_certified_upper_bound":False}
    (out/"estimator_selection.json").write_text(json.dumps(sel,indent=2))

    # D3 tracking figure.
    fig,ax=plt.subplots(figsize=(7.2,4.8))
    for t in traces:
        if t["config"]!="g32_w16_h4_f16": continue
        xy=[(r["iteration"],r["estimate"]) for r in t["series"] if r["accepted"]]
        if xy: ax.plot([a for a,b in xy],[b for a,b in xy],label=f"p={t['memory']}")
        lp=t["lambda_plus"]
    ax.axhline(lp,linestyle="--",linewidth=1.0,label="oracle lambda+")
    ax.set_xlabel("iteration"); ax.set_ylabel("estimated dominant edge"); ax.set_title("D3 — Passive dominant-edge tracking"); ax.legend(); fig.tight_layout(); fig.savefig(out/"figures"/"D3_online_edge_tracking.png",dpi=180); plt.close(fig)

    # D3b error distribution by memory.
    fig,ax=plt.subplots(figsize=(6.5,4.6)); data=[]; labels=[]
    for p in cfgall["memories"]:
        data.append([r["median_rel_error"] for r in rows if r["memory"]==p and r["median_rel_error"] is not None]); labels.append(f"p={p}")
    ax.boxplot(data,tick_labels=labels,showfliers=False); ax.axhline(cfgall["controlled_median_rel_error_gate"],linestyle="--",linewidth=1)
    ax.set_ylabel("tail median relative error"); ax.set_title("D3b — Edge-estimation error across STFT cases"); fig.tight_layout(); fig.savefig(out/"figures"/"D3b_error_by_memory.png",dpi=180); plt.close(fig)

    # D3c conditioning.
    fig,ax=plt.subplots(figsize=(6.5,4.6))
    for p in cfgall["memories"]:
        valsc=[r.get("median_condition") for r in rows if r["memory"]==p and r.get("median_condition") is not None]
        ax.scatter([p]*len(valsc),valsc,alpha=.55,s=18)
    ax.set_yscale("log"); ax.set_xlabel("memory p"); ax.set_ylabel("median retained secant condition number"); ax.set_title("D3c — Memory versus secant conditioning"); fig.tight_layout(); fig.savefig(out/"figures"/"D3c_memory_conditioning.png",dpi=180); plt.close(fig)

    # D3d impossibility visual.
    fig,ax=plt.subplots(figsize=(6.6,4.4)); names=["active estimate","full edge A","full edge B"]; valsplot=[d2["estimate_A"],d2["full_lambda_plus_A"],d2["full_lambda_plus_B"]]
    ax.bar(names,valsplot); ax.axhline(d2["active_edge"],linestyle="--",linewidth=1,label="active edge"); ax.set_ylim(0,1.05); ax.set_ylabel("spectral value"); ax.set_title("D3d — Hidden modes are not passively identifiable"); ax.legend(); fig.tight_layout(); fig.savefig(out/"figures"/"D3d_active_spectrum_failure.png",dpi=180); plt.close(fig)

    b=per_mem[str(best)]
    d0max=max(r["abs_error"] for r in d0)
    summary={"d0_max_abs_error":float(d0max),"n_stft_estimator_rows":len(rows),"selected_memory":best,
             "selected_median_rel_error":b["median_rel_error"],"selected_p90_rel_error":b["p90_rel_error"],
             "selected_median_under_fraction":b["median_under_fraction"],
             "identifiability_trajectory_max_difference":d2["trajectory_max_difference"],
             "d0_pass":bool(d0max<5e-4),
             "d1_median_gate_pass":bool(b["median_rel_error"]<cfgall["controlled_median_rel_error_gate"]),
             "d1_p90_gate_pass":bool(b["p90_rel_error"]<cfgall["controlled_p90_rel_error_gate"]),
             "raw_estimate_upper_bound_safe":False}
    if summary["d0_pass"] and summary["d1_median_gate_pass"] and summary["d1_p90_gate_pass"]:
        # Because underestimation is expected and the impossibility test is exact, the correct scientific verdict is YELLOW:
        # useful active-edge estimator, but not a certified full-spectrum bound.
        summary["phase1d_gate"]="YELLOW-GREEN: active edge identifiable; safeguard/margin required"
    else: summary["phase1d_gate"]="REVIEW"
    (out/"summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2)); return summary


def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",default="configs/phase1d_grid.json"); p.add_argument("--out",default="results/phase1d"); a=p.parse_args(); run(a.config,a.out)
if __name__=="__main__": main()
