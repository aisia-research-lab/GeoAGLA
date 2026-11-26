from __future__ import annotations
import numpy as np


def root_rate_from_errors(errors, floor: float = 1e-13, min_points: int = 8):
    """Estimate geometric root rate from a robust log-linear fit.

    Selects the longest usable prefix after the initial transient while errors
    remain above the floating-point floor.
    """
    e = np.asarray(errors, dtype=float)
    idx = np.where(np.isfinite(e) & (e > floor))[0]
    idx = idx[idx >= 2]
    if idx.size < min_points:
        raise ValueError("not enough errors above numerical floor")
    # Use later 60% of usable indices, but keep at least min_points.
    start = max(0, int(0.4 * idx.size))
    sel = idx[start:]
    if sel.size < min_points:
        sel = idx[-min_points:]
    x = sel.astype(float)
    y = np.log(e[sel])
    slope, intercept = np.polyfit(x, y, 1)
    return float(np.exp(slope)), {"indices": sel, "slope": float(slope), "intercept": float(intercept)}
