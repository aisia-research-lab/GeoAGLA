# Student A --- Final Real-Audio Patch & Horizon Audit Handoff v1

## ICLR 2027 --- *Geometry Determines Acceleration in Phase Retrieval*

### Status before this handoff

The **Neutral-Mode Exactness Gate is GREEN**.

The targeted high-precision audit established that the two MUSAN cases
previously reported with

``` text
neutral_count_topk = 2
```

at `phase_tol = 1e-7` do **not** provide evidence for a second exact
neutral symmetry. Instead, each contains one global-phase neutral mode
and one extremely near-neutral transverse mode.

High-precision transverse edges:

``` text
noise-free-sound-0043.wav:
lambda_plus = 0.999999949551514

noise-free-sound-0389.wav:
lambda_plus = 0.999999902833544
```

Therefore the original 202-file real-audio tables must be patched for
these two cases before the real-audio branch is frozen.

This handoff has exactly **two tasks**:

1.  **Patch the two affected real-audio rows and regenerate the
    canonical 202-file aggregate.**
2.  **Audit the 29 observed rate-ordering failures at longer horizons.**

Do not redesign the algorithm, retune parameters, or rerun unrelated
experiments.

------------------------------------------------------------------------

# Task A --- Patch the Two Near-Neutral Cases

## A1. Scientific reason

In the original experiment, `phase_tol = 1e-7` classified the second
eigenvalue as neutral in these two files. Consequently, the reported
transverse edge corresponded to the next eigenvalue.

The high-precision audit now shows that the second mode is transverse:

\[ `\lambda`{=tex}\_2\<1, \]

with

\[ 1-`\lambda`{=tex}\_2 = 5.0448`\times10`{=tex}\^{-8} \]

for `noise-free-sound-0043.wav`, and

\[ 1-`\lambda`{=tex}\_2 = 9.7166`\times10`{=tex}\^{-8} \]

for `noise-free-sound-0389.wav`.

Hence the correct numerical transverse edges are

\[ `\boxed{\lambda_+=0.999999949551514}`{=tex} \]

and

\[ `\boxed{\lambda_+=0.999999902833544}`{=tex}. \]

------------------------------------------------------------------------

## A2. Required action

Rerun/recompute **only these two cases** using the refined neutral-mode
classification justified by the exactness audit.

Do not rerun the other 200 MUSAN files unless a reproducibility failure
makes this unavoidable.

The two cases are:

``` text
noise-free-sound-0043.wav
noise-free-sound-0389.wav
```

For these cases regenerate every downstream quantity that depends on
(`\lambda`{=tex}\_+), including where applicable:

``` text
lambda_plus
cos2_theta
geometry_rel_error
q_gla_pred
q_fgla_pred
q_oracle_pred
oracle parameters
observed rate quantities
final errors
ordering flags
```

Do not manually overwrite derived columns. Recompute them through the
experiment code.

------------------------------------------------------------------------

## A3. Canonical merge

Create a new canonical 202-file result set by:

1.  taking the original 200 unaffected rows unchanged;
2.  replacing the two affected rows with the newly recomputed rows;
3.  regenerating all aggregate statistics from the merged canonical
    ledger.

Suggested filenames:

``` text
geometry_results_final.csv
geometry_results_final.json
rate_results_final.csv
rate_results_final.json
summary_final.json
```

Keep the original files unchanged for provenance.

------------------------------------------------------------------------

## A4. Recompute all aggregate statistics

At minimum regenerate:

-   total valid cases;
-   category counts;
-   median/max geometry discrepancy;
-   (`\lambda`{=tex}\_+) distribution;
-   fraction with (`\lambda`{=tex}\_+`\ge0.999`{=tex});
-   predicted-rate errors;
-   observed-rate errors;
-   observed ordering fraction;
-   category-specific ordering fractions;
-   paired finite-horizon error-reduction ratios;
-   all reported percentiles;
-   all tables and figures derived from these quantities.

For finite-horizon gain, use paired per-file ratios:

\[ R\_{{`\rm FGLA`{=tex}},i} = `\frac{e_{{\rm GLA},i}}`{=tex}
{e\_{{`\rm FGLA`{=tex}},i}}, \]

\[ R\_{{`\rm Oracle`{=tex}},i} = `\frac{e_{{\rm GLA},i}}`{=tex}
{e\_{{`\rm Oracle`{=tex}},i}}. \]

Report the median across files, not the ratio of two separately computed
medians.

Where feasible, provide bootstrap 95% confidence intervals for the
median paired ratios.

------------------------------------------------------------------------

## A5. Regenerate figures

Regenerate all real-audio figures affected by the patch, including the
equivalents of:

``` text
D1_real_audio_geometry_parity.png
D2_real_audio_convergence_curves.png
D3_real_audio_rate_comparison.png
```

Figures must be generated from the final canonical files, not from
manually copied statistics.

------------------------------------------------------------------------

# Task B --- 29-Case Multi-Horizon Ordering Audit

## B1. Objective

