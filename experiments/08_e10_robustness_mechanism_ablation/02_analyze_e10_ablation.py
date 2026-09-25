from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd
V=['fgla_oracle','fixed_1e_oracle','online_raw','online_env','online_fallback','online_full']
CON=[('fgla_oracle','fixed_1e_oracle'),('fixed_1e_oracle','online_raw'),('online_raw','online_env'),('online_raw','online_fallback'),('online_env','online_full'),('fgla_oracle','online_full')]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('ledger'); ap.add_argument('--out',default=None); ap.add_argument('--B',type=int,default=5000); ap.add_argument('--seed',type=int,default=20270920); a=ap.parse_args()
 df=pd.read_csv(a.ledger); out=Path(a.out or Path(a.ledger).parent); out.mkdir(parents=True,exist_ok=True)
 counts=df.groupby('run_key').variant.nunique(); assert counts.min()==counts.max()==len(V),'incomplete pairing'
 summary=df.groupby('variant').success.agg(['count','sum','mean']).reindex(V).reset_index(); summary.to_csv(out/'e10_success_summary.csv',index=False)
 wide=df.pivot(index='run_key',columns='variant',values='success').astype(bool); meta=df.drop_duplicates('run_key').set_index('run_key'); wide=wide.join(meta[['file']])
 rng=np.random.default_rng(a.seed); files=wide.file.unique(); boot={c:[] for c in CON}
 for _ in range(a.B):
  samp=rng.choice(files,size=len(files),replace=True); chunks=[wide[wide.file==f] for f in samp]; z=pd.concat(chunks,ignore_index=True)
  for c in CON: boot[c].append(float(z[c[1]].mean()-z[c[0]].mean()))
 rows=[]
 for A,B in CON:
  z=wide; rescue=float((~z[A]&z[B]).mean()); loss=float((z[A]&~z[B]).mean()); d=float(z[B].mean()-z[A].mean()); vals=np.asarray(boot[(A,B)])
  rows.append(dict(A=A,B=B,delta_success=d,ci_low=float(np.quantile(vals,.025)),ci_high=float(np.quantile(vals,.975)),rescue=rescue,loss=loss,net_rescue=rescue-loss))
 pd.DataFrame(rows).to_csv(out/'e10_contrasts.csv',index=False)
 print(summary.to_string(index=False)); print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__': main()
