from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import json
from pathlib import Path
import numpy as np
from geometry_gla.operators.stft import periodic_stft_matrix, gaussian_window, AnalysisOperator
from geometry_gla.geometry.oracle_spectrum import transverse_spectrum
from geometry_gla.geometry.realify import r2c
from geometry_gla.algorithms.minimax import oracle_minimax, fgla_opt
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.metrics.phase import orbit_distance
from geometry_gla.metrics.contraction import root_rate_from_errors


def main(out_dir="results/phase1b",seed=3):
    rng=np.random.default_rng(seed)
    N,W,hop,n_fft=16,8,4,8
    op=AnalysisOperator(periodic_stft_matrix(N,gaussian_window(W),hop,n_fft))
    x=rng.normal(size=N)+1j*rng.normal(size=N)
    c_star=op.analyze(x)
    s=np.abs(c_star)
    spec=transverse_spectrum(c_star,op,phase_tol=1e-8)
    if spec["neutral_count"] != 1:
        raise RuntimeError(f"smoke case is not regular: neutral_count={spec['neutral_count']}")
    lm,lp=spec["lambda_minus"],spec["lambda_plus"]
    prm_o=oracle_minimax(lm,lp)
    prm_f=fgla_opt(lp)
    # perturb along lambda+ eigenvector to expose the slowest local mode
    vals, vecs=np.linalg.eigh(spec["J"])
    idx=np.where(vals < 1-1e-8)[0][-1]
    v=r2c(spec["QU"] @ vecs[:,idx])
    v=v/np.linalg.norm(v)
    eps=1e-5
    t0=c_star+eps*v
    tminus=t0.copy()
    methods={
      "gla":{"alpha":0.,"beta":0.,"gamma":1.,"q":lp},
      "fgla_opt":prm_f,
      "oracle":prm_o,
    }
    out={"lambda_minus":lm,"lambda_plus":lp,"methods":{}}
    for name,p in methods.items():
        traj=run_agla_state(t0,tminus,s,op,p["alpha"],p["beta"],p["gamma"],80)
        errors=[orbit_distance(z,c_star) for z in traj]
        try:
            qobs,meta=root_rate_from_errors(errors,floor=5e-13,min_points=6)
        except ValueError:
            # Fall back to a shorter pre-floor fit.
            e=np.asarray(errors)
            sel=np.where((e>5e-13)&(np.arange(e.size)>=2))[0]
            sel=sel[-max(4,min(12,sel.size)):]
            slope,_=np.polyfit(sel,np.log(e[sel]),1)
            qobs=float(np.exp(slope)); meta={"indices":sel.tolist()}
        out["methods"][name]={"q_pred":float(p["q"]),"q_obs":qobs,
                              "abs_error":abs(qobs-float(p["q"])),
                              "final_error":float(errors[-1])}
    Path(out_dir).mkdir(parents=True,exist_ok=True)
    (Path(out_dir)/"h2_results.json").write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
    return out

if __name__=="__main__": main()