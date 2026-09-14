# Student B — Final Correction & Audit Handoff

## ICLR 2027 — *Geometry Determines Acceleration in Phase Retrieval*

### Status Before This Audit

Your current experimental branch is assessed as:

\[
\boxed{\textbf{GREEN — PENDING MINOR FINAL CORRECTIONS}}
\]

The major scientific experiments are complete. **Do not rerun the large-scale MUSAN experiment and do not retune the Online algorithm.**

This final audit has four narrowly defined objectives:

1. audit \(R_{\rm capture}>1\);
2. clarify censoring in the signal-scale iterations-to-tolerance experiment;
3. reconcile the computational-cost numbers;
4. correct several manuscript-level claims that are stronger than the evidence supports.

After completing these four items, **STOP and hand the package back to the supervisor**.

---

# Task C1 — Audit \(R_{\rm capture}>1\)

The current multi-horizon experiment reports, at \(H=60\),

\[
\operatorname{median}R_{\rm capture}=1.976,
\]

where

\[
R_{\rm capture}
=
\frac{q_{\rm FGLA}-q_{\rm Online}}
{\max(10^{-6},q_{\rm FGLA}-q_{\rm Oracle})}.
\]

A value greater than one must **not** automatically be interpreted as Online recovering more than 100% of the theoretically available Oracle acceleration.

## C1.1 Required case-level audit

For every evaluated case and horizon, export:

```text
case_id
horizon
q_gla
q_fgla
q_online
q_oracle
delta_oracle
delta_online
R_capture
oracle_denominator_clipped
rate_fit_quality_fgla
rate_fit_quality_online
rate_fit_quality_oracle
```

with

\[
\Delta_{\rm oracle}
=
q_{\rm FGLA}-q_{\rm Oracle},
\]

and

\[
\Delta_{\rm online}
=
q_{\rm FGLA}-q_{\rm Online}.
\]

Add flags:

```text
R_CAPTURE_GT_1
R_CAPTURE_LT_0
NEGLIGIBLE_ORACLE_OPPORTUNITY
DENOMINATOR_CLIPPED
POOR_RATE_FIT
```

## C1.2 Questions to answer

Determine whether \(R_{\rm capture}>1\) is associated with:

- very small \(\Delta_{\rm oracle}\);
- denominator clipping at \(10^{-6}\);
- finite-horizon fitted-rate fluctuations;
- poor rate-fit quality;
- or genuine cases where the finite-horizon Online fitted rate is below the Oracle asymptotic prediction.

Do **not** force \(R_{\rm capture}\) into \([0,1]\).

Do **not** clip values for the primary audit.

Instead, report the raw values and explain why \(R_{\rm capture}>1\) can occur in finite-horizon empirical measurements.

## C1.3 Required summary

For every horizon \(H\), report:

```text
n_cases
median_R_capture
IQR_R_capture
fraction_R_capture_gt_1
fraction_R_capture_between_0_and_1
fraction_R_capture_lt_0
fraction_negligible_oracle_opportunity
fraction_denominator_clipped
```

### Safe interpretation

If supported by the audit, use wording such as:

> Values of \(R_{\rm capture}>1\) occur in finite-horizon fitted-rate comparisons and should not be interpreted as exceeding the theoretical Oracle optimum. They primarily indicate that empirical finite-horizon rates and very small Oracle-opportunity denominators can make the normalized gain ratio exceed one.

Do not use phrases such as:

> Online recovers 197.6% of the Oracle optimum.

### Deliverables

```text
final_audit/
├── C1_capture_ratio_audit.csv
├── C1_capture_ratio_summary.json
└── C1_capture_ratio_audit.md
```

---

# Task C2 — Clarify the Signal-Scale Iterations-to-Tolerance Experiment

The current report gives

\[
T_{\rm GLA}
=
T_{\rm FGLA}
=
T_{\rm Online}
=
100
\]

for all four synthetic signal types.

This is ambiguous.

We must determine whether `100` means:

### Case A — Threshold reached exactly at iteration 100

or

