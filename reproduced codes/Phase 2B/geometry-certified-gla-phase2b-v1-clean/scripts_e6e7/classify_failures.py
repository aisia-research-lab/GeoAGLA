#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import *
ap=argparse.ArgumentParser(); ap.add_argument('--ledger',required=True); ap.add_argument('--out',required=True); ap.add_argument('--opportunity-tol',type=float,default=0.001); ap.add_argument('--near-degenerate',type=float,default=0.999); ap.add_argument('--edge-tol',type=float,default=.005); a=ap.parse_args()
rows=read_csv(a.ledger); fails=[]
for r in rows:
 q=fnum(r.get('q_online_obs')); f=fnum(r.get('q_fgla_obs'))
 if q is None or f is None or q<f: continue
 opp=fnum(r.get('delta_oracle_obs')); lp=fnum(r.get('lambda_plus')); ee=fnum(r.get('edge_rel_error_final'))
 if opp is not None and opp<=a.opportunity_tol: c='negligible_oracle_opportunity'
 elif lp is not None and lp>=a.near_degenerate: c='near_degenerate_geometry'
 elif ee is not None and ee>a.edge_tol: c='estimator_not_mature'
 else:c='unexplained'
 z=dict(r); z['failure_category']=c; fails.append(z)
out=Path(a.out); out.mkdir(parents=True,exist_ok=True); write_csv(fails,out/'failure_cases.csv'); counts={}
for z in fails: counts[z['failure_category']]=counts.get(z['failure_category'],0)+1
dump_json({'n_failures':len(fails),'counts':counts,'thresholds':{'opportunity_tol':a.opportunity_tol,'near_degenerate':a.near_degenerate,'edge_tol':a.edge_tol}},out/'failure_summary.json'); print(counts)
