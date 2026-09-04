"""Matrix-free periodic STFT operator for signal-scale diagnostics.

The operator uses the full complex FFT at every frame.  For a periodic signal and
full FFT bins, the frame operator T^*T is diagonal, which makes the canonical
least-squares synthesis and the isometric range coordinates inexpensive.
"""
from __future__ import annotations
import numpy as np


class FFTAnalysisOperator:
    def __init__(self, signal_length: int, window: np.ndarray, hop: int, n_fft: int):
        self.N = int(signal_length)
        self.window = np.asarray(window, dtype=float)
        self.W = int(len(self.window))
        self.hop = int(hop)
        self.n_fft = int(n_fft)
        if self.N % self.hop != 0:
            raise ValueError("signal_length must be divisible by hop")
        if self.n_fft < self.W:
            raise ValueError("n_fft must be >= window length")
        self.n_frames = self.N // self.hop
        self.M = self.n_frames * self.n_fft
        diag = np.zeros(self.N, dtype=float)
        for m in range(self.n_frames):
            idx = (m * self.hop + np.arange(self.W)) % self.N
            diag[idx] += self.n_fft * self.window**2
        if np.min(diag) <= 1e-14:
            raise ValueError("STFT frame operator is singular")
        self.frame_diag = diag
        self.frame_sqrt = np.sqrt(diag)
        self.frame_inv_sqrt = 1.0 / self.frame_sqrt

    @property
    def signal_dim(self) -> int:
        return self.N

    @property
    def coeff_dim(self) -> int:
        return self.M

    def analyze(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.complex128)
        out = np.empty((self.n_frames, self.n_fft), dtype=np.complex128)
        for m in range(self.n_frames):
            idx = (m * self.hop + np.arange(self.W)) % self.N
            frame = np.zeros(self.n_fft, dtype=np.complex128)
            frame[: self.W] = self.window * x[idx]
            out[m] = np.fft.fft(frame)
        return out.reshape(-1)

    def adjoint(self, c: np.ndarray) -> np.ndarray:
        C = np.asarray(c, dtype=np.complex128).reshape(self.n_frames, self.n_fft)
        out = np.zeros(self.N, dtype=np.complex128)
        for m in range(self.n_frames):
            idx = (m * self.hop + np.arange(self.W)) % self.N
            frame = np.fft.ifft(C[m]) * self.n_fft
            out[idx] += self.window * frame[: self.W]
        return out

    def synthesize_ls(self, c: np.ndarray) -> np.ndarray:
        return self.adjoint(c) / self.frame_diag

    def project_range(self, c: np.ndarray) -> np.ndarray:
        return self.analyze(self.synthesize_ls(c))

    # Q = T (T^*T)^(-1/2): an isometry from signal coordinates to range(T).
    def q_analyze(self, z: np.ndarray) -> np.ndarray:
        return self.analyze(np.asarray(z, dtype=np.complex128) * self.frame_inv_sqrt)

    def q_adjoint(self, c: np.ndarray) -> np.ndarray:
        return self.adjoint(c) * self.frame_inv_sqrt
