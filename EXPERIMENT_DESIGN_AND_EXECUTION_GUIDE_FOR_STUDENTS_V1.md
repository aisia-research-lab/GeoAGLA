# ICLR 2027 Experiment Design & Execution Guide v1

## Project
**Geometry Determines Acceleration in Phase Retrieval**  
Target: **ICLR 2027**  
Experimental role: validate the theory and online mechanism; do **not** tune toward favorable outcomes.

This document is the frozen handoff for the two student experimenters. The manuscript theory is already developed around five results: geometry–spectrum correspondence, exact local modal dynamics, exact minimax acceleration, trajectory-active spectral estimation, and online local rate recovery. The experiments must test those statements at the level they are actually claimed. They are **not** intended to prove global recovery, uniform finite-budget superiority, or complete recovery of the local spectrum.

---

## 1. Non-negotiable scientific rules

1. **Do not change frozen hyperparameters before audit.** In particular, the online configuration remains `p=3`, block length `K=8`, margin `0`, and the dynamic running-envelope edge policy unless the supervisor explicitly opens an ablation.
2. **Do not delete hard cases.** Cases with \(\lambda_+\approx 1\), small transverse gap, estimator delay, or Online-\(\lambda_+\) losing to FGLA at a finite horizon must remain in the result ledger.
3. **Do not select seeds after seeing performance.** Use the seeds in the frozen config files.
4. **Do not replace a failed gate by a new threshold.** A failed gate is a scientific result and must be handed back for audit.
5. **Do not manually edit JSON/CSV result files or publication figures.** Re-run the generating command if something is wrong.
6. **Keep raw logs.** Every run should have command, machine information, Git/package version, timestamp, config, and output directory recorded.
7. **Separate asymptotic claims from finite-horizon observations.** The theory predicts local root rates. The experiments may show delayed rate realization, especially near \(\lambda_+=1\).
8. **The Ritz estimator estimates trajectory-active geometry.** Do not describe it as a certified upper bound or full-spectrum estimator.
9. **Real-audio experiments use no retuning.** The real-audio stage tests transfer of the frozen mechanism.
10. **Stop at each assigned handoff gate.** Send the requested files to the supervisor before changing code, thresholds, or protocol.

---

## 2. Student responsibilities

### Student A — Geometry and Oracle-Rate Validation
Primary responsibility: **E1–E2**, plus reproduction checks supporting the theory core.

Student A owns:
- S0 linear/modal smoke test;
- geometry–spectrum identity across controlled STFT settings;
- local rate prediction for GLA, optimally tuned FGLA, and oracle geometry-optimal acceleration;
- finite-window rate audit;
- preparation of the controlled-theory figures and result tables.

Student A must not modify the online estimator or safeguard implementation.

### Student B — Online Geometry and Real-Audio Transfer
Primary responsibility: **E3–E5**, using the frozen online design.

Student B owns:
- low-memory Ritz estimator reproduction and memory comparison;
- passive non-identifiability diagnostic;
- Online-\(\lambda_+\) rate realization and horizon audit;
- real-audio basin/geometry validation;
- online/real-audio figures and result tables.

Student B must not retune `p`, `K`, margin, or the dynamic-envelope rule based on observed performance.

### Cross-check rule
Each student should independently rerun **one small experiment owned by the other student** after the main runs are complete. This is a reproducibility cross-check, not a second tuning pass.

---

## 3. Software package and environment

Use the frozen repository archive supplied by the supervisor:

```text
geometry-certified-gla-phase2b-v1.zip
```

