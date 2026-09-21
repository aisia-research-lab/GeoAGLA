import sys
from pathlib import Path
import numpy as np

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root / "src") not in sys.path:
    sys.path.insert(0, str(_repo_root / "src"))

from geometry_gla.operators.stft import gaussian_window
from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.algorithms.online_ablation import run_online_ablation


def _case():
    rng = np.random.default_rng(17)
    x = rng.normal(size=128).astype(np.complex128)
    op = FFTAnalysisOperator(128, gaussian_window(32), 8, 32)
    c = op.q_analyze(x)
    s = np.abs(c)
    c0 = c + 1e-3 * op.q_analyze(rng.normal(size=128))
    return c0, s, op


def test_e10_full_switches_reproduce_canonical_online():
    c0, s, op = _case()
    kw = dict(n_iter=36, warmup=12, block_size=8, memory=3, margin=0.0)
    a = run_online_policy(c0, c0, s, op, policy="dynamic_envelope", **kw)
    b = run_online_ablation(c0, c0, s, op, use_envelope=True, use_fallback=True, **kw)
    assert np.allclose(a["trajectory"], b["trajectory"], rtol=0, atol=1e-12)


def test_e10_raw_and_env_are_executable():
    c0, s, op = _case()
    for env in (False, True):
        z = run_online_ablation(
            c0, c0, s, op, n_iter=28, warmup=12, block_size=8, memory=3, use_envelope=env, use_fallback=False
        )
        assert z["trajectory"].shape[0] == 29
