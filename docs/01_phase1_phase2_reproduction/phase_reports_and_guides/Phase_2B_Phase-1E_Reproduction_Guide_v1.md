# Phase-1E — Reproduction Guide v1

## 1. Create an environment

```bash
cd geometry-certified-gla-phase1e-v1
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

## 2. Run the full package

```bash
python reproduce/run_phase1e.py
```

The command runs the complete unit-test suite followed by the Phase-1E experiment
matrix.

Expected unit-test result:

```text
12 passed
```

## 3. Run only Phase-1E experiments

```bash
python -m experiments.phase1e_safeguarded.run
```

## 4. Main outputs

```text
results/phase1e/
├── main_runs.json
├── main_runs.csv
├── setting_selection.json
├── hostile_estimator.json
├── summary.json
└── figures/
    ├── D4_online_acceleration.png
    ├── D5_safeguard_decisions.png
    └── D5b_h4_setting_sweep.png
```

## 5. What to send back for audit

Please send these three files after reproduction:

```text
results/phase1e/summary.json
results/phase1e/setting_selection.json
results/phase1e/hostile_estimator.json
```

If the run errors, also save:

```bash
python --version
python -m pip freeze
```

and the complete terminal output.

## 6. Current reference result

The reference run bundled with v1 gives:

- 216 main online runs;
- selected setting `K=8`, `margin=0.001`;
- H5 eventual-inactivity diagnostic: PASS;
- safe-fallback E1 diagnostic: PASS;
- hostile-estimator convergence diagnostic: PASS;
- H4 online-vs-FGLA performance gate: FAIL at 66.7% versus the frozen 70% threshold;
- overall Phase-1E v1 gate: **YELLOW**.

This is intentional and scientifically important: do not alter the gate merely to
make the package report GREEN.
