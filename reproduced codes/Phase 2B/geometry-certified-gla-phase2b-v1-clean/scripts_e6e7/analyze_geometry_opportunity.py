#!/usr/bin/env python3
import argparse, math
from pathlib import Path
from common import *
import numpy as np
import matplotlib.pyplot as plt
ap=argparse.ArgumentParser(); ap.add_argument('--ledger',required=True); ap.add_argument('--out',required=True); ap.add_argument('--denom-tol',type=float,default=1e-8); a=ap.parse_args()
r=read_csv(a.ledger)
for x in r:
 for k in ['lambda_minus','lambda_plus','spectral_width','transverse_gap','delta_oracle_pred','delta_oracle_obs','delta_online_obs','r_capture','q_online_obs','q_fgla_obs','q_oracle_obs']:
  x[k]=fnum(x.get(k))
valid=[x for x in r if x['delta_oracle_obs'] is not None and x['delta_online_obs'] is not None]
cap=[x['delta_online_obs']/x['delta_oracle_obs'] for x in valid if x['delta_oracle_obs']>a.denom_tol]
def corr(x,y,rank=False):
 x=np.asarray(x,float); y=np.asarray(y,float)
 if rank:
  x=np.argsort(np.argsort(x)); y=np.argsort(np.argsort(y))
 return float(np.corrcoef(x,y)[0,1]) if len(x)>1 else None
xo=[x['delta_oracle_obs'] for x in valid]; yo=[x['delta_online_obs'] for x in valid]
summary={'n_cases':len(r),'n_online_valid':len(valid),'denom_tol':a.denom_tol,'n_capture_valid':len(cap),
 'oracle_opportunity':{'median':median(xo),'iqr':[quantile(xo,.25),quantile(xo,.75)],'p10':quantile(xo,.1),'p90':quantile(xo,.9)},
 'online_gain':{'median':median(yo),'iqr':[quantile(yo,.25),quantile(yo,.75)]},
 'capture':{'median':median(cap),'iqr':[quantile(cap,.25),quantile(cap,.75)],'p10':quantile(cap,.1),'p90':quantile(cap,.9),'bootstrap95_median':bootstrap_ci(cap),
 'frac_gt0':sum(v>0 for v in cap)/len(cap) if cap else None,'frac_ge_0p5':sum(v>=.5 for v in cap)/len(cap) if cap else None,'frac_ge_0p8':sum(v>=.8 for v in cap)/len(cap) if cap else None,'frac_gt1':sum(v>1 for v in cap)/len(cap) if cap else None,'frac_lt0':sum(v<0 for v in cap)/len(cap) if cap else None},
 'correlation':{'pearson':corr(xo,yo),'spearman':corr(xo,yo,True)}}
out=Path(a.out); (out/'figures').mkdir(parents=True,exist_ok=True); dump_json(summary,out/'e6_summary.json')
plots=[('lambda_plus','delta_oracle_obs','A1a_oracle_vs_lambda_plus.png'),('transverse_gap','delta_oracle_obs','A1b_oracle_vs_gap.png'),('spectral_width','delta_oracle_obs','A1c_oracle_vs_width.png'),('delta_oracle_obs','delta_online_obs','A2_online_vs_oracle_gain.png')]
for xk,yk,n in plots:
 xx=[z[xk] for z in valid if z[xk] is not None and z[yk] is not None]; yy=[z[yk] for z in valid if z[xk] is not None and z[yk] is not None]
 fig,ax=plt.subplots(figsize=(5.4,4.1)); ax.scatter(xx,yy,s=24); ax.set_xlabel(xk); ax.set_ylabel(yk); ax.grid(alpha=.25)
 if xk=='delta_oracle_obs' and xx:
  lo=min(min(xx),min(yy),0); hi=max(max(xx),max(yy),0); ax.plot([lo,hi],[lo,hi],'--',lw=1); ax.axhline(0,lw=1)
 fig.tight_layout(); fig.savefig(out/'figures'/n,dpi=220); plt.close(fig)
print(summary)
