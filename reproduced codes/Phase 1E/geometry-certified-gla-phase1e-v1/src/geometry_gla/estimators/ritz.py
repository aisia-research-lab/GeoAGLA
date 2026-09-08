"""Passive secant/Ritz estimators for the dominant local spectral edge.

The estimator uses only secant pairs (s_k,y_k), with y_k approximately J s_k.
For GLA, y_k = G(c_k)-G(c_{k-1}) equals the next trajectory secant, so no
extra Griffin--Lim map evaluation is required.
"""
from __future__ import annotations
import numpy as np


def _real_matrix(cols: list[np.ndarray]) -> np.ndarray:
    if not cols:
        raise ValueError("at least one column is required")
    return np.column_stack([np.concatenate([np.real(z), np.imag(z)]) for z in cols])


def ritz_largest(
    secants: list[np.ndarray],
    images: list[np.ndarray],
    *,
    svd_rtol: float = 1e-9,
    cond_max: float = 1e10,
) -> dict:
    """Largest symmetric Ritz value on the span of the supplied secants.

    A truncated SVD of S is used to build an orthonormal basis Q for the
    numerically active secant subspace.  If S=U Sigma V^T and Y≈J S, then
    JQ≈Y V Sigma^{-1}; hence Q^T JQ is available without applying J again.
    """
    if len(secants) != len(images) or not secants:
        raise ValueError("secants/images must have equal positive length")
    S = _real_matrix(secants)
    Y = _real_matrix(images)
    U, sig, Vt = np.linalg.svd(S, full_matrices=False)
    if sig.size == 0 or sig[0] == 0:
        return {"accepted": False, "reason": "zero_secants", "estimate": None,
                "rank": 0, "condition": float("inf")}
    keep = sig > (svd_rtol * sig[0])
    r = int(np.sum(keep))
    if r == 0:
        return {"accepted": False, "reason": "rank_zero", "estimate": None,
                "rank": 0, "condition": float("inf")}
    sig_r = sig[:r]
    cond = float(sig_r[0] / sig_r[-1])
    if cond > cond_max:
        return {"accepted": False, "reason": "ill_conditioned", "estimate": None,
                "rank": r, "condition": cond}
    U_r = U[:, :r]
    V_r = Vt[:r, :].T
    JQ = (Y @ V_r) / sig_r[np.newaxis, :]
    K = U_r.T @ JQ
    K = 0.5 * (K + K.T)
    eig = np.linalg.eigvalsh(K)
    est = float(eig[-1])
    return {"accepted": True, "reason": "ok", "estimate": est,
            "rank": r, "condition": cond,
            "ritz_min": float(eig[0]), "ritz_max": est}


def estimate_edge_series(
    trajectory: np.ndarray,
    memory: int,
    *,
    svd_rtol: float = 1e-9,
    cond_max: float = 1e10,
) -> list[dict]:
    """Estimate lambda_+ along a GLA trajectory without extra map evaluations.

    For c_{n+1}=G(c_n), define s_n=c_n-c_{n-1}. Then
    y_n=G(c_n)-G(c_{n-1})=c_{n+1}-c_n=s_{n+1}.  The trajectory therefore
    contains every secant-image pair needed by the estimator.
    """
    tr = np.asarray(trajectory)
    if tr.ndim != 2 or tr.shape[0] < 3:
        raise ValueError("trajectory must have shape (n_iter+1, coeff_dim) and >=3 points")
    diffs = [tr[k] - tr[k-1] for k in range(1, len(tr))]
    out = []
    # Pair index j uses s_j=diffs[j] and y_j=diffs[j+1].
    for j in range(len(diffs)-1):
        lo = max(0, j-memory+1)
        ss = diffs[lo:j+1]
        yy = diffs[lo+1:j+2]
        res = ritz_largest(ss, yy, svd_rtol=svd_rtol, cond_max=cond_max)
        res = dict(res)
        res["iteration"] = j + 1
        res["memory"] = memory
        out.append(res)
    return out
