from __future__ import annotations
import numpy as np
from .realify import c2r, r2c, complex_subspace_real_basis
from geometry_gla.operators.projections import tangent_project_magnitude
from geometry_gla.operators.stft import AnalysisOperator


def jacobian_action(c_star: np.ndarray, h: np.ndarray, op: AnalysisOperator) -> np.ndarray:
    return op.project_range(tangent_project_magnitude(c_star, h))


def jacobian_matrix_on_range(c_star: np.ndarray, op: AnalysisOperator):
    """Real matrix representation Q_U^T J Q_U and real range basis Q_U."""
    QU = complex_subspace_real_basis(op.T)
    d = QU.shape[1]
    J = np.zeros((d, d), dtype=float)
    for j in range(d):
        h = r2c(QU[:, j])
        Jh = jacobian_action(c_star, h, op)
        J[:, j] = QU.T @ c2r(Jh)
    J = 0.5 * (J + J.T)  # numerical symmetrization only
    return J, QU