### Case B — Right-censored at `max_iter = 100`

meaning that the target tolerance was not reached before the experiment terminated.

These two interpretations are scientifically very different.

## C2.1 Inspect the raw traces

For each:

```text
harmonic
chirp
speech_like
transient
```

and each method, inspect the complete error trajectory.

Export:

```text
signal_type
method
max_iter
target_tolerance
first_iteration_below_tolerance
reached_tolerance
final_error
censored
```

Define:

```text
censored = true
```

if the target tolerance was not reached before `max_iter`.

## C2.2 Correct iterations-to-tolerance representation

If a method does not reach tolerance, do not write:

\[
T_m(\tau)=100.
\]

Instead represent it as:

\[
T_m(\tau)>100
\]

or use a machine-readable censoring flag.

For example:

```text
T_online = >100
censored = true
```

## C2.3 Decision rule

If most or all methods are censored at 100 iterations, then this experiment does **not** provide useful evidence for iteration savings.

In that case:

- retain it as a convergence/stability sanity check if appropriate;
- remove any claim about iteration savings;
- do not use it as a main paper figure.

**Do not rerun with a larger horizon during this correction round.**

A larger-horizon experiment would constitute new experimental work and requires supervisor approval.

### Deliverables

```text
final_audit/
├── C2_signal_scale_censoring.csv
└── C2_signal_scale_audit.md
```

---

# Task C3 — Reconcile Computational-Cost Measurements

The current report states approximately

\[
t_{\rm FGLA}=4.256\ {\rm ms/iteration},
\]

and

\[
t_{\rm Online}=3.866\ {\rm ms/iteration}.
\]

These point estimates imply

\[
\frac{t_{\rm Online}}{t_{\rm FGLA}}
\approx0.908,
\]

not \(1.12\times\).

The report currently contains both approximately \(0.91\times\) and \(1.12\times\), which must be reconciled.

## C3.1 Trace the origin of every runtime number

Create a table containing:

```text
environment
device
signal_length
STFT_configuration
method
number_of_repeats
number_of_iterations
warmup_excluded
mean_ms_per_iteration
median_ms_per_iteration
std_ms_per_iteration
relative_to_FGLA
source_file
```

Identify exactly where the reported \(1.12\times\) value came from.

Possible outcomes include:

- another machine;
- another STFT configuration;
- worst-case run;
- confidence-interval endpoint;
- earlier experiment;
- or a reporting mistake.

Do not combine measurements from different environments into one point estimate.

## C3.2 Separate algorithmic overhead from wall-clock timing

The scientifically important fact is that the Ritz estimator uses only a small

\[
p\times p=3\times3
\]

generalized eigenproblem every \(K=8\) iterations.

Report, if already measured:

```text
base_iteration_cost
ritz_update_cost
ritz_update_frequency
amortized_estimator_cost
total_online_iteration_cost
```

Do not claim that Online is intrinsically faster per iteration merely because one wall-clock benchmark happens to give \(3.866<4.256\) ms.

Timing noise, implementation details, caching, and system load can produce such differences.

### Preferred claim

If supported by the measurements:

> The computational overhead of the online Ritz estimator is small relative to the cost of the underlying Griffin–Lim iteration.

This is safer and more scientifically relevant than claiming that Online itself has lower per-iteration cost.

### Deliverables

```text
final_audit/
├── C3_runtime_provenance.csv
├── C3_runtime_summary.json
└── C3_runtime_audit.md
```

---

# Task C4 — Final Claim-Discipline Audit

Several phrases in the current report are stronger than the experiments establish.

This task requires **editing only**, not new computation.

## C4.1 Safeguard reliability

### Do not write

> absolute safety

or

> the safeguard completely eliminates divergence risk.

### Use

> No safeguard failure was observed among the 4680 basin runs in the full real-audio evaluation.

If earlier evaluations also showed zero failures, state this separately rather than summing overlapping experimental stages into an apparently independent denominator.

Do not use `0/7176` unless all 7176 runs are verified to be distinct, non-overlapping runs.

---

