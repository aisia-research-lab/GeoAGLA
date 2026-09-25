# Lead Researcher — Final Reconciliation Assignment Before Scientific Freeze

## ICLR 2027 Project
### *Geometry Determines Acceleration in Phase Retrieval*

**Assignment Type:** Final scientific reconciliation and reporting correction  
**Current Status:** **Almost Frozen — One Final Patch Required**  
**Experiment Status:** **No additional experiments required**

---

# 1. Purpose of This Assignment

The Lead Researcher experimental branch has completed the planned Online-adaptation, estimator-maturation, multi-horizon, real-audio basin, safeguard, and computational-cost evaluations.

The latest canonical C1 ledger has resolved the previous multi-horizon data-version inconsistency. The branch is therefore close to scientific freeze.

However, the final supervisor audit identified a small number of **interpretation and reporting inconsistencies** between the new canonical C1 data and the current final report.

This assignment is intended to resolve those issues.

> **This is a reconciliation and editorial audit only.**
>
> Do **not** rerun the large experiments, retune the algorithm, change the frozen rate-fitting protocol, modify the Online policy, remove cases, or search for a more favorable result.

After completing the tasks below:

\[
\boxed{\textbf{STOP AND HAND OFF TO THE SUPERVISOR}}
\]

---

# 2. Summary of Results Already Achieved

## 2.1 Online Estimator and Frozen Adaptive Policy

The Online method uses the frozen configuration:

- dynamic-envelope policy;
- Ritz memory \(p=3\);
- block size \(K=8\);
- margin \(=0\);
- GLA safe fallback;
- no post-hoc hyperparameter tuning.

The passive Ritz estimator operates using trajectory secants without additional Griffin–Lim operator evaluations.

The estimator-maturation experiments provide useful evidence that the trajectory contains information about the active local spectral geometry.

\[
\boxed{\textbf{Estimator-maturation branch: GREEN}}
\]

---

## 2.2 Canonical Multi-Horizon C1 Result

The latest canonical C1 ledger contains:

\[
15\text{ cases}\times4\text{ horizons}=60\text{ evaluations}.
\]

The canonical Online-versus-FGLA results are:

| Horizon | Online Wins | Win Rate | Median \(R_{\rm capture}\) |
|---:|---:|---:|---:|
| \(H=60\) | \(13/15\) | **86.7%** | **1.9764** |
| \(H=120\) | \(7/15\) | **46.7%** | **-0.0827** |
| \(H=180\) | \(6/15\) | **40.0%** | **-0.8199** |
| \(H=360\) | \(6/15\) | **40.0%** | **-1.2610** |

These values have been independently recomputed from the canonical CSV and agree with the canonical summary JSON.

\[
\boxed{\textbf{Canonical C1 ledger consistency: GREEN}}
\]

The earlier ledger-version mismatch is considered resolved.

---

## 2.3 Interpretation of the Multi-Horizon Result

The experiment does **not** establish universal paired-rate superiority of Online over FGLA.

The strongest raw Online win fraction occurs at the shortest evaluated horizon:

\[
86.7\%\qquad(H=60).
\]

At longer horizons, the paired comparison becomes mixed:

\[
46.7\%,\quad40.0\%,\quad40.0\%.
\]

The intended high-level interpretation is:

> Online exhibits its strongest finite-horizon advantage at the short evaluated horizon, whereas optimal fixed FGLA remains highly competitive in longer-horizon paired-rate comparisons.

Finite-window rate-fit quality must be respected when interpreting these numbers.

Do not turn this result into a universal asymptotic acceleration claim.

---

## 2.4 Real-Audio Basin Result

Across the frozen real-audio basin experiment:

\[
P_{\rm success}^{\rm Online}=74.94\%,
\]

versus

\[
P_{\rm success}^{\rm FGLA}=54.87\%.
\]

Therefore the observed difference is:

\[
74.94-54.87
=
\boxed{20.07\text{ percentage points}}.
\]

This provides empirical evidence that Online adaptation improves **convergence robustness across the evaluated initialization conditions**.

The correct conceptual distinction remains:

\[
\boxed{
\textbf{Basin robustness}
\neq
\textbf{Paired local-rate superiority}.
}
\]

---

## 2.5 Safeguard Reliability

The frozen large-scale evaluation observed:

\[
\boxed{0\text{ safeguard failures among }4680\text{ basin runs}.}
\]

