import numpy as np

from geometry_gla.algorithms.online_ablation import run_online_ablation
from geometry_gla.algorithms.online_safe import run_online_policy, run_safeguarded_online
from geometry_gla.estimators.ritz import ritz_largest
from geometry_gla.operators.stft import AnalysisOperator, hann_window, periodic_stft_matrix
from geometry_gla.safeguards.checkpoint import checkpoint_accept, fixed_checkpoint_merit


def test_exact_ritz_on_invariant_subspace():
    rng = np.random.default_rng(5)
    d = 12
    A = rng.normal(size=(d, d))
    Q, _ = np.linalg.qr(A)
    eigs = np.linspace(0.1, 0.9, d)
    J = Q @ np.diag(eigs) @ Q.T
    S = [Q[:, -1] + 0.3 * Q[:, -2], Q[:, -2] - 0.2 * Q[:, -3], Q[:, -3]]
    Y = [J @ s for s in S]
    res = ritz_largest(S, Y)
    assert res["accepted"]
    assert abs(res["estimate"] - 0.9) < 1e-11


def test_safeguard_monotonicity_under_hostile_bias():
    rng = np.random.default_rng(13)
    N = 32
    T = periodic_stft_matrix(N, hann_window(16), hop=8, n_fft=16)
    op = AnalysisOperator(T)
    x = rng.normal(size=N) + 1j * rng.normal(size=N)
    c_star = op.analyze(x)
    s = np.abs(c_star)
    t0 = op.project_range(c_star * np.exp(1j * 0.2 * rng.normal(size=len(c_star))))

    out = run_safeguarded_online(t0, t0, s, op, n_iter=60, warmup=12, block_size=8, estimator_bias=0.5)
    assert np.isfinite(out["trajectory"]).all()
    for blk in out["blocks"]:
        assert blk["fallback_e1_pass"]


def test_online_ablation_full_matches_canonical_online():
    rng = np.random.default_rng(21)
    N = 32
    T = periodic_stft_matrix(N, hann_window(16), hop=8, n_fft=16)
    op = AnalysisOperator(T)
    x = rng.normal(size=N) + 1j * rng.normal(size=N)
    c_star = op.analyze(x)
    s = np.abs(c_star)
    t0 = op.project_range(c_star * np.exp(1j * 0.15 * rng.normal(size=len(c_star))))

    ref = run_online_policy(t0, t0, s, op, n_iter=44, warmup=12, block_size=8, policy="dynamic_envelope")
    abl = run_online_ablation(t0, t0, s, op, n_iter=44, warmup=12, block_size=8, use_envelope=True, use_fallback=True)
    assert np.max(np.abs(ref["trajectory"] - abl["trajectory"])) < 1e-12


def test_checkpoint_merit_is_finite_and_nonnegative():
    rng = np.random.default_rng(3)
    t = rng.normal(size=16) + 1j * rng.normal(size=16)
    tp = t + 0.05 * (rng.normal(size=16) + 1j * rng.normal(size=16))
    s = np.abs(t) + 0.01
    phi = fixed_checkpoint_merit(t, tp, s)
    assert phi >= 0.0
    chk = checkpoint_accept(t, tp, t, t, np.asarray([t, t]), s)
    assert chk["accepted"]
