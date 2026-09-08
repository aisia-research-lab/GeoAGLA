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