Approved wording:

> No safeguard failure was observed among the 4,680 basin runs in the full real-audio evaluation.

Do not use:

- “absolute safety”;
- “guaranteed safety”;
- “completely eliminates divergence”;
- the previous composite \(0/7176\) denominator.

\[
\boxed{\textbf{Safeguard empirical reliability: GREEN}}
\]

---

## 2.6 Near-Degenerate Geometry on Real Audio

Under the evaluated MUSAN subset and tested STFT configurations,

\[
81.28\%
\]

of valid cases satisfy the pre-specified near-phase-degeneracy criterion.

Approved interpretation:

> Near-phase-degenerate geometry was common in the evaluated MUSAN subset under the tested STFT configurations.

Do not generalize this result to all natural audio or all STFT systems.

---

## 2.7 Synthetic Signal Experiment

The censoring audit established that:

\[
11/12
\]

synthetic signal/method configurations did not reach

\[
\tau=10^{-2}
\]

within \(100\) iterations.

Only Online on the harmonic signal reached the target, at iteration \(99\).

Therefore the synthetic experiment:

- does **not** provide valid iterations-to-tolerance comparison evidence;
- must not be used to claim iteration savings;
- may remain only as a stability/sanity-check experiment;
- should not be a primary paper figure.

\[
\boxed{\textbf{Synthetic censoring audit: GREEN}}
\]

---

## 2.8 Computational Cost

The isolated \(3\times3\) Ritz computation costs approximately

\[
0.0381\text{ ms/update}.
\]

Because it is performed every

\[
K=8
\]

iterations, its amortized cost is approximately

\[
\frac{0.0381}{8}
\approx
0.0048\text{ ms/iteration}.
\]

Relative to the measured baseline Griffin–Lim step, this corresponds to approximately

\[
0.28\%
\]

amortized overhead.

Approved claim:

> The computational overhead of the online Ritz estimator is small relative to the cost of the underlying Griffin–Lim iteration.

Do not claim that Online is intrinsically faster per iteration based on noisy wall-clock measurements.

\[
\boxed{\textbf{Computational-overhead audit: GREEN}}
\]

---

# 3. Final Required Correction — C1 Interpretation

This is the most important remaining task.

## 3.1 Current Problem

The current report explains \(R_{\rm capture}>1\) primarily using:

1. negligible Oracle opportunity,
   \[
   \Delta_{\rm oracle}<10^{-4},
   \]
2. denominator clipping at
   \[
   10^{-6}.
   \]

This explanation is **not supported by the latest canonical C1 ledger**.

The latest canonical summary reports:

\[
\boxed{
\texttt{fraction\_negligible\_oracle\_opportunity}=0
}
\]

for every horizon, and

\[
\boxed{
\texttt{fraction\_denominator\_clipped}=0
}
\]

for every horizon.

Therefore these mechanisms must not be presented as explanations of \(R_{\rm capture}>1\) in the canonical 60-case C1 experiment.

---

# 4. Task F1 — Correct the Interpretation of \(R_{\rm capture}>1\)

Recall:

\[
R_{\rm capture}
=
\frac{q_{\rm FGLA}-q_{\rm Online}}
{q_{\rm FGLA}-q_{\rm Oracle}}
\]

when the denominator is valid and positive.

In the canonical C1 experiment, cases with

\[
R_{\rm capture}>1
\]

correspond empirically to:

\[
q_{\rm Online}<q_{\rm Oracle}
\]

over the fitted finite-horizon observation window.

This must **not** be interpreted as violating the Oracle optimality theorem.

The theoretical Oracle rate concerns the local asymptotic linearized model. The empirical \(q_{\rm Online}\) is a contraction factor estimated from a finite trajectory window and may contain transient nonlinear effects.

### Replace the current explanation with:

> **Values of \(R_{\rm capture}>1\) in the canonical multi-horizon experiment arise when the finite-horizon fitted Online contraction factor is temporarily smaller than the local asymptotic Oracle prediction. Such values should not be interpreted as violating Oracle optimality, because the theoretical Oracle result concerns the local asymptotic linearized regime, whereas the empirical contraction factors are estimated from finite nonlinear trajectory windows.**

Do not claim denominator clipping or negligible Oracle opportunity as the primary explanation unless referring to a different experiment where those mechanisms are actually present.

