# ICLR 2027 --- Next Experimental Handoff for Students A & B

## Geometry-Opportunity, Online-Gain, and Real-Audio Validation Protocol v1

**Project goal.** Produce a rigorous, auditable experimental package for
the ICLR 2027 paper on geometry-certified acceleration for Griffin--Lim
/ phase retrieval.

**Current frozen status.** - E1 Geometry--Spectrum: **GREEN ---
freeze** - E2 Local Rate Prediction: **GREEN --- freeze** - E3 Passive
Ritz / Active Edge: **YELLOW-GREEN --- accurate, but raw estimate is not
a certified upper bound** - Original online policy: **FAILED/ABLATION
--- preserve** - Repaired `dynamic_envelope` policy: **GREEN ---
freeze** - Next priority: **E6 Geometry-Opportunity / Acceleration-Gain
Audit** - Then: **E7 Generalization + Real-Audio Validation**

The purpose of this next round is **not to tune the method until it
wins**. The purpose is to determine, under a frozen protocol, **when
geometry makes acceleration possible, how much of the oracle opportunity
the online method captures, and whether the mechanism transfers beyond
the controlled cases.**

------------------------------------------------------------------------

# 1. Scientific Questions for the Next Round

The next experiments must answer four questions.

### Q1 --- When is meaningful acceleration geometrically available?

For each frozen case, quantify the improvement that an oracle
geometry-aware design can theoretically/empirically obtain over
optimally tuned FGLA.

### Q2 --- How much of that opportunity does the online method recover?

The online method should be evaluated relative to the **available oracle
headroom**, not only by raw win/loss against FGLA.

### Q3 --- Why does the online method succeed or fail?

Relate success/failure to: - (`\lambda`{=tex}*+); - transverse gap
(1-`\lambda`{=tex}*+); - spectral width
(`\lambda`{=tex}*+-`\lambda`{=tex}*-); - estimator error; - estimator
maturation time; - finite iteration horizon; - safeguard activity.

### Q4 --- Does the same mechanism transfer to unseen controlled configurations and genuine audio?

This is the external/generalization gate. No retuning is permitted after
seeing these results.

------------------------------------------------------------------------

# 2. Non-Negotiable Experimental Rules

1.  **Freeze all existing E1--E4 raw results.** Never overwrite them.
2.  **Freeze the repaired `dynamic_envelope` online policy.**
3.  Keep the current primary online settings unchanged unless the
    supervisor explicitly opens a new ablation:
    -   Ritz memory (p=3);
    -   block length (K=8);
    -   zero margin if that is the repaired frozen configuration;
    -   dynamic running-envelope policy;
    -   safe GLA fallback.
4.  Preserve the original failed online policy as an ablation.
5.  **No seed selection.**
6.  **No post-hoc fit-window selection.**
7.  **No deletion of near-degenerate cases.**
8.  Do not discard cases because Online loses to FGLA.
9.  Do not modify a threshold after inspecting test-set performance.
10. Every new run must save:
    -   config;
    -   seed;
    -   exact command;
    -   environment;
    -   raw per-iteration trace;
    -   raw per-case result;
    -   aggregate summary.
11. Any bug fix must be documented and followed by rerunning all
    affected cases.
12. Separate **development/calibration** cases from
    **held-out/generalization** cases.
13. Do not use the held-out set to choose hyperparameters.
14. Report negative and null results.
15. Stop and hand off results at each gate below before proceeding.

------------------------------------------------------------------------

# 3. Work Split

## Student A --- Geometry-Opportunity & Controlled Generalization

Student A owns:

-   **A1 / E6-A:** geometry-opportunity audit on all existing frozen
    cases;
-   **A2 / E6-B:** oracle-gain capture analysis;
-   **A3 / E6-C:** controlled held-out geometry generalization;
-   **A4:** statistical summaries and controlled-case figures.

Student A should not change the online algorithm.

## Student B --- Online Dynamics & Real-Audio Generalization

Student B owns:

