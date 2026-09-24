# E10-R2F: Forensic Closure Repair & Final Freeze Protocol
## Mandatory Execution & Verification Guide for Khoa & Bao

**Project:** GeoAGLA — ICLR 2027  
**Phase:** E10-R2F — Forensic Closure Repair  
**Objective:** Close the **two missing hard gates** of E10-R2 without reopening the scientific protocol and without retuning any hyperparameters.

> **Supreme Principle:** E10-R2F is a *forensic and reproducibility closure*, not a new exploratory experimental phase to optimize numerical performance.

---

# 1. Baseline State Locked Prior to E10-R2F

The primary E10-R2 run ledger has passed all structural cardinality and integrity checks:

```text
Locked geometry cases : 395
Paired instances      : 4,740
Variants / run_key    : 6
Primary ledger rows   : 28,440
Duplicate key pairs   : 0
Seed convention       : historical_batch2
Orbit ratio threshold : 0.10
Magnitude threshold   : 1e-5
```

Primary provisional success rates:

| Variant | Success Rate (%) |
| :--- | :---: |
| `fgla_oracle` | 30.17% |
| `fixed_1e_oracle` | 16.52% |
| `online_raw` | 55.61% |
| `online_env` | 50.46% |
| `online_fallback` | 55.65% |
| `online_full` | 56.29% |

Headline contrast:
$$\Delta_{\mathrm{Full - FGLA}} \approx +26.12 \text{ percentage points} \quad [95\% \text{ CI: } 24.33, 27.89]$$

**These numbers are NOT targets to artificially engineer.** They represent the locked primary evidence that must be preserved intact during forensic closure.

---

# 2. Two Missing Hard Gates to Close

E10-R2F exclusively resolves:

## Gate F1 — Six-Variant Canonical Trajectory Equivalence & No-Oracle Leakage
Mathematically prove that the execution wrapper paths of **all six variants** match canonical implementations within numerical tolerance $\le 10^{-12}$, and verify invariance against oracle parameter perturbations.

## Gate F2 — Complete Event-Ledger Integrity (834,240 Rows)
The previous resume execution omitted earlier event rows. E10-R2F reconstructs the complete 834,240-row event ledger (44 blocks per run across 18,960 online runs) with lossless checkpointing, and audits event semantics.

No other scientific questions or experimental branches may be opened.

---

# 3. Inviolable Protocols (Strictly Frozen)

Do not alter:
```text
locked population (395 cases)
precomputed lambda_plus values
STFT window and hop profiles
audio preprocessing and excerpts
initialization grid (3 modes, 6 levels, 2 seeds)
historical_batch2 seed convention
n_iter = 360, warmup = 12, block_size = 8
Ritz memory p = 4
margin and parameter bounds
success criteria:
  final_orbit_error <= 0.10 * initial_orbit_error
  final_magnitude_residual <= 1e-5
rate-fitting and checkpoint rules
fallback and envelope policies
```

Under no circumstances may `1e-3` be substituted for `1e-5`.

---

# 4. Read-Only Preservation of Primary Ledger

The primary E10-R2 run ledger (`e10r2_run_ledger.csv`, 28,440 rows) is **read-only historical evidence**.

Khoa and Bao must not:
- modify any row;
- recompute and overwrite the primary ledger;
- drop convergence failures;
- alter `success` flags;
- replace primary results with rerun data.

Outputs of the forensic online rerun must be saved under distinct filenames:
```text
forensic_rerun/e10r2f_online_event_rerun_ledger.csv
events/e10r2_complete_event_ledger.csv
```

---

# 5. Task F1: Six-Variant Canonical Trajectory Equivalence

Implemented in:
```text
experiments/08_e10_robustness_mechanism_ablation/06_e10r2f_equivalence.py
```
Output:
```text
tests/trajectory_equivalence_report.csv
```

## Deterministic Equivalence Fixtures
Evaluated across **at least 3 deterministic fixtures**:
- **Fixture A (Synthetic Case):** Small deterministic synthetic problem for fast bit-exact verification.
- **Fixture B (Real-Audio Gaussian):** Real audio excerpt under profile `agla_gaussian`.
- **Fixture C (Real-Audio Hann):** Real audio excerpt under profile `mezza_hann`.

Each fixture records:
```text
source_id, profile, init_kind, level, seed, init_seed, lambda_plus
```

## Evaluated Variants
All six variants must be tested against direct canonical calls:
1. `fgla_oracle`
2. `fixed_1e_oracle`
3. `online_raw`
4. `online_env`
5. `online_fallback`
6. `online_full`

Testing only `online_full` is strictly forbidden.

## Tolerance Specification
- Hard tolerance: $\text{max\_trajectory\_abs\_diff} \le 10^{-12}$.
- Scalar final errors: $\text{abs\_diff} \le 10^{-12}$.
- Event and boolean sequences: Exact bitwise equality.
- Success flag: `success_exact_match == True`.

---

# 6. No-Oracle Leakage Recheck

Online policies must not depend on $\lambda_+$:
1. Run online variants with original $\lambda_+$.
2. Perturb diagnostic $\lambda_+ \to 0.5 \cdot \lambda_+$.
3. Rerun online variants with perturbed parameter.
4. Trajectory difference must satisfy:
   $$\text{max\_trajectory\_abs\_diff} \le 10^{-12}$$