---

# 5. Task F2 — Explicitly Separate the Two Experimental Populations

The current report also discusses a **41-case failure taxonomy**.

This population must not be confused with the canonical C1 population.

The canonical C1 experiment contains:

\[
60=15\times4
\]

multi-horizon evaluations.

The 41-case taxonomy was generated from a **broader configuration sweep**.

Add an explicit statement before the taxonomy:

> **Population clarification.** The following 41-case diagnostic taxonomy is derived from the broader configuration sweep and is distinct from the canonical 60-evaluation C1 multi-horizon ledger. Consequently, frequencies reported in this taxonomy should not be interpreted as frequencies within the canonical C1 experiment.

This distinction must also appear in the figure caption for the failure-taxonomy figure.

---

# 6. Task F3 — Report Rate-Fit Quality Transparently

Finite-window contraction-factor estimation is itself imperfect.

The canonical C1 ledger contains a `POOR_RATE_FIT` diagnostic flag.

Report the number and fraction of poor-rate-fit cases by horizon.

Do not delete those cases from the primary results.

The primary table must continue to report all:

\[
15
\]

cases per horizon.

A secondary diagnostic table may report rate-fit quality.

### Required table

```text
horizon
n_total
n_poor_rate_fit
fraction_poor_rate_fit
n_good_rate_fit
```

If desired, good-fit-only statistics may be included as **diagnostic sensitivity analysis**, but they must be clearly labeled as secondary and must not replace the all-case primary result.

### Required interpretation

> Finite-window rate fitting introduces additional uncertainty into paired-rate comparisons. We therefore retain all cases in the primary analysis and report the pre-specified rate-fit quality flag separately rather than filtering cases post hoc.

Do not select only good-fit cases to improve the Online win rate.

---

# 7. Task F4 — Correct “Basin Diameter”

The report currently converts

\[
74.94\%-54.87\%=20.07\%
\]

into an “absolute gain in basin diameter.”

This terminology is incorrect because the experiment measures empirical convergence frequency under sampled initializations, not geometric basin diameter.

### Replace:

> a \(+20.07\%\) absolute gain in basin diameter

### With:

> a **20.07 percentage-point increase in empirical convergence success rate**

or:

> Online achieved a \(74.94\%\) empirical convergence success rate compared with \(54.87\%\) for FGLA, corresponding to a \(20.07\)-percentage-point difference under the evaluated initialization protocol.

Do not use “basin diameter” unless a geometric diameter is explicitly measured.

---

# 8. Task F5 — Change Causal Failure-Taxonomy Language

The current taxonomy uses terminology such as:

> Root Cause & Physical Mechanism

The current experiments primarily establish diagnostic associations, not formal causal identification for every failure category.

### Replace the column title with:

> **Diagnostic Category & Associated Mechanism**

Similarly, avoid statements such as:

> This geometry caused the failure.

Prefer:

> The failure was associated with near-degenerate geometry.

or:

> This case was classified under the near-degenerate-geometry diagnostic criterion.

In particular, terms such as:

- `NONCONVEX_PHASE_STALL`;
- off-target saddle;
- spectral misclassification;

must not be presented as mathematically certified causal mechanisms unless the corresponding evidence explicitly establishes them.

---

# 9. Task F6 — Moderate the Final Accuracy Declaration

Do not write:

> 100% ACCURATE, MATHEMATICALLY VERIFIED, AND FULLY AUDITED

before supervisor sign-off.

Replace it with:

> **All reported numerical summaries in the final Lead Researcher package have been reconciled against the designated canonical ledgers and are ready for final supervisor verification.**

The final decision to declare the Lead Researcher branch scientifically frozen belongs to the supervisor after this handoff.

---

# 10. Required Final Deliverables

Create:

```text
Lead Researcher_Final_Freeze_Candidate_v1/
│
├── README.md
├── corrected_final_report.md
├── final_freeze_reconciliation.md
│
├── canonical_c1/
│   ├── C1_capture_ratio_audit.csv
│   ├── C1_capture_ratio_summary.json
│   └── C1_capture_ratio_audit.md
│
├── diagnostics/
│   ├── C1_rate_fit_quality.csv
│   └── failure_taxonomy_population_note.md
│
├── figures/
│   ├── Figure_B1_estimator_maturation_traces.png
│   ├── Figure_B2_online_gain_vs_maturation_ratio.png
│   ├── Figure_B3_multi_horizon_performance.png
│   ├── Figure_B4_failure_taxonomy_distribution.png
│   └── Figure_B5_real_audio_iterations_to_tolerance.png
│
├── integrity_report.json
├── commands.txt
├── environment.txt
└── source_commit.txt
```

