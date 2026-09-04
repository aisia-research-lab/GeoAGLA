import numpy as np
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.operators.stft import AnalysisOperator, periodic_stft_matrix, gaussian_window

def test_phase1er_policy_runner_smoke():
    T=periodic_stft_matrix(16,gaussian_window(8),4,8); op=AnalysisOperator(T)
    rng=np.random.default_rng(3); c=op.analyze(rng.normal(size=16)+1j*rng.normal(size=16)); s=np.abs(c)
    r=run_online_policy(c+1e-4*op.analyze(rng.normal(size=16)+1j*rng.normal(size=16)),c,s,op,n_iter=20,warmup=6,block_size=4,memory=3,policy='dynamic_envelope')
    assert len(r['trajectory'])==21
    assert all('fallback_e1_pass' in b for b in r['blocks'])
