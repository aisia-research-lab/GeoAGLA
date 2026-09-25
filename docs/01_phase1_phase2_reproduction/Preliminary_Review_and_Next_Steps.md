# Preliminary Experimental Results --- Review & Next-Step Recommendations

## 1. Overall Assessment

The two preliminary experimental packages are scientifically encouraging
and broadly consistent with the current theoretical development. Most
importantly, the experiments do **not** reveal a contradiction with the
geometry--spectrum--acceleration theory. The strongest evidence
currently comes from the geometry/spectral validation, local rate
validation, and active-edge identifiability experiments.

The main limitation is no longer basic correctness. The remaining issue
is **empirical effect size and generalization**: the online method can
approach the oracle behavior, but its improvement over optimally tuned
FGLA is still modest on several current configurations. Therefore, the
next experiments should focus on understanding **when the geometry
creates a meaningful acceleration opportunity** and whether the online
method can reliably capture that opportunity.

------------------------------------------------------------------------

## 2. Student Result 1 --- Geometry, Spectrum, Local Rates, and Passive Identification

### What is strong

The first result package provides very strong validation of the
mathematical core.

**Geometry → spectrum validation is essentially exact numerically.**
Across the tested configurations, the Jacobian/principal-angle spectral
correspondence is reproduced to machine precision (maximum relative
spectral error approximately (9.7`\times10`{=tex}\^{-16})), with exactly
one neutral mode in every tested regular case.

**Predicted local convergence ordering is consistently observed.** The
experiments verify

\[ q\_{`\mathrm{Oracle}`{=tex}} \<
q\_{`\mathrm{FGLA}`{=tex}}\^`\star`{=tex} \< q\_{`\mathrm{GLA}`{=tex}},
\]

with the predicted and observed ordering holding across all reported
cases. GLA agrees extremely closely with its predicted asymptotic rate,
while FGLA and the oracle method exhibit small finite-horizon deviations
that decrease toward the local asymptotic regime.

**Passive active-edge estimation is promising.** A short-memory Ritz
estimator with memory (p=3) achieves approximately

\[
`\text{median relative error}`{=tex}`\approx0.25`{=tex}%,`\qquad`{=tex}
p90`\approx0.48`{=tex}%. \]

The non-identifiability control is particularly useful: two systems with
different unexcited full-spectrum edges can produce identical
trajectories and the same estimated active edge. This supports the
theoretical distinction between the **full transverse spectral edge**
and the **trajectory-active spectral edge**.

### Main caveat

The raw Ritz estimate should **not** be interpreted as a certified upper
bound. The reported experiments show a systematic tendency toward
underestimation in the selected (p=3) configuration. This is
scientifically important rather than merely an implementation issue: a
direct plug-in of the raw estimate into aggressive acceleration
parameters can therefore be unsafe.

### Assessment

**Status: GREEN / YELLOW-GREEN.**

The geometry and local-rate components are sufficiently strong to
freeze. The active-edge estimator is also useful, but its role should be
stated carefully: it is an accurate trajectory-based estimator, not by
itself a conservative spectral certificate.

------------------------------------------------------------------------

## 3. Student Result 2 --- Online Acceleration and Safeguard/Repair

### What is strong

The initial online policy exposed a genuine weakness rather than
artificially producing a positive result. The original safeguard
configuration beat optimally tuned FGLA in only about **54%** of cases
and therefore failed the intended performance gate.

The subsequent repair is meaningful. The **dynamic-envelope** policy
improves the result to approximately

\[ `\text{beat fraction}`{=tex}=70.8%, \]

with

\[ `\operatorname{median}`{=tex}
`\frac{q_{\mathrm{Online}}}{q_{\mathrm{FGLA}}}`{=tex}
`\approx0.99798`{=tex}, \]

and

\[ `\operatorname{median}`{=tex}
`\frac{q_{\mathrm{Online}}}{q_{\mathrm{Oracle}}}`{=tex}
`\approx1.00374`{=tex}. \]

The final active-edge error is also extremely small, around
(1.7`\times10`{=tex}\^{-6}) in the reported median statistic. The
repaired experiment passes the reported performance,
eventual-inactivity, and safe-fallback gates.

The stress tests are also reassuring: the safeguard reacts to
deliberately biased estimates without producing fallback failures, and
the tested trajectories remain convergent.

### Main limitation

Although the repaired method wins in a clear majority of cases, the
**absolute improvement in contraction factor over optimal FGLA is
currently small**. The median ratio
(q\_{`\mathrm{Online}`{=tex}}/q\_{`\mathrm{FGLA}`{=tex}}`\approx0.998`{=tex})
corresponds to only a modest rate improvement.

However, this should not immediately be interpreted as a failure of the
online method. The oracle itself has only limited advantage over FGLA in
many of the current cases. Therefore, the important scientific question
is not simply:

> "How often does Online beat FGLA?"

but rather:

> "When the local geometry offers a meaningful oracle acceleration
> opportunity, how much of that opportunity does the online method
> recover?"

### Assessment

**Status after repair: GREEN, but not yet final-paper strong.**

The mechanism appears to work. The next task is to demonstrate that its
benefit is systematically connected to the underlying geometry rather
than relying only on an aggregate win fraction.

------------------------------------------------------------------------

## 4. Combined Scientific Interpretation

Taken together, the two student results support the current paper
narrative:

\[ `\boxed{
\text{local geometry}
\rightarrow
\text{Jacobian spectrum}
\rightarrow
\text{optimal acceleration}
\rightarrow
\text{active spectral identification}
\rightarrow
\text{online acceleration}.
}`{=tex} \]

