import numpy as np

from geometry_gla.operators.stft import AnalysisOperator, gaussian_window, hann_window, periodic_stft_matrix
from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.operators.stft_torch import TorchPeriodicSTFT


def test_range_projector_is_orthogonal():
    rng = np.random.default_rng(1)
    T = periodic_stft_matrix(16, hann_window(8), hop=4, n_fft=8)
    op = AnalysisOperator(T)
    v = rng.normal(size=op.coeff_dim) + 1j * rng.normal(size=op.coeff_dim)
    pv = op.project_range(v)
    ppv = op.project_range(pv)
    assert np.linalg.norm(ppv - pv) < 1e-13 * np.linalg.norm(v)
    assert abs(np.vdot(v - pv, pv)) < 1e-13 * np.linalg.norm(v) ** 2


def test_fft_and_torch_stft_match_explicit_matrix():
    rng = np.random.default_rng(2)
    N = 64
    w = gaussian_window(16)
    T = periodic_stft_matrix(N, w, hop=4, n_fft=16)
    mat_op = AnalysisOperator(T)
    fft_op = FFTAnalysisOperator(N, w, hop=4, n_fft=16)
    torch_op = TorchPeriodicSTFT(N, w, hop=4, n_fft=16, device="cpu")

    x = rng.normal(size=N) + 1j * rng.normal(size=N)
    c_mat = mat_op.analyze(x)
    c_fft = fft_op.analyze(x)
    c_torch = torch_op.analyze(x).detach().cpu().numpy()

    assert np.linalg.norm(c_fft - c_mat) < 1e-12 * np.linalg.norm(c_mat)
    assert np.linalg.norm(c_torch - c_mat) < 1e-12 * np.linalg.norm(c_mat)

    p_mat = mat_op.project_range(c_mat + 0.1)
    p_fft = fft_op.project_range(c_mat + 0.1)
    p_torch = torch_op.project_range(torch_op.tensor(c_mat + 0.1)).detach().cpu().numpy()
    assert np.linalg.norm(p_fft - p_mat) < 1e-12 * np.linalg.norm(p_mat)
    assert np.linalg.norm(p_torch - p_mat) < 1e-12 * np.linalg.norm(p_mat)
