# Student B --- Scientific Conclusion and Next-Task Handoff v1

## ICLR 2027 --- *Geometry Determines Acceleration in Phase Retrieval*

**Purpose of this document:**\
This document records the scientific conclusion from Student B's
completed full real-audio Phase 2B evaluation and defines the next tasks
to be executed. The next stage is **not** intended to tune the current
experiment until the paired-rate gate passes. Its purpose is to (i)
close the current result cleanly, (ii) understand the basin-versus-rate
separation, and (iii) determine what part of the geometry-informed
Oracle opportunity can actually be recovered by an online estimator.

------------------------------------------------------------------------

# 1. Current Scientific Verdict

\[ `\boxed{\textbf{Student B experimental execution: GREEN}}`{=tex} \]

\[ `\boxed{\textbf{Phase 2B overall scientific result: YELLOW}}`{=tex}
\]

\[ `\boxed{\textbf{G2B\_E paired-rate gate: genuine FAIL}}`{=tex} \]

The failure of the paired-rate gate must be **preserved as a scientific
result**. Student B should not retune the algorithm, thresholds, memory
length, initialization, or STFT configurations merely to convert this
failure into a pass.

The current experiment supports a more nuanced and scientifically useful
conclusion:

\[ `\boxed{
\text{Online adaptation improves empirical basin robustness substantially,}
}`{=tex} \]

but

\[ `\boxed{
\text{it does not automatically recover Oracle-like paired local acceleration on real audio.}
}`{=tex} \]

This distinction should become a central part of the empirical story.

------------------------------------------------------------------------

# 2. Accepted Results from the Full Real-Audio Evaluation

The submitted full evaluation reports:

\[ n\_{`\rm manifest`{=tex}}=201, `\qquad`{=tex}
n\_{`\rm geometry`{=tex}}=390, `\qquad`{=tex}
n\_{`\rm basin`{=tex}}=4680. \]

The main aggregate results are:

\[ `\text{Online success fraction}`{=tex}=0.7494, \]

\[ `\text{FGLA success fraction}`{=tex}=0.5487, \]

\[ `\text{small-basin Online success}`{=tex}=0.8224, \]

\[ `\text{median final-edge relative error}`{=tex} =
6.27`\times10`{=tex}\^{-5}, \]

and

\[ `\text{mean late-reject fraction}`{=tex}=0.01447. \]

No safeguard fallback failure was observed in the full 4680-run
evaluation.

These results support the conclusion that the online method tracks the
spectral edge accurately and provides a substantially larger empirical
convergence basin than FGLA under the evaluated configurations.

------------------------------------------------------------------------

# 3. The Paired-Rate Result Must Remain a Failure

Among runs in which both Online and FGLA succeed,

\[ n\_{`\rm paired`{=tex}}=2541. \]

The observed fraction satisfying

\[ q\_{`\rm Online`{=tex}}\<q\_{`\rm FGLA`{=tex}} \]

is only

\[ `\boxed{0.3447}`{=tex}, \]

well below the pre-specified 0.60 gate.

Moreover,

\[ `\operatorname{median}`{=tex} `\left`{=tex}(
`\frac{q_{\rm Online}}{q_{\rm FGLA}}`{=tex} `\right`{=tex}) =
1.00093\>1. \]

A file-clustered bootstrap audit gives an approximate 95% interval

\[ \[0.313,;0.377\] \]

for the paired beat fraction, which remains far below 0.60.

Therefore:

\[ `\boxed{\textbf{G2B\_E FAIL is statistically robust.}}`{=tex} \]

Increasing the sample size slightly is not expected to change this
conclusion materially.

Student B must **not** optimize the experiment against this gate after
observing the result.

------------------------------------------------------------------------

# 4. Basin Robustness Is a Genuine Positive Result

The difference between overall convergence-success fractions is
approximately

\[ 0.7494-0.5487 = 0.2007. \]

A file-clustered bootstrap audit indicates that this advantage is also
stable.

Thus the principal positive result of Phase 2B is:

> **Online geometry adaptation substantially enlarges the empirical
> basin of successful convergence relative to FGLA under the evaluated
> real-audio configurations.**

This result is distinct from paired local-rate acceleration.

