# E10-R2F Code Package v1

This package is a **forensic closure patch** for the existing GeoAGLA repository. It does not replace the repository.

## Files

Copy these three scripts into:

```text
experiments/08_e10_robustness_mechanism_ablation/
```

- `06_e10r2f_equivalence.py`
- `07_e10r2f_event_repair.py`
- `08_audit_e10r2f.py`

The package assumes the repository already contains:

```text
04_run_e10r2_canonical.py
configs/phase2b_grid.json
experiments/05_real_audio_basin_transfer/03_phase2b_real_audio_basin_sweep.py
experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv
src/geometry_gla/...
```

## Step 0 — Preserve the primary ledger

Copy the final E10-R2 primary ledger somewhere read-only:

```bash
mkdir -p results/08_e10r2f_forensic/primary
cp /PATH/TO/e10r2_run_ledger.csv \
   results/08_e10r2f_forensic/primary/e10r2_run_ledger.csv
```

Do not modify this file.

## Step 1 — Run six-variant equivalence

```bash
PYTHONPATH=src python experiments/08_e10_robustness_mechanism_ablation/06_e10r2f_equivalence.py \
  --audio-dir /PATH/TO/MUSAN_ODD_202 \
  --locked-geometry experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv \
  --out results/08_e10r2f_forensic/tests
```

Expected:

```text
equivalence rows=18
leakage rows=12
failures=0
E10-R2F F1 PASS
```

If any row fails: **STOP**.

## Step 2 — Run online-only event reconstruction

This reruns only the four online variants. It never overwrites the primary ledger.

```bash
PYTHONPATH=src python experiments/08_e10_robustness_mechanism_ablation/07_e10r2f_event_repair.py \
  --audio-dir /PATH/TO/MUSAN_ODD_202 \
  --locked-geometry experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv \
  --primary-ledger results/08_e10r2f_forensic/primary/e10r2_run_ledger.csv \
  --out results/08_e10r2f_forensic
```

Expected hard gates:

```text
online rows = 18,960
event rows = 834,240
44 events per (run_key, online variant)
0 duplicate event keys
0 rerun-to-primary failures
```

The runner checkpoints **both run rows and event rows**. If interrupted, rerun the same command and it resumes.

If `rerun_primary_failures > 0`: **STOP** and do not overwrite anything.

## Step 3 — Mechanical audit

```bash
PYTHONPATH=src python experiments/08_e10_robustness_mechanism_ablation/08_audit_e10r2f.py \
  --closure-dir results/08_e10r2f_forensic
```

Expected:

```text
"status": "PASS"
```

## Step 4 — Pytest

Run the repository test suite:

```bash
PYTHONPATH=src pytest -q | tee results/08_e10r2f_forensic/tests/pytest.log
```

Requirement: `0 failed`.

## Step 5 — Provenance

Copy the exact executed scripts into:

```text
results/08_e10r2f_forensic/executed_code/
```

Then create hashes:

```bash
cd results/08_e10r2f_forensic
sha256sum \
  executed_code/* \
  primary/e10r2_run_ledger.csv \
  events/e10r2_complete_event_ledger.csv \
  > executed_code/SHA256SUMS.txt
```

Also save:

```bash
python --version > logs/python_version.txt
pip freeze > logs/pip_freeze.txt
```

## Step 6 — Independent forensic audit

The independent forensic audit inspects:

- 18 equivalence rows, all PASS;
- 12 no-oracle-leakage rows, all PASS;
- 18,960 online forensic rows;
- 834,240 event rows;
- 44 events/run/variant;
- no duplicate event keys;
- rerun-to-primary equivalence all PASS;
- raw/env variants never use fallback;
- hashes and logs.

The audit produces:

```text
audit/E10R2F_FORENSIC_AUDIT.md
```

with a final verdict:

```text
GREEN — eligible for final E10 freeze
```

or

```text
NO-GO — unresolved forensic/reproducibility issue
```

## Important

Do **not** change:

- threshold `1e-5`;
- orbit ratio `0.10`;
- locked 395 cases;
- historical-batch2 seeds;
- initialization grid;
- online parameters;
- primary ledger.

Do not attempt to reproduce a desired effect size. The only target is exact canonical reproducibility.