-   **B1 / E6-D:** estimator maturation and horizon analysis;
-   **B2 / E6-E:** online failure decomposition;
-   **B3 / E7-A:** held-out signal-scale evaluation;
-   **B4 / E7-B:** genuine real-audio evaluation;
-   **B5:** computational-cost and iterations-to-tolerance analysis.

Student B must use the frozen online implementation.

## Independent cross-check

After both primary packages are complete: - Student A reruns a small
held-out online case from Student B. - Student B independently
recomputes the E6 opportunity statistics from Student A's exported
per-case CSV.

------------------------------------------------------------------------

# 4. Student A --- E6 Geometry-Opportunity Audit

## A1. Build one canonical per-case ledger

Start from the **existing frozen results**. Do not rerun unless a
required field is missing.

Create:

``` text
results/e6_geometry_opportunity/e6_case_ledger.csv
results/e6_geometry_opportunity/e6_case_ledger.json
```

Each row must correspond to one scientifically comparable case and
contain at least:

``` text
case_id
config
seed
epsilon_or_initialization
lambda_minus
lambda_plus
spectral_width
transverse_gap
q_gla_pred
q_fgla_pred
q_oracle_pred
q_gla_obs
q_fgla_obs
q_oracle_obs
q_online_obs
edge_estimate_final
edge_rel_error_final
online_beats_fgla
fit_window
horizon
```

Derived columns:

\[ W=`\lambda`{=tex}*+-`\lambda`{=tex}*-, \]

\[ G=1-`\lambda`{=tex}\_+, \]

\[ `\Delta`{=tex}*{`\rm oracle`{=tex}}\^{`\rm pred`{=tex}} =
q*{`\rm FGLA`{=tex}}\^{`\rm pred`{=tex}} -
q\_{`\rm Oracle`{=tex}}\^{`\rm pred`{=tex}}, \]

\[ `\Delta`{=tex}*{`\rm oracle`{=tex}}\^{`\rm obs`{=tex}} =
q*{`\rm FGLA`{=tex}}\^{`\rm obs`{=tex}} -
q\_{`\rm Oracle`{=tex}}\^{`\rm obs`{=tex}}, \]

\[ `\Delta`{=tex}*{`\rm online`{=tex}}\^{`\rm obs`{=tex}} =
q*{`\rm FGLA`{=tex}}\^{`\rm obs`{=tex}} -
q\_{`\rm Online`{=tex}}\^{`\rm obs`{=tex}}. \]

Define oracle-gain capture only when the denominator is safely positive:

\[ R\_{`\rm capture`{=tex}} =
`\frac{\Delta_{\rm online}^{\rm obs}}`{=tex}
{`\Delta`{=tex}\_{`\rm oracle`{=tex}}\^{`\rm obs`{=tex}}}. \]

**Important:** choose a numerical denominator tolerance before looking
at (R\_{`\rm capture`{=tex}}), document it, and report how many cases
are excluded from this ratio because oracle headroom is numerically
negligible. Those cases remain in every other analysis.

Also compute a clipped ratio for visualization only:

\[ R\_{`\rm capture`{=tex}}\^{\[0,1\]} =
`\min`{=tex}{1,`\max`{=tex}{0,R\_{`\rm capture`{=tex}}}}. \]

Never replace the raw ratio with the clipped ratio in tables.

------------------------------------------------------------------------

# 5. Student A --- Required E6 Analyses

## A2. Opportunity distribution

Report: - median / IQR / p10 / p90 of predicted oracle opportunity; -
median / IQR / p10 / p90 of observed oracle opportunity; - fraction of
cases with negligible, small, medium, and large oracle opportunity.

The bins must be defined **before** inspecting Online performance.
Prefer quantile-based opportunity groups if no scientifically natural
absolute threshold exists.

### Figure A1

**Oracle opportunity vs. geometry**

Produce separate scatter plots:

\[ `\Delta`{=tex}*{`\rm oracle`{=tex}} `\text{ vs. }`{=tex}
`\lambda`{=tex}*+, \]

\[ `\Delta`{=tex}*{`\rm oracle`{=tex}} `\text{ vs. }`{=tex}
1-`\lambda`{=tex}*+, \]