The original (H=360) real-audio experiment yielded

\[ 173/202 \]

cases satisfying the observed hierarchy

\[ q\_{`\rm Oracle`{=tex}}\^{obs} \< q\_{`\rm FGLA`{=tex}}\^{obs} \<
q\_{`\rm GLA`{=tex}}\^{obs}, \]

leaving 29 cases with `Ordered = False`.

The purpose of this audit is to test the hypothesis that a substantial
portion of these failures arise from **finite-horizon/transient rate
fitting** in strongly near-degenerate cases.

This is a diagnostic experiment. Do not assume in advance that the
hypothesis is correct.

------------------------------------------------------------------------

## B2. Freeze the failure set

Freeze the exact list of 29 cases that failed the original (H=360)
ordering test.

Save:

``` text
ordering_failure_manifest.json
ordering_failure_manifest.csv
```

Each entry should include at least:

``` text
file_id
category
original_lambda_plus
original_q_gla_obs
original_q_fgla_obs
original_q_oracle_obs
original_ordered
```

If either of the two patched near-neutral cases belongs to this set, use
its **final corrected geometry configuration**.

Do not add or remove cases after inspecting the new results.

------------------------------------------------------------------------

## B3. Horizons

Evaluate the same frozen 29 cases at:

\[ `\boxed{H=360,\;720,\;1440}`{=tex}. \]

The (H=360) result should be reproduced as a control wherever possible.

Do not change algorithm parameters between horizons.

------------------------------------------------------------------------

## B4. Freeze all algorithm parameters

Use exactly the same:

-   signal preprocessing;
-   STFT parameters;
-   initialization;
-   random seed;
-   GLA configuration;
-   FGLA configuration;
-   Oracle synthesis rule;
-   objective/error definition;
-   convergence metric,

as in the original real-audio experiment.

The **only intended experimental variable is horizon**.

No per-case tuning is allowed.

------------------------------------------------------------------------

# Task C --- Rate-Fitting Integrity

## C1. Avoid post-hoc fit-window selection

Do not inspect a trajectory and then manually choose a fit interval that
produces the expected ordering.

The rate-fitting rule must be fixed before examining the (H=720) and
(H=1440) outcomes.

Document the exact rule in:

``` text
rate_fit_protocol.md
```

------------------------------------------------------------------------

## C2. Preferred reporting

For each algorithm and horizon report:

\[ q\_{`\rm obs`{=tex}}, \]

fit interval,

\[ R\^2 \]

or another fit-quality statistic already supported by the
implementation, and number of fitted points.

Suggested fields:

``` text
file_id
category
horizon
algorithm
lambda_plus
q_pred
q_obs
fit_start
fit_end
fit_n
fit_quality
final_error
```

------------------------------------------------------------------------

## C3. Numerical floor

Longer horizons may push trajectories toward floating-point or objective
floors.

Therefore flag cases in which the fitted region is contaminated by a
numerical plateau.

Do not interpret plateau-dominated slopes as asymptotic convergence
rates.

Suggested flag:

``` text
numerical_floor_flag
```

If a predefined numerical-floor rule already exists, use it unchanged.
Otherwise document any newly introduced rule explicitly and apply it
uniformly.

------------------------------------------------------------------------

# Task D --- Required Horizon Analysis

For each horizon compute:

\[ F_H = `\frac{
\#\{i:q_{{\rm Oracle},i}^{obs}
<
q_{{\rm FGLA},i}^{obs}
<
q_{{\rm GLA},i}^{obs}\}
}{29}`{=tex}. \]

Report:

``` text
ordering_fraction_H360
ordering_fraction_H720
ordering_fraction_H1440
```

Also report the full ordering fraction after combining the audited
failures with the 173 originally passing cases, but clearly distinguish
this from (F_H).

------------------------------------------------------------------------

## D1. Pairwise inequalities

Do not report only the three-way hierarchy.

For every horizon calculate separately:

\[ P(q\_{`\rm FGLA`{=tex}}^{obs}\<q\_{`\rm GLA`{=tex}}^{obs}), \]

\[ P(q\_{`\rm Oracle`{=tex}}^{obs}\<q\_{`\rm GLA`{=tex}}^{obs}), \]

\[ P(q\_{`\rm Oracle`{=tex}}^{obs}\<q\_{`\rm FGLA`{=tex}}^{obs}). \]

This tells us which inequality causes the remaining failures.

------------------------------------------------------------------------

## D2. Transition matrix

For each of the 29 cases classify:

``` text
FAIL -> PASS
FAIL -> FAIL
```

between (H=360) and (H=720), and again between (H=720) and (H=1440).

Also report the first horizon at which the full hierarchy is observed:

``` text
first_pass_horizon
```

with values:

``` text
360
720
1440
never
```

------------------------------------------------------------------------

## D3. Gap-aware analysis

For each case compute the predicted separations

\[ `\Delta`{=tex}*{OF} = q*{`\rm FGLA`{=tex}}\^{pred} -
q\_{`\rm Oracle`{=tex}}\^{pred}, \]