The paper should therefore separate:

\[ `\boxed{\text{Basin robustness}}`{=tex} \]

from

\[ `\boxed{\text{Local rate acceleration}}`{=tex}. \]

They are not empirically interchangeable.

------------------------------------------------------------------------

# 5. Correction to the Current Causal Interpretation

The current report attributes the paired-rate weakness primarily to

``` text
mezza_hann × transverse amplitude = 0.05
```

but the raw stratified results do not support such a narrow causal
conclusion.

The weakness is visible across **transverse initialization more
broadly**, including Gaussian-profile cases.

For example, the paired Online-beat fractions under transverse
initialization are approximately:

  STFT profile     Transverse level   Paired Online-beat fraction
  -------------- ------------------ -----------------------------
  Gaussian                    0.001                         0.299
  Gaussian                     0.01                         0.319
  Gaussian                     0.05                         0.302
  Mezza-Hann                  0.001                         0.253
  Mezza-Hann                   0.01                         0.320
  Mezza-Hann                   0.05                         0.289

Therefore the safe interpretation is:

> **The paired-rate weakness is associated with transverse
> initialization across multiple tested STFT profiles, rather than being
> isolated to the Mezza-Hann / amplitude-0.05 configuration.**

This statement is descriptive. It should not yet be presented as a
proved causal mechanism.

------------------------------------------------------------------------

# 6. Phase-Jitter Results Must Be Interpreted Separately

For some Gaussian phase-jitter settings, the Online method shows
stronger paired-rate behavior, particularly at larger perturbation
levels.

However, difficult Mezza-Hann phase-jitter settings contain very
few---or no---paired-success runs because FGLA often fails to enter the
convergent regime.

Therefore those cases primarily support a **basin-robustness** claim
rather than a paired-rate claim.

Do not report Online as faster than FGLA in strata where the
paired-success population is absent or too small to support that
comparison.

------------------------------------------------------------------------

# 7. Mandatory Archival Corrections Before Phase 2B Freeze

These tasks require **analysis and documentation only**. Do not rerun
the full experiment.

## Task B0.1 --- Resolve the 202 → 201 Manifest Discrepancy

The intended evaluation contained 202 files, while the submitted
manifest contains 201.

Student B must identify:

``` text
missing_file
reason_missing
source_manifest
final_manifest
```

Do not write that the missing file was "probably removed by regularity
preprocessing" unless the logs or source manifest establish that fact.

Deliver:

``` text
manifest_audit.md
manifest_diff.csv
```

------------------------------------------------------------------------

## Task B0.2 --- Document Geometry-Case Exclusions

The raw results contain 402 possible profile/file geometry combinations
but only 390 valid geometry cases.

Document all 12 invalid cases explicitly.

The current audit indicates two distinct mechanisms:

``` text
GEOMETRY_FAIL
SKIP_IRREGULAR
```

and the fully irregular files include:

``` text
noise-free-sound-0564.wav
noise-free-sound-0624.wav
```

Student B should provide a machine-readable table containing:

``` text
file
profile
status
reason
solver_message
included_in_basin_analysis
```

Deliver:

``` text
geometry_exclusion_audit.csv
geometry_exclusion_audit.md
```

No invalid case may be silently deleted.

------------------------------------------------------------------------

## Task B0.3 --- Correct the Final Phase 2B Report

Revise the report so that it does **not** claim:

``` text
paired-rate failure is specifically caused by mezza_hann × transverse 0.05
```

or:

``` text
the observed sample-size sequence proves convergence to the true population value
```

or:

``` text
0 safeguard failures in 7176 independent runs
```

if the earlier experiments overlap with the final dataset.

Use instead:

> The paired-rate weakness is broadly associated with transverse
> initialization across the tested profiles.

> The near-phase-degenerate fraction stabilizes around 0.8 as the
> evaluated sample is enlarged, suggesting that near-degeneracy is
> common under the tested configurations.

> No safeguard failure was observed in the full 4680-run evaluation;
> none was observed in the earlier smaller-scale evaluations either.

------------------------------------------------------------------------

## Task B0.4 --- Add the Full Stratification Table

Create a canonical table stratified by:

``` text
STFT profile
initialization family
initialization level
```