\[ `\Delta`{=tex}*{`\rm oracle`{=tex}} `\text{ vs. }`{=tex}
`\lambda`{=tex}*+-`\lambda`{=tex}\_-. \]

Include all cases.

------------------------------------------------------------------------

## A3. Online gain versus available oracle gain

### Figure A2 --- central experimental figure candidate

Plot:

\[ x=`\Delta`{=tex}*{`\rm oracle`{=tex}}\^{`\rm obs`{=tex}},
`\qquad`{=tex} y=`\Delta`{=tex}*{`\rm online`{=tex}}\^{`\rm obs`{=tex}}.
\]

Include: - identity line (y=x); - zero-gain line (y=0); - one point per
frozen case; - clear marking of Online losses; - no point deletion.

Compute: - Pearson correlation; - Spearman rank correlation; - bootstrap
95% CI for both correlations; - slope of a simple descriptive regression
through the origin **and** ordinary regression with intercept.

Regression is descriptive only; do not claim causal inference.

### Figure A3

Plot raw (R\_{`\rm capture`{=tex}}) versus
(`\Delta`{=tex}\_{`\rm oracle`{=tex}}\^{`\rm obs`{=tex}}).

Report: - median raw (R\_{`\rm capture`{=tex}}); - IQR; - p10/p90; -
fraction (R\_{`\rm capture`{=tex}}\>0); - fraction
(R\_{`\rm capture`{=tex}}`\ge0.5`{=tex}); - fraction
(R\_{`\rm capture`{=tex}}`\ge0.8`{=tex}); - fraction
(R\_{`\rm capture`{=tex}}\>1); - fraction (R\_{`\rm capture`{=tex}}\<0).

This analysis is more informative than the simple FGLA beat fraction.

------------------------------------------------------------------------

# 6. Student A --- Held-Out Controlled Geometry Set

The current controlled experiments are mainly validation cases. We need
a modest **held-out geometry set** to ensure the story is not specific
to the original grid.

Before running Online on this set, freeze a new list of configurations
spanning: - several STFT window sizes; - several hop ratios /
redundancies; - at least two signal dimensions; - multiple random
seeds; - geometries producing a range of (`\lambda`{=tex}\_+); - where
feasible, a range of spectral widths.

Target approximately **30--50 new regular cases**, depending on
computational cost.

### Critical rule

Generate/freeze the configuration list first and save:

``` text
configs/e6_heldout_geometry.json
```

Only then run the methods.

Do not regenerate the grid because the resulting geometry is
unfavorable.

### Methods

Run exactly: - GLA; - optimally tuned constant FGLA; - oracle
full-interval minimax; - oracle conservative (\[0,`\lambda`{=tex}\_+\])
design where relevant; - frozen Online-geometry method.

### Handoff Gate A

Student A sends:

``` text
e6_case_ledger.csv
e6_case_ledger.json
e6_summary.json
e6_heldout_summary.json
figures/
environment.txt
commands.txt
README_RESULTS.md
```

Then **STOP**.

------------------------------------------------------------------------

# 7. Student B --- Estimator Maturation Audit

The theorem is asymptotic, while the empirical gains are finite-horizon.
We therefore need to understand how quickly the estimator and adaptive
parameters enter their useful regime.

For every frozen online case save iteration-level traces:

``` text
iteration
lambda_hat_raw
lambda_hat_envelope
lambda_plus_oracle
edge_rel_error
alpha
beta
gamma
safeguard_accept
objective_or_orbit_error
```

## B1. Define maturation metrics

Predefine edge-accuracy thresholds:

\[ 1%,`\qquad0.5`{=tex}%,`\qquad0.1`{=tex}%. \]

For each case compute the first iteration after which the envelope
estimate remains within each threshold for the rest of the valid tail.

Define:

``` text
T_edge_1pct
T_edge_0p5pct
T_edge_0p1pct
```

Also compute parameter stabilization time, e.g. first iteration after
which relative changes in the synthesized parameters remain below a
frozen tolerance.

Do not choose the tolerance after seeing which one gives the best plot.

### Figure B1

For representative cases from low-, medium-, and high-opportunity
regimes, plot: - oracle (`\lambda`{=tex}\_+); - raw Ritz estimate; -
envelope estimate; - iteration.

