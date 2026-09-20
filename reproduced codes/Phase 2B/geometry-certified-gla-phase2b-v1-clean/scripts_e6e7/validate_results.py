#!/usr/bin/env python3
import argparse, math
from pathlib import Path
from common import *
ap=argparse.ArgumentParser(); ap.add_argument('--ledger',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); rs=read_csv(a.ledger); issues=[]; ids=[]
for i,r in enumerate(rs):
 cid=r.get('case_id'); ids.append(cid); lm=fnum(r.get('lambda_minus')); lp=fnum(r.get('lambda_plus'))
 if lm is None or lp is None: issues.append({'case':cid,'issue':'missing_spectrum'})
 elif not (-1e-10<=lm<=lp<=1+1e-10): issues.append({'case':cid,'issue':'illegal_spectrum','lambda_minus':lm,'lambda_plus':lp})
 for k in ['q_gla_pred','q_fgla_pred','q_oracle_pred']:
  v=fnum(r.get(k));
  if v is None or not math.isfinite(v): issues.append({'case':cid,'issue':'invalid_'+k})
 qg,qf,qo=map(lambda k:fnum(r.get(k)),['q_gla_pred','q_fgla_pred','q_oracle_pred'])
 if None not in (qg,qf,qo) and not (qo<qf<qg): issues.append({'case':cid,'issue':'predicted_ordering_fail'})
for cid in set(ids):
 if ids.count(cid)>1: issues.append({'case':cid,'issue':'duplicate_case_id'})
rep={'n_rows':len(rs),'n_issues':len(issues),'pass':len(issues)==0,'issues':issues}
out=Path(a.out); out.mkdir(parents=True,exist_ok=True); dump_json(rep,out/'integrity_report.json'); print(rep['pass'],rep['n_issues'])
