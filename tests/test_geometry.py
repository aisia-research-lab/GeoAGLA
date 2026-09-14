import numpy as np
from geometry_gla.operators.stft import periodic_stft_matrix, gaussian_window, AnalysisOperator
from geometry_gla.geometry.jacobian import jacobian_matrix_on_range
from geometry_gla.geometry.principal_angles import principal_angle_spectrum


def build_case(seed=0, N=16, W=8, hop=4, n_fft=8):
    rng = np.random.default_rng(seed)
    T = periodic_stft_matrix(N, gaussian_window(W), hop, n_fft)
    op = AnalysisOperator(T)
    x = rng.normal(size=N) + 1j * rng.normal(size=N)
    c = op.analyze(x)
    if np.min(np.abs(c)) < 1e-9:
        raise RuntimeError("near-zero coefficient in smoke case")
    return op, c


def test_jacobian_principal_angle_identity():
    op, c = build_case(seed=11)
    J, _ = jacobian_matrix_on_range(c, op)
    vals = np.sort(np.linalg.eigvalsh(J))
    geom, _ = principal_angle_spectrum(op.T, c)
    assert np.linalg.norm(J - J.T) < 1e-10
    assert vals.size == geom.size
    rel = np.linalg.norm(vals - geom) / (np.linalg.norm(vals) + 1e-15)
    assert rel < 1e-9
