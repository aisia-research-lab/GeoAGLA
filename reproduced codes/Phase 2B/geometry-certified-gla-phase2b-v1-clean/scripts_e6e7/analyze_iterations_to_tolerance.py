#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import *
ap=argparse.ArgumentParser(); ap.add_argument('--traces',required=True,help='CSV columns case_id,method,iteration,error'); ap.add_argument('--tolerances',default='1e-3,1e-4,1e-5'); ap.add_argument('--out',required=True); a=ap.parse_args(); rs=read_csv(a.traces); tol=[float(x) for x in a.tolerances.split(',')]
by={}
for r in rs: by.setdefault((r['case_id'],r['method']),[]).append((int(r['iteration']),float(r['error'])))
outrows=[]
for (cid,m),tr in by.items():
 tr=sorted(tr)
 for t in tol:
  hit=next((i for i,e in tr if e<=t),None); outrows.append({'case_id':cid,'method':m,'tolerance':t,'iterations_to_tolerance':hit,'censored':hit is None})
out=Path(a.out); out.mkdir(parents=True,exist_ok=True); write_csv(outrows,out/'iterations_to_tolerance.csv'); dump_json(outrows,out/'iterations_to_tolerance.json')
