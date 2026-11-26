"""Fixed-merit checkpoint safeguard for adaptive Griffin-Lim acceleration.

The checkpoint merit is independent of the candidate acceleration parameters:

    Phi(t, t-) = 1/2 * dist(t + alpha_s (t - t-), M_s)^2 + (K_s / 2) * ||t - t-||^2.

With alpha_s = 0, every committed iterate t lies in range(T), so the restricted
gradient of 1/2 * dist(t, M_s)^2 on range(T) is t - G(t).
"""
from __future__ import annotations
import numpy as np
from geometry_gla.operators.projections import griffin_lim_map
from geometry_gla.operators.stft import AnalysisOperator


def magnitude_distance_sq(c: np.ndarray, s: np.ndarray) -> float:
    c=np.asarray(c,dtype=np.complex128); s=np.asarray(s,dtype=float)
    return float(np.sum((np.abs(c)-s)**2))


def fixed_checkpoint_merit(
    t: np.ndarray,
    t_prev: np.ndarray,
    s: np.ndarray,
    *,
    alpha_safe: float = 0.0,
    K_safe: float = 0.25,
) -> float:
    t=np.asarray(t,dtype=np.complex128); tp=np.asarray(t_prev,dtype=np.complex128)
    delta=t-tp
    c_safe=t + float(alpha_safe)*delta
    return 0.5*magnitude_distance_sq(c_safe,s) + 0.5*float(K_safe)*float(np.vdot(delta,delta).real)


def block_path_size(states: np.ndarray) -> float:
    """D = sqrt(sum_j ||t_j-t_{j-1}||^2) for one proposed block."""
    tr=np.asarray(states,dtype=np.complex128)
    if len(tr)<2: return 0.0
    d=np.diff(tr,axis=0)
    return float(np.sqrt(np.sum(np.abs(d)**2)))


def checkpoint_accept(
    start_t: np.ndarray,
    start_prev: np.ndarray,
    end_t: np.ndarray,
    end_prev: np.ndarray,
    block_states: np.ndarray,
    s: np.ndarray,
    *,
    alpha_safe: float=0.0,
    K_safe: float=0.25,
    descent_a: float=1e-4,
    atol: float=1e-14,
) -> dict:
    phi0=fixed_checkpoint_merit(start_t,start_prev,s,alpha_safe=alpha_safe,K_safe=K_safe)
    phi1=fixed_checkpoint_merit(end_t,end_prev,s,alpha_safe=alpha_safe,K_safe=K_safe)
    D=block_path_size(block_states)
    lhs=phi1+float(descent_a)*D*D
    ok=bool(lhs <= phi0 + atol*max(1.0,abs(phi0)))
    return {'accepted':ok,'phi_start':phi0,'phi_end':phi1,'path_size':D,
            'lhs':float(lhs),'descent_slack':float(phi0-lhs)}


def restricted_merit_gradient_norm(
    t: np.ndarray,
    t_prev: np.ndarray,
    s: np.ndarray,
    op: AnalysisOperator,
    *,
    alpha_safe: float=0.0,
    K_safe: float=0.25,
) -> float:
    """Norm of the restricted smooth gradient for the fixed checkpoint merit.

    Exact for alpha_safe = 0, used to monitor the relative-error inequality
    ||grad Phi(X_{k+1})|| <= b * (D_k + D_{k-1}).
    """
    if abs(alpha_safe)>1e-15:
        raise NotImplementedError('restricted_merit_gradient_norm requires alpha_safe=0')
    t=np.asarray(t,dtype=np.complex128); tp=np.asarray(t_prev,dtype=np.complex128)
    delta=t-tp
    g=griffin_lim_map(t,s,op)
    grad_t=(t-g)+float(K_safe)*delta
    grad_prev=-float(K_safe)*delta
    return float(np.sqrt(np.vdot(grad_t,grad_t).real + np.vdot(grad_prev,grad_prev).real))
