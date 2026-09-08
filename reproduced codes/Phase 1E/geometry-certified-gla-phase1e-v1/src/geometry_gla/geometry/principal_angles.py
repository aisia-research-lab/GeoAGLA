from __future__ import annotations
import numpy as np
from scipy.linalg import subspace_angles
from .realify import complex_subspace_real_basis, tangent_torus_real_basis


def principal_angle_spectrum(T: np.ndarray, c_star: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    QU = complex_subspace_real_basis(T)
    QV = tangent_torus_real_basis(c_star)
    angles = subspace_angles(QU, QV)
    lambdas = np.cos(angles) ** 2
    return np.sort(lambdas), np.sort(angles)
