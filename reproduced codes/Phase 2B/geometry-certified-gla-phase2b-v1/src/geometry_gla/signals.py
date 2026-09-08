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