## C4.2 Near-degenerate real-audio geometry

The observed

\[
81.28\%
\]

near-phase-degenerate fraction is valuable, but it applies to the evaluated dataset and STFT configurations.

### Do not write

> Near-degeneracy is a natural geometric property of STFT on real audio.

### Use

> Near-phase-degenerate geometry was common in the evaluated MUSAN subset under the tested STFT configurations, with 81.28% of valid cases satisfying the pre-specified near-degeneracy criterion.

Do not generalize this result to all natural audio or all STFT configurations.

---

## C4.3 Six-file real-audio transfer experiment

### Do not write

> External generalization is proved.

or

> divergence risk is completely eliminated.

### Use

> No divergence was observed in the frozen 6-file × 2-STFT-regime transfer evaluation.

The six-file experiment is useful as a **frozen transfer sanity check**, not as universal evidence of external generalization.

---

## C4.4 Online versus FGLA

Preserve the actual multi-horizon result:

\[
86.7\%
\rightarrow
46.7\%
\rightarrow
40.0\%
\rightarrow
40.0\%
\]

for \(H=60,120,180,360\).

Do not summarize Student B's results as:

> Online is consistently faster than optimal FGLA.

The supported interpretation is:

> Online shows a strong early finite-horizon advantage in the controlled multi-horizon experiment, while optimal FGLA becomes highly competitive at longer horizons.

The large-scale real-audio result should remain conceptually separate:

> Online substantially improves empirical basin success relative to FGLA, but does not exhibit universal paired-rate superiority.

This distinction is scientifically important:

\[
\boxed{
\text{basin robustness}
\neq
\text{paired local-rate superiority}.
}
\]

---

# Final Required Package

Return one archive:

```text
StudentB_Final_Correction_Audit_v1.zip
│
├── README.md
├── corrected_final_report.md
├── integrity_report.json
│
├── final_audit/
│   ├── C1_capture_ratio_audit.csv
│   ├── C1_capture_ratio_summary.json
│   ├── C1_capture_ratio_audit.md
│   ├── C2_signal_scale_censoring.csv
│   ├── C2_signal_scale_audit.md
│   ├── C3_runtime_provenance.csv
│   ├── C3_runtime_summary.json
│   ├── C3_runtime_audit.md
│   └── C4_claim_corrections.md
│
├── figures/
│   └── [only corrected figures if labels/captions changed]
│
├── commands.txt
├── environment.txt
└── source_commit.txt
```

---

# Integrity Rules

For this final correction round:

- **No hyperparameter retuning.**
- **No new large-scale experiment.**
- **No removal of failure cases.**
- **No post-hoc seed selection.**
- **No modification of the frozen Online policy.**
- **No clipping of \(R_{\rm capture}\) to make plots look cleaner.**
- **No changing the success criterion.**
- **No rerunning until a preferred conclusion appears.**

If an existing raw output is insufficient to answer one of the four audit questions, explicitly mark:

```text
NOT RESOLVABLE FROM CURRENT OUTPUTS
```

and stop on that item.

Do not silently generate replacement evidence.

---

# Stop Rule

After completing C1–C4:

\[
\boxed{\textbf{STOP AND HAND OFF TO THE SUPERVISOR}}
\]

Do not start another experiment.

The supervisor will perform the final scientific audit and decide whether the Student B branch can be frozen.

---

# Expected Scientific Conclusion

If the four corrections are resolved cleanly, the intended final empirical conclusion is:

\[
\boxed{
\begin{aligned}
&\text{The passive Ritz estimator can accurately track local geometry;}\\
&\text{Online adaptation can provide strong early finite-horizon benefits;}\\
&\text{Online adaptation substantially enlarges the empirical convergence basin;}\\
&\text{the safeguard is empirically reliable in the evaluated experiments;}\\
&\text{but Online does not universally outperform optimal FGLA in paired local rate.}
\end{aligned}
}
\]

This is a scientifically meaningful result.

The objective of this final audit is **not to make every gate positive**. The objective is to ensure that every reported conclusion is exactly supported by the experimental evidence.