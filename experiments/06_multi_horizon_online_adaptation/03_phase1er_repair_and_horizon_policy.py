from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import argparse,csv,json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from geometry_gla.operators.stft import AnalysisOperator,periodic_stft_matrix,gaussian_window,hann_window
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.geometry.realify import r2c
from geometry_gla.algorithms.minimax import fgla_opt,oracle_minimax
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.metrics.phase import orbit_distance

def _window(kind,n): return gaussian_window(n) if kind=='gaussian' else hann_window(n)
def _case(cfg,seed,tol):
    rng=np.random.default_rng(seed); T=periodic_stft_matrix(cfg['signal_length'],_window(cfg['window'],cfg['window_length']),cfg['hop'],cfg['n_fft']); op=AnalysisOperator(T)
    x=rng.normal(size=cfg['signal_length'])+1j*rng.normal(size=cfg['signal_length']); c=op.analyze(x)
    if np.min(np.abs(c))<=tol: raise RuntimeError('near-zero coefficient')
    return op,c,rng

def _errors(tr,cstar): return np.asarray([orbit_distance(z,cstar) for z in tr],float)
def _rate(errors,fraction=.35,floor=1e-13):
    e=np.asarray(errors); idx=np.where(np.isfinite(e)&(e>floor))[0]; idx=idx[idx>=5]
    if len(idx)<10:return None
    n=max(10,int(np.ceil(fraction*len(idx)))); sel=idx[-n:]; slope,_=np.polyfit(sel,np.log(e[sel]),1); return float(np.exp(slope))
def _fixed(c0,cstar,s,op,p,n):
    tr=run_agla_state(c0,c0,s,op,p['alpha'],p['beta'],p['gamma'],n); e=_errors(tr,cstar); return e,_rate(e)
def _label(p):
    if p['name']=='thresholded': return f"thresholded_{p['update_rel_tol']}"
    if p['name']=='ema': return f"ema_{p['ema_eta']}"
    return p['name']