Unpack it once and work from a clean copy. Do not work inside the ZIP file.

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pytest -q
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pytest -q
```

For the Phase-2B package, the expected reference test status is:

```text
17 passed
```

If tests fail, **stop** and send the full terminal output. Do not patch library versions or source code without approval.

### Environment record
Before the first scientific run, save:

```bash
python --version > environment.txt
python -m pip freeze >> environment.txt
```

Also append OS, CPU, RAM, and GPU information manually if available. The core experiments are CPU-compatible; GPU acceleration is not required.

---

## 4. Experimental map

| Experiment | Scientific question | Owner | Primary output |
|---|---|---|---|
| S0 | Does the scalar/modal implementation match the derived recurrence? | A | smoke-test report |
| E1 | Does \(DG(c^\star)\) match principal-angle geometry? | A | geometry spectral error |
| E2 | Do observed local rates match GLA/FGLA/oracle predictions? | A | predicted vs observed rate |
| E3 | Can passive low-memory Ritz recover the trajectory-active dominant edge? | B | \(\widehat\lambda_+\) error |
| E4 | Does Online-\(\lambda_+\) increasingly realize the geometry-designed rate? | B | horizon rate ratios |
| E5 | Do geometry, edge tracking, basin behavior, and safeguard transfer to real recordings without retuning? | B | real-audio transfer/basin results |

The experimental section of the paper will be filled only after the outputs below are audited.

---

# Part A — Student A Protocol

## A0. S0 smoke test

Run:

```bash
python reproduce/run_phase1b.py
```

The purpose is purely mechanical/theoretical consistency. Confirm that the modal recurrence and predicted spectral radii agree with direct eigenvalue calculations.

### Handoff A0
Send the generated smoke-test summary/report and the terminal log. If any modal case disagrees beyond numerical precision, stop.

---

## A1. E1 — Geometry–Spectrum Correspondence

### Scientific hypothesis
At a regular feasible solution,

\[
J_\star=P_U P_V|_U,
\qquad
\lambda_j(J_\star)=\cos^2\theta_j
\]

on the nontrivial modes, with one neutral phase mode under the frozen regularity assumptions.

### Run the multi-configuration controlled experiment

```bash
python reproduce/run_phase1c.py
```

This is the main controlled geometry/rate grid already encoded in the repository config.

### Required outputs
At minimum preserve:

```text
results/phase1c/summary.json
results/phase1c/h1_multi.json
results/phase1c/h1_multi.csv
results/phase1c/figures/D1_geometry_identity.png
```

### Metrics to report
- maximum relative spectral error;
- median relative spectral error;
- number/fraction of cases with exactly one neutral phase mode;
- any irregular/skipped cases, with reason;
- dimension/configuration metadata.

### Paper figure candidate
A parity-style plot of direct Jacobian eigenvalues versus \(\cos^2\theta_j\), including the identity line.

### Interpretation
A small numerical error supports the **geometry identity implementation and transfer across controlled STFT configurations**. It does not establish global convergence.

---

## A2. E2 — Exact Local Rate Prediction

### Scientific hypotheses
For the local transverse interval \([\lambda_-,\lambda_+]\):

\[
q_{\mathrm{GLA}}=\lambda_+,
\qquad
q_{\mathrm{FGLA}}^\star=1-\sqrt{1-\lambda_+},
\]

and the oracle design has predicted factor

\[
q^\star(\lambda_-,\lambda_+)
<q_{\mathrm{FGLA}}^\star
<q_{\mathrm{GLA}}.
\]

### Main run
The Phase-1C command above already produces the multi-configuration rate experiment. Preserve:

```text
results/phase1c/h2_multi.json
results/phase1c/h2_multi.csv
results/phase1c/finite_window_audit.json
results/phase1c/figures/D2_rate_prediction.png
results/phase1c/figures/D2b_finite_window_audit.png
```

### Metrics to report by method
For GLA, optimal FGLA, and Oracle:
- theoretical \(q_{\rm pred}\);
- fitted \(q_{\rm obs}\);
- absolute and relative error;
- fit window;
- final orbit-aligned error;
- ordering correctness: `oracle < fgla < gla`.

### Important rate-fitting rule
Do not choose the fitting window separately for each method after looking at the curves. Use the frozen analysis windows generated by the code. Keep early/middle/late-window diagnostics to expose finite-window effects.

### Handoff A1–A2
After E1–E2 finish, send the complete `results/phase1c/` directory or at least the files listed above. **Do not start new hyperparameter sweeps.**

---

# Part B — Student B Protocol

## B0. E3 — Passive Ritz Estimation

### Scientific question
Can the trajectory-active dominant edge be recovered from passive secant pairs without an extra phase-retrieval map evaluation?

### Main run

```bash
python reproduce/run_phase1d.py
```

### Frozen estimator
Primary memory:

```text
p = 3
```

The `p=1` and `p=5` cases are diagnostic comparisons only. Do not choose the best memory independently on each signal.

### Required outputs

```text
results/phase1d/summary.json
results/phase1d/estimator_selection.json
results/phase1d/d0_synthetic.json
results/phase1d/d1_local_stft.json
results/phase1d/d1_local_stft.csv
results/phase1d/d2_identifiability.json
results/phase1d/tracking_traces.json
```

and figures under:

```text
results/phase1d/figures/
```

### Metrics to report
- median and 90th-percentile relative edge error;
- final relative edge error;
- under-/over-estimation fraction;
- conditioning of the small Gram/Ritz problem;
- behavior across `p=1,3,5`;
- active-spectrum non-identifiability example.

### Required wording
The raw Ritz estimate is **not a certified upper bound**. Report it as a trajectory-active estimate.

---

## B1. E4 — Online-\(\lambda_+\) Rate Realization

### Frozen design

```text
Ritz memory p = 3
block length K = 8
margin = 0
dynamic running-envelope edge synthesis
safe fallback = GLA
```

Do not retune these values.

### Main repaired online experiment

```bash
python reproduce/run_phase1er.py
```

### Required outputs

```text
results/phase1er/summary.json
results/phase1er/policy_summary.json
results/phase1er/failure_decomposition.json
results/phase1er/failure_decomposition.csv
results/phase1er/horizon_audit.json
```

and figures under:

```text
results/phase1er/figures/
```

### Metrics
- beat fraction against optimal FGLA;
- median \(q_{\rm Online}/q_{\rm FGLA}\);
- 90th percentile of the same ratio;
- median \(q_{\rm Online}/q_{\rm Oracle[0,\lambda_+]}\);
- final edge relative error;
- number of edge updates;
- overall and late rejection fractions;
- fallback E1 failures;
- performance as a function of horizon.

### Mandatory finite-horizon audit
Report all frozen horizons, not just the best one. The paper must be able to show estimator-maturation delay and near-degenerate failures instead of hiding them.

### Handoff B0–B1
Send the complete `results/phase1d/` and `results/phase1er/` directories. Stop before changing estimator policies or thresholds.

---

## B2. E5 — Signal-Scale Transfer Check

Before real audio, reproduce the controlled signal-scale gate:

```bash
python reproduce/run_phase2a.py
```

Required outputs:

```text
results/phase2a/summary.json
results/phase2a/case_results.json
results/phase2a/case_results.csv
results/phase2a/horizon_audit.json
results/phase2a/horizon_summary.json
```

and the figures under `results/phase2a/figures/`.

Keep the hard near-degenerate transient case even if it loses to FGLA at all finite horizons.

---

## B3. E5 — Real-Audio Basin & Geometry Validation

### Audio data requirements
Prepare **4–6 genuine WAV recordings** spanning at least two content types, preferably:
- speech;
- music/harmonic content;
- transient/percussive content.

Recordings must be ordinary audio and must not be synthetic files generated by the smoke-test script. No class labels are required.

Do not manually crop, normalize, or cherry-pick a segment because it performs well. The engine performs deterministic preprocessing/excerpt selection.

### Preflight

```bash
python reproduce/run_phase2b.py \
  --audio-dir "/absolute/path/to/wavs" \
  --max-files 2 \
  --out results/phase2b_preflight