For each stratum report at least:

``` text
n_runs
online_success_fraction
fgla_success_fraction
n_paired_success
online_beat_fraction
median_q_online
median_q_fgla
median_q_ratio
late_reject_fraction
```

Deliver:

``` text
phase2b_stratified_results.csv
phase2b_stratified_results.md
```

After Tasks B0.1--B0.4 are complete:

\[ `\boxed{\textbf{Phase 2B may be frozen.}}`{=tex} \]

------------------------------------------------------------------------

# 8. Next Scientific Question

The next stage should **not** ask:

> "How can we tune Online until it beats FGLA in more than 60% of runs?"

Instead, the scientifically relevant question is:

\[ `\boxed{
\textbf{Why does online geometry adaptation enlarge the basin without consistently recovering the local Oracle rate?}
}`{=tex} \]

This question directly connects the empirical findings to the
theoretical scope of the paper.

------------------------------------------------------------------------

# 9. Next Task B1 --- Geometry-Opportunity / Gain-Capture Analysis

## Objective

Measure how much acceleration is theoretically available in each case
and how much of that opportunity the Online method actually captures.

For each valid paired case define

\[ `\Delta`{=tex}*{`\rm oracle`{=tex}} = q*{`\rm FGLA`{=tex}} -
q\_{`\rm Oracle`{=tex}}, \]

and

\[ `\Delta`{=tex}*{`\rm online`{=tex}} = q*{`\rm FGLA`{=tex}} -
q\_{`\rm Online`{=tex}}. \]

When

\[ `\Delta`{=tex}\_{`\rm oracle`{=tex}}\>0 \]

is meaningfully separated from numerical noise, define

\[ R\_{`\rm capture`{=tex}} = `\frac{\Delta_{\rm online}}`{=tex}
{`\Delta`{=tex}\_{`\rm oracle`{=tex}}}. \]

Interpretation:

-   (R\_{`\rm capture`{=tex}}`\approx1`{=tex}): Online captures most
    Oracle opportunity;
-   (0\<R\_{`\rm capture`{=tex}}\<1): partial recovery;
-   (R\_{`\rm capture`{=tex}}`\le0`{=tex}): no observed rate gain over
    FGLA;
-   (R\_{`\rm capture`{=tex}}\>1): investigate finite-horizon/fitting
    effects before interpretation.

## Critical rule

All three rates used in a gain-capture comparison must be measured at
the **same observation horizon** and with the same frozen fitting
protocol.

Never combine an Online rate fitted at one horizon with FGLA/Oracle
rates fitted at another.

## Required analysis

Report:

1.  distribution of (`\Delta`{=tex}\_{`\rm oracle`{=tex}});
2.  distribution of (`\Delta`{=tex}\_{`\rm online`{=tex}});
3.  distribution of (R\_{`\rm capture`{=tex}});
4.  correlation between available Oracle opportunity and observed Online
    gain;
5.  results stratified by profile and initialization family;
6.  results stratified by geometry regime, especially
    (`\lambda`{=tex}\_+);
7.  confidence intervals using file-clustered bootstrap.

Deliver:

``` text
B1_geometry_opportunity_ledger.csv
B1_geometry_opportunity_summary.json
B1_geometry_opportunity_report.md
```

------------------------------------------------------------------------

# 10. Next Task B2 --- Estimator Maturation Audit

## Objective

Determine whether the Online method's local-rate weakness is associated
with the time required for the edge estimator to become accurate.

For each Online trajectory record:

\[ `\widehat{\lambda}`{=tex}\_{+,n} \]

through time and compare it with the final/reference edge.

Define a fixed estimator-error measure:

\[ e\_{`\lambda`{=tex}}(n) = `\frac{
|\widehat{\lambda}_{+,n}-\lambda_+|
}{
\max(\lambda_+,\epsilon)
}`{=tex}. \]

Predefine thresholds such as

\[ 10^{-2},`\quad10`{=tex}^{-3},`\quad10`{=tex}\^{-4} \]

and record the first iteration at which each threshold is reached and
remains stable according to a frozen rule.

Required outputs include:

``` text
edge_error_at_iteration
first_stable_1e-2
first_stable_1e-3
first_stable_1e-4
fraction_of_horizon_before_maturation
q_online
q_fgla
q_oracle
```

