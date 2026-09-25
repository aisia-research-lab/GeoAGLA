#!/usr/bin/env python3
"""
Phase 4H-R2: Step 2 — Validate Implementation Equivalence Gates (Section 7).
Validates:
- Gate R2-A: NAGLA (H=49) recurrence equivalence (max abs diff <= 1e-12)
- Gate R2-B: AGLA Table-II (1.05, 1.35, 1.25) recurrence equivalence (max abs diff <= 1e-12)
- Gate R2-C: AGLA non-collapse check (beta != 0, gamma != 1, trajectory != FGLA)
- Gate R2-D: Determinism check across identical initializations (max abs diff <= 1e-12)

Produces:
- tests/nagla_h49_recurrence_equivalence.csv
- tests/agla_tableII_recurrence_equivalence.csv
- tests/determinism.csv
- tests/pytest.log
"""
import sys
from pathlib import Path

EXP_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXP_DIR.parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np
import pandas as pd

from geometry_gla.operators.stft import hann_window, AnalysisOperator
from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.operators.projections import griffin_lim_map
from geometry_gla.algorithms.agla import run_agla_state, run_nagla_state

TESTS_DIR = EXP_DIR / "tests"
TESTS_DIR.mkdir(parents=True, exist_ok=True)


def create_deterministic_fixtures():
    """Create 3 deterministic, reproducible fixtures spanning different sizes."""
    fixtures = []
    configs = [
        {"seed": 101, "n_sig": 512, "n_fft": 128, "hop": 32, "win": 128},
        {"seed": 202, "n_sig": 1024, "n_fft": 256, "hop": 64, "win": 256},
        {"seed": 303, "n_sig": 2048, "n_fft": 512, "hop": 128, "win": 512},
    ]
    for cfg in configs:
        rng = np.random.default_rng(cfg["seed"])
        raw_x = rng.normal(size=cfg["n_sig"])
        raw_x -= np.mean(raw_x)
        raw_x /= np.linalg.norm(raw_x)
        
        op = FFTAnalysisOperator(cfg["n_sig"], hann_window(cfg["win"]), cfg["hop"], cfg["win"])
        c_star = op.analyze(raw_x)
        s = np.abs(c_star)
        
        # Perturbed initial state in range
        pert_x = rng.normal(size=cfg["n_sig"])
        pert_x -= np.mean(pert_x)
        pert_x /= np.linalg.norm(pert_x)
        pert_c = op.analyze(pert_x)
        c0 = c_star + 0.05 * pert_c
        
        fixtures.append({
            "name": f"fixture_{cfg['seed']}",
            "op": op,
            "c0": c0,
            "s": s,
            "c_star": c_star,
        })
    return fixtures


def validate_gate_r2_a(fixtures):
    """Gate R2-A: NAGLA (H=49) recurrence equivalence."""
    print("--- [Gate R2-A] Validating NAGLA (H=49) Recurrence Equivalence ---")
    results = []
    all_pass = True

    for fix in fixtures:
        c0, s, op = fix["c0"], fix["s"], fix["op"]
        n_iter = 15
        H = 49

        # 1. Implementation
        impl_traj = run_nagla_state(c0, s, op, n_iter=n_iter, H=H)

        # 2. Reference formula strictly evaluated from Section 1.1:
        # X_{i+1} = P_V(P_T(Y_i))
        # Y_{i+1} = X_{i+1} + alpha_i * (X_{i+1} - X_i)
        # alpha_i = (i + H - 2) / (i + H + 1)
        ref_traj = [c0.copy()]
        x_prev = c0.copy()
        y = c0.copy()
        for i in range(1, n_iter + 1):
            x_next = griffin_lim_map(y, s, op)
            alpha_i = float(i + H - 2.0) / float(i + H + 1.0)
            y = x_next + alpha_i * (x_next - x_prev)
            x_prev = x_next
            ref_traj.append(x_prev.copy())
        ref_traj = np.asarray(ref_traj)

        max_err = float(np.max(np.abs(impl_traj - ref_traj)))
        status = "PASS" if max_err <= 1e-12 else "FAIL"
        if status != "PASS":
            all_pass = False

        results.append({
            "fixture": fix["name"],
            "comparator": "NAGLA_H49",
            "iterations": n_iter,
            "max_abs_diff": max_err,
            "tolerance": 1e-12,
            "status": status,
        })
        print(f"  {fix['name']}: max_diff={max_err:.2e} -> {status}")

    df_a = pd.DataFrame(results)
    out_csv = TESTS_DIR / "nagla_h49_recurrence_equivalence.csv"
    df_a.to_csv(out_csv, index=False)
    print(f"Gate R2-A Status: {'3/3 PASS' if all_pass else 'FAILED'}\n")
    return all_pass


