from __future__ import annotations
import numpy as np


def oracle_minimax(lambda_minus: float, lambda_plus: float) -> dict:
    lm, lp = float(lambda_minus), float(lambda_plus)
    if -1e-12 < lm < 0:
        lm = 0.0
    if not (0 <= lm < lp < 1):
        raise ValueError("require 0 <= lambda_minus < lambda_plus < 1")
    D = lp - lm
    B = 3 * lp + lm - lp**2 - 3 * lp * lm
    disc = B**2 - 4 * lp * D**2
    if disc < -1e-12:
        raise ValueError("negative discriminant")
    q = (B - np.sqrt(max(0.0, disc))) / (2 * D)
    gamma = (1 - q) ** 2 / (1 - lp)
    alpha = q**2 * (1 - lp) / (lp * (1 - q) ** 2)
    beta = 0.0
    return {"q": float(q), "alpha": float(alpha), "beta": beta, "gamma": float(gamma)}


def fgla_opt(lambda_plus: float) -> dict:
    lp = float(lambda_plus)
    if not (0 < lp < 1):
        raise ValueError("require 0 < lambda_plus < 1")
    s = np.sqrt(1 - lp)
    alpha = (1 - s) / (1 + s)
    q = 1 - s
    return {"q": float(q), "alpha": float(alpha), "beta": 0.0, "gamma": 1.0}


def modal_coefficients(lam: float, alpha: float, beta: float, gamma: float):
    A = (1 - gamma) * (1 + beta) + gamma * (1 + alpha) * lam
    C = (1 - gamma) * beta + gamma * alpha * lam
    return float(A), float(C)


def modal_radius(lam: float, alpha: float, beta: float, gamma: float) -> float:
    A, C = modal_coefficients(lam, alpha, beta, gamma)
    roots = np.roots([1.0, -A, C])
    return float(np.max(np.abs(roots)))


def one_edge_minimax(lambda_plus: float) -> dict:
    """Exact stationary minimax parameters on the realizable Griffin-Lim interval [0, L] (Theorem 4.1)."""
    lp = float(lambda_plus)
    if not (0 < lp < 1):
        raise ValueError("require 0 < lambda_plus < 1")
    q = float(2.0 * lp / (3.0 - lp + np.sqrt((1.0 - lp) * (9.0 - lp))))
    alpha = q / (3.0 - q)
    gamma = 1.0 + q
    return {"q": q, "alpha": float(alpha), "beta": 0.0, "gamma": float(gamma)}


def mismatch_companion_matrix(lam: float, u: float) -> np.ndarray:
    """2x2 modal companion matrix for one-edge AGLA synthesized at root factor u = q0(ell)."""
    d = u * (1.0 + u) / (3.0 - u)
    return np.array([[-u + (1.0 + u + d) * lam, -d * lam], [1.0, 0.0]], dtype=float)


def mismatch_radius(L: float, ell: float) -> float:
    """Exact worst-case local root factor R(L, q0(ell)) under upper-edge mismatch (Theorem 4.2)."""
    u = one_edge_minimax(ell)["q"]
    eig_L = float(np.max(np.abs(np.linalg.eigvals(mismatch_companion_matrix(float(L), u)))))
    return max(u, eig_L)


def mismatch_acceleration_interval(L: float) -> tuple[float, float]:
    """Exact open interval (ell_min, ell_max) on which one-edge AGLA strictly beats optimal FGLA (Theorem 4.2)."""
    lp = float(L)
    if not (0 < lp < 1):
        raise ValueError("require 0 < L < 1")
    t = 1.0 - np.sqrt(1.0 - lp)
    u = 6.0 * t / (np.sqrt((5.0 - 3.0 * t) ** 2 + 12.0 * t) + (5.0 - 3.0 * t))
    h = lambda x: float(x * (3.0 - x) / (1.0 + x))
    return h(u), h(t)
