"""Deterministic, license-free audio-like signals for transfer diagnostics."""
from __future__ import annotations
import numpy as np


def make_signal(kind: str, n: int, seed: int = 0, fs: float = 16000.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(n) / fs
    if kind == "harmonic":
        f0 = 180.0 + 13.0*seed
        x = sum((1.0/k) * np.sin(2*np.pi*(k*f0)*t + 0.2*k) for k in range(1,7))
        x *= 0.65 + 0.35*np.sin(2*np.pi*3.1*t + 0.3)**2
    elif kind == "chirp":
        f0, f1 = 120.0, 2800.0
        k = (f1-f0)/max(t[-1],1/fs)
        phase = 2*np.pi*(f0*t + 0.5*k*t*t)
        x = np.sin(phase) + 0.25*np.sin(2*phase+0.4)
    elif kind == "speech_like":
        # voiced carrier + slowly varying envelope + weak colored-noise aspiration
        f0 = 115.0 + 7.0*seed
        carrier = sum((1.0/k) * np.sin(2*np.pi*k*f0*t + rng.uniform(-np.pi,np.pi)) for k in range(1,10))
        env = 0.15 + 0.85*(0.5+0.5*np.sin(2*np.pi*4.3*t + 0.7))**2
        noise = rng.normal(size=n)
        noise = np.convolve(noise, np.ones(9)/9.0, mode='same')
        x = env*carrier + 0.04*noise
    elif kind == "transient":
        x = np.zeros(n)
        centers = np.linspace(0.08,0.92,7)*max(n-1,1)
        idx = np.arange(n)
        for j,c in enumerate(centers):
            width = max(2.0, n*(0.006+0.002*(j%3)))
            pulse = np.exp(-0.5*((idx-c)/width)**2)
            x += pulse*np.sin(2*np.pi*(350+220*j)*t + 0.3*j)
        x += 0.02*rng.normal(size=n)
    else:
        raise ValueError(kind)
    x = np.asarray(x, float)
    x -= np.mean(x)
    norm = np.linalg.norm(x)
    return x / norm if norm > 0 else x


def _to_float(raw: np.ndarray) -> np.ndarray:
    a = np.asarray(raw)
    if a.ndim > 1:
        a = np.mean(a.astype(np.float64), axis=1)
    else:
        a = a.astype(np.float64)
    if np.issubdtype(raw.dtype, np.integer):
        info = np.iinfo(raw.dtype)
        scale = max(abs(info.min), abs(info.max))
        a /= max(float(scale), 1.0)
    return a


def _resample(x: np.ndarray, fs: int, target_fs: int) -> np.ndarray:
    import math
    from scipy.signal import resample_poly
    if fs == target_fs:
        return np.asarray(x, float)
    g = math.gcd(int(fs), int(target_fs))
    return resample_poly(x, target_fs // g, fs // g)


def _max_rms_excerpt(x: np.ndarray, N: int) -> tuple[np.ndarray, int]:
    x = np.asarray(x, float)
    if len(x) < N:
        y = np.zeros(N, float)
        y[:len(x)] = x
        return y, 0
    hop = max(1, N // 4)
    starts = list(range(0, len(x) - N + 1, hop))
    if starts[-1] != len(x) - N:
        starts.append(len(x) - N)
    best_s, best_e = 0, -1.0
    for s in starts:
        z = x[s:s + N]
        e = float(np.mean(z * z))
        if e > best_e:
            best_s, best_e = s, e
    return x[best_s:best_s + N].copy(), best_s


def load_audio(path, target_fs: int, N: int):
    from pathlib import Path
    from scipy.io import wavfile
    fs, raw = wavfile.read(path)
    x = _to_float(raw)
    x = _resample(x, int(fs), target_fs)
    x = x - float(np.mean(x))
    excerpt, start = _max_rms_excerpt(x, N)
    rms = float(np.sqrt(np.mean(excerpt**2)))
    peak = float(np.max(np.abs(excerpt))) if len(excerpt) else 0.0
    nrm = float(np.linalg.norm(excerpt))
    if nrm > 0:
        excerpt = excerpt / nrm
    return excerpt.astype(np.complex128), {
        'source_sample_rate': int(fs), 'target_sample_rate': int(target_fs),
        'source_num_samples': int(len(raw)), 'resampled_num_samples': int(len(x)),
        'excerpt_start_resampled': int(start), 'excerpt_length': int(N),
        'excerpt_rms_before_norm': rms, 'excerpt_peak_before_norm': peak,
    }

