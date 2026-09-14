import numpy as np
from geometry_gla.operators.stft import hann_window
from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.geometry.matrixfree import top_transverse_spectrum, principal_angle_power_check


def test_fft_operator_adjoint_projector_and_isometry():
    rng=np.random.default_rng(2)
    op=FFTAnalysisOperator(64,hann_window(32),8,32)
    x=rng.normal(size=64)+1j*rng.normal(size=64)
    c=rng.normal(size=op.coeff_dim)+1j*rng.normal(size=op.coeff_dim)
    lhs=np.vdot(op.analyze(x),c); rhs=np.vdot(x,op.adjoint(c))
    assert abs(lhs-rhs) <= 1e-10*max(1,abs(lhs),abs(rhs))
    p=op.project_range(c)
    assert np.linalg.norm(op.project_range(p)-p) <= 1e-10*max(1,np.linalg.norm(p))
    z=rng.normal(size=64)+1j*rng.normal(size=64)
    assert abs(np.linalg.norm(op.q_analyze(z))-np.linalg.norm(z)) <= 1e-10*np.linalg.norm(z)


def test_matrixfree_geometry_power_matches_eigsh():
    rng=np.random.default_rng(4)
    op=FFTAnalysisOperator(48,hann_window(24),6,24)
    x=rng.normal(size=48)+1j*rng.normal(size=48)
    c=op.analyze(x)
    spec=top_transverse_spectrum(c,op,k=5,eig_tol=1e-10)
    chk=principal_angle_power_check(c,op,spec['lambda_plus'],seed=8,n_steps=600)
    assert spec['neutral_count_topk'] >= 1
    assert chk['relative_error'] < 2e-3
