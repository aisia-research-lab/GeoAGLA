# E10-R2: Canonical-Equivalence Repair & Final Freeze Protocol
## Mandatory Execution & Verification Guide for Author / Investigator

**Project:** GeoAGLA — ICLR 2027  
**Objective:** Finalize Experiment E10 definitively, guaranteeing **canonical implementation fidelity + frozen scientific protocol compliance + exact numerical reproducibility**.  
**Baseline Status:** While earlier iterations verified mechanical reproducibility, **no numerical results may be incorporated into the manuscript until E10-R2 passes all canonical equivalence gates**.

---

# 0. The Paramount Rule

> **E10-R2 MUST NOT REIMPLEMENT ANY ALGORITHM LOCALLY.**

The E10-R2 execution engine must directly import and invoke the **canonical GeoAGLA / Phase-2B implementation** established in the foundational experiment repository.

Do not copy/paste or rewrite:
- STFT analysis/synthesis operators;
- Metric projections (Griffin-Lim map);
- Ritz spectrum estimation;
- `online_full` adaptive policy;
- Safeguard checkpoints;
- Rollback/fallback mechanisms;
- Minimax and FGLA parameter synthesis mappings;
- Quotient orbit distance metrics;
- Magnitude residual computations;
- Basin convergence success criteria.

Whenever a canonical function exists in the repository, it must be **directly imported and executed**.

The sole objective of E10-R2 is **rigorous scientific equivalence**, not constructing a secondary implementation that is merely "conceptually equivalent."

---

# 1. Motivation: Why E10-R2 is Mandatory

Prior validation established mechanical closure on:
- 395 locked geometry cases;
- 4,740 paired instances;
- 28,440 ledger rows;
- `historical_batch2` seed bookkeeping;
- Complete variant pairing;
- Artifact packaging and source/log provenance.

However, deep source audits revealed that the standalone runner exhibited implementation and parameter drift relative to the frozen Phase-2B protocol.

Crucial repairs enforced in E10-R2:
1. **Convergence Threshold:** The basin success threshold must strictly revert to canonical Phase-2B/E10 ($10^{-5}$ magnitude residual, not $10^{-3}$).
2. **Direct Canonical Imports:** The runner must invoke the canonical package directly rather than running local duplicates.
3. **Equivalence Preflight:** Bit-exact numerical equivalence must be mathematically proven before executing the full 28,440-row sweep.

---

# 2. Frozen Scientific Protocol

All scientific parameters are strictly locked and must not be altered:

## 2.1 Locked Population
- Population: **Exactly 395 cases** (`frozen/e10r_locked_geometry_395.csv`).
- Benchmark Audio: **Exactly 202 unique audio files** from the MUSAN benchmark.
- STFT Profiles:
  - `agla_gaussian`: Gaussian window ($\sigma = 96$), length 512, hop 128, FFT 1024.
  - `mezza_hann`: Hann window, length 1024, hop 256, FFT 2048.
- Exact precomputed $\lambda_+$ values mapped per `(file, profile)`.

## 2.2 Initialization Grid
- 3 initialization modes: `spectral`, `random_phase`, `transverse`.
- Perturbation levels: 2 levels per mode (total 6 levels).
- Random seeds: 2 seeds per level (seeds 0 and 1).
- Total paired instances per case: $3 \times 2 \times 2 = 12$ instances.
- Total paired instances in population: $395 \times 12 = \mathbf{4,740}$ instances.

## 2.3 Success Criterion — Mandatory Specification
The canonical convergence criterion is dual-gated:

$$e_{\mathrm{orbit}}^{\mathrm{final}} \le 0.10 \cdot e_{\mathrm{orbit}}^{\mathrm{initial}} \quad \text{AND} \quad r_{\mathrm{mag}}^{\mathrm{final}} \le 10^{-5}$$

Expressed programmatically:
```python
final_orbit_error <= 0.10 * initial_orbit_error and final_magnitude_residual <= 1e-5
```