### Figure B2

Plot online gain at horizon (H) against estimator maturation ratio:

\[ `\frac{T_{\rm edge}}{H}`{=tex}. \]

Hypothesis to test:

> Online acceleration is limited when estimator maturation consumes a
> large fraction of the available iteration budget.

This is a hypothesis, not a guaranteed conclusion.

------------------------------------------------------------------------

# 8. Student B --- Multi-Horizon Rate Audit

Use a frozen set of horizons, for example those already present in the
repository. Do not select only the horizon where Online performs best.

For each horizon (H), report: - FGLA beat fraction; - median
(q\_{`\rm Online`{=tex}}/q\_{`\rm FGLA`{=tex}}); - p90 ratio; - median
(q\_{`\rm Online`{=tex}}/q\_{`\rm Oracle`{=tex}}); - median oracle-gain
capture; - number of valid rate fits.

### Figure B3

Plot these quantities versus horizon.

The desired analysis distinguishes: 1. estimator maturation; 2.
asymptotic rate realization; 3. genuinely unfavorable geometry.

------------------------------------------------------------------------

# 9. Student B --- Failure Decomposition

Every Online loss should receive a machine-generated category based on
predefined diagnostics.

Candidate categories:

1.  **Negligible oracle opportunity**\
    FGLA and oracle are already nearly indistinguishable.

2.  **Estimator not mature by horizon**\
    Edge error remains above the frozen accuracy threshold for too much
    of the run.

3.  **Near-degenerate geometry**\
    (`\lambda`{=tex}\_+) is extremely close to one.

4.  **Safeguard-dominated transient**\
    Frequent rejection/fallback prevents the accelerated regime from
    becoming active.

5.  **Rate-fit uncertainty / insufficient tail**\
    Too few valid local iterations for stable rate estimation.

6.  **Unexplained**\
    None of the predefined diagnostics explains the loss.

Do not force every failure into a favorable category. Preserve
`unexplained`.

Produce:

``` text
results/e6_failure_analysis/failure_cases.csv
results/e6_failure_analysis/failure_summary.json
```

### Figure B4

Stacked count or fraction of loss categories.

This figure is primarily appendix material.

------------------------------------------------------------------------

# 10. E7 --- Held-Out Signal-Scale Validation

Before genuine audio, evaluate the frozen method on a held-out
deterministic signal-scale set.

Include multiple signal structures such as: - harmonic; - chirp; -
speech-like; - transient/percussive; - mixtures if already supported by
the code.

The held-out signals/configurations must not be used for hyperparameter
selection.

For each case record: - geometry; - oracle opportunity; - online gain; -
gain capture; - edge maturation; - safeguard statistics; - iterations to
fixed error thresholds.

### Iterations-to-tolerance

Choose several tolerances **before running the held-out set**.

For example, if the existing orbit-error scale supports them, freeze
2--4 thresholds spanning easy to difficult convergence regimes.

For method (m), define:

\[ T_m(`\tau`{=tex}) = `\min`{=tex}{n:e_n`\le`{=tex}`\tau`{=tex}}. \]

Report: - median iterations; - IQR; - fraction reaching tolerance within
budget; - paired iteration saving versus FGLA:

\[ S\_{`\rm iter`{=tex}} = `\frac{T_{\rm FGLA}-T_{\rm Online}}`{=tex}
{T\_{`\rm FGLA`{=tex}}}. \]

If a method does not reach the threshold, mark it censored rather than
inventing a value.

------------------------------------------------------------------------

# 11. E7 --- Genuine Real-Audio Validation

## B3. Freeze the audio manifest before the final run

Use approximately **6--10 genuine WAV files** if computationally
feasible, covering at least: - speech; - harmonic/music; -
transient/percussive content.

Prefer legally usable or internally recorded signals whose provenance
can be documented.

Create:

``` text
configs/e7_audio_manifest_frozen.json
```

Record: - file identifier; - source/provenance; - original sample
rate; - duration; - content category; - selected deterministic excerpt
rule.

Do not replace a recording because it gives an unfavorable result.

------------------------------------------------------------------------

