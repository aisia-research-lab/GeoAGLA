#!/usr/bin/env python3
import argparse, random, json
from pathlib import Path
from common import *
ap=argparse.ArgumentParser(); ap.add_argument('--spec',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); s=load_json(a.spec); R=random.Random(int(s['seed']))
c=[]
for i in range(int(s['n_cases'])):
 N=R.choice(s['dimensions']); W=R.choice([w for w in s['window_lengths'] if w<=N]); H=R.choice([h for h in s['hops'] if h<=W]);
 c.append({'case_id':f'H{i:03d}','N':N,'window':R.choice(s['windows']),'W':W,'hop':H,'n_fft':W,'seed':R.choice(s['case_seeds']),'epsilon':R.choice(s['epsilons'])})
out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); dump_json({'schema_version':1,'frozen':True,'cases':c},out); print(sha256_file(out))
