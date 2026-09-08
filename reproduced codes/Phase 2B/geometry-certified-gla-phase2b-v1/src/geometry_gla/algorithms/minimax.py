from __future__ import annotations
import numpy as np


def oracle_minimax(lambda_minus: float, lambda_plus: float) -> dict:
    lm, lp = float(lambda_minus), float(lambda_plus)
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