The central question is:

\[ `\boxed{
\text{Does Online spend too much of the finite horizon learning geometry before it can exploit it?}
}`{=tex} \]

This is a hypothesis to test, not a conclusion to assume.

Deliver:

``` text
B2_estimator_maturation.csv
B2_estimator_maturation_summary.json
B2_estimator_maturation_report.md
```

------------------------------------------------------------------------

# 11. Next Task B3 --- Basin-vs-Rate Mechanism Audit

## Objective

Separate two empirical effects:

1.  **entering/staying in the local convergent basin**, and
2.  **achieving the predicted accelerated rate once inside that basin**.

For every run, classify:

``` text
ONLINE_ONLY_SUCCESS
FGLA_ONLY_SUCCESS
BOTH_SUCCESS
BOTH_FAIL
```

For `BOTH_SUCCESS`, analyze paired rates.

For `ONLINE_ONLY_SUCCESS`, analyze whether the Online safeguard or
adaptive parameters prevent escape from the basin.

For `BOTH_FAIL`, characterize geometry and initialization severity
without deleting the cases.

Required stratification:

``` text
profile
initialization family
initialization level
lambda_plus bin
spectral-gap bin
```

The purpose is to determine whether the Online method's main empirical
benefit is:

\[ `\boxed{
\text{stabilization / basin enlargement}
}`{=tex} \]

rather than

\[ `\boxed{
\text{uniform finite-horizon rate acceleration}.
}`{=tex} \]

Deliver:

``` text
B3_basin_rate_state_table.csv
B3_basin_rate_summary.json
B3_basin_rate_report.md
```

------------------------------------------------------------------------

# 12. Next Task B4 --- Failure-Decomposition Audit

For every paired-success case where

\[ q\_{`\rm Online`{=tex}}`\ge `{=tex}q\_{`\rm FGLA`{=tex}}, \]

assign a **diagnostic**, not speculative, category.

Candidate categories:

``` text
SMALL_ORACLE_OPPORTUNITY
ESTIMATOR_NOT_MATURE
LATE_PARAMETER_REJECTION
POOR_RATE_FIT
NEAR_NUMERICAL_FLOOR
TRANSVERSE_INITIALIZATION_ASSOCIATED
OTHER_UNRESOLVED
```

A case may have multiple diagnostic flags.

Do not invent a causal explanation when the data only show an
association.

The final report should answer:

-   Is Online slow because there is little Oracle opportunity to
    capture?
-   Is the estimator accurate only late in the trajectory?
-   Are adaptive parameters frequently rejected?
-   Is the rate-fit itself unreliable?
-   Is transverse initialization associated with the failure after
    controlling descriptively for profile and geometry?
-   Which cases remain unresolved?

Deliver:

``` text
B4_failure_decomposition.csv
B4_failure_decomposition_summary.json
B4_failure_decomposition_report.md
```

------------------------------------------------------------------------

# 13. Next Task B5 --- Iterations-to-Tolerance Analysis

Local fitted rate is not the only practically meaningful metric.

For each successful trajectory compute iterations required to reach
fixed normalized error thresholds, for example:

\[ 10^{-2},`\quad10`{=tex}^{-3},`\quad10`{=tex}\^{-4}, \]

subject to the existing error definition.

For each threshold compare:

``` text
GLA
FGLA
Online
Oracle
```

Use paired comparisons whenever both methods reach the threshold.

Report:

-   fraction reaching each threshold;
-   median iterations-to-tolerance;
-   paired iteration difference;
-   paired iteration ratio;
-   file-clustered bootstrap confidence intervals.

This analysis is especially important because the current Phase 2B
result suggests that Online may provide practical robustness even when
its fitted asymptotic rate does not beat FGLA.

Deliver:

``` text
B5_iterations_to_tolerance.csv
B5_iterations_to_tolerance_summary.json
B5_iterations_to_tolerance_report.md
```

------------------------------------------------------------------------

# 14. Experimental Integrity Rules for B1--B5

The following rules are mandatory.

## Do not retune Phase 2B

Do not change:

``` text
Ritz memory
block length
margin
safeguard policy
initialization levels
STFT profiles
rate-fit rule
success criterion
```

