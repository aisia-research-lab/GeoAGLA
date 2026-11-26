"""Shared operators, dataset loading, initializations, and PyTorch solver engine."""
from __future__ import annotations

import hashlib
import json
import math
import time
from math import gcd
from pathlib import Path
from typing import Iterator

import numpy as np
import torch
from scipy.signal import resample_poly

from geometry_gla.algorithms.minimax import (
    mismatch_acceleration_interval,
    mismatch_radius,
    one_edge_minimax,
    oracle_minimax,
)
from geometry_gla.operators.stft_torch import TorchPeriodicSTFT

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "configs"
INPUT_DIR = REPO_ROOT / "inputs"

STFT_PROFILES: dict[str, tuple[int, int]] = {
    "gaussian": (256, 32),
    "hann": (512, 128),
}

STANDARD_INITS: list[str] = [
    "transverse_0.001",
    "transverse_0.01",
    "transverse_0.05",
    "phase_jitter_0.05",
    "phase_jitter_0.15",
    "phase_jitter_0.30",
]
ALL_INITS: list[str] = STANDARD_INITS + ["signal_noise_0.1", "random_phase"]

METHODS: list[str] = [
    "Online",
    "NAGLA_H2",
    "FGLA_095",
    "RestartNAG",
    "OneEdgeOracle",
    "OnlineNoFallback",
    "OnlineRaw",
    "OnlineGram",
    "GLA",
    "AGLA_tuned",
]

CALL_BUDGETS: list[int] = [90, 180, 360, 720, 1440, 2880]
WALL_BUDGETS: list[float] = [0.05, 0.1, 0.2, 0.5, 1.0]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_window(profile: str) -> tuple[np.ndarray, int, int]:
    """Return (window_array, hop, n_fft) for a named STFT profile."""
    frame_len, hop = STFT_PROFILES[profile]
    n = np.arange(frame_len, dtype=float)
    if profile == "gaussian":
        sigma = frame_len / 6.0
        w = np.exp(-0.5 * ((n - (frame_len - 1) / 2.0) / sigma) ** 2)
    elif profile == "hann":
        w = 0.5 - 0.5 * np.cos(2.0 * np.pi * n / frame_len)
    else:
        raise ValueError(f"Unknown STFT profile: {profile}")
    return w, hop, frame_len


class NumpyPeriodicSTFT:
    """Periodic full-complex STFT operator in NumPy (complex128)."""

    def __init__(self, signal_length: int, window: np.ndarray, hop: int, n_fft: int):
        self.N = int(signal_length)
        self.w = np.asarray(window, dtype=float)
        self.hop = int(hop)
        self.f = int(n_fft)
        n_frames = self.N // self.hop
        self.ix = (np.arange(n_frames)[:, None] * self.hop + np.arange(len(self.w))[None, :]) % self.N
        self.frame_diag = np.zeros(self.N, dtype=float)
        np.add.at(self.frame_diag, self.ix.ravel(), np.tile(self.f * self.w * self.w, n_frames))
        self.projections = 0

    def analyze(self, x: np.ndarray) -> np.ndarray:
        return np.fft.fft(x[self.ix] * self.w, n=self.f, axis=-1).ravel()

    def adjoint(self, c: np.ndarray) -> np.ndarray:
        z = np.fft.ifft(c.reshape(-1, self.f), axis=-1) * self.f
        out = np.zeros(self.N, dtype=np.complex128)
        np.add.at(out, self.ix.ravel(), (z[:, : len(self.w)] * self.w).ravel())
        return out

    def synthesize(self, c: np.ndarray) -> np.ndarray:
        return self.adjoint(c) / self.frame_diag

    def project_range(self, c: np.ndarray) -> np.ndarray:
        self.projections += 1
        return self.analyze(self.synthesize(c))

    def G(self, c: np.ndarray, s: np.ndarray) -> np.ndarray:
        mag = np.abs(c)
        phase = np.divide(c, mag, out=np.ones_like(c), where=mag > 0)
        return self.project_range(s * phase)

    def synchronize(self) -> None:
        pass

    def tensor(self, x: np.ndarray) -> np.ndarray:
        return np.asarray(x, dtype=np.complex128)


