from __future__ import annotations
import numpy as np
from scipy.linalg import qr


def c2r(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z)
    if z.ndim == 1:
        return np.concatenate([z.real, z.imag])
    return np.vstack([z.real, z.imag])


def r2c(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v)
    if v.ndim == 1:
        n = v.size // 2
        return v[:n] + 1j * v[n:]
    n = v.shape[0] // 2
    return v[:n] + 1j * v[n:]


def complex_subspace_real_basis(T: np.ndarray, tol: float = 1e-12) -> np.ndarray:
    """Orthonormal real basis of the complex column space of T."""
    T = np.asarray(T, dtype=np.complex128)
    Bc = np.hstack([T, 1j * T])
    Br = c2r(Bc)
    Q, R = qr(Br, mode="economic")
    diag = np.abs(np.diag(R))
    rank = int(np.sum(diag > tol * max(1.0, diag.max(initial=0.0))))
    return Q[:, :rank]


def tangent_torus_real_basis(c_star: np.ndarray, tol: float = 1e-14) -> np.ndarray:
    """Orthonormal real basis for product-of-circles tangent space."""
    c_star = np.asarray(c_star, dtype=np.complex128)
    mag = np.abs(c_star)
    if np.any(mag <= tol):
        raise ValueError("regular tangent basis requires nonzero coordinates")
    u = c_star / mag
    M = c_star.size
    B = np.zeros((2 * M, M), dtype=float)
    for i in range(M):
        z = np.zeros(M, dtype=np.complex128)
        z[i] = 1j * u[i]
        B[:, i] = c2r(z)
    return B
