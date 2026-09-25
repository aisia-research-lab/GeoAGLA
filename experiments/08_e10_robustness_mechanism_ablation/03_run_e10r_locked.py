from __future__ import annotations
import sys, json, csv, argparse, importlib.util
from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
base=ROOT/'experiments'/'05_real_audio_basin_transfer'/'03_phase2b_real_audio_basin_sweep.py'
spec=importlib.util.spec_from_file_location('phase2b_frozen',base)
B=importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.algorithms.online_ablation import run_online_ablation

VARIANTS=['fgla_oracle','fixed_1e_oracle','online_raw','online_env','online_fallback','online_full']

def run_variant(name,c0,cstar,s,op,lp,C):
    if name=='fgla_oracle':
        tr,er,q=B._fixed(c0,cstar,s,op,fgla_opt(lp),C['n_iter'],C['rate_tail_fraction'],C['rate_floor']); blocks=[]
    elif name=='fixed_1e_oracle':
        tr,er,q=B._fixed(c0,cstar,s,op,oracle_minimax(0.0,lp),C['n_iter'],C['rate_tail_fraction'],C['rate_floor']); blocks=[]
    else:
        kw=dict(n_iter=C['n_iter'],warmup=C['warmup'],block_size=C['block_size'],memory=C['memory'],margin=C['margin'],
                lambda_ceiling=C['lambda_ceiling'],svd_rtol=C['svd_rtol'],cond_max=C['cond_max'],alpha_safe=C['alpha_safe'],
                beta_safe=C['beta_safe'],gamma_safe=C['gamma_safe'],K_safe=C['K_safe'],descent_a=C['descent_a'])
        if name=='online_full': rr=run_online_policy(c0,c0,s,op,policy='dynamic_envelope',**kw)
        elif name=='online_raw': rr=run_online_ablation(c0,c0,s,op,use_envelope=False,use_fallback=False,**kw)
        elif name=='online_env': rr=run_online_ablation(c0,c0,s,op,use_envelope=True,use_fallback=False,**kw)
        elif name=='online_fallback': rr=run_online_ablation(c0,c0,s,op,use_envelope=False,use_fallback=True,**kw)
        else: raise ValueError(name)
        tr=rr['trajectory']; er=B._errors(tr,cstar); q=B._rate(er,C['rate_tail_fraction'],C['rate_floor']); blocks=rr['blocks']
    fm=B._magnitude_residual(tr[-1],s)
    succ=B._success(float(B.orbit_distance(c0,cstar)),float(er[-1]),fm,C)
    return tr,er,q,fm,succ,blocks

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--audio-dir',required=True)
    ap.add_argument('--out',default=str(ROOT/'results/08_e10r_locked'))
    ap.add_argument('--seed-mode',choices=['historical_batch2','global'],default='historical_batch2')
    a=ap.parse_args()
    C=json.loads((ROOT/'configs/phase2b_grid.json').read_text())
    G=pd.read_csv(ROOT/'experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv')
    gmap={(r.file,r.profile):float(r.lambda_plus) for r in G.itertuples()}
    paths=sorted(p for p in Path(a.audio_dir).rglob('*') if p.is_file() and p.suffix.lower()=='.wav')
    pmap={p.name:p for p in paths}
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    rows=[]; events=[]
    for global_fi,name in enumerate(sorted(set(G.file))):
        if name not in pmap: raise FileNotFoundError(name)
        path=pmap[name]; x,meta=B.load_audio(path,C['target_sample_rate'],C['excerpt_length'])
        # Historical Kaggle jobs processed sorted files in consecutive batches of two and reset fi inside each batch.
        fi=(global_fi % 2) if a.seed_mode=='historical_batch2' else global_fi
        for pi,P in enumerate(C['stft_profiles']):
            key=(name,P['id'])
            if key not in gmap: continue
            win=B._window(P['window'],P['window_length'])
            op=FFTAnalysisOperator(len(x),win,P['hop'],P['n_fft'])
            cstar=op.q_analyze(x); s=np.abs(cstar); xstar=x
            lp=gmap[key]
            for init in C['basin_initializations']:
                for level in init['levels']:
                    for seed in C['seeds']:
                        init_seed=10000*fi+100*pi+10*seed+int(round(1000*level))
                        c0=B._init_state(init['kind'],level,init_seed,cstar,s,xstar,op)
                        init_err=float(B.orbit_distance(c0,cstar)); init_mag=B._magnitude_residual(c0,s)
                        run_key=f'{name}|{P["id"]}|{init["kind"]}|{level:g}|{seed}'
                        for v in VARIANTS:
                            tr,er,q,fm,succ,blocks=run_variant(v,c0,cstar,s,op,lp,C)
                            rows.append(dict(run_key=run_key,file=name,profile=P['id'],init_kind=init['kind'],level=float(level),
                                seed=int(seed),init_seed=int(init_seed),seed_mode=a.seed_mode,variant=v,lambda_plus=lp,
                                initial_orbit_error=init_err,initial_magnitude_residual=init_mag,final_orbit_error=float(er[-1]),
                                final_magnitude_residual=fm,success=bool(succ),q_fitted=q,n_blocks=len(blocks),
                                n_checkpoint_reject=int(sum(not b.get('candidate_accepted',b.get('checkpoint_accepted',True)) for b in blocks)),
                                n_fallback=int(sum(bool(b.get('fallback_used',False)) for b in blocks))))
                            for b in blocks: events.append(dict(run_key=run_key,variant=v,lambda_plus=lp,**b))
    def wc(p,data):
        if not data: return
        fields=sorted(set().union(*(r.keys() for r in data)))
        with p.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(data)
    wc(out/'e10r_run_ledger.csv',rows); wc(out/'e10r_event_ledger.csv',events)
    (out/'e10r_run_ledger.json').write_text(json.dumps(rows,indent=2,allow_nan=True))
    expected=395*12*6
    if len(rows)!=expected: raise RuntimeError(f'closure cardinality failed: {len(rows)} != {expected}')
    print('PASS: rows',len(rows),'paired instances',len(rows)//6,'locked geometry cases',len(G))
if __name__=='__main__': main()
