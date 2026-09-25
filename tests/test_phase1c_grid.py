import json
from pathlib import Path
import numpy as np
from geometry_gla.operators.stft import periodic_stft_matrix, gaussian_window, hann_window, AnalysisOperator
from geometry_gla.geometry.jacobian import jacobian_matrix_on_range
from geometry_gla.geometry.principal_angles import principal_angle_spectrum


def test_phase1c_config_is_valid():
    cfg = json.loads(Path("configs/phase1c_grid.json").read_text())
    assert len(cfg["configs"]) >= 4
    assert len(cfg["seeds"]) >= 3
    assert len(cfg["perturbations"]) >= 2


def test_hann_and_gaussian_h1_identity_small():
    rng = np.random.default_rng(123)
    for wf in (gaussian_window, hann_window):
        T = periodic_stft_matrix(16, wf(8), 4, 8)
        op = AnalysisOperator(T)
        x = rng.normal(size=16) + 1j*rng.normal(size=16)
        c = op.analyze(x)
        J,_ = jacobian_matrix_on_range(c, op)
        vals = np.sort(np.linalg.eigvalsh(J))
        geom,_ = principal_angle_spectrum(op.T, c)
        assert np.linalg.norm(vals-geom)/(np.linalg.norm(vals)+1e-15) < 1e-10
