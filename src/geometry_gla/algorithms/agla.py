from __future__ import annotations
import numpy as np
from geometry_gla.operators.projections import griffin_lim_map
from geometry_gla.operators.stft import AnalysisOperator


def run_agla_state(
    t0: np.ndarray,
    t_minus1: np.ndarray,
    s: np.ndarray,
    op: AnalysisOperator,
    alpha: float,
    beta: float,
    gamma: float,
    n_iter: int,
):
    """Run the AGLA t-state recurrence with fixed parameters.

    State relations: c_n=t_n+alpha(t_n-t_{n-1}),
    d_n=t_n+beta(t_n-t_{n-1}).
    """
    t_prev = np.asarray(t0, dtype=np.complex128).copy()
    t_preprev = np.asarray(t_minus1, dtype=np.complex128).copy()
    out = [t_prev.copy()]
    for _ in range(n_iter):
        delta = t_prev - t_preprev
        c_prev = t_prev + alpha * delta
        d_prev = t_prev + beta * delta
        g = griffin_lim_map(c_prev, s, op)
        t_new = (1 - gamma) * d_prev + gamma * g
        t_preprev, t_prev = t_prev, t_new
        out.append(t_prev.copy())
    return np.asarray(out)


def run_nagla_state(
    t0: np.ndarray,
    s: np.ndarray,
    op: AnalysisOperator,
    n_iter: int,
    H: int = 2,
    gamma: float = 1.0,
):
    """Run Nesterov Accelerated Griffin-Lim Algorithm (NAGLA).

    Literature recurrence:
        alpha_i = (i + H - 2) / (i + H + 1), for i >= 1, H >= 2.
        c_i = t_i + alpha_i * (t_i - t_{i-1})
        t_{i+1} = (1 - gamma) * c_i + gamma * P_S P_M(c_i)
    Initial conditions:
        t_0 given, t_{-1} = t_0.
    """
    if H < 2:
        raise ValueError(f"NAGLA requires H >= 2, got H={H}")
    t_prev = np.asarray(t0, dtype=np.complex128).copy()
    t_preprev = t_prev.copy()
    out = [t_prev.copy()]
    for i in range(1, n_iter + 1):
        alpha_i = float(i + H - 2.0) / float(i + H + 1.0)
        c_i = t_prev + alpha_i * (t_prev - t_preprev)
        g = griffin_lim_map(c_i, s, op)
        t_new = (1.0 - gamma) * c_i + gamma * g if gamma != 1.0 else g
        t_preprev, t_prev = t_prev, t_new
        out.append(t_prev.copy())
    return np.asarray(out)

