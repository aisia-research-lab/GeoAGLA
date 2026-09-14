import numpy as np
from geometry_gla.operators.stft import periodic_stft_matrix, gaussian_window, AnalysisOperator


def test_range_projector_is_orthogonal_projector():
    T=periodic_stft_matrix(16,gaussian_window(8),4,8)
    op=AnalysisOperator(T)
    rng=np.random.default_rng(0)
    c=rng.normal(size=op.coeff_dim)+1j*rng.normal(size=op.coeff_dim)
    p=op.project_range(c)
    pp=op.project_range(p)
    assert np.linalg.norm(pp-p)/np.linalg.norm(p)<1e-10
    # residual orthogonal to range(T)
    assert np.linalg.norm(T.conj().T@(c-p))/np.linalg.norm(c)<1e-10
