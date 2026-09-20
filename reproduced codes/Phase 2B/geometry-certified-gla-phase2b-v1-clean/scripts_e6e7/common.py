from pathlib import Path
import json, hashlib, csv, math, statistics, random

def load_json(p):
    with open(p, encoding='utf-8') as f: return json.load(f)
def dump_json(obj,p):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with open(p,'w',encoding='utf-8') as f: json.dump(obj,f,indent=2,ensure_ascii=False)
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def median(xs):
    xs=[float(x) for x in xs if x is not None and math.isfinite(float(x))]
    return statistics.median(xs) if xs else None
def quantile(xs,q):
    xs=sorted(float(x) for x in xs if x is not None and math.isfinite(float(x)))
    if not xs:return None
    z=(len(xs)-1)*q; i=int(z); j=min(i+1,len(xs)-1); a=z-i
    return xs[i]*(1-a)+xs[j]*a
def bootstrap_ci(values, stat=median, n_boot=5000, seed=20270911, alpha=.05):
    v=[float(x) for x in values if x is not None and math.isfinite(float(x))]
    if not v:return [None,None]
    r=random.Random(seed); bs=[]
    for _ in range(n_boot): bs.append(stat([v[r.randrange(len(v))] for __ in v]))
    return [quantile(bs,alpha/2),quantile(bs,1-alpha/2)]
def write_csv(rows,p):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(p,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
def read_csv(p):
    with open(p,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def fnum(x):
    try:return float(x)
    except:return None