The evidence is strongest for the first three arrows. The active-edge
estimator is accurate but requires a conservative envelope/safeguard.
The repaired online method then behaves close to the oracle, although
the practical gain over FGLA varies substantially across geometries.

Therefore, the experiments currently support the **mechanism** of the
theory more strongly than they support a broad claim of uniformly large
practical speedup.

This distinction should be preserved in the ICLR paper.

------------------------------------------------------------------------

## 5. Recommended Next Step --- Geometry-Opportunity / Acceleration-Gain Audit

Before performing a large new benchmark sweep, reuse the frozen
experimental cases and quantify the available acceleration opportunity.

For every case compute

\[ `\Delta`{=tex}*{`\mathrm{oracle}`{=tex}} =
q*{`\mathrm{FGLA}`{=tex}}-q\_{`\mathrm{Oracle}`{=tex}}, \]

\[ `\Delta`{=tex}*{`\mathrm{online}`{=tex}} =
q*{`\mathrm{FGLA}`{=tex}}-q\_{`\mathrm{Online}`{=tex}}, \]

and the **oracle-gain capture ratio**

\[ R\_{`\mathrm{capture}`{=tex}} =
`\frac{\Delta_{\mathrm{online}}}`{=tex}
{`\Delta`{=tex}\_{`\mathrm{oracle}`{=tex}}}, \]

whenever (`\Delta`{=tex}\_{`\mathrm{oracle}`{=tex}}) is sufficiently
positive to make the ratio numerically meaningful.

The analysis should relate these quantities to

\[ `\lambda`{=tex}*+,`\qquad
1`{=tex}-`\lambda`{=tex}*+,`\qquad`{=tex}
`\lambda`{=tex}*+-`\lambda`{=tex}*-, \]

as well as estimator maturation time and iteration horizon.

### Key plots

1.  Oracle opportunity (`\Delta`{=tex}\_{`\mathrm{oracle}`{=tex}})
    versus spectral geometry.
2.  Online gain (`\Delta`{=tex}\_{`\mathrm{online}`{=tex}}) versus
    oracle opportunity.
3.  (R\_{`\mathrm{capture}`{=tex}}) versus oracle opportunity.
4.  Online/FGLA/Oracle contraction factors grouped by low-, medium-, and
    high-opportunity regimes.
5.  Win/loss cases against (`\lambda`{=tex}\_+) and spectral width.
6.  Estimator error and parameter stabilization versus iteration.
7.  Iterations-to-tolerance or actual computational savings, not only
    fitted contraction factors.

### Desired conclusion

A substantially stronger experimental conclusion would be:

> **When local geometry provides a meaningful acceleration opportunity,
> the online geometry estimator recovers a substantial fraction of the
> oracle improvement while retaining safeguarded behavior.**

This would connect the experiments directly to the central scientific
thesis rather than presenting the method merely as another FGLA variant.

------------------------------------------------------------------------

## 6. Real-Audio Validation

After the geometry-opportunity audit, the next major gate should be
genuine real-audio validation.

The purpose should **not** be to turn the paper into a large audio
benchmark. Instead, real audio should test whether the controlled
geometric mechanism survives realistic STFT conditions.

At minimum, compare:

-   GLA;
-   conventional/practical FGLA;
-   optimally tuned constant-momentum FGLA;
-   oracle geometry-optimal method;
-   proposed online safeguarded method.

Report convergence curves, iterations to fixed tolerances, final
reconstruction objective/error, estimator evolution, safeguard
activations, and the gap between online and oracle performance.

Cases should cover different windows/hops/redundancies and several audio
signals or signal classes.

------------------------------------------------------------------------

## 7. Priority for the Two Students

**Student 1:** Freeze the geometry/spectrum and local-rate experiments,
then extend the analysis toward the geometry-opportunity
characterization. In particular, extract (`\lambda`{=tex}*-),
(`\lambda`{=tex}*+), spectral width, predicted oracle opportunity, and
observed acceleration gains for every frozen case.

**Student 2:** Freeze the repaired `dynamic_envelope` implementation and
avoid further ad-hoc parameter tuning for now. Use the frozen policy to
evaluate oracle-gain capture and then move to real-audio/generalization
experiments. Preserve the original failed policy as an ablation
demonstrating why the repair is needed.

Both students should keep the current frozen seeds/configurations
unchanged for the main comparison and treat any additional
configurations as a separate generalization set.

------------------------------------------------------------------------

## 8. Current Gate Decision

  -----------------------------------------------------------------------
  Component                           Current assessment
  ----------------------------------- -----------------------------------
  Geometry--spectrum correspondence   **GREEN --- freeze**

  Local rate prediction               **GREEN --- freeze**

  Passive/active-edge identification  **YELLOW-GREEN --- accurate, but
                                      not a certified upper bound**

  Initial online policy               **FAILED/ABLATION --- preserve as
                                      diagnostic evidence**

  Dynamic-envelope repair             **GREEN --- freeze implementation**

  Geometry-conditioned gain analysis  **NEXT PRIORITY**

  Real-audio/generalization evidence  **PENDING**
  -----------------------------------------------------------------------

### Bottom line

The preliminary results are scientifically coherent and support the
theoretical mechanism. There is currently no experimental evidence
suggesting that the central geometry-based theory needs to be revised.

The main improvement needed is **not another round of parameter
tuning**. The priority is to establish when acceleration is
geometrically available, quantify how much of the oracle opportunity the
online method captures, and then verify that this mechanism transfers to
realistic audio/STFT settings.

If these two steps are successful, the experimental section can support
a substantially stronger ICLR 2027 story.
