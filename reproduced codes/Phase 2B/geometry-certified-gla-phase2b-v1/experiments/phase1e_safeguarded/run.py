from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from geometry_gla.operators.stft import AnalysisOperator,periodic_stft_matrix,gaussian_window,hann_window
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.geometry.realify import r2c
from geometry_gla.algorithms.minimax import fgla_opt,oracle_minimax
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.algorithms.online_safe import run_safeguarded_online
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
    if len(idx)<10: return None
    n=max(10,int(np.ceil(fraction*len(idx)))); sel=idx[-n:]; slope,_=np.polyfit(sel,np.log(e[sel]),1); return float(np.exp(slope))

def _run_fixed(c0,cstar,s,op,pars,n_iter):
    tr=run_agla_state(c0,c0,s,op,pars['alpha'],pars['beta'],pars['gamma'],n_iter); return tr,_errors(tr,cstar)

def run(config_path='configs/phase1e_grid.json',out_dir='results/phase1e'):
    C=json.loads(Path(config_path).read_text()); out=Path(out_dir); (out/'figures').mkdir(parents=True,exist_ok=True)
    rows=[]; traces=[]; base_cache={}
    for cfg in C['configs']:
      for seed in C['seeds']:
        op,cstar,rng=_case(cfg,seed,C['near_zero_tol']); spec=transverse_spectrum(cstar,op,C['phase_tol'])
        if spec['neutral_count']!=1: continue
        lp=float(spec['lambda_plus']); lm=float(max(0.0,spec['lambda_minus']))
        vals,vecs=np.linalg.eigh(spec['J']); phase_idx=int(np.argmax(vals)); coeff=rng.normal(size=spec['J'].shape[0]); coeff[phase_idx]=0; v=r2c(spec['QU']@coeff); v/=np.linalg.norm(v)
        for eps in C['perturbations']:
          c0=cstar+eps*v; s=np.abs(cstar); key=(cfg['id'],seed,eps)
          fpars=fgla_opt(lp); otr=oracle_minimax(0.0,lp); full=oracle_minimax(lm,lp) if lm>1e-12 else otr
          ftr,fe=_run_fixed(c0,cstar,s,op,fpars,C['n_iter']); otraj,oe=_run_fixed(c0,cstar,s,op,otr,C['n_iter']); fulltr,fulle=_run_fixed(c0,cstar,s,op,full,C['n_iter'])
          base_cache[key]={'fgla_q_obs':_rate(fe,C['online_win_fraction']),'online_oracle_q_obs':_rate(oe,C['online_win_fraction']),'full_oracle_q_obs':_rate(fulle,C['online_win_fraction']),
                           'fgla_final':float(fe[-1]),'online_oracle_final':float(oe[-1]),'lp':lp,'lm':lm}
          for K in C['block_sizes']:
            for margin in C['margins']:
              rr=run_safeguarded_online(c0,c0,s,op,n_iter=C['n_iter'],warmup=C['warmup'],block_size=K,memory=C['memory'],margin=margin,
                   lambda_ceiling=C['lambda_ceiling'],svd_rtol=C['svd_rtol'],cond_max=C['cond_max'],alpha_safe=C['alpha_safe'],beta_safe=C['beta_safe'],gamma_safe=C['gamma_safe'],K_safe=C['K_safe'],descent_a=C['descent_a'])
              er=_errors(rr['trajectory'],cstar); q=_rate(er,C['online_win_fraction']); blocks=rr['blocks']; late=blocks[-min(C['late_block_count'],len(blocks)):]
              rejects=sum(not b['candidate_accepted'] for b in blocks); late_rej=sum(not b['candidate_accepted'] for b in late)
              fallback_fail=sum(not b['fallback_e1_pass'] for b in blocks if not b['candidate_accepted'])
              e2=[b['e2_ratio'] for b in blocks if np.isfinite(b['e2_ratio'])]
              row={'config':cfg['id'],'seed':seed,'epsilon':eps,'block_size':K,'margin':margin,'lambda_plus':lp,'lambda_minus':lm,
                   'q_online':q,'q_fgla_opt':base_cache[key]['fgla_q_obs'],'q_oracle0':base_cache[key]['online_oracle_q_obs'],'final_error':float(er[-1]),
                   'reject_fraction':rejects/max(1,len(blocks)),'late_reject_fraction':late_rej/max(1,len(late)),'n_blocks':len(blocks),'fallback_e1_failures':fallback_fail,
                   'max_e2_ratio':float(max(e2)) if e2 else None,'median_e2_ratio':float(np.median(e2)) if e2 else None,
                   'beats_fgla':bool(q is not None and base_cache[key]['fgla_q_obs'] is not None and q<base_cache[key]['fgla_q_obs'])}
              rows.append(row)
              if cfg['id']=='g24_w8_h4_f8' and seed==0 and eps==C['perturbations'][0] and K==4:
                  traces.append({'margin':margin,'errors':er.tolist(),'blocks':blocks,'fgla_errors':fe.tolist(),'oracle_errors':oe.tolist(),'lambda_plus':lp})
          print('Phase-1E',cfg['id'],'seed',seed,'eps',eps)
    (out/'main_runs.json').write_text(json.dumps(rows,indent=2,allow_nan=True));
    with (out/'main_runs.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    # Select online setting by: no safe-fallback E1 failures, then high beat fraction,
    # low late rejection, and low median q ratio.
    settings=[]
    for K in C['block_sizes']:
      for m in C['margins']:
        rr=[r for r in rows if r['block_size']==K and r['margin']==m and r['q_online'] is not None]
        beat=float(np.mean([r['beats_fgla'] for r in rr])); late=float(np.mean([r['late_reject_fraction'] for r in rr])); rej=float(np.mean([r['reject_fraction'] for r in rr]))
        ratios=np.asarray([r['q_online']/r['q_fgla_opt'] for r in rr if r['q_fgla_opt']]); ff=sum(r['fallback_e1_failures'] for r in rr)
        settings.append({'block_size':K,'margin':m,'n':len(rr),'beat_fraction':beat,'mean_late_reject_fraction':late,'mean_reject_fraction':rej,
                         'median_q_ratio_vs_fgla':float(np.median(ratios)),'p90_q_ratio_vs_fgla':float(np.percentile(ratios,90)),'fallback_e1_failures':ff})
    admiss=[x for x in settings if x['fallback_e1_failures']==0]
    best=min(admiss if admiss else settings,key=lambda x:(-x['beat_fraction'],x['mean_late_reject_fraction'],x['median_q_ratio_vs_fgla']))
    (out/'setting_selection.json').write_text(json.dumps({'settings':settings,'selected':best},indent=2))

    # Hostile estimator perturbation on selected setting, one perturbation per regular case.
    hostile=[]
    for cfg in C['configs']:
      for seed in C['seeds']:
        op,cstar,rng=_case(cfg,seed,C['near_zero_tol']); spec=transverse_spectrum(cstar,op,C['phase_tol']); vals,_=np.linalg.eigh(spec['J']); coeff=rng.normal(size=spec['J'].shape[0]); coeff[int(np.argmax(vals))]=0; v=r2c(spec['QU']@coeff); v/=np.linalg.norm(v); c0=cstar+C['perturbations'][0]*v; s=np.abs(cstar)
        for bias in C['hostile_biases']:
          rr=run_safeguarded_online(c0,c0,s,op,n_iter=C['n_iter'],warmup=C['warmup'],block_size=best['block_size'],memory=C['memory'],margin=best['margin'],lambda_ceiling=C['lambda_ceiling'],svd_rtol=C['svd_rtol'],cond_max=C['cond_max'],alpha_safe=C['alpha_safe'],beta_safe=C['beta_safe'],gamma_safe=C['gamma_safe'],K_safe=C['K_safe'],descent_a=C['descent_a'],estimator_bias=bias)
          er=_errors(rr['trajectory'],cstar); blocks=rr['blocks']; hostile.append({'config':cfg['id'],'seed':seed,'bias':bias,'final_error':float(er[-1]),'initial_error':float(er[0]),'converged':bool(er[-1]<er[0]),
                    'reject_fraction':float(np.mean([not b['candidate_accepted'] for b in blocks])),'fallback_e1_failures':sum(not b['fallback_e1_pass'] for b in blocks if not b['candidate_accepted'])})
    (out/'hostile_estimator.json').write_text(json.dumps(hostile,indent=2))

    # Figures.
    fig,ax=plt.subplots(figsize=(7.2,4.8))
    for t in traces:
        ax.semilogy(t['errors'],label=f"online margin={t['margin']}")
    if traces:
        ax.semilogy(traces[0]['fgla_errors'],linestyle='--',label='FGLA-opt'); ax.semilogy(traces[0]['oracle_errors'],linestyle=':',label='Oracle-[0,lambda+]')
    ax.set_xlabel('iteration'); ax.set_ylabel('orbit error'); ax.set_title('D4 — Safeguarded online acceleration'); ax.legend(); fig.tight_layout(); fig.savefig(out/'figures'/'D4_online_acceleration.png',dpi=180); plt.close(fig)

    fig,ax=plt.subplots(figsize=(7.2,4.6))
    if traces:
      t=min(traces,key=lambda z:abs(z['margin']-best['margin'])); xs=[b['end_iter'] for b in t['blocks']]; ys=[0 if b['candidate_accepted'] else 1 for b in t['blocks']]
      ax.scatter(xs,ys); ax.set_yticks([0,1],['accept','reject']); ax.set_xlabel('iteration'); ax.set_title('D5 — Checkpoint decisions for selected online setting')
    fig.tight_layout(); fig.savefig(out/'figures'/'D5_safeguard_decisions.png',dpi=180); plt.close(fig)

    fig,ax=plt.subplots(figsize=(7.0,4.6)); labels=[f"K={s['block_size']}, m={s['margin']}" for s in settings]; vals=[s['beat_fraction'] for s in settings]; ax.bar(np.arange(len(vals)),vals); ax.set_xticks(np.arange(len(vals)),labels,rotation=55,ha='right'); ax.set_ylim(0,1.05); ax.set_ylabel('fraction beating FGLA-opt'); ax.set_title('D5b — H4 performance across safeguard settings'); fig.tight_layout(); fig.savefig(out/'figures'/'D5b_h4_setting_sweep.png',dpi=180); plt.close(fig)

    h4=bool(best['beat_fraction']>=0.70 and best['median_q_ratio_vs_fgla']<1.0)
    h5=bool(best['mean_late_reject_fraction']<=0.05)
    e1=bool(best['fallback_e1_failures']==0)
    hostile_pass=bool(all(r['converged'] and r['fallback_e1_failures']==0 for r in hostile))
    e2vals=[r['max_e2_ratio'] for r in rows if r['block_size']==best['block_size'] and r['margin']==best['margin'] and r['max_e2_ratio'] is not None]
    summary={'n_main_runs':len(rows),'selected_setting':best,'H4_performance_pass':h4,'H5_eventual_inactivity_pass':h5,'E1_safe_fallback_pass':e1,'hostile_estimator_convergence_pass':hostile_pass,
             'selected_max_observed_e2_ratio':float(max(e2vals)) if e2vals else None,
             'phase1e_gate':'GREEN' if (h4 and h5 and e1 and hostile_pass) else 'YELLOW: inspect safeguard/performance diagnostics'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2)); return summary


def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',default='configs/phase1e_grid.json'); p.add_argument('--out',default='results/phase1e'); a=p.parse_args(); run(a.config,a.out)
if __name__=='__main__': main()