> **STRICT BAN:** Any use of `final_magnitude_residual_max = 1e-3` or `1e-4` is strictly forbidden. The exact value of $1\times 10^{-5}$ must be enforced.

## 2.4 Seed Determination
Seed assignment must strictly preserve the `historical_batch2` convention:
```python
fi = global_fi % 2
init_seed = 10000 * fi + 100 * pi + 10 * seed + int(round(1000 * level))
```

---

# 3. Canonical Architecture & Import Hierarchy

The E10-R2 runner must import symbols directly from canonical paths:
```text
src/geometry_gla/algorithms/agla.py
src/geometry_gla/algorithms/minimax.py
src/geometry_gla/algorithms/online_safe.py
src/geometry_gla/algorithms/online_ablation.py
src/geometry_gla/estimators/ritz.py
src/geometry_gla/safeguards/checkpoint.py
src/geometry_gla/operators/stft_fft.py
src/geometry_gla/operators/projections.py
```

Helper routines for audio loading, metrics, and error calculation must be reused from:
```text
experiments/05_real_audio_basin_transfer/03_phase2b_real_audio_basin_sweep.py
```

Specifically:
- `load_audio`
- `_init_state`
- `_fixed`
- `_errors`
- `_rate`
- `_magnitude_residual`
- `_success`
- `orbit_distance`

---

# 4. Six-Variant Mechanistic Specification

The experiment evaluates exactly six variants under identical initialization $(c_0, c^*, s, \text{op}, \lambda_+)$:

### V1 — `fgla_oracle`
Classical Fast Griffin-Lim Algorithm parameterized with oracle upper edge:
$$\theta = \text{fgla\_opt}(\lambda_+)$$

### V2 — `fixed_1e_oracle`
Fixed single-edge minimax policy with zero lower edge:
$$\theta = \text{oracle\_minimax}(0.0, \lambda_+)$$

### V3 — `online_raw`
Trajectory-adaptive online control without safeguards:
- Ritz Estimator: **ON**
- Dynamic Envelope: **OFF**
- Rollback Fallback: **OFF**

### V4 — `online_env`
Trajectory-adaptive online control with stability envelope only:
- Ritz Estimator: **ON**
- Dynamic Envelope: **ON**
- Rollback Fallback: **OFF**

### V5 — `online_fallback`
Trajectory-adaptive online control with fallback safeguard only:
- Ritz Estimator: **ON**
- Dynamic Envelope: **OFF**
- Rollback Fallback: **ON**

### V6 — `online_full`
Full proposed adaptive policy combining spectral estimation, running envelope, and rollback safeguard:
```python
run_online_policy(c0, c0, s, op, policy="dynamic_envelope", **kw)
```

---

# 5. Preflight Equivalence Gates (Gates A to G)

Before full-scale execution, the environment must validate:

- **Gate A (Import Identity):** All operators, estimators, and policy functions resolve to canonical package files.
- **Gate B (Threshold Integrity):** Configuration assertions verify `final_magnitude_residual_max == 1e-5` and `final_orbit_ratio_max == 0.10`.
- **Gate C (Seed Invariance):** Deterministic initialization reproduces bit-exact seeds under `historical_batch2`.
- **Gate D (Full Policy Equivalence):** The wrapper call matches direct canonical `run_online_policy(..., policy="dynamic_envelope")` within $\text{atol} \le 10^{-12}$.
- **Gate E (Fixed Method Equivalence):** `fgla_oracle` and `fixed_1e_oracle` synthesize identical parameter maps.
- **Gate F (No-Oracle Leakage):** Online policies do not receive or alter behavior when $\lambda_+$ is perturbed.
- **Gate G (Pytest Clean Sheet):** The complete test suite runs with 0 failures.

---

# 6. Hard Cardinality & Structural Gates

Execution halts immediately if any condition fails:
- Total rows in run ledger: **Exactly 28,440**.
- Unique paired instances: **Exactly 4,740**.
- Locked cases evaluated: **Exactly 395**.
- Variants per instance: **Exactly 6 (min = 6, max = 6)**.
- Duplicate `(run_key, variant)` entries: **Exactly 0**.

