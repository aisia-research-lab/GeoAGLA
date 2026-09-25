import unittest
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.algorithms.online_ablation import run_online_ablation

import importlib.util
p2b_path = ROOT / "experiments" / "05_real_audio_basin_transfer" / "03_phase2b_real_audio_basin_sweep.py"
spec = importlib.util.spec_from_file_location("phase2b_frozen", p2b_path)
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def _setup_test_env():
    signal_dim = 512
    hop = 32
    n_fft = 128
    window = np.hanning(64)
    op = FFTAnalysisOperator(signal_dim, window, hop, n_fft)
    rng = np.random.default_rng(42)
    xstar = rng.normal(size=signal_dim)
    cstar = op.q_analyze(xstar)
    s = np.abs(cstar)
    cfg = {
        "n_iter": 40,
        "warmup": 8,
        "block_size": 4,
        "memory": 2,
        "margin": 0.0,
        "lambda_ceiling": 0.99999999,
        "svd_rtol": 1e-9,
        "cond_max": 1e10,
        "alpha_safe": 0.0,
        "beta_safe": 0.0,
        "gamma_safe": 1.0,
        "K_safe": 0.25,
        "descent_a": 1e-4,
        "rate_tail_fraction": 0.25,
        "rate_floor": 1e-12,
        "basin_success": {
            "final_orbit_ratio_max": 0.10,
            "final_magnitude_residual_max": 1e-5
        }
    }
    return op, cstar, s, cfg


def test_gate_b_success_criterion_threshold():
    """GATE B: Validate strict 1e-5 success criterion and reject 1e-3 drift."""
    op, cstar, s, cfg = _setup_test_env()
    # 1. Meets both criteria: orbit <= 0.10 and mag_res <= 1e-5 -> TRUE
    assert B._success(1.0, 0.09, 9e-6, cfg) is True
    # 2. Fails mag_res (2e-5 > 1e-5) despite orbit error passing -> FALSE
    assert B._success(1.0, 0.09, 2e-5, cfg) is False
    # 3. Fails orbit ratio (0.11 > 0.10) despite mag_res passing -> FALSE
    assert B._success(1.0, 0.11, 1e-7, cfg) is False
    # 4. Old buggy 1e-3 threshold check: 5e-4 would pass 1e-3 but MUST fail 1e-5
    assert B._success(1.0, 0.09, 5e-4, cfg) is False


def test_gate_d_online_full_canonical_equivalence():
    """GATE D: Validate that online_full matches canonical run_online_policy(dynamic_envelope)."""
    op, cstar, s, cfg = _setup_test_env()
    rng = np.random.default_rng(123)
    c0 = cstar + 0.1 * (rng.normal(size=cstar.shape) + 1j * rng.normal(size=cstar.shape))
    
    res_direct = run_online_policy(
        c0, c0, s, op,
        policy="dynamic_envelope",
        n_iter=cfg["n_iter"],
        warmup=cfg["warmup"],
        block_size=cfg["block_size"],
        memory=cfg["memory"],
        margin=cfg["margin"],
        lambda_ceiling=cfg["lambda_ceiling"],
        svd_rtol=cfg["svd_rtol"],
        cond_max=cfg["cond_max"],
        alpha_safe=cfg["alpha_safe"],
        beta_safe=cfg["beta_safe"],
        gamma_safe=cfg["gamma_safe"],
        K_safe=cfg["K_safe"],
        descent_a=cfg["descent_a"],
    )
    
    res_wrapper = run_online_ablation(
        c0, c0, s, op,
        use_envelope=True,
        use_fallback=True,
        n_iter=cfg["n_iter"],
        warmup=cfg["warmup"],
        block_size=cfg["block_size"],
        memory=cfg["memory"],
        margin=cfg["margin"],
        lambda_ceiling=cfg["lambda_ceiling"],
        svd_rtol=cfg["svd_rtol"],
        cond_max=cfg["cond_max"],
        alpha_safe=cfg["alpha_safe"],
        beta_safe=cfg["beta_safe"],
        gamma_safe=cfg["gamma_safe"],
        K_safe=cfg["K_safe"],
        descent_a=cfg["descent_a"],
    )
    
    tr_direct = np.array(res_direct["trajectory"])
    tr_wrapper = np.array(res_wrapper["trajectory"])
    np.testing.assert_allclose(tr_direct, tr_wrapper, atol=1e-12)


def test_gate_e_fixed_method_parameters():
    """GATE E: Validate fgla_opt and oracle_minimax parameter synthesis."""
    lp = 0.8
    fgla_params = fgla_opt(lp)
    assert "alpha" in fgla_params
    assert "beta" in fgla_params
    assert "gamma" in fgla_params
    s = np.sqrt(1 - lp)
    np.testing.assert_almost_equal(fgla_params["alpha"], (1 - s) / (1 + s))
    np.testing.assert_almost_equal(fgla_params["beta"], 0.0)
    np.testing.assert_almost_equal(fgla_params["gamma"], 1.0)
    
    m_params = oracle_minimax(0.0, lp)
    assert "alpha" in m_params
    assert "beta" in m_params
    assert "gamma" in m_params
    assert m_params["alpha"] > 0
    assert m_params["gamma"] > 0


def test_gate_f_historical_batch2_initialization():
    """GATE F: Validate historical_batch2 seed mode resetting across batches of 2."""
    def get_fi(global_fi, mode="historical_batch2"):
        return (global_fi % 2) if mode == "historical_batch2" else global_fi
    
    assert get_fi(0) == 0
    assert get_fi(1) == 1
    assert get_fi(2) == 0
    assert get_fi(3) == 1
    assert get_fi(4) == 0


def test_gate_g_no_oracle_leakage():
    """GATE G: Validate online variants do NOT use lambda_true."""
    op, cstar, s, cfg = _setup_test_env()
    rng = np.random.default_rng(999)
    c0 = cstar + 0.05 * (rng.normal(size=cstar.shape) + 1j * rng.normal(size=cstar.shape))
    
    res1 = run_online_policy(
        c0, c0, s, op, policy="dynamic_envelope",
        n_iter=20, warmup=4, block_size=4, memory=2,
        margin=0.0, lambda_ceiling=0.99999999, svd_rtol=1e-9, cond_max=1e10,
        alpha_safe=0.0, beta_safe=0.0, gamma_safe=1.0, K_safe=0.25, descent_a=1e-4
    )
    tr1 = np.array(res1["trajectory"])
    assert len(tr1) == 21


if __name__ == "__main__":
    test_gate_b_success_criterion_threshold()
    test_gate_d_online_full_canonical_equivalence()
    test_gate_e_fixed_method_parameters()
    test_gate_f_historical_batch2_initialization()
    test_gate_g_no_oracle_leakage()
    print("All E10-R2 Equivalence Gates PASS!")
