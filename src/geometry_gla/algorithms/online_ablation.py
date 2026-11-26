"""Configurable mechanism-ablation runner built on the safeguarded online engine.

Switches isolate (i) passive Rayleigh-Ritz estimation, (ii) running-max edge
envelope memory, and (iii) checkpoint rollback to standard GLA.
"""
from __future__ import annotations
import numpy as np
from geometry_gla.algorithms.minimax import oracle_minimax
from geometry_gla.algorithms.online_safe import _align_pair, _edge_from_history, _one_step, _run_block
from geometry_gla.safeguards.checkpoint import checkpoint_accept


def run_online_ablation(
    t0,
    t_minus1,
    s,
    op,
    *,
    n_iter=360,
    warmup=12,
    block_size=8,
    memory=3,
    margin=0.0,
    lambda_ceiling=1 - 1e-8,
    svd_rtol=1e-9,
    cond_max=1e10,
    alpha_safe=0.0,
    beta_safe=0.0,
    gamma_safe=1.0,
    K_safe=0.25,
    descent_a=1e-4,
    use_envelope=False,
    use_fallback=False,
):
    """Run an online policy variant with explicit mechanism switches.

    Warmup and estimator history match the standard safeguarded online runner.
    When ``use_fallback=False``, the candidate block is committed regardless of
    the checkpoint diagnostic, while the diagnostic is still evaluated and logged.
    """
    t = np.asarray(t0, np.complex128).copy()
    tp = np.asarray(t_minus1, np.complex128).copy()
    committed = [t.copy()]
    qhist = []
    ghist = []
    logs = []
    n_done = 0
    edge_state = None

    for _ in range(min(warmup, n_iter)):
        new, q, g = _one_step(t, tp, s, op, alpha_safe, beta_safe, gamma_safe)
        ref = qhist[-1] if qhist else None
        qa, ga = _align_pair(q, g, ref)
        qhist.append(qa)
        ghist.append(ga)
        tp, t = t, new
        committed.append(t.copy())
        n_done += 1

    block_id = 0
    while n_done < n_iter:
        K = min(block_size, n_iter - n_done)
        block_id += 1
        estres = _edge_from_history(qhist, ghist, memory, svd_rtol, cond_max)
        raw = float(estres["estimate"]) if estres is not None else None
        if raw is not None:
            edge_state = max(edge_state, raw) if (use_envelope and edge_state is not None) else raw

        if edge_state is None:
            synth = None
            pars = {"alpha": 0.0, "beta": 0.0, "gamma": 1.0, "q": None}
            proposal = "safe_no_estimate"
        else:
            synth = float(np.clip(edge_state + margin, 1e-8, lambda_ceiling))
            pars = oracle_minimax(0.0, synth)
            proposal = "online"

        st = t.copy()
        sp = tp.copy()
        ct, cp, cstates, cq, cg = _run_block(t, tp, s, op, pars["alpha"], pars["beta"], pars["gamma"], K)
        check = checkpoint_accept(st, sp, ct, cp, cstates, s, alpha_safe=alpha_safe, K_safe=K_safe, descent_a=descent_a)
        rejected = not check["accepted"]
        fallback_used = bool(use_fallback and rejected)

        if fallback_used:
            et, ep, states, qs, gs = _run_block(st, sp, s, op, alpha_safe, beta_safe, gamma_safe, K)
        else:
            et, ep, states, qs, gs = ct, cp, cstates, cq, cg

        ref = qhist[-1] if qhist else None
        for q, g in zip(qs, gs):
            qa, ga = _align_pair(q, g, ref)
            qhist.append(qa)
            ghist.append(ga)
            ref = qa
        for z in states[1:]:
            committed.append(z.copy())

        logs.append(
            dict(
                block=block_id,
                start_iter=n_done,
                end_iter=n_done + K,
                raw_current=raw,
                edge_state=edge_state,
                synth_edge=synth,
                alpha=pars["alpha"],
                beta=pars["beta"],
                gamma=pars["gamma"],
                checkpoint_accepted=not rejected,
                fallback_used=fallback_used,
                candidate_phi_start=check["phi_start"],
                candidate_phi_end=check["phi_end"],
            )
        )
        t, tp = et, ep
        n_done += K

    return {"trajectory": np.asarray(committed), "blocks": logs, "query_history": qhist, "image_history": ghist}