If Figure B3 or Figure B4 contains outdated wording or an incorrect caption, regenerate **only the figure labels/caption**, using the same frozen data.

Do not regenerate experimental observations.

---

# 11. Required `final_freeze_reconciliation.md`

This file should explicitly certify the following items:

```text
[ ] Canonical C1 ledger contains 60 evaluations.
[ ] C1 CSV and C1 JSON summaries agree.
[ ] Multi-horizon win rates are 86.7%, 46.7%, 40.0%, 40.0%.
[ ] Median R_capture values are 1.9764, -0.0827, -0.8199, -1.2610.
[ ] No canonical C1 case is attributed to denominator clipping unless supported by the ledger.
[ ] No canonical C1 case is attributed to negligible Oracle opportunity unless supported by the ledger.
[ ] R_capture > 1 is interpreted as a finite-horizon fitted-rate phenomenon.
[ ] Rate-fit quality is reported without post-hoc case removal.
[ ] The 41-case taxonomy is explicitly identified as a broader-sweep population.
[ ] “Basin diameter” has been removed.
[ ] Failure taxonomy uses diagnostic rather than unjustified causal language.
[ ] Synthetic iteration-savings claims remain removed.
[ ] Safeguard wording remains empirical rather than absolute.
[ ] Computational-overhead wording remains conservative.
[ ] No hyperparameter was retuned.
[ ] No large-scale experiment was rerun.
[ ] No case was removed.
```

---

# 12. Integrity Rules

During this assignment:

\[
\boxed{\textbf{NO NEW SCIENTIFIC EXPERIMENTS}}
\]

Specifically:

- no hyperparameter retuning;
- no changing \(p=3\);
- no changing \(K=8\);
- no changing the dynamic-envelope policy;
- no changing the safeguard;
- no new seeds;
- no larger-horizon experiment;
- no new audio dataset;
- no removal of difficult cases;
- no replacement of the canonical C1 ledger;
- no post-hoc rate-fit filtering;
- no redefinition of success;
- no clipping \(R_{\rm capture}\) into \([0,1]\).

If an inconsistency is discovered, document it rather than attempting to make the result look better.

---

# 13. Stop Rule

Once Tasks F1–F6 and the required package are complete:

\[
\boxed{\textbf{STOP}}
\]

Do not conduct another experiment.

Send the complete `Lead Researcher_Final_Freeze_Candidate_v1` package to the supervisor for final hostile audit.

---

# 14. Expected Final Scientific Story

The final Lead Researcher branch should support the following evidence-calibrated narrative:

\[
\boxed{
\begin{aligned}
&\text{The passive Ritz estimator provides useful online information}\\
&\text{about trajectory-active local geometry;}\\[2mm]
&\text{Online adaptation exhibits a strong finite-horizon advantage}\\
&\text{in part of the controlled regime;}\\[2mm]
&\text{paired-rate superiority over optimal FGLA is not universal;}\\[2mm]
&\text{Online adaptation substantially improves empirical convergence}\\
&\text{success across the evaluated real-audio initialization protocol;}\\[2mm]
&\text{the safeguard exhibited no failures in the 4,680-run evaluation;}\\[2mm]
&\text{and the additional Ritz computation has small amortized cost.}
\end{aligned}
}
\]

The most important empirical conclusion is:

\[
\boxed{
\textbf{Online geometry adaptation primarily provides robustness and adaptability,}
}
\]

while

\[
\boxed{
\textbf{optimal fixed acceleration remains highly competitive in paired local-rate comparisons.}
}
\]

This is compatible with the conditional scope of the G4–G5 theory.

---

# 15. Final Instruction to Lead Researcher

The goal of this assignment is **not to improve the experimental result**.

The goal is to ensure that:

\[
\boxed{
\textbf{data}
\Longrightarrow
\textbf{analysis}
\Longrightarrow
\textbf{claim}
}
\]

is exact at every step.

Complete the reconciliation, package the corrected files, and stop.

The supervisor will perform the final freeze decision.
