# Phase-1E-R Reproduction Guide v1

## Purpose

Reproduce the Online Rate-Realization Failure Decomposition & Repair gate after Phase-1E.

## Install

```bash
cd geometry-certified-gla-phase1er-v1
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -e .
```

## Run tests

```bash
pytest -q
```

Expected: 13 tests pass.

## Reproduce Phase-1E-R

```bash
python reproduce/run_phase1er.py
```

This executes both the 192-run policy decomposition and the independent horizon audit at 120/180/240/360 iterations.

## Main outputs

```text
results/phase1er/
├── failure_decomposition.csv
├── failure_decomposition.json
├── policy_summary.json
├── horizon_audit.json
├── summary.json
└── figures/
    ├── ER1_rate_realization.png
    ├── ER2_h4_policy.png
    ├── ER3_switching_vs_frozen.png
    └── ER4_horizon_realization.png
```

## Files to send back for audit

Please send:

```text
results/phase1er/summary.json
results/phase1er/policy_summary.json
results/phase1er/horizon_audit.json
```

## Frozen gates

- H4: beat fraction >= 0.70 and median `q_online/q_FGLA < 1`.
- H5: mean late rejection fraction <= 0.05.
- E1: zero safe-fallback E1 failures.

Do not change these thresholds after observing the run.

## Interpretation warning

`oracle_frozen` is a diagnostic control only and is excluded from practical-policy selection. The online estimator is a performance estimator, not a certified spectral upper bound. Global safety continues to come from the fixed checkpoint merit and rollback fallback.
