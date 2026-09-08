"""Small explicit periodic STFT analysis operator for theorem diagnostics.

This module intentionally uses an explicit analysis matrix. It is not intended
for large audio experiments; it makes projector/Jacobian identities transparent
and deterministic for Phase-1B verification.
"""
from __future__ import annotations
import numpy as np


def hann_window(length: int) -> np.ndarray:
    # Periodic Hann, suited to overlap-add style diagnostics.
    n = np.arange(length)
    return 0.5 - 0.5 * np.cos(2 * np.pi * n / length)


def gaussian_window(length: int, sigma: float | None = None) -> np.ndarray:
    if sigma is None:
        sigma = length / 6.0
    n = np.arange(length) - (length - 1) / 2.0
    return np.exp(-0.5 * (n / sigma) ** 2)


def periodic_stft_matrix(
    signal_length: int,
    window: np.ndarray,
    hop: int,
    n_fft: int,
) -> np.ndarray:
    """Return T in C^{M x N} for a periodic STFT.

    Frames start at 0, hop, ... around the periodic signal. The local window
    samples are modulated by the n_fft-point DFT basis. No normalization is
    needed because all projection formulas use T(T^*T)^{-1}T^*.
    """
    N = int(signal_length)
    w = np.asarray(window, dtype=float)
    W = len(w)
    if N % hop != 0:
        raise ValueError("signal_length must be divisible by hop for this diagnostic operator")
    if n_fft < W:
        raise ValueError("n_fft must be >= window length")
    n_frames = N // hop
    rows = []
    for m in range(n_frames):
        start = m * hop
        idx = (start + np.arange(W)) % N
        for k in range(n_fft):
            row = np.zeros(N, dtype=np.complex128)
            phase = np.exp(-2j * np.pi * k * np.arange(W) / n_fft)
            row[idx] += w * phase
            rows.append(row)
    T = np.vstack(rows)
    if np.linalg.matrix_rank(T) < N:
        raise ValueError("constructed STFT analysis matrix is not full column rank")
    return T


class AnalysisOperator:
    def __init__(self, T: np.ndarray):
        self.T = np.asarray(T, dtype=np.complex128)
        gram = self.T.conj().T @ self.T
        self._gram_inv = np.linalg.inv(gram)

    @property
    def signal_dim(self) -> int:
        return self.T.shape[1]

    @property
    def coeff_dim(self) -> int:
        return self.T.shape[0]

    def analyze(self, x: np.ndarray) -> np.ndarray:
        return self.T @ np.asarray(x, dtype=np.complex128)

    def synthesize_ls(self, c: np.ndarray) -> np.ndarray:
        return self._gram_inv @ (self.T.conj().T @ np.asarray(c, dtype=np.complex128))

    def project_range(self, c: np.ndarray) -> np.ndarray:
        return self.analyze(self.synthesize_ls(c))