def validate_gate_r2_b(fixtures):
    """Gate R2-B: AGLA Table-II (1.05, 1.35, 1.25) recurrence equivalence."""
    print("--- [Gate R2-B] Validating AGLA Table-II (1.05, 1.35, 1.25) Recurrence Equivalence ---")
    results = []
    all_pass = True

    alpha = 1.05
    beta = 1.35
    gamma = 1.25

    for fix in fixtures:
        c0, s, op = fix["c0"], fix["s"], fix["op"]
        n_iter = 15

        # 1. Implementation
        impl_traj = run_agla_state(c0, s, op, n_iter=n_iter, alpha=alpha, beta=beta, gamma=gamma)

        # 2. Reference formula strictly evaluated from Section 2:
        # t_n = (1 - gamma)*d_{n-1} + gamma*P_C1(P_C2(c_{n-1}))
        # c_n = t_n + alpha*(t_n - t_{n-1})
        # d_n = t_n + beta*(t_n - t_{n-1})
        ref_traj = [c0.copy()]
        t_prev = c0.copy()
        c_prev = c0.copy()
        d_prev = c0.copy()
        for n in range(1, n_iter + 1):
            g = griffin_lim_map(c_prev, s, op)
            t_next = (1.0 - gamma) * d_prev + gamma * g
            delta = t_next - t_prev
            c_prev = t_next + alpha * delta
            d_prev = t_next + beta * delta
            t_prev = t_next
            ref_traj.append(t_prev.copy())
        ref_traj = np.asarray(ref_traj)

        max_err = float(np.max(np.abs(impl_traj - ref_traj)))
        status = "PASS" if max_err <= 1e-12 else "FAIL"
        if status != "PASS":
            all_pass = False

        results.append({
            "fixture": fix["name"],
            "comparator": "AGLA_TableII",
            "iterations": n_iter,
            "max_abs_diff": max_err,
            "tolerance": 1e-12,
            "status": status,
        })
        print(f"  {fix['name']}: max_diff={max_err:.2e} -> {status}")

    df_b = pd.DataFrame(results)
    out_csv = TESTS_DIR / "agla_tableII_recurrence_equivalence.csv"
    df_b.to_csv(out_csv, index=False)
    print(f"Gate R2-B Status: {'3/3 PASS' if all_pass else 'FAILED'}\n")
    return all_pass


def validate_gate_r2_c(fixtures):
    """Gate R2-C: AGLA non-collapse check."""
    print("--- [Gate R2-C] Validating AGLA Non-Collapse Check ---")
    alpha, beta, gamma = 1.05, 1.35, 1.25
    assert beta != 0, "Gate R2-C Failed: beta must not be 0"
    assert gamma != 1, "Gate R2-C Failed: gamma must not be 1"

    fix = fixtures[0]
    c0, s, op = fix["c0"], fix["s"], fix["op"]

    traj_agla = run_agla_state(c0, s, op, n_iter=10, alpha=alpha, beta=beta, gamma=gamma)
    traj_fgla_like = run_agla_state(c0, s, op, n_iter=10, alpha=alpha, beta=0.0, gamma=1.0)

    diff = float(np.max(np.abs(traj_agla[-1] - traj_fgla_like[-1])))
    passes = diff > 1e-4
    print(f"  beta={beta} (!=0), gamma={gamma} (!=1)")
    print(f"  Discrepancy against collapsed FGLA dynamics: {diff:.4e}")
    print(f"Gate R2-C Status: {'PASS' if passes else 'FAIL'}\n")
    return passes


def validate_gate_r2_d(fixtures):
    """Gate R2-D: Determinism check across identical initializations."""
    print("--- [Gate R2-D] Validating Determinism (Max diff <= 1e-12) ---")
    results = []
    all_pass = True

    for fix in fixtures:
        c0, s, op = fix["c0"], fix["s"], fix["op"]
        
        # Test NAGLA
        traj_nagla_1 = run_nagla_state(c0, s, op, n_iter=10, H=49)
        traj_nagla_2 = run_nagla_state(c0, s, op, n_iter=10, H=49)
        diff_nagla = float(np.max(np.abs(traj_nagla_1 - traj_nagla_2)))
        
        # Test AGLA
        traj_agla_1 = run_agla_state(c0, s, op, n_iter=10, alpha=1.05, beta=1.35, gamma=1.25)
        traj_agla_2 = run_agla_state(c0, s, op, n_iter=10, alpha=1.05, beta=1.35, gamma=1.25)
        diff_agla = float(np.max(np.abs(traj_agla_1 - traj_agla_2)))
        
        for m_name, diff_val in [("NAGLA_H49", diff_nagla), ("AGLA_TableII", diff_agla)]:
            st = "PASS" if diff_val <= 1e-12 else "FAIL"
            if st != "PASS":
                all_pass = False
            results.append({
                "fixture": fix["name"],
                "method": m_name,
                "reproducibility_diff": diff_val,
                "tolerance": 1e-12,
                "status": st,
            })
            print(f"  {fix['name']} [{m_name}]: diff={diff_val:.2e} -> {st}")

    df_d = pd.DataFrame(results)
    out_csv = TESTS_DIR / "determinism.csv"
    df_d.to_csv(out_csv, index=False)
    print(f"Gate R2-D Status: {'PASS' if all_pass else 'FAILED'}\n")
    return all_pass


def main():
    fixtures = create_deterministic_fixtures()
    pass_a = validate_gate_r2_a(fixtures)
    pass_b = validate_gate_r2_b(fixtures)
    pass_c = validate_gate_r2_c(fixtures)
    pass_d = validate_gate_r2_d(fixtures)

    log_lines = [
        "==================================================",
        "PHASE 4H-R2 IMPLEMENTATION EQUIVALENCE GATES AUDIT",
        "==================================================",
        f"Gate R2-A (NAGLA H=49 Recurrence Equivalence) : {'PASS' if pass_a else 'FAIL'}",
        f"Gate R2-B (AGLA Table-II Recurrence Equiv.)   : {'PASS' if pass_b else 'FAIL'}",
        f"Gate R2-C (AGLA Non-Collapse Check)          : {'PASS' if pass_c else 'FAIL'}",
        f"Gate R2-D (Numerical Determinism)             : {'PASS' if pass_d else 'FAIL'}",
        "==================================================",
        f"OVERALL EQUIVALENCE AUDIT: {'ALL GATES PASSED (GREEN)' if (pass_a and pass_b and pass_c and pass_d) else 'FAILED'}",
        "==================================================",
    ]
    log_text = "\n".join(log_lines)
    print(log_text)
    (TESTS_DIR / "pytest.log").write_text(log_text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
