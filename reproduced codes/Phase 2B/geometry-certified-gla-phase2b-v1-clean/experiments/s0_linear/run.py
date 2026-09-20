from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from geometry_gla.algorithms.minimax import oracle_minimax, modal_coefficients
from geometry_gla.metrics.contraction import root_rate_from_errors

INTERVALS = [(0.0,.2),(0.0,.5),(0.0,.8),(0.1,.5),(0.5,.8),(0.8,.95)]


def run_case(lm, lp, n=120):
    prm = oracle_minimax(lm, lp)
    # Endpoint lambda+ produces the worst critical-damped root q*.
    A, C = modal_coefficients(lp, prm["alpha"], prm["beta"], prm["gamma"])
    z_prevprev, z_prev = 0.8, 1.0
    errors = [abs(z_prev)]
    for _ in range(n):
        z = A*z_prev - C*z_prevprev
        z_prevprev, z_prev = z_prev, z
        errors.append(abs(z_prev))
    q_obs, _ = root_rate_from_errors(errors, floor=1e-18)
    return {"lambda_minus":lm,"lambda_plus":lp, **prm, "q_observed":q_obs, "abs_error":abs(q_obs-prm["q"])}


def main(out_dir="results/phase1b"):
    rows=[run_case(*x) for x in INTERVALS]
    p=Path(out_dir); p.mkdir(parents=True,exist_ok=True)
    (p/"s0_results.json").write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows,indent=2))
    return rows

if __name__ == "__main__": main()