```

If all geometry cases are skipped as irregular, use different non-silent recordings. Do **not** relax the regularity tolerance.

### Frozen real-audio run

```bash
python reproduce/run_phase2b.py \
  --audio-dir "/absolute/path/to/wavs" \
  --max-files 6 \
  --out results/phase2b
```

Do not edit `configs/phase2b_grid.json` before audit.

### Required outputs

```text
results/phase2b/summary.json
results/phase2b/audio_manifest.json
results/phase2b/geometry_results.json
results/phase2b/basin_results.json
results/phase2b/initialization_summary.json
```

Also preserve all generated CSV files, logs, and figures.

### Real-audio quantities to summarize
For each audio/STFT/initialization combination:
- oracle \(\lambda_+\) and transverse gap \(1-\lambda_+\);
- geometry error;
- final trajectory-active edge error;
- GLA / optimal-FGLA / Online-\(\lambda_+\) rate estimates where valid;
- convergence/success indicator;
- basin profile by perturbation family and magnitude;
- rejection fraction and fallback E1 failures;
- whether Online-\(\lambda_+\) beats optimal FGLA at the frozen horizon.

### Mandatory failure analysis
Flag cases with:

```text
lambda_plus >= 0.999
```

as near-degenerate diagnostics. This threshold is for reporting/stratification only; it must not be used to exclude cases from aggregate results.

### Handoff B2–B3
Send all five required Phase-2B JSON files plus the audio manifest and exact terminal command used. Do not replace an unfavorable audio file after seeing the results unless there is a documented decoding/data-integrity failure.

---

## 5. Cross-student reproducibility check

After the primary handoffs are audited:

- Student A independently runs `python reproduce/run_phase1d.py` and sends only the new `summary.json` plus terminal log.
- Student B independently runs `python reproduce/run_phase1c.py` and sends only the new `summary.json` plus terminal log.

The purpose is to verify that two independent machines produce scientifically equivalent summaries. Exact floating-point equality is not required, but qualitative gates and numerical magnitudes should agree.

---

## 6. Result naming and archival structure

Do not overwrite the canonical run. Recommended structure:

```text
student_runs/
  student_A/
    environment.txt
    terminal_logs/
    phase1b/
    phase1c/
  student_B/
    environment.txt
    terminal_logs/
    phase1d/
    phase1er/
    phase2a/
    phase2b_preflight/
    phase2b/
