# Experiment 08: E10-R2 / E10-R2F Robustness Mechanism Ablation & Forensic Closure

This directory contains the canonical scripts, locked population, and independent forensic audit pipeline for **Experiment E10-R2** and **E10-R2F** under the frozen GeoAGLA / Phase-2B protocol (ICLR 2027).

---

## 1. Protocol Architecture & Division of Responsibility

According to `E10R2F_Forensic_Closure_Guide.md`:

```
========================================================================================
STAGE 1: Forensic Rerun & Event Reconstruction (Gate F1 & F2) — Experimental Execution & Hard Gates F1/F2
========================================================================================
04_run_e10r2_canonical.py           Canonical E10-R2 synchronous 6-way sweep runner
06_e10r2f_equivalence.py            Gate F1: Six-variant canonical trajectory equivalence,
                                    no-oracle leakage, and resume equivalence
07_e10r2f_event_repair.py           Gate F2: Online event ledger repair (sequential)
09_e10r2f_event_repair_parallel.py  Gate F2: Online event ledger repair (parallel pool)
08_audit_e10r2f.py                  Mechanical fast audit check

                                    ↓ Produces Raw Artifacts ↓
              primary/e10r2_run_ledger.csv                  (28,440 rows, untouched)
              tests/trajectory_equivalence_report.csv       (diff <= 1e-12, PASS)
              tests/no_oracle_leakage_report.csv            (diff <= 1e-12, PASS)
              tests/resume_equivalence_report.csv           (diff <= 1e-12, PASS)
              events/e10r2_complete_event_ledger.csv        (834,240 rows, 44/run)
              forensic_rerun/e10r2f_online_event_rerun_ledger.csv (18,960 rows)
              forensic_rerun/rerun_primary_equivalence.csv  (0 failures)
              logs/full_run.log

========================================================================================
STAGE 2: Independent Forensic Audit & Packaging — Verification, Pytest, Provenance & Deliverable
========================================================================================
10_e10r2f_forensic_audit.py (CLI Script)
e10r2f_forensic_audit.ipynb      (Kaggle / Local Standalone Notebook)

                                    ↓ Generates & Verifies ↓
              audit/primary_integrity_summary.json          (Section 39 schema)
              audit/event_integrity_summary.json            (Section 38 schema)
              audit/E10R2F_MECHANICAL_AUDIT.json            (14 check items, PASS)
              audit/E10R2F_FORENSIC_AUDIT.md                (Section 40, Author / Investigator sign-offs)
              tests/pytest.log                              (Section 33, 0 failed)
              executed_code/SHA256SUMS.txt                  (Section 31 provenance)
              E10R2F_FORENSIC_CLOSURE.zip                   (Section 37, 19 required files)
```

---

## 2. Frozen Scientific Parameters

The following parameters are strictly frozen across all scripts:
- **Locked Cases:** 395 cases across 202 audio files from MUSAN Odd.
- **Paired Instances:** 4,740 ($395 \times 12$ inits).
- **Primary Rows:** 28,440 ($4,740 \times 6$ variants).
- **Dual Success Thresholds:**
  - $\text{Orbit Ratio} \le 0.10$ ($\|\hat{c}_T - c^*\| / \|\hat{c}_0 - c^*\| \le 0.10$).
  - $\text{Magnitude Residual} \le 10^{-5}$ ($\||\hat{c}_T| - s\|_\infty \le 10^{-5}$).
- **Seed Mode:** `historical_batch2` ($10000 \cdot (fi \pmod 2) + 100 \cdot pi + 10 \cdot seed + \lfloor 1000 \cdot level \rfloor$).
- **Equivalence Tolerance:** $\le 10^{-12}$.
- **Event Cardinality:** Exactly 44 block events per online run; $18,960 \times 44 = \mathbf{834,240}$ event rows.

---

## 3. Execution Instructions

