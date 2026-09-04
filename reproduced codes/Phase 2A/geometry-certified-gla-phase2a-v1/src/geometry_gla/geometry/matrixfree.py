"""Matrix-free local tangent geometry for signal-scale STFT phase retrieval."""
from __future__ import annotations
import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh


def c2r(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=np.complex128)
    return np.concatenate([z.real, z.imag])


def r2c(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = v.size // 2
    return v[:n] + 1j * v[n:]


def tangent_project(c_star: np.ndarray, h: np.ndarray, zero_tol: float = 1e-14) -> np.ndarray:
    c = np.asarray(c_star, dtype=np.complex128)
    h = np.asarray(h, dtype=np.complex128)
    mag = np.abs(c)
    if np.min(mag) <= zero_tol:
        raise ValueError("regular tangent projection requires nonzero coefficients")
    u = c / mag
    return h - u * np.real(np.conj(u) * h)


def jacobian_signal_action(c_star: np.ndarray, op, z: np.ndarray) -> np.ndarray:
    """Apply Q^* P_V Q in isometric signal coordinates."""
    qz = op.q_analyze(z)
    return op.q_adjoint(tangent_project(c_star, qz))


def jacobian_linear_operator(c_star: np.ndarray, op) -> LinearOperator:
    n = op.signal_dim
    def mv(v):
        z = r2c(v)
        return c2r(jacobian_signal_action(c_star, op, z))
    return LinearOperator((2*n, 2*n), matvec=mv, rmatvec=mv, dtype=float)


def top_transverse_spectrum(c_star: np.ndarray, op, *, k: int = 6, phase_tol: float = 1e-7,
                            eig_tol: float = 1e-10, maxiter: int = 4000) -> dict:
    A = jacobian_linear_operator(c_star, op)
    dim = A.shape[0]
    kk = min(max(2, k), dim - 1)
    vals, vecs = eigsh(A, k=kk, which="LA", tol=eig_tol, maxiter=maxiter)
    order = np.argsort(vals)[::-1]
    vals = np.clip(vals[order], -1e-12, 1 + 1e-12)
    vecs = vecs[:, order]
    neutral = vals >= 1 - phase_tol
    transverse = vals[~neutral]
    if transverse.size == 0:
        raise RuntimeError("no transverse eigenvalue resolved")
    return {
        "top_eigenvalues": vals,
        "top_vectors": vecs,
        "neutral_count_topk": int(np.sum(neutral)),
        "lambda_plus": float(transverse[0]),
        "spectral_gap_to_phase": float(1.0 - transverse[0]),
    }


def principal_angle_power_check(c_star: np.ndarray, op, lambda_plus: float, *, seed: int = 0,
                                n_steps: int = 80, phase_deflate: bool = True) -> dict:
    """Independent power-style check of cos^2(theta)=lambda on the transverse space.

    The iteration acts on B^*B with B=P_V Q.  We explicitly form B and B^* actions,
    rather than calling the Jacobian LinearOperator/eigensolver used for the oracle edge.
    """
    rng = np.random.default_rng(seed)
    z = rng.normal(size=op.signal_dim) + 1j*rng.normal(size=op.signal_dim)
    # Neutral vector z_phase satisfies Q z_phase = i c_star.
    x_star = op.synthesize_ls(c_star)
    z_phase = 1j * x_star * op.frame_sqrt
    z_phase /= np.linalg.norm(z_phase)
    if phase_deflate:
        z -= z_phase * np.real(np.vdot(z_phase, z))
    z /= np.linalg.norm(z)
    ray = 0.0
    for _ in range(n_steps):
        Bz = tangent_project(c_star, op.q_analyze(z))
        w = op.q_adjoint(Bz)
        if phase_deflate:
            w -= z_phase * np.real(np.vdot(z_phase, w))
        nw = np.linalg.norm(w)
        if nw <= 1e-15:
            break
        z = w / nw
        Bz = tangent_project(c_star, op.q_analyze(z))
        ray = float(np.vdot(Bz, Bz).real / np.vdot(z, z).real)
    return {
        "lambda_power": ray,
        "lambda_eigsh": float(lambda_plus),
        "relative_error": float(abs(ray-lambda_plus)/max(abs(lambda_plus),1e-15)),
        "cos_theta": float(np.sqrt(max(0.0, ray))),
    }