Output:
```text
tests/no_oracle_leakage_report.csv
```

---

# 7. Resume-Equivalence Unit Test

Verify that interrupted execution introduces zero numerical drift:
- **Continuous Run:** Execute fixture to completion.
- **Interrupted Run:** Execute partial trajectory $\to$ save checkpoint $\to$ terminate $\to$ resume $\to$ complete.
- Verify: $\text{continuous} \equiv \text{resumed}$ within $\le 10^{-12}$.

Output:
```text
tests/resume_equivalence_report.csv
```

---

# 8. Task F2: Complete Event-Ledger Reconstruction

## Mathematical Cardinality Derivation
- Paired instances: $4,740$
- Online variants evaluated: $4$ (`online_raw`, `online_env`, `online_fallback`, `online_full`)
- Total online runs: $4,740 \times 4 = \mathbf{18,960}$ runs
- Blocks per run ($N_{\text{iter}}=360, \text{warmup}=12, \text{block\_size}=8$):
  $$12 + 43 \times 8 = 356 \implies 43 \text{ full blocks} + 1 \text{ terminal block} = \mathbf{44\text{ blocks}}$$
- Expected total event rows:
  $$18,960 \times 44 = \mathbf{834,240\text{ event rows}}$$

## Lossless Checkpointing Architecture
Checkpointing must store both tables simultaneously after each audio file:
```text
checkpoint/
├── run_rows_checkpoint.csv
├── event_rows_checkpoint.csv
└── progress.json
```

---

# 9. Rerun-to-Primary Equivalence Gate

Every online instance rerun must match the primary ledger bit-for-bit:
```text
|rerun_final_orbit - primary_final_orbit| <= 1e-12
|rerun_final_mag   - primary_final_mag|   <= 1e-12
rerun_success == primary_success
```

Output:
```text
forensic_rerun/rerun_primary_equivalence.csv
```
Failures allowed: **0**. If any mismatch occurs, execution terminates immediately.

---

# 10. Independent Mechanical Audit

Implemented in:
```text
experiments/08_e10_robustness_mechanism_ablation/08_audit_e10r2f.py
```

Automated verification verifies all conditions:
1. `equivalence_rows_at_least_18 == True`
2. `all_equivalence_pass == True`
3. `no_oracle_leakage_pass == True`
4. `resume_equivalence_pass == True`
5. `online_rerun_rows_18960 == True`
6. `event_rows_834240 == True`
7. `event_duplicates_zero == True`
8. `events_per_run_exact_44 == True`
9. `rerun_primary_equivalence_pass == True`
10. `raw_no_fallback == True`
11. `env_no_fallback == True`

---

# 11. Final Submission Package Structure (Section 37)

The deliverable archive `E10R2F_FORENSIC_CLOSURE.zip` must match this exact tree:

```text
E10R2F_FORENSIC_CLOSURE/
│
├── primary/
│   └── e10r2_run_ledger.csv
│
├── tests/
│   ├── trajectory_equivalence_report.csv
│   ├── no_oracle_leakage_report.csv
│   ├── resume_equivalence_report.csv
│   └── pytest.log
│
├── events/
│   └── e10r2_complete_event_ledger.csv
│
├── forensic_rerun/
│   ├── e10r2f_online_event_rerun_ledger.csv
│   └── rerun_primary_equivalence.csv
│
├── audit/
│   ├── E10R2F_FORENSIC_AUDIT.md
│   ├── event_integrity_summary.json
│   └── primary_integrity_summary.json
│
├── logs/
│   ├── full_run.log
│   ├── python_version.txt
│   ├── machine_info.txt
│   └── pip_freeze.txt
│
└── executed_code/
    ├── e10r2f_six_variant_equivalence.py
    ├── event_repair_or_rerun.py
    ├── canonical_runner_used.py
    └── SHA256SUMS.txt
```

---

# 12. Final GREEN Verdict Criteria

The overall audit status is **GREEN** if and only if every single check passes:

- [ ] Primary ledger untouched (28,440 rows, 4,740 pairs, 395 cases, 0 duplicates).
- [ ] Convergence threshold strictly $10^{-5}$ magnitude residual, $0.10$ orbit ratio.
- [ ] Seed assignment matches `historical_batch2`.
- [ ] Six variants tested across at least 3 equivalence fixtures.
- [ ] Every trajectory-equivalence row passes with $\text{atol} \le 10^{-12}$.
- [ ] Direct `online_full` canonical equivalence passes with $\text{diff} = 0.0$.
- [ ] No-oracle leakage passes with $\text{diff} \le 10^{-12}$.
- [ ] Resume equivalence passes with $\text{diff} \le 10^{-12}$.
- [ ] Complete event ledger has exactly 834,240 rows.
- [ ] Exactly 44 events per online run with 0 duplicate event keys.
- [ ] Rerun-to-primary equivalence passes with 0 failures.
- [ ] Pytest suite completes with 0 failures.
- [ ] SHA-256 manifest records all executed scripts.
- [ ] Formal sign-offs from Khoa and Bao included.

If even a single check fails, the verdict is strictly **NO-GO**.