```

For every scientific run, save the command in a text file, for example:

```text
student_runs/student_B/terminal_logs/phase2b_command.txt
```

If code must be changed because of a real bug, create a new versioned branch/package. Never silently modify the frozen package and keep the same result label.

---

## 7. What will enter the ICLR paper

The current manuscript intentionally contains placeholders rather than fabricated numbers. After audit, the following evidence will be inserted:

### Main paper
- **Figure 1 / E1:** principal-angle prediction versus direct Jacobian spectrum;
- **Figure 2 / E2:** predicted versus observed contraction factors for GLA, optimal FGLA, and oracle geometry-optimal acceleration;
- **Figure 3 / E3–E4:** trajectory-active edge estimation and online rate realization over horizon;
- **Table 1:** compact quantitative summary across controlled and signal-scale cases;
- **Real-audio panel/table:** compact Phase-2B transfer summary if the real-audio gate is scientifically usable.

### Appendix
- full STFT configurations and seeds;
- all rate-fitting windows;
- memory ablations `p=1,3,5`;
- policy/failure decomposition;
- hard/near-degenerate cases;
- audio manifest and preprocessing;
- basin initialization details;
- complete per-case tables.

The main-text empirical message must remain:

> The geometry predicts the local dynamics accurately; the oracle minimax design realizes the predicted hierarchy; passive low-memory Ritz estimation tracks the trajectory-active dominant edge under excitation; and the online method increasingly realizes the geometry-designed advantage, while finite-horizon hard cases remain near phase degeneracy.

---

## 8. Claims the experiments must **not** make

Do not write or report any of the following as conclusions:

- “Online-\(\lambda_+\) is always faster than FGLA.”
- “The estimator recovers the complete phase-retrieval spectrum.”
- “The Ritz estimate is a certified upper bound.”
- “The algorithm converges globally from arbitrary initialization.”
- “The theory guarantees finite-horizon superiority.”
- “The safeguard theorem proves global convergence of the switched online method.”
- “Cases with \(\lambda_+\approx1\) are outliers and can be removed.”

Instead, preserve the conditional/local nature of the theorems and report hard cases explicitly.

---

## 9. Minimum handoff checklist

Before sending results, each student must verify:

- [ ] `pytest -q` passed before scientific runs.
- [ ] `environment.txt` saved.
- [ ] frozen configs unchanged.
- [ ] terminal command/log saved.
- [ ] all requested JSON/CSV files present.
- [ ] no rows/cases manually deleted.
- [ ] no figures manually edited.
- [ ] failed/irregular cases documented.
- [ ] no new hyperparameter search performed.
- [ ] result directory zipped before handoff.

---

## 10. Stop rule

If a result conflicts with theory, differs materially from the reference behavior, or a gate becomes RED/YELLOW, **stop and hand off the raw result package**. Do not repair the scientific result by tuning parameters. The supervisor and research team will first determine whether the cause is implementation, numerical conditioning, finite-horizon behavior, regularity failure, or a genuine theoretical limitation.

