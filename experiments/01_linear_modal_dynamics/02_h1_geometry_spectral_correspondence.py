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
from geometry_gla.geometry.jacobian import jacobian_matrix_on_range
from geometry_gla.geometry.principal_angles import principal_angle_spectrum


def build_case(seed=0,N=16,W=8,hop=4,n_fft=8):
    rng=np.random.default_rng(seed)
    T=periodic_stft_matrix(N,gaussian_window(W),hop,n_fft)
    op=AnalysisOperator(T)
    x=rng.normal(size=N)+1j*rng.normal(size=N)
    c=op.analyze(x)
    # A continuous random signal almost surely avoids exact zero STFT coefficients.
    if np.min(np.abs(c)) < 1e-9:
        raise RuntimeError("near-zero coefficient in smoke case")
    return op,c


def main(out_dir="results/phase1b"):
    op,c=build_case()
    J,_=jacobian_matrix_on_range(c,op)
    vals=np.sort(np.linalg.eigvalsh(J))
    geom,_=principal_angle_spectrum(op.T,c)
    # scipy subspace_angles returns min(dimU, dimV), equal to dimU here.
    if vals.size != geom.size:
        raise RuntimeError(f"spectrum size mismatch {vals.size} vs {geom.size}")
    err=float(np.linalg.norm(vals-geom)/(np.linalg.norm(vals)+1e-15))
    sym=float(np.linalg.norm(J-J.T))
    neutral=int(np.sum(vals>1-1e-8))
    result={"relative_spectral_error":err,"symmetry_error":sym,"neutral_count":neutral,
            "lambda_min":float(vals[0]),"lambda_max":float(vals[-1]),"dimension":int(vals.size)}
    p=Path(out_dir);p.mkdir(parents=True,exist_ok=True)
    (p/"h1_results.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return result

if __name__=="__main__": main()