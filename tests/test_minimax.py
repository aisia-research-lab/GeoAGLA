import numpy as np

from geometry_gla.algorithms.minimax import (
    fgla_opt,
    mismatch_acceleration_interval,
    mismatch_radius,
    modal_radius,
    one_edge_minimax,
    oracle_minimax,
)


def test_one_edge_minimax_matches_zero_lower_edge_and_beats_fgla():
    for L in (0.2, 0.5, 0.8, 0.95, 0.99):
        o1 = one_edge_minimax(L)
        o2 = oracle_minimax(0.0, L)
        f = fgla_opt(L)
        assert abs(o1["q"] - o2["q"]) < 1e-12
        assert abs(o1["alpha"] - o2["alpha"]) < 1e-12
        assert abs(o1["gamma"] - o2["gamma"]) < 1e-12
        assert o1["beta"] == 0.0
        assert 0.0 < o1["q"] < f["q"] < L < 1.0
        assert abs(modal_radius(L, o1["alpha"], o1["beta"], o1["gamma"]) - o1["q"]) < 1e-7
        assert abs(modal_radius(0.0, o1["alpha"], o1["beta"], o1["gamma"]) - o1["q"]) < 1e-12


def test_two_edge_endpoint_equioscillation_and_non_stft_transfer():
    for m, L in ((0.2, 0.8), (0.45, 0.85), (0.7, 0.95), (0.9, 0.99)):
        two = oracle_minimax(m, L)
        one = one_edge_minimax(L)
        assert two["q"] < one["q"] < fgla_opt(L)["q"] < L
        assert abs(modal_radius(m, two["alpha"], two["beta"], two["gamma"]) - two["q"]) < 1e-7
        assert abs(modal_radius(L, two["alpha"], two["beta"], two["gamma"]) - two["q"]) < 1e-7
        grid = np.linspace(m, L, 101)
        worst = max(modal_radius(x, two["alpha"], two["beta"], two["gamma"]) for x in grid)
        assert abs(worst - two["q"]) < 1e-7


def test_mismatch_tolerance_interval_and_near_degenerate_limit():
    for L in (0.5, 0.8, 0.95, 0.999):
        lo, hi = mismatch_acceleration_interval(L)
        q_fgla = fgla_opt(L)["q"]
        assert 0.0 < lo < L < hi < 1.0
        assert abs(mismatch_radius(L, lo) - q_fgla) < 1e-7
        assert abs(mismatch_radius(L, hi) - q_fgla) < 1e-7
        assert mismatch_radius(L, 0.5 * (lo + L)) < q_fgla
        assert mismatch_radius(L, 0.5 * (L + hi)) < q_fgla

    L_deg = 1.0 - 1e-6
    lo, hi = mismatch_acceleration_interval(L_deg)
    assert abs((1.0 - hi) / (1.0 - L_deg) - 0.5) < 1e-2
    assert abs((1.0 - lo) / (1.0 - L_deg) - 1.125) < 1e-2