### A. For Stage 1 (Equivalence & Event Reconstruction):
Run Gate F1 equivalence:
```bash
python experiments/08_e10_robustness_mechanism_ablation/06_e10r2f_equivalence.py \
    --audio-dir /path/to/MUSAN_ODD_202 \
    --locked-geometry experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv \
    --out results/08_e10r2f_forensic/tests
```

Run Gate F2 event repair (parallel):
```bash
python experiments/08_e10_robustness_mechanism_ablation/09_e10r2f_event_repair_parallel.py \
    --audio-dir /path/to/MUSAN_ODD_202 \
    --locked-geometry experiments/08_e10_robustness_mechanism_ablation/frozen/e10r_locked_geometry_395.csv \
    --primary-ledger results/08_e10r2f_forensic/primary/e10r2_run_ledger.csv \
    --out results/08_e10r2f_forensic \
    --workers 6
```

### B. For Stage 2 (Forensic Audit & Packaging):
Run the independent audit CLI:
```bash
python experiments/08_e10_robustness_mechanism_ablation/10_e10r2f_forensic_audit.py \
    --closure-dir results/08_e10r2f_forensic \
    --primary-ledger results/08_e10r2f_forensic/primary/e10r2_run_ledger.csv \
    --out-zip results/08_e10r2f_forensic/E10R2F_FORENSIC_CLOSURE.zip
```

---

## 4. Stage 3: Final Archive Packaging & Provenance Closure (E10R2F_FINAL_ARCHIVE)

According to `E10R2F_FINAL_ARCHIVE_Khoa_Instructions.md`:
Stage 3 represents the **final provenance and packaging closure** of E10-R2F. No scientific experiments are rerun, no hyperparameters are retuned, and the frozen primary ledger (`28,440` rows, SHA-256: `873cd31f7f9fbd5326454e284b97579683f0c2c5b94704b8f3a6e62bb4c442fd`) is strictly immutable.

### Execution Scripts:
- `experiments/08_e10_robustness_mechanism_ablation/11_e10r2f_final_archive.py`: Master packaging and cryptographic verification CLI script.
- `experiments/08_e10_robustness_mechanism_ablation/resume_equivalence_test.py`: Standalone Gate F1-C deterministic checkpoint & resume equivalence test suite (12/12 PASS).
- `reproduce/run_e10r2f_archive.py`: One-line reproduce launcher.
- `notebooks/kaggle_execution/e10r2f_final_archive_runner.ipynb`: Standalone Kaggle / Local Jupyter Notebook runner.

### How to Run:
```bash
# Direct execution via reproduce launcher
python reproduce/run_e10r2f_archive.py --search-dir . --output-dir E10R2F_FINAL_ARCHIVE --zip-path E10R2F_FINAL_ARCHIVE.zip

# Or directly via experiment script
python experiments/08_e10_robustness_mechanism_ablation/11_e10r2f_final_archive.py

# Run standalone resume equivalence test suite
python experiments/08_e10_robustness_mechanism_ablation/resume_equivalence_test.py --output-dir tests
```

### Deliverable:
- Output archive: `E10R2F_FINAL_ARCHIVE.zip`
- Includes:
  - `README_FINAL_ARCHIVE.md` (explicit provenance and non-rerun declaration)
  - `reference/primary_e10r2_ledger.csv` and `reference/PRIMARY_LEDGER_REFERENCE.txt`
  - `forensic_rerun/rerun_primary_equivalence.csv` (18,960 comparisons, 0 mismatches)
  - `events/e10r2_complete_event_ledger.csv` (834,240 rows, 44 events/run)
  - `tests/` (18/18 trajectory, 12/12 leakage, 12/12 resume, 37/37 pytest)
  - `audit/` (mechanical_audit.json PASS, SIGNOFF.md dual GREEN)
  - `executed_code/` (all 13 canonical forensic scripts)
  - `provenance/SHA256SUMS.txt` and `provenance/SHA256_VERIFY.txt` (0 failures).