# 12. Real-Audio Experimental Design

Use at least two frozen STFT regimes representing different
redundancies/geometries.

Use multiple initialization severities/radii if already supported.

For every case compare:

1.  GLA;
2.  conventional/practical FGLA if already part of the benchmark;
3.  optimally tuned FGLA using oracle local (`\lambda`{=tex}\_+) for the
    theoretical comparison;
4.  oracle minimax geometry-aware method;
5.  frozen Online geometry-aware method.

Do not use oracle quantities to tune the Online method.

### Primary real-audio outcomes

Report: - final objective/orbit error; - iterations to tolerance; -
fitted local rate where valid; - oracle opportunity; - online gain
capture; - final active-edge error; - maturation time; - safeguard
rejection fraction; - convergence/success fraction.

### Stratified reporting

Report overall results and stratify by: - content type; - STFT regime; -
initialization severity; - opportunity level; - near-degenerate vs
non-near-degenerate geometry.

Near-degenerate cases remain in the overall result.

------------------------------------------------------------------------

# 13. Statistical Protocol

The paper should not rely only on means.

For principal scalar metrics report: - (n); - median; - IQR; - p10/p90
where useful; - paired differences; - bootstrap 95% confidence
intervals.

Use paired comparisons because methods run on the same problem
instances.

For a scalar paired difference

\[ D_i=q\_{{`\rm Online`{=tex}},i}-q\_{{`\rm FGLA`{=tex}},i}, \]

report: - median (D_i); - bootstrap 95% CI; - fraction (D_i\<0).

If enough independent problem instances are available, a Wilcoxon
signed-rank test may be reported as secondary evidence, but **effect
sizes and confidence intervals are more important than p-values**.

Do not treat repeated perturbation magnitudes from the same base
geometry as fully independent scientific replicates without stating the
nesting.

For final paper statistics, aggregate at the scientifically appropriate
independent unit (e.g. configuration/seed or audio/configuration), and
retain per-perturbation data in the appendix.

------------------------------------------------------------------------

# 14. Robustness Checks

Only after the primary frozen analysis is complete may the following
robustness checks be opened.

### R1 --- Memory

Compare:

\[ p`\in`{=tex}{1,3,5}. \]

This is an ablation; (p=3) remains the frozen primary setting.

### R2 --- Envelope versus raw estimator

Compare: - raw Ritz plug-in; - repaired dynamic envelope.

This should demonstrate why the repair is necessary.

### R3 --- Original failed policy

Preserve the original policy as a negative ablation.

### R4 --- Horizon

Report multiple frozen horizons.

### R5 --- Numerical precision / machine reproducibility

Rerun a small subset on both student machines.

None of these ablations may be used retrospectively to replace the
frozen primary method.

------------------------------------------------------------------------

# 15. Sanity Checks Before Any Result Is Accepted

For every case automatically check:

### Geometry

\[ 0`\le`{=tex}`\lambda`{=tex}*-`\le`{=tex}`\lambda`{=tex}*+\<1 \]

for regular transverse cases, allowing documented numerical tolerance.

Check exactly one neutral global-phase mode when required by the
controlled regular setting.

### Rate ordering

For predicted quantities verify:

\[ q\_{`\rm Oracle`{=tex}} \< q\_{`\rm FGLA`{=tex}}\^`\star`{=tex} \<
q\_{`\rm GLA`{=tex}} \]

whenever the theorem assumptions apply.

### Online parameters

Check finite values and legal domains for
(`\alpha`{=tex},`\beta`{=tex},`\gamma`{=tex}).

### Ritz

Check: - finite generalized eigenvalues; - Gram conditioning; - number
of valid updates; - no silent NaNs; - no use of invalid windows.

### Result integrity

Check: - all expected case IDs present; - no duplicate IDs; - no missing
seeds without explanation; - no manually edited aggregate values.

Generate an automated `integrity_report.json`.

------------------------------------------------------------------------

# 16. Required Publication Figures

The next round should aim to produce these publication candidates.

### Main-text candidates

**Fig. 1 --- Geometry predicts spectrum**\
Already essentially frozen from E1.

