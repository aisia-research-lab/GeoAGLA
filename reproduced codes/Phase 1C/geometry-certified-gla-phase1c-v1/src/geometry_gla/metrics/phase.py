from __future__ import annotations
import numpy as np


def align_global_phase(c: np.ndarray, ref: np.ndarray) -> np.ndarray:
    inner = np.vdot(ref, c)
    if abs(inner) == 0:
        return np.asarray(c)
    phi = np.angle(inner)
    return np.exp(-1j * phi) * np.asarray(c)


def orbit_distance(c: np.ndarray, ref: np.ndarray) -> float:
    ca = align_global_phase(c, ref)
    return float(np.linalg.norm(ca - ref))
