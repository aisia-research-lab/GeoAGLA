from __future__ import annotations
import numpy as np
from .jacobian import jacobian_matrix_on_range
from geometry_gla.operators.stft import AnalysisOperator


def transverse_spectrum(c_star: np.ndarray, op: AnalysisOperator, phase_tol: float = 1e-8):
    J, QU = jacobian_matrix_on_range(c_star, op)
    vals, vecs = np.linalg.eigh(J)
    vals = np.clip(vals.real, -1e-12, 1 + 1e-12)
    # Remove all numerically neutral eigenvalues. A regular instance should have exactly one.
    neutral = vals >= 1 - phase_tol
    transverse = vals[~neutral]
    if transverse.size == 0:
        raise ValueError("no transverse eigenvalues found")
    return {
        "eigenvalues": vals,
        "eigenvectors": vecs,
        "transverse": transverse,
        "lambda_minus": float(np.min(transverse)),
        "lambda_plus": float(np.max(transverse)),
        "neutral_count": int(np.sum(neutral)),
        "J": J,
        "QU": QU,
    }