def run(config_path='configs/phase1er_grid.json',out_dir='results/phase1er'):
    C=json.loads(Path(config_path).read_text()); out=Path(out_dir); (out/'figures').mkdir(parents=True,exist_ok=True)
    rows=[]; traces=[]
    for cfg in C['configs']:
      for seed in C['seeds']:
        op,cstar,rng=_case(cfg,seed,C['near_zero_tol']); spec=transverse_spectrum(cstar,op,C['phase_tol'])
        if spec['neutral_count']!=1: continue
        lp=float(spec['lambda_plus']); vals,_=np.linalg.eigh(spec['J']); coeff=rng.normal(size=spec['J'].shape[0]); coeff[int(np.argmax(vals))]=0; v=r2c(spec['QU']@coeff); v/=np.linalg.norm(v)
        for eps in C['perturbations']:
          c0=cstar+eps*v; s=np.abs(cstar); fe,qf=_fixed(c0,cstar,s,op,fgla_opt(lp),C['n_iter']); oe,qo=_fixed(c0,cstar,s,op,oracle_minimax(0.0,lp),C['n_iter'])
          for pol in C['policies']:
            kw={k:v for k,v in pol.items() if k!='name'}
            rr=run_online_policy(c0,c0,s,op,n_iter=C['n_iter'],warmup=C['warmup'],block_size=C['block_size'],memory=C['memory'],margin=C['margin'],lambda_ceiling=C['lambda_ceiling'],svd_rtol=C['svd_rtol'],cond_max=C['cond_max'],alpha_safe=C['alpha_safe'],beta_safe=C['beta_safe'],gamma_safe=C['gamma_safe'],K_safe=C['K_safe'],descent_a=C['descent_a'],policy=pol['name'],oracle_edge=lp if pol['name']=='oracle_frozen' else None,**kw)
            er=_errors(rr['trajectory'],cstar); q=_rate(er,C['online_win_fraction']); blocks=rr['blocks']; late=blocks[-min(C['late_block_count'],len(blocks)):]
            edges=np.asarray([b['edge_state'] for b in blocks if b['edge_state'] is not None],float); changes=sum(bool(b['edge_changed']) for b in blocks)
            row={'config':cfg['id'],'seed':seed,'epsilon':eps,'policy':_label(pol),'lambda_plus':lp,'q_online':q,'q_fgla':qf,'q_oracle0':qo,
                 'q_ratio_fgla':q/qf if q and qf else None,'q_ratio_oracle':q/qo if q and qo else None,'beats_fgla':bool(q and qf and q<qf),
                 'final_error':float(er[-1]),'reject_fraction':float(np.mean([not b['candidate_accepted'] for b in blocks])),'late_reject_fraction':float(np.mean([not b['candidate_accepted'] for b in late])),
                 'fallback_e1_failures':sum(not b['fallback_e1_pass'] for b in blocks if not b['candidate_accepted']),'edge_updates':changes,
                 'final_edge_rel_error':float(abs(edges[-1]-lp)/lp) if len(edges) else None,'edge_range':float(np.ptp(edges)) if len(edges) else None}
            rows.append(row)
            if cfg['id']=='g24_w8_h4_f8' and seed==0 and eps==C['perturbations'][0]: traces.append({'policy':_label(pol),'errors':er.tolist(),'blocks':blocks,'fgla':fe.tolist(),'oracle':oe.tolist()})
          print('Phase-1E-R',cfg['id'],seed,eps)
    (out/'failure_decomposition.json').write_text(json.dumps(rows,indent=2,allow_nan=True))
    with (out/'failure_decomposition.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    agg=[]
    for name in sorted(set(r['policy'] for r in rows)):
        z=[r for r in rows if r['policy']==name and r['q_online'] is not None]; ratios=np.array([r['q_ratio_fgla'] for r in z]); orat=np.array([r['q_ratio_oracle'] for r in z])
        agg.append({'policy':name,'n':len(z),'beat_fraction':float(np.mean([r['beats_fgla'] for r in z])),'median_q_ratio_fgla':float(np.median(ratios)),'p90_q_ratio_fgla':float(np.percentile(ratios,90)),
                    'median_q_ratio_oracle':float(np.median(orat)),'mean_late_reject_fraction':float(np.mean([r['late_reject_fraction'] for r in z])),'mean_reject_fraction':float(np.mean([r['reject_fraction'] for r in z])),
                    'fallback_e1_failures':int(sum(r['fallback_e1_failures'] for r in z)),'median_edge_updates':float(np.median([r['edge_updates'] for r in z])),'median_final_edge_rel_error':float(np.median([r['final_edge_rel_error'] for r in z]))})
    # Repair selection excludes oracle control and uses pre-frozen H4/H5/E1 gates.
    practical=[a for a in agg if a['policy']!='oracle_frozen' and a['fallback_e1_failures']==0]
    best=min(practical,key=lambda a:(-a['beat_fraction'],a['p90_q_ratio_fgla'],a['mean_late_reject_fraction']))
    oracle=[a for a in agg if a['policy']=='oracle_frozen'][0]
    h4=best['beat_fraction']>=0.70 and best['median_q_ratio_fgla']<1.0; h5=best['mean_late_reject_fraction']<=0.05; e1=best['fallback_e1_failures']==0
    # Diagnosis: if frozen oracle realizes its fixed-method rate closely but dynamic policies do not, switching/estimation is implicated.
    diagnosis={'oracle_control':oracle,'selected_repair':best,'oracle_control_close_to_fixed_oracle':bool(oracle['median_q_ratio_oracle']<=1.01),
               'selected_h4_pass':bool(h4),'selected_h5_pass':bool(h5),'selected_e1_pass':bool(e1)}
    (out/'policy_summary.json').write_text(json.dumps({'policies':agg,'diagnosis':diagnosis},indent=2))
    summary={'n_runs':len(rows),'selected_repair':best,'oracle_control':oracle,'H4_performance_pass':bool(h4),'H5_eventual_inactivity_pass':bool(h5),'E1_safe_fallback_pass':bool(e1),
             'phase1er_gate':'GREEN' if h4 and h5 and e1 else 'YELLOW: failure decomposed; repair not yet sufficient'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    # Figures
    fig,ax=plt.subplots(figsize=(8.0,4.8)); names=[a['policy'] for a in agg]; vals=[a['median_q_ratio_fgla'] for a in agg]; ax.bar(np.arange(len(vals)),vals); ax.axhline(1.0,linestyle='--'); ax.set_xticks(np.arange(len(vals)),names,rotation=50,ha='right'); ax.set_ylabel('median q_online / q_FGLA'); ax.set_title('E-R1 — Rate-realization decomposition'); fig.tight_layout(); fig.savefig(out/'figures'/'ER1_rate_realization.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.0,4.8)); vals=[a['beat_fraction'] for a in agg]; ax.bar(np.arange(len(vals)),vals); ax.axhline(.70,linestyle='--'); ax.set_xticks(np.arange(len(vals)),names,rotation=50,ha='right'); ax.set_ylabel('fraction beating FGLA-opt'); ax.set_ylim(0,1.05); ax.set_title('E-R2 — H4 by adaptation policy'); fig.tight_layout(); fig.savefig(out/'figures'/'ER2_h4_policy.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.4,4.8)); chosen={'dynamic_envelope','freeze_first','freeze_calibrated','oracle_frozen'}
    for t in traces:
        if t['policy'] in chosen: ax.semilogy(t['errors'],label=t['policy'])
    if traces: ax.semilogy(traces[0]['fgla'],linestyle='--',label='FGLA-opt'); ax.semilogy(traces[0]['oracle'],linestyle=':',label='fixed Oracle-[0,lambda+]')
    ax.set_xlabel('iteration'); ax.set_ylabel('orbit error'); ax.set_title('E-R3 — Switching versus frozen synthesis'); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(out/'figures'/'ER3_switching_vs_frozen.png',dpi=180); plt.close(fig)
    print(json.dumps(summary,indent=2)); return summary

def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',default='configs/phase1er_grid.json'); p.add_argument('--out',default='results/phase1er'); a=p.parse_args(); run(a.config,a.out)
if __name__=='__main__': main()