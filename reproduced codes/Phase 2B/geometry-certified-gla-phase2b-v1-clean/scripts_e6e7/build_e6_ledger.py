#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import *
ap=argparse.ArgumentParser(); ap.add_argument('--h2',required=True); ap.add_argument('--horizon',required=True); ap.add_argument('--out',required=True); ap.add_argument('--horizon-value',type=int,default=None); a=ap.parse_args()
h2=load_json(a.h2); hz=load_json(a.horizon); hzrows=hz['rows'] if isinstance(hz,dict) else hz
# Default to the controlled H2 observation horizon; never mix rate estimates from different horizons.
controlled_horizons=[int(r.get('fit_hi',0)) for r in h2 if r.get('fit_hi') is not None]
H=a.horizon_value or max(controlled_horizons)
on={(r['config'],int(r['seed']),float(r['epsilon'])):r for r in hzrows if int(r['n_iter'])==H}
base={}
for r in h2:
 k=(r['config'],int(r['seed']),float(r['epsilon'])); base.setdefault(k,{})[r['method']]=r
rows=[]
for k,m in sorted(base.items()):
 if not {'gla','fgla_opt','oracle'}<=set(m): continue
 g,f,o=m['gla'],m['fgla_opt'],m['oracle']; z=on.get(k,{})
 dm=float(g['lambda_plus'])-float(g['lambda_minus']); gap=1-float(g['lambda_plus'])
 dpo=float(f['q_pred'])-float(o['q_pred']); do=float(f['q_obs'])-float(o['q_obs'])
 qonline=fnum(z.get('q_online')); qfgla_same=fnum(z.get('q_fgla'))
 # Only compute Online-vs-Oracle capture when the Online/FGLA horizon matches the H2 fit horizon.
 don=None if qonline is None else float(f['q_obs'])-qonline
 rows.append(dict(case_id=f"{k[0]}__s{k[1]}__e{k[2]:g}",config=k[0],seed=k[1],epsilon=k[2],horizon=H,
 lambda_minus=g['lambda_minus'],lambda_plus=g['lambda_plus'],spectral_width=dm,transverse_gap=gap,
 q_gla_pred=g['q_pred'],q_fgla_pred=f['q_pred'],q_oracle_pred=o['q_pred'],q_gla_obs=g['q_obs'],q_fgla_obs=f['q_obs'],q_oracle_obs=o['q_obs'],
 q_online_obs=qonline,q_fgla_online_horizon=qfgla_same,edge_rel_error_final=z.get('final_edge_rel_error'),online_beats_fgla=z.get('beats'),
 delta_oracle_pred=dpo,delta_oracle_obs=do,delta_online_obs=don,
 r_capture=(don/do if don is not None and do>1e-8 else None),fit_lo=o.get('fit_lo'),fit_hi=o.get('fit_hi')))
out=Path(a.out); out.mkdir(parents=True,exist_ok=True); write_csv(rows,out/'e6_case_ledger.csv'); dump_json(rows,out/'e6_case_ledger.json')
print(f'wrote {len(rows)} cases at horizon {H}')