**Fig. 2 --- Theory predicts local rates**\
Already essentially frozen from E2.

**Fig. 3 --- Geometry determines acceleration opportunity**\
Oracle opportunity against geometry.

**Fig. 4 --- Online captures oracle opportunity**\
(`\Delta`{=tex}*{`\rm online`{=tex}}) versus
(`\Delta`{=tex}*{`\rm oracle`{=tex}}).

**Fig. 5 --- Online rate realization over horizon**\
Show maturation and convergence toward oracle behavior.

**Fig. 6 --- Real-audio transfer**\
Compact paired comparison / iterations-to-tolerance.

Because the ICLR main text is limited, the final paper will likely
retain only 3--4 of these; generate all first and decide only after the
scientific audit.

### Appendix candidates

-   Ritz memory ablation;
-   raw versus envelope estimator;
-   failed original policy;
-   failure decomposition;
-   near-degenerate cases;
-   full real-audio per-case results;
-   additional horizon plots.

------------------------------------------------------------------------

# 17. Required Tables

## Table T1 --- Controlled theorem validation

Include: - spectral error; - rate-prediction error; - ordering fraction.

## Table T2 --- Online opportunity capture

Include: - number of cases; - FGLA beat fraction; - median online/FGLA
rate ratio; - median online/oracle ratio; - median
(R\_{`\rm capture`{=tex}}); - bootstrap CI; - estimator error.

## Table T3 --- Held-out / real-audio generalization

Include: - number of cases/signals; - iterations-to-tolerance; - success
fraction; - paired savings; - oracle-gain capture; - safeguard
diagnostics.

------------------------------------------------------------------------

# 18. What Counts as a Strong Result?

The next round does **not** need Online to win every case.

A scientifically strong outcome would be:

1.  geometry reliably predicts where oracle acceleration opportunity is
    large;
2.  Online gain positively tracks oracle opportunity;
3.  Online captures a substantial fraction of oracle gain in
    medium/high-opportunity cases;
4.  failures concentrate in interpretable regimes such as negligible
    opportunity, near-degeneracy, or insufficient estimator maturation;
5.  the same pattern appears on held-out configurations and real audio;
6.  the frozen safeguard prevents catastrophic failures;
7.  results are reproducible across the two students' machines.

A negative but still publishable result would be that Online gain does
not correlate with oracle opportunity or fails to transfer to held-out
data. **Do not hide such a result.** Stop and return it for
theoretical/algorithmic audit.

------------------------------------------------------------------------

# 19. Stop Gates

## Gate A --- Geometry Opportunity

Proceed only after the supervisor audits: - canonical ledger; -
opportunity plots; - gain-capture analysis; - held-out controlled
geometry.

## Gate B --- Online Dynamics

Proceed only after audit of: - maturation traces; - multi-horizon
analysis; - failure decomposition.

## Gate C --- Real Audio

Proceed only after the audio manifest is frozen.

## Gate D --- Final Experiment Freeze

No result enters the manuscript until: - both students have completed
cross-checks; - integrity report passes; - all negative cases are
retained; - the final aggregate script reproduces every paper number
from raw ledgers.

------------------------------------------------------------------------

# 20. Final Handoff Structure

Each student should return one ZIP with the following structure.

``` text
ICLR2027_experiments/
├── README_RESULTS.md
├── environment.txt
├── commands.txt
├── configs/
├── raw/
├── processed/
├── traces/
├── figures/
├── tables/
├── integrity_report.json
└── summary.json
```

`README_RESULTS.md` must state: - what was run; - what was not run; -
any failures; - any bug fixes; - any deviation from the protocol; - the
student's own interpretation in no more than one page.

------------------------------------------------------------------------

# 21. Final Instruction to Both Students

The goal is **not** to produce the most favorable number.

The goal is to produce a result package for which an independent
reviewer could trace every paper claim back to: 1. a frozen
configuration; 2. a raw experimental record; 3. a deterministic analysis
script; 4. a clearly defined metric; 5. an explicit theorem or empirical
hypothesis.

If an experiment contradicts our expectation, preserve it and stop for
review.

**Scientific reliability has priority over a positive result.**
