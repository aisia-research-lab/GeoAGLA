
import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import json
from pathlib import Path
import numpy as np
from experiments.phase1er_repair.run import _case,_errors,_rate
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.geometry.realify import r2c
from geometry_gla.algorithms.minimax import fgla_opt
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.algorithms.online_safe import run_online_policy
C=json.loads(Path('configs/phase1er_grid.json').read_text()); rows=[]
for n_iter in [120,180,240,360]:
 for cfg in C['configs']:
  for seed in C['seeds']:
   op,cstar,rng=_case(cfg,seed,C['near_zero_tol']); spec=transverse_spectrum(cstar,op,C['phase_tol']); lp=float(spec['lambda_plus']); vals,_=np.linalg.eigh(spec['J']); coeff=rng.normal(size=spec['J'].shape[0]); coeff[int(np.argmax(vals))]=0; v=r2c(spec['QU']@coeff); v/=np.linalg.norm(v)
   for eps in C['perturbations']:
    c0=cstar+eps*v;s=np.abs(cstar);fp=fgla_opt(lp); ftr=run_agla_state(c0,c0,s,op,fp['alpha'],fp['beta'],fp['gamma'],n_iter);qf=_rate(_errors(ftr,cstar),C['online_win_fraction'])
    rr=run_online_policy(c0,c0,s,op,n_iter=n_iter,warmup=C['warmup'],block_size=8,memory=3,margin=0.0,lambda_ceiling=C['lambda_ceiling'],svd_rtol=C['svd_rtol'],cond_max=C['cond_max'],alpha_safe=C['alpha_safe'],beta_safe=C['beta_safe'],gamma_safe=C['gamma_safe'],K_safe=C['K_safe'],descent_a=C['descent_a'],policy='dynamic_envelope'); qo=_rate(_errors(rr['trajectory'],cstar),C['online_win_fraction']); edges=[b['edge_state'] for b in rr['blocks'] if b['edge_state'] is not None]
    rows.append({'n_iter':n_iter,'config':cfg['id'],'seed':seed,'epsilon':eps,'q_online':qo,'q_fgla':qf,'ratio':qo/qf,'beats':qo<qf,'final_edge_rel_error':abs(edges[-1]-lp)/lp})
summary=[]
for n in [120,180,240,360]:
 z=[r for r in rows if r['n_iter']==n]; ratios=np.array([r['ratio'] for r in z]); summary.append({'n_iter':n,'n':len(z),'beat_fraction':float(np.mean([r['beats'] for r in z])),'median_ratio':float(np.median(ratios)),'p90_ratio':float(np.percentile(ratios,90)),'median_final_edge_rel_error':float(np.median([r['final_edge_rel_error'] for r in z]))})
Path('results/phase1er/horizon_audit.json').write_text(json.dumps({'rows':rows,'summary':summary},indent=2))
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(6.8,4.5)); xs=[x['n_iter'] for x in summary]; ys=[x['beat_fraction'] for x in summary]; ax.plot(xs,ys,marker='o'); ax.axhline(.70,linestyle='--'); ax.set_ylim(0,1.05); ax.set_xlabel('iteration horizon'); ax.set_ylabel('fraction beating FGLA-opt'); ax.set_title('E-R4 — H4 realization versus horizon'); fig.tight_layout(); fig.savefig('results/phase1er/figures/ER4_horizon_realization.png',dpi=180); plt.close(fig)
print(json.dumps(summary,indent=2))