unless the supervisor explicitly opens a new ablation study.

## No post-hoc case selection

Do not remove:

-   hard cases;
-   near-degenerate cases;
-   eigensolver failures;
-   Online losses;
-   FGLA wins;
-   unresolved cases.

## Freeze analysis definitions first

Before calculating B1--B5, write:

``` text
StudentB_B1_B5_Analysis_Protocol.md
```

containing:

-   exact formulas;
-   inclusion/exclusion rules;
-   horizon used;
-   fitting protocol;
-   thresholds;
-   bootstrap unit;
-   missing-value handling;
-   numerical-floor rule;
-   all stratification bins.

The protocol must be frozen before inspecting headline B1--B5 outcomes.

------------------------------------------------------------------------

# 15. Required Final Handoff Package

After B0--B5, return:

``` text
StudentB_Final_Scientific_Handoff_v1.zip
├── README.md
├── StudentB_B1_B5_Analysis_Protocol.md
├── integrity_report.json
│
├── phase2b_freeze/
│   ├── final_corrected_report.md
│   ├── manifest_audit.md
│   ├── manifest_diff.csv
│   ├── geometry_exclusion_audit.csv
│   ├── geometry_exclusion_audit.md
│   ├── phase2b_stratified_results.csv
│   └── phase2b_stratified_results.md
│
├── B1_geometry_opportunity/
│   ├── ledger.csv
│   ├── summary.json
│   └── report.md
│
├── B2_estimator_maturation/
│   ├── results.csv
│   ├── summary.json
│   └── report.md
│
├── B3_basin_vs_rate/
│   ├── state_table.csv
│   ├── summary.json
│   └── report.md
│
├── B4_failure_decomposition/
│   ├── results.csv
│   ├── summary.json
│   └── report.md
│
├── B5_iterations_to_tolerance/
│   ├── results.csv
│   ├── summary.json
│   └── report.md
│
├── figures/
├── tables/
├── environment.txt
├── commands.txt
└── source_commit.txt
```

------------------------------------------------------------------------

# 16. Stop Rule

After B0--B5:

\[ `\boxed{\textbf{STOP AND HAND OFF TO THE SUPERVISOR}}`{=tex} \]

Do not automatically:

-   tune Online to improve the paired-rate gate;
-   add a new estimator;
-   increase Ritz memory;
-   change safeguard thresholds;
-   add new STFT profiles;
-   rerun the entire audio benchmark;
-   expand to another audio dataset;
-   redesign the algorithm.

Any such work would constitute a **new scientific phase** and requires
an explicit decision after the B1--B5 audit.

------------------------------------------------------------------------

# 17. What Would Constitute a Strong Final Student B Result?

Student B does **not** need to make Online beat FGLA in a majority of
paired-success cases.

A strong and publishable outcome would be a rigorous empirical
characterization such as:

\[ `\boxed{
\begin{aligned}
&\text{Online geometry estimation is accurate;}\\
&\text{adaptive geometry substantially enlarges the convergence basin;}\\
&\text{the safeguard is empirically reliable;}\\
&\text{paired finite-horizon rate recovery is incomplete;}\\
&\text{and the missing rate gain can be quantitatively decomposed}\\
&\text{into geometry opportunity, estimator maturation, and}\\
&\text{finite-horizon / fitting effects where supported by evidence.}
\end{aligned}
}`{=tex} \]

This would be scientifically stronger than tuning the experiment until a
pre-selected success threshold is crossed.

------------------------------------------------------------------------

# 18. Final Message to Student B

The current Phase 2B result is **not a failed experiment**.

It identifies an important boundary between two different benefits of
online geometry adaptation:

\[ `\boxed{
\textbf{robustness of convergence}
\neq
\textbf{local rate acceleration}.
}`{=tex} \]

The next stage should explain this separation carefully and
quantitatively.

Preserve the negative paired-rate result. Do not hide it, remove
difficult cases, or tune against it.

The goal of B1--B5 is to determine **what Online actually gains, when it
gains it, and why the remaining Oracle acceleration is not always
recovered within the observed finite horizon**.

That is the scientific question to close before the Student B branch is
finally frozen.
