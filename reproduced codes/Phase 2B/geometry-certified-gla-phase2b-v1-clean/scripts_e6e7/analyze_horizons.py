#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import *
ap=argparse.ArgumentParser(); ap.add_argument('--horizon',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
x=load_json(a.horizon); rows=x['rows'] if isinstance(x,dict) else x
by={}
for r in rows: by.setdefault(int(r['n_iter']),[]).append(r)
s=[]
for h,rs in sorted(by.items()):
 ratios=[float(z['ratio']) for z in rs]; edge=[float(z['final_edge_rel_error']) for z in rs if z.get('final_edge_rel_error') is not None]
 s.append({'horizon':h,'n':len(rs),'beat_fraction':sum(bool(z['beats']) for z in rs)/len(rs),'median_ratio':median(ratios),'p90_ratio':quantile(ratios,.9),'median_edge_rel_error':median(edge)})
out=Path(a.out); out.mkdir(parents=True,exist_ok=True); dump_json({'rows':s},out/'horizon_summary_recomputed.json'); write_csv(s,out/'horizon_summary_recomputed.csv'); print(s)
