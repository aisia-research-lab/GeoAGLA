import numpy as np

from geometry_gla.geometry.jacobian import jacobian_action, jacobian_matrix_on_range
from geometry_gla.geometry.matrixfree import top_transverse_spectrum
from geometry_gla.geometry.principal_angles import principal_angle_spectrum
from geometry_gla.operators.projections import tangent_project_magnitude
from geometry_gla.operators.stft import AnalysisOperator, gaussian_window, hann_window, periodic_stft_matrix
from geometry_gla.operators.stft_fft import FFTAnalysisOperator


def test_radial_zero_mode_identity():
    """c* lies in U and is real-orthogonal to ic* and V, so J* c* = 0 (lambda_- = 0)."""
    rng = np.random.default_rng(42)
    N = 32
    T = periodic_stft_matrix(N, hann_window(16), hop=8, n_fft=16)
    op = AnalysisOperator(T)
    x = rng.normal(size=N) + 1j * rng.normal(size=N)
    c_star = op.analyze(x)
    c_star /= np.linalg.norm(c_star)

    assert abs(np.vdot(c_star, 1j * c_star).real) < 1e-14
    assert np.linalg.norm(op.project_range(c_star) - c_star) < 1e-14
    assert np.linalg.norm(tangent_project_magnitude(c_star, c_star)) < 1e-14
    assert np.linalg.norm(jacobian_action(c_star, c_star, op)) < 1e-14


def test_jacobian_principal_angle_identity():
    rng = np.random.default_rng(7)
    N = 32
    for win in (hann_window(16), gaussian_window(16)):
        T = periodic_stft_matrix(N, win, hop=8, n_fft=16)
        op = AnalysisOperator(T)
        x = rng.normal(size=N) + 1j * rng.normal(size=N)
        c_star = op.analyze(x)

        J, _ = jacobian_matrix_on_range(c_star, op)
        eig_J = np.sort(np.linalg.eigvalsh(J))
        cos_sq, _ = principal_angle_spectrum(T, c_star)
        assert np.max(np.abs(eig_J - cos_sq)) < 1e-12


def test_matrixfree_spectrum_matches_explicit_jacobian():
    rng = np.random.default_rng(11)
    N = 64
    w = gaussian_window(16)
    T = periodic_stft_matrix(N, w, hop=4, n_fft=16)
    op_mat = AnalysisOperator(T)
    op_fft = FFTAnalysisOperator(N, w, hop=4, n_fft=16)
    x = rng.normal(size=N) + 1j * rng.normal(size=N)
    c_star = op_mat.analyze(x)

    J, _ = jacobian_matrix_on_range(c_star, op_mat)
    vals = np.sort(np.linalg.eigvalsh(J))[::-1]
    L_exact = float(vals[1])  # exclude simple global-phase mode at 1.0

    mf = top_transverse_spectrum(c_star, op_fft, k=4)
    assert abs(mf["lambda_plus"] - L_exact) < 1e-9