---

# 7. Statistical Analysis & Clustered Bootstrap ($B=5,000$)

Analysis is performed by `05_analyze_e10r2.py`:
- **Clustered Bootstrap:** $B = 5,000$ resamples clustered by source WAV audio file (seed `20270920`).
- **Pre-Specified Contrasts:**
  1. $\Delta_1 = P(\text{Fixed1E}) - P(\text{FGLA})$ (Minimax single-edge gain)
  2. $\Delta_2 = P(\text{OnlineRaw}) - P(\text{Fixed1E})$ (Online adaptation gain)
  3. $\Delta_3 = P(\text{OnlineEnv}) - P(\text{OnlineRaw})$ (Stability envelope standalone effect)
  4. $\Delta_4 = P(\text{OnlineFallback}) - P(\text{OnlineRaw})$ (Fallback standalone effect)
  5. $\Delta_5 = P(\text{OnlineFull}) - P(\text{OnlineEnv})$ (Fallback effect on enveloped policy)
  6. $\Delta_6 = P(\text{OnlineFull}) - P(\text{FGLA})$ (Headline canonical gain)
  7. $\Delta_7 = P(\text{OnlineFull}) - P(\text{OnlineRaw})$ (Exploratory interaction contrast)
- **Paired Rescue & Loss:**
  - Rescue: A fails, B succeeds.
  - Loss: A succeeds, B fails.
  - Net Rescue: $\text{Rescue} - \text{Loss}$.

---

# 8. Final Submission Package Structure (Section 26)

The deliverable archive `E10R2_FINAL_CANONICAL_RETURN.zip` must match this exact tree:

```text
E10R2_FINAL_CANONICAL_RETURN/
├── results/
│   ├── e10r2_run_ledger.csv
│   ├── e10r2_run_ledger.json
│   ├── e10r2_event_ledger.csv
│   ├── e10r2_success_summary.csv
│   └── e10r2_contrasts.csv
├── frozen/
│   └── e10r_locked_geometry_395.csv
├── tests/
│   ├── pytest.log
│   ├── trajectory_equivalence_report.csv
│   └── no_oracle_leakage_report.txt
├── audit/
│   ├── E10R2_CANONICAL_IMPORT_AUDIT.md
│   ├── E10R2_INTEGRITY_AUDIT.md
│   └── integrity_summary.json
├── logs/
│   ├── full_run.log
│   ├── pip_freeze.txt
│   ├── python_version.txt
│   └── machine_info.txt
└── executed_code/
    ├── 04_run_e10r2_canonical.py
    ├── 05_analyze_e10r2.py
    └── SHA256SUMS.txt
```

---

# 9. Protocol Execution & Audit Stages

- **Stage 1 (Experimental Execution):**
  - Executes canonical runner without modifying scientific hyperparameters.
  - Captures full logs, environment states, and SHA-256 source manifests.
  - Ensures all 28,440 rows are completed losslessly.
- **Stage 2 (Independent Integrity & Statistical Audit):**
  - Independently audits data integrity, cardinality, and success metrics.
  - Verifies canonical imports and ensures zero implementation drift.
  - Validates clustered bootstrap statistics and contrast intervals.
  - Produces final audit sign-offs.

---

# 10. Academic Claims Firewall

Until final manuscript sign-off, all scientific reporting must adhere to these guardrails:

### Permissible Claims
- Finite-horizon empirical convergence success under the locked benchmark protocol.
- Paired instance rescue/loss trade-offs and net rescue counts.
- Cluster-bootstrap confidence intervals ($B=5,000$).
- Mechanistic ablation attributing relative gains between adaptive spectral control and safeguards.

### Prohibited Claims
- Claims of global convergence.
- Claims of mathematically expanding the theoretical basin of attraction.
- Claims that fallback or envelopes guarantee asymptotic convergence.
- Asserting that safeguards are universally necessary outside the finite-horizon setting.