def preprocess_audio(x: np.ndarray, sr: int, excerpt_len: int, record: dict | None = None) -> np.ndarray:
    """Convert to mono, resample to 16 kHz, center, crop fixed excerpt, and unit-normalize."""
    mono = x.mean(axis=1)
    g = gcd(sr, 16000)
    if sr != 16000:
        mono = resample_poly(mono, 16000 // g, sr // g)
    mono = mono - mono.mean()
    if len(mono) < excerpt_len:
        raise ValueError(f"Audio shorter than requested excerpt length {excerpt_len}")
    rec = record or {}
    historical = rec.get("historical_excerpt_length") == excerpt_len and "historical_excerpt_start" in rec
    start = int(rec["historical_excerpt_start"]) if historical else (len(mono) - excerpt_len) // 2
    if start < 0 or start + excerpt_len > len(mono):
        raise ValueError("Excerpt bounds fall outside decoded audio")
    excerpt = mono[start : start + excerpt_len].copy()
    norm_val = float(np.linalg.norm(excerpt))
    if historical:
        rms = float(rec["historical_rms"])
        if abs(norm_val / math.sqrt(excerpt_len) - rms) > 1e-7 * max(1.0, rms):
            raise ValueError("Historical excerpt RMS mismatch")
    if norm_val < 1e-12:
        raise ValueError("Silent audio excerpt")
    return excerpt / norm_val


def load_audio_records(
    audio_root: str | Path,
    manifest_path: Path | None = None,
) -> Iterator[tuple[dict, np.ndarray]]:
    """Yield (record_dict, normalized_signal) pairs from a local audio directory.

    Every file must match the source SHA256 and decoded-PCM SHA256 recorded in
    inputs/prior_audit.json; mismatching or missing files raise instead of being replaced.
    """
    import soundfile as sf

    mpath = manifest_path or (INPUT_DIR / "manifest.json")
    audit = json.loads((INPUT_DIR / "prior_audit.json").read_text(encoding="utf-8"))
    if audit.get("status") != "PASS" or audit.get("manifest_sha256") != sha256_bytes(mpath.read_bytes()):
        raise ValueError(f"Manifest {mpath} does not match inputs/prior_audit.json")
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    root = Path(audio_root)
    for rec in manifest:
        wav_path = root / rec["path"]
        if not wav_path.exists():
            # Allow the original nested MUSAN layout (e.g., music/fma/...), but only an unambiguous match.
            matches = list(root.rglob(Path(rec["path"]).name))
            if len(matches) != 1:
                raise FileNotFoundError(f"Expected exactly one {rec['path']} under {root}, found {len(matches)}")
            wav_path = matches[0]
        expected = audit["sources"][rec["source_id"]]
        if sha256_bytes(wav_path.read_bytes()) != expected["source_sha256"]:
            raise ValueError(f"Source SHA256 mismatch: {wav_path}")
        audio, sr = sf.read(str(wav_path), dtype="float64", always_2d=True)
        if audio.size == 0 or not np.isfinite(audio).all():
            raise ValueError(f"Invalid or empty audio file: {wav_path}")
        audio = np.asarray(audio, dtype="<f8", order="C")
        pcm_hash = sha256_bytes(str((int(sr), audio.shape)).encode() + audio.tobytes())
        if pcm_hash != expected["pcm_sha256"]:
            raise ValueError(f"Decoded PCM SHA256 mismatch: {wav_path}")
        sig = preprocess_audio(audio, int(sr), int(rec.get("historical_excerpt_length", 4096)), rec)
        yield rec, sig


def build_initial_state(c_star: np.ndarray, op: NumpyPeriodicSTFT, kind: str, seed: int) -> np.ndarray:
    """Construct a reproducible starting spectrogram in range(T)."""
    rng = np.random.default_rng(seed)
    R = float(np.linalg.norm(c_star))
    if kind.startswith("transverse_"):
        eps = float(kind.split("_")[-1])
        d = op.analyze(rng.normal(size=op.N) + 1j * rng.normal(size=op.N))
        d = d - 1j * c_star * np.vdot(1j * c_star, d).real / (R**2)
        return c_star + eps * R * d / np.linalg.norm(d)
    if kind == "signal_noise_0.1":
        d = op.analyze(rng.normal(size=op.N) + 1j * rng.normal(size=op.N))
        return c_star + 0.1 * R * d / np.linalg.norm(d)
    if kind.startswith("phase_jitter_"):
        sigma = float(kind.split("_")[-1])
        return op.project_range(c_star * np.exp(1j * sigma * rng.normal(size=len(c_star))))
    if kind == "random_phase":
        return op.project_range(np.abs(c_star) * np.exp(1j * rng.uniform(-np.pi, np.pi, len(c_star))))
    raise ValueError(f"Unknown initialization kind: {kind}")


def _vec_norm(x: torch.Tensor) -> torch.Tensor:
    return torch.linalg.vector_norm(x)


def _tensor_hash(x: torch.Tensor) -> str:
    return hashlib.sha256(x.detach().cpu().numpy().tobytes()).hexdigest()


def _ritz_edge_torch(
    qhist: list[torch.Tensor],
    ghist: list[torch.Tensor],
    use_gram: bool = False,
) -> tuple[float | None, int, float | None]:
    """Passive Rayleigh-Ritz dominant eigenvalue estimate from recent secants."""
    if len(qhist) < 4:
        return None, 0, None
    S = torch.stack([qhist[i] - qhist[i - 1] for i in range(1, 4)], dim=1)
    Y = torch.stack([ghist[i] - ghist[i - 1] for i in range(1, 4)], dim=1)
    if use_gram:
        eigvals, eigvecs = torch.linalg.eigh((S.conj().T @ S).real)
        eigvals = eigvals.flip(0).clamp(min=0.0)
        eigvecs = eigvecs.flip(1)
        sig = eigvals.sqrt()
        if float(sig[0]) == 0.0:
            return None, 0, None
        rank = int((sig > 1e-9 * sig[0]).sum())
        cond = float(sig[0] / sig[rank - 1])
        if cond > 1e10:
            return None, rank, cond
        W = eigvecs[:, :rank] / sig[:rank]
        C = W.T @ (S.conj().T @ Y).real @ W
    else:
        S_real = torch.cat((S.real, S.imag), dim=0)
        Y_real = torch.cat((Y.real, Y.imag), dim=0)
        U, sig, Vh = torch.linalg.svd(S_real, full_matrices=False)
        if float(sig[0]) == 0.0:
            return None, 0, None
        rank = int((sig > 1e-9 * sig[0]).sum())
        cond = float(sig[0] / sig[rank - 1])
        if cond > 1e10:
            return None, rank, cond
        C = U[:, :rank].T @ (Y_real @ Vh[:rank, :].T / sig[:rank])
    sym_C = 0.5 * (C + C.T)
    return float(torch.linalg.eigvalsh(sym_C)[-1]), rank, cond


def _checkpoint_merit_torch(t: torch.Tensor, tp: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
    return 0.5 * torch.sum((torch.abs(t) - s) ** 2) + 0.125 * torch.sum(torch.abs(t - tp) ** 2)


def _check_block_torch(
    t: torch.Tensor,
    tp: torch.Tensor,
    tn: torch.Tensor,
    pp: torch.Tensor,
    path: list[torch.Tensor],
    s: torch.Tensor,
) -> dict:
    m0 = float(_checkpoint_merit_torch(t, tp, s))
    m1 = float(_checkpoint_merit_torch(tn, pp, s))
    D2 = float(torch.sum(torch.abs(torch.diff(torch.stack(path), dim=0)) ** 2))
    slack = m0 - m1 - 1e-4 * D2
    accepted = bool(m1 + 1e-4 * D2 <= m0 + 1e-14 * max(1.0, abs(m0)))
    return {"phi_start": m0, "phi_end": m1, "D2": D2, "slack": slack, "accepted": accepted}


def _compute_errors_torch(
    t: torch.Tensor, tp: torch.Tensor, c: torch.Tensor, s: torch.Tensor
) -> tuple[float, float, float]:
    norm_c = _vec_norm(c)
    phase = torch.angle(torch.vdot(c, t))
    orbit_err = float(_vec_norm(t - c * torch.exp(1j * phase)) / norm_c)
    mag_err = float(_vec_norm(torch.abs(t) - s) / _vec_norm(s))
    phase2 = torch.angle(torch.vdot(c, t + tp))
    state_err = float(
        torch.sqrt(
            _vec_norm(t - c * torch.exp(1j * phase2)) ** 2
            + _vec_norm(tp - c * torch.exp(1j * phase2)) ** 2
        )
        / (math.sqrt(2.0) * norm_c)
    )
    return orbit_err, mag_err, state_err


def run_solver(
    op: TorchPeriodicSTFT,
    c_star: np.ndarray,
    init: np.ndarray,
    method: str,
    L: float | None = None,
    max_iter: int = 2884,
    wall_limit: float | None = None,
    record_trace: bool = False,
    record_hashes: bool = False,
) -> dict:
    """Execute one solver trajectory on the unified PyTorch STFT backend."""
    if method not in METHODS:
        raise ValueError(f"Unknown method: {method}")
    if method == "OneEdgeOracle" and L is None:
        raise ValueError("OneEdgeOracle requires true spectral edge L")

    c = op.tensor(c_star)
    s = torch.abs(c)
    t = op.tensor(init).clone()
    tp = t.clone()
    qhist: list[torch.Tensor] = []
    ghist: list[torch.Tensor] = []

    edge_state: float | None = None
    step_idx = 0
    elapsed = 0.0
    t0_wall = time.perf_counter()
    op.projections = 0

    e0, mag0, state0 = _compute_errors_torch(t, tp, c, s)
    R = float(_vec_norm(c))
    lo, hi = mismatch_acceleration_interval(L) if L is not None else (None, None)
    trajectory = [t.detach().cpu().numpy().copy()] if record_trace else None
    block_logs: list[dict] = []
    restart_age = 0

    def _one_step(cur: torch.Tensor, prev: torch.Tensor, a: float, b: float, g: float):
        q = cur + a * (cur - prev)
        d = cur + b * (cur - prev)
        y = op.G(q, s)
        return (1.0 - g) * d + g * y, q, y

    def _run_block(cur: torch.Tensor, prev: torch.Tensor, K: int, a: float, b: float, g: float):
        path = [cur]
        qs, gs = [], []
        for _ in range(K):
            nxt, q, y = _one_step(cur, prev, a, b, g)
            prev, cur = cur, nxt
            path.append(cur)
            qs.append(q)
            gs.append(y)
        return cur, prev, path, qs, gs

    def _append_history(q: torch.Tensor, y: torch.Tensor) -> None:
        if qhist:
            dot = torch.vdot(qhist[-1], q)
            fac = torch.exp(-1j * torch.angle(dot)) if float(torch.abs(dot)) != 0.0 else 1.0
            q = q * fac
            y = y * fac
        qhist.append(q)
        ghist.append(y)
        if len(qhist) > 4:
            qhist.pop(0)
            ghist.pop(0)

    rows = [
        dict(
            iteration=0,
            calls=0,
            solver_seconds=0.0,
            instrumented_seconds=0.0,
            orbit=e0,
            mag=mag0,
            state=state0,
            success=bool(e0 <= 0.1 * e0 and mag0 <= 1e-5),
        )
    ]

    while step_idx < max_iter and (wall_limit is None or elapsed < wall_limit):
        K = min(12 - step_idx if step_idx < 12 else 8, max_iter - step_idx)
        is_online = method.startswith("Online")
        raw_est = None
        rank = 0
        cond = None
        synth_edge = None
        proposal = "warmup" if (is_online and step_idx < 12) else method
        candidate = None
        committed = None
        fallback = False
        extra_calls = 0
        grad_merit = None
        ap, bp, gp = 0.0, 0.0, 1.0

        calls_before = op.projections
        op.synchronize()
        clock_start = time.perf_counter()

        if is_online and step_idx >= 12:
            use_gram = method == "OnlineGram"
            raw_est, rank, cond = _ritz_edge_torch(qhist, ghist, use_gram=use_gram)
            if raw_est is not None and (not use_gram or 0.0 < raw_est < 1.0):
                if edge_state is None or method == "OnlineRaw":
                    edge_state = raw_est
                else:
                    edge_state = max(edge_state, raw_est)

            if edge_state is not None:
                synth_edge = float(np.clip(edge_state, 1e-8, 1.0 - 1e-8))
                par = one_edge_minimax(synth_edge) if use_gram else oracle_minimax(0.0, synth_edge)
                ap, bp, gp = par["alpha"], par["beta"], par["gamma"]
                proposal = "candidate"
            else:
                proposal = "safe_no_estimate"

            tn, pp, path, qs, gs = _run_block(t, tp, K, ap, bp, gp)
            candidate = _check_block_torch(t, tp, tn, pp, path, s)
            fallback = (not candidate["accepted"]) and (method != "OnlineNoFallback")
            if fallback:
                tn, pp, path, qs, gs = _run_block(t, tp, K, 0.0, 0.0, 1.0)
            committed = _check_block_torch(t, tp, tn, pp, path, s) if fallback else candidate
            for q, y in zip(qs, gs):
                _append_history(q, y)
            dg = op.G(tn, s)
            extra_calls = 1
            delta = tn - pp
            grad_merit = float(torch.sqrt(_vec_norm(tn - dg + 0.25 * delta) ** 2 + _vec_norm(0.25 * delta) ** 2))
        elif is_online:
            tn, pp, path, qs, gs = _run_block(t, tp, K, 0.0, 0.0, 1.0)
            for q, y in zip(qs, gs):
                _append_history(q, y)
        elif method in ("NAGLA_H2", "RestartNAG"):
            path = [t]
            tn, pp = t, tp
            for j in range(K):
                age = (step_idx + j) if method == "NAGLA_H2" else restart_age
                alpha_k = age / (age + 3.0)
                xn, q, _ = _one_step(tn, pp, alpha_k, 0.0, 1.0)
                if method == "RestartNAG":
                    restart_age = 0 if float(torch.vdot(q - xn, xn - tn).real) > 0.0 else (restart_age + 1)
                pp, tn = tn, xn
                path.append(tn)
        else:
            if method == "FGLA_095":
                ap = 0.95
            elif method == "AGLA_tuned":
                ap, bp, gp = 0.8, 1.0, 1.1
            elif method == "OneEdgeOracle":
                par = one_edge_minimax(L)
                ap, bp, gp = par["alpha"], par["beta"], par["gamma"]
            tn, pp, path, _, _ = _run_block(t, tp, K, ap, bp, gp)

        op.synchronize()
        elapsed += time.perf_counter() - clock_start
        used = op.projections - calls_before
        assert used == K * (1 + int(fallback)) + extra_calls

        step_idx += K
        t, tp = tn, pp
        if trajectory is not None:
            trajectory.extend(v.detach().cpu().numpy().copy() for v in path[1:])

        e_val, m_val, d_val = _compute_errors_torch(t, tp, c, s)
        assert all(math.isfinite(x) for x in (e_val, m_val, d_val)), "Non-finite iterate"

        row = dict(
            iteration=step_idx,
            calls=op.projections,
            solver_seconds=elapsed,
            instrumented_seconds=time.perf_counter() - t0_wall,
            orbit=e_val,
            mag=m_val,
            state=d_val,
            success=bool(e_val <= 0.1 * e0 and m_val <= 1e-5),
        )
        rows.append(row)

        if is_online and candidate is not None:
            gradient_f = float(_vec_norm(t - dg))
            D_step = math.sqrt(committed["D2"])
            phase_dir = 1j * c
            phase_overlap = max(
                (
                    float(abs(torch.vdot(q2 - q1, phase_dir).real) / (_vec_norm(q2 - q1) * R))
                    for q1, q2 in zip(qhist[:-1], qhist[1:])
                    if float(_vec_norm(q2 - q1)) > 0.0
                ),
                default=0.0,
            )
            block_logs.append(
                dict(
                    **row,
                    proposal=proposal,
                    K=K,
                    raw_current=raw_est,
                    rank=rank,
                    condition=cond,
                    edge_state=edge_state,
                    synth_edge=synth_edge,
                    L=L,
                    gap_ratio=None if (L is None or synth_edge is None) else (1.0 - synth_edge) / (1.0 - L),
                    in_tolerance=None if (L is None or synth_edge is None) else bool(lo < synth_edge < hi),
                    alpha=ap,
                    beta=bp,
                    gamma=gp,
                    candidate=candidate,
                    committed=committed,
                    fallback=fallback,
                    committed_GLA=bool(fallback or edge_state is None),
                    diagnostic_G=extra_calls,
                    gradient_merit_norm=grad_merit,
                    gradient_f_norm=gradient_f,
                    relative_error_ratio=gradient_f / D_step if D_step > 0.0 else None,
                    phase_secant_overlap=phase_overlap,
                    stationary_predicted_R=None if (L is None or synth_edge is None) else mismatch_radius(L, synth_edge),
                    query_hashes=[_tensor_hash(q) for q in qs] if record_hashes else None,
                    state_hash=_tensor_hash(t) if record_hashes else None,
                    orbit_proxy=bool(d_val <= 1e-6),
                )
            )

    return dict(
        rows=rows,
        blocks=block_logs,
        trajectory=trajectory,
        initial_error=e0,
        wall_reached=(wall_limit is None or elapsed >= wall_limit),
    )
