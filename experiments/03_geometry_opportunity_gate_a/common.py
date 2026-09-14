
import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

from pathlib import Path
import json, hashlib, csv, math, statistics, random
import numpy as np

def load_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def dump_json(obj, p):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def median(xs):
    xs = [float(x) for x in xs if x is not None and math.isfinite(float(x))]
    return statistics.median(xs) if xs else None

def quantile(xs, q):
    xs = sorted(float(x) for x in xs if x is not None and math.isfinite(float(x)))
    if not xs:
        return None
    z = (len(xs) - 1) * q
    i = int(z)
    j = min(i + 1, len(xs) - 1)
    a = z - i
    return xs[i] * (1 - a) + xs[j] * a

def quantiles(xs):
    return {
        "p10": quantile(xs, 0.10),
        "p25": quantile(xs, 0.25),
        "p50": median(xs),
        "p75": quantile(xs, 0.75),
        "p90": quantile(xs, 0.90),
    }

def bootstrap_ci(values, stat=median, n_boot=5000, seed=20270911, alpha=0.05):
    v = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    if not v:
        return [None, None]
    r = random.Random(seed)
    bs = []
    for _ in range(n_boot):
        bs.append(stat([v[r.randrange(len(v))] for _ in range(len(v))]))
    return [quantile(bs, alpha / 2), quantile(bs, 1 - alpha / 2)]

def bootstrap_corr_ci(x, y, rank=False, n_boot=5000, seed=20270911, alpha=0.05):
    pairs = [(float(xi), float(yi)) for xi, yi in zip(x, y) if xi is not None and yi is not None and math.isfinite(float(xi)) and math.isfinite(float(yi))]
    if len(pairs) < 3:
        return [None, None]
    
    def calc_corr(ps):
        xs = np.array([p[0] for p in ps])
        ys = np.array([p[1] for p in ps])
        if rank:
            xs = np.argsort(np.argsort(xs))
            ys = np.argsort(np.argsort(ys))
        c = np.corrcoef(xs, ys)[0, 1]
        return float(c) if math.isfinite(c) else 0.0

    r = random.Random(seed)
    bs = []
    for _ in range(n_boot):
        sample = [pairs[r.randrange(len(pairs))] for _ in range(len(pairs))]
        bs.append(calc_corr(sample))
    return [quantile(bs, alpha / 2), quantile(bs, 1 - alpha / 2)]

def write_csv(rows, p):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

def read_csv(p):
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def fnum(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except:
        return None