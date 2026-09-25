from __future__ import annotations
import numpy as np
from geometry_gla.operators.projections import griffin_lim_map
from geometry_gla.operators.stft import AnalysisOperator


def run_agla_state(
    t0: np.ndarray,
    s: np.ndarray,
    op: AnalysisOperator,
    n_iter: int,
    alpha: float = 1.05,
    beta: float = 1.35,
    gamma: float = 1.25,
    t_minus1: np.ndarray | None = None,
):
    """Run Literature-Faithful 3-state AGLA (Phase 4H-R2 Section 2).

    Recurrence (Perraudin et al., Nenov et al.):
        t_n = (1 - gamma) * d_{n-1} + gamma * P_C1(P_C2(c_{n-1}))
        c_n = t_n + alpha * (t_n - t_{n-1})
        d_n = t_n + beta  * (t_n - t_{n-1})

    Primary literature configuration (Nenov et al., Table II leading):
        alpha = 1.05, beta = 1.35, gamma = 1.25
    Secondary literature configuration (WASPAA 2013):
        alpha = 0.99, beta = 0.95, gamma = 1.20
    """
    t_prev = np.asarray(t0, dtype=np.complex128).copy()
    t_preprev = np.asarray(t_minus1, dtype=np.complex128).copy() if t_minus1 is not None else t_prev.copy()
    c_prev = t_prev + alpha * (t_prev - t_preprev)
    d_prev = t_prev + beta * (t_prev - t_preprev)
    out = [t_prev.copy()]
    for _ in range(n_iter):
        g = griffin_lim_map(c_prev, s, op)
        t_new = (1.0 - gamma) * d_prev + gamma * g
        delta = t_new - t_prev
        c_prev = t_new + alpha * delta
        d_prev = t_new + beta * delta
        t_preprev, t_prev = t_prev, t_new
        out.append(t_prev.copy())
    return np.asarray(out)


def run_nagla_state(
    x0: np.ndarray,
    s: np.ndarray,
    op: AnalysisOperator,
    n_iter: int,
    H: int = 49,
):
    """Run Literature-Faithful NAGLA (Phase 4H-R2 Section 1.1).

    Recurrence (Nesterov, 1983; Perraudin et al., 2013):
        X_{i+1} = P_V(P_T(Y_i))
        Y_{i+1} = X_{i+1} + alpha_i * (X_{i+1} - X_i)
        with alpha_i = (i + H - 2) / (i + H + 1)

    Primary literature configuration:
        H = 49 (from contemporary NAGLA null-phase benchmark)
    Sensitivity configuration:
        H = 2 (old Phase 4H-R setting, retained only as sensitivity evidence)
    """
    if H < 2:
        raise ValueError(f"NAGLA requires H >= 2, got H={H}")
    x_prev = np.asarray(x0, dtype=np.complex128).copy()
    y = x_prev.copy()
    out = [x_prev.copy()]
    for i in range(1, n_iter + 1):
        x_next = griffin_lim_map(y, s, op)
        alpha_i = float(i + H - 2.0) / float(i + H + 1.0)
        y = x_next + alpha_i * (x_next - x_prev)
        x_prev = x_next
        out.append(x_prev.copy())
    return np.asarray(out)