\[ `\Delta`{=tex}*{FG} = q*{`\rm GLA`{=tex}}\^{pred} -
q\_{`\rm FGLA`{=tex}}\^{pred}. \]

Investigate whether failures are concentrated where these theoretical
gaps are small.

This is an analysis, not permission to remove small-gap cases.

Report correlations or stratified summaries if informative.

------------------------------------------------------------------------

# Task E --- Failure Taxonomy

For every case that still fails at (H=1440), assign a descriptive
diagnostic category supported by the data.

Possible categories include:

``` text
ORACLE_FGLA_SWAP
FGLA_GLA_SWAP
ORACLE_GLA_SWAP
MULTIPLE_ORDERING_FAILURE
POOR_RATE_FIT
NUMERICAL_FLOOR
OTHER_UNRESOLVED
```

Do not force every failure into a theoretical explanation.

If evidence is insufficient, use:

``` text
OTHER_UNRESOLVED
```

and state what is unknown.

------------------------------------------------------------------------

# Task F --- Integrity Requirements

The following are mandatory:

-   no seed selection;
-   no deletion of difficult files;
-   no post-hoc parameter tuning;
-   no manual alteration of rate values;
-   no post-hoc fit-window optimization;
-   no change to the 29-case manifest after results are viewed;
-   retain all failures;
-   preserve original outputs;
-   save commands and environment;
-   generate final tables from canonical machine-readable results.

Create:

``` text
integrity_report.json
```

containing at least:

``` text
manifest_frozen
parameters_frozen
seeds_frozen
fit_rule_frozen
all_cases_retained
manual_edits
unexpected_failures
notes
```

------------------------------------------------------------------------

# Task G --- Required Deliverables

Return one ZIP:

``` text
studentA_final_real_audio_patch_horizon_audit.zip
├── README.md
├── summary_final.json
├── integrity_report.json
│
├── patch/
│   ├── patched_two_cases.csv
│   ├── geometry_results_final.csv
│   ├── geometry_results_final.json
│   ├── rate_results_final.csv
│   └── rate_results_final.json
│
├── horizon_audit/
│   ├── ordering_failure_manifest.csv
│   ├── ordering_failure_manifest.json
│   ├── horizon_results.csv
│   ├── horizon_results.json
│   ├── horizon_summary.json
│   ├── transition_table.csv
│   └── failure_taxonomy.csv
│
├── figures/
│   ├── real_audio_geometry_parity_final.png
│   ├── real_audio_rate_comparison_final.png
│   ├── ordering_vs_horizon.png
│   └── predicted_gap_vs_ordering.png
│
├── tables/
│   ├── real_audio_summary_final.csv
│   ├── category_summary_final.csv
│   └── horizon_summary_table.csv
│
├── rate_fit_protocol.md
├── environment.txt
└── commands.txt
```

------------------------------------------------------------------------

# Task H --- Final Student Report

Write:

``` text
StudentA_Final_RealAudio_Audit_Report.md
```

The report should answer only evidence-supported questions:

1.  What changed after correcting the two near-neutral cases?
2.  Did any headline 202-file statistic materially change?
3.  How does observed hierarchy evolve from (H=360) to (720) to (1440)?
4.  Which pairwise inequality causes the remaining failures?
5.  Are failures associated with small predicted spectral/rate
    separation?
6.  Are any long-horizon fits affected by numerical floors?
7.  Which cases, if any, remain scientifically unresolved?
8.  What claims are safe for the ICLR manuscript?

Avoid language such as:

``` text
proved on real audio
universally valid
perfectly confirmed
natural audio always ...
```

Experiments provide numerical evidence consistent with the theory; they
do not prove the theorem.

------------------------------------------------------------------------

# Stop Rule

After completing the two tasks:

\[ `\boxed{
\text{2-case canonical patch}
+
\text{29-case multi-horizon audit}
}`{=tex} \]

**STOP and hand off all raw outputs to the supervisor.**

Do not:

-   start a new ablation;
-   modify the acceleration algorithm;
-   change the estimator;
-   tune parameters based on the horizon results;
-   expand the audio dataset;
-   rerun the full 202-file suite without explicit supervisor approval.

------------------------------------------------------------------------

# Scientific Success Criteria

This experiment does **not** require all 29 cases to become ordered at
(H=1440).

A scientifically successful audit means:

1.  the two near-neutral rows are corrected reproducibly;
2.  the final 202-file ledger is internally consistent;
3.  the behavior of the 29 failures across horizon is measured without
    tuning;
4.  remaining failures are reported rather than hidden;
5.  numerical-floor and fit-quality effects are separated from genuine
    unresolved behavior;
6.  the final manuscript claims follow the evidence.

The desired scientific conclusion, **only if supported by the data**,
is:

\[ `\boxed{
\text{The theoretical rate hierarchy becomes increasingly visible as the finite observation horizon grows.}
}`{=tex} \]

If the data do not support this statement, report the observed behavior
exactly and stop.
