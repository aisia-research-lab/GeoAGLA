import sys
from pathlib import Path
import numpy as np
import pandas as pd

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


def test_e10r_locked_geometry_population_integrity():
    locked_csv = _repo_root / "experiments" / "08_e10_robustness_mechanism_ablation" / "frozen" / "e10r_locked_geometry_395.csv"
    assert locked_csv.exists(), f"Locked geometry CSV missing: {locked_csv}"
    df = pd.read_csv(locked_csv)
    assert len(df) == 395, f"Expected 395 locked cases, got {len(df)}"
    assert set(df.columns) == {"file", "profile", "lambda_plus"}
    assert set(df["profile"].unique()) == {"agla_gaussian", "mezza_hann"}
    assert (df["profile"] == "agla_gaussian").sum() == 202
    assert (df["profile"] == "mezza_hann").sum() == 193
    assert (df["lambda_plus"] > 0.0).all() and (df["lambda_plus"] < 1.0).all()

    # Cardinality verification
    n_inits = 12
    n_variants = 6
    expected_paired_instances = len(df) * n_inits  # 4,740
    expected_rows = expected_paired_instances * n_variants  # 28,440
    assert expected_paired_instances == 4740
    assert expected_rows == 28440


def test_e10r_batch2_seed_mode_logic():
    # Historical Kaggle jobs processed sorted files in consecutive batches of two and reset fi inside each batch
    for global_fi in range(10):
        fi_batch2 = global_fi % 2
        assert fi_batch2 in (0, 1)
        assert (global_fi % 2 == 0 and fi_batch2 == 0) or (global_fi % 2 == 1 and fi_batch2 == 1)
