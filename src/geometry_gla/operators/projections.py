from __future__ import annotations
import numpy as np
from .stft import AnalysisOperator


def project_magnitude(c: np.ndarray, s: np.ndarray, zero_phase_value: complex = 1.0 + 0j) -> np.ndarray:
    c = np.asarray(c, dtype=np.complex128)
    s = np.asarray(s, dtype=float)
    out = np.empty_like(c)
    mag = np.abs(c)
    nz = mag > 0
    out[nz] = s[nz] * c[nz] / mag[nz]
    out[~nz] = s[~nz] * zero_phase_value
    return out


def griffin_lim_map(c: np.ndarray, s: np.ndarray, op: AnalysisOperator) -> np.ndarray:
    return op.project_range(project_magnitude(c, s))


def tangent_project_magnitude(c_star: np.ndarray, h: np.ndarray, tol: float = 1e-14) -> np.ndarray:
    """Real derivative of magnitude projection at a feasible regular point.

    For c_i* = s_i u_i with s_i > 0: P_V h_i = h_i - u_i Re(conj(u_i) h_i).
    Coordinates with |c_i*| <= tol are rejected because smoothness fails there.
    """
    c_star = np.asarray(c_star, dtype=np.complex128)
    h = np.asarray(h, dtype=np.complex128)
    mag = np.abs(c_star)
    if np.any(mag <= tol):
        raise ValueError("regular tangent projection requires all |c_star_i| > tol")
    u = c_star / mag
    return h - u * np.real(np.conj(u) * h)
