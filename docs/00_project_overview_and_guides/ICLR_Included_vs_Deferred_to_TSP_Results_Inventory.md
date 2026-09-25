# ICLR Included vs Deferred-to-TSP Results Inventory v1

## Scope and status convention

This inventory was prepared against the current ICLR 2027 Geometry manuscript package (`main_iclr2027_v9.tex` with Appendices A--F) and the frozen theory/experiment handoff material.

Status codes:

- **ICLR / PROVED**: proved and present in the ICLR manuscript (main text and/or appendix).
- **PROVED / DEFERRED**: mathematically proved in our project but intentionally omitted from ICLR.
- **IMPLEMENTED / NOT THEOREM**: code/protocol/diagnostic exists, but no theorem currently establishes the desired property.
- **OPEN GATE**: not yet proved; this is genuine SafeGeoAGLA/TSP research.
- **EXTERNAL FOUNDATION**: available from prior literature (especially Nenov et al. AGLA), not a new theorem of our current project.

---

## A. Results already proved and included in ICLR 2027

| Scientific component | Formal object(s) in current manuscript | Mathematical status | ICLR role | SafeGeoAGLA/TSP reuse |
|---|---|---:|---|---|
| Regular feasible geometry | Assumption `ass:regular` | Assumption, not theorem | Defines smooth/local regime | Reuse as target local regime |
| Scalar magnitude-projector derivative | `lem:scalar-proj-derivative` | PROVED | Appendix A foundation | Reuse |
| Product magnitude-manifold derivative | `lem:product-proj-derivative` | PROVED | Appendix A foundation | Reuse |
| Griffin--Lim Jacobian as tangent-projector product | `thm:geometry-spectrum`, `lem:J-spectrum` | PROVED | Central ICLR result | Import/cite, do not re-sell as TSP novelty |
| Principal-angle spectral characterization | `thm:geometry-spectrum` | PROVED | Central ICLR result | Local sensor/design foundation |
| Global-phase neutral eigenspace and transverse slice | `lem:phase-mode` | PROVED | Removes symmetry correctly | Reuse in local TSP analysis |
| Restricted gradient/Hessian identity | `cor:hessian`, `lem:gradient-hessian` | PROVED | Geometry-to-curvature bridge | Reuse |
| Local quadratic growth modulo phase | `cor:hessian`, `lem:phase-alignment` | PROVED | Local regularity result | Useful for safeguard-local analysis |
| Exact two-step AGLA linearization | `lem:agla-linearization` | PROVED | Modal dynamics foundation | Reuse |
| Scalar modal polynomial | `lem:scalar-modal` | PROVED | Exact local modal dynamics | Reuse |
| Exact unit-disk Jury criterion | `lem:quadratic-jury` | PROVED | Stability tool | Reuse |
| Exact transverse modal Schur stability | `prop:modal-stability` | PROVED | Local stability characterization | Reuse |
| Full quotient-state orbital Schur stability | `cor:linear-orbital-stability` | PROVED | Correctly retains phase-secondary root | Reuse |
| Radius-\(q\) Jury feasibility | `lem:radius-q-jury` | PROVED | Minimax proof tool | Reuse |
| Endpoint reduction of robust radius-\(q\) feasibility | `lem:endpoint-reduction` | PROVED | Appendix C | Reuse |
| Universal upper-edge lower bound | `lem:upper-edge-bound` | PROVED | Appendix C | Reuse |
| Necessary minimax quadratic inequality | `lem:necessary-quadratic` | PROVED | Appendix C | Reuse |
| Location of minimax root | `lem:qstar-location` | PROVED | Appendix C | Reuse |
| Global lower bound for transverse minimax factor | `prop:minimax-lower` | PROVED | Central proof | Cite/import |
| Attainment/equioscillation of closed-form optimizer | `prop:minimax-attainment` | PROVED | Central proof | Cite/import |
| Exact geometry-optimal AGLA design | `thm:minimax` | PROVED | Hero ICLR theorem | TSP local target controller |
| Exact optimal FGLA factor | `cor:optimal-fgla`, `prop:optimal-fgla` | PROVED | Strong baseline theorem | Reuse baseline |
| Strict AGLA--FGLA--GLA local hierarchy | `cor:optimal-fgla` | PROVED | ICLR claim | Do not claim as new in TSP |
| One-edge specialization \(q^\star(0,\lambda_+)\) | Appendix C specialization | PROVED | Conservative online target | Central controller target for SafeGeoAGLA |
| Spectral-width asymptotic | Appendix C | PROVED | Interpretation | Optional TSP discussion |
| Asymptotically exact secant action | `lem:secant-action` | PROVED | Passive sensing foundation | Reuse |
| Finite passive non-identifiability | `prop:passive-nonidentifiability` | PROVED | ICLR information boundary | Cite/import |
| Ritz compression perturbation identity | Appendix D generalized Ritz compression | PROVED | Estimation mechanism | Reuse |
| Convergent-subspace basis alignment | `lem:aligned-bases` | PROVED | Ritz proof tool | Reuse |
| Exact Ritz-spectrum convergence | `lem:exact-ritz-convergence` | PROVED | Ritz proof tool | Reuse |
| Trajectory-active Ritz consistency | `thm:ritz-consistency` | PROVED under explicit assumptions | Central ICLR estimation theorem | TSP must strengthen coupling, not repeat |
| Normalized residual from conditioned secants | `lem:conditioned-secants` | PROVED | Makes Ritz assumption checkable | Important TSP bridge |
| Continuity of one-edge parameter map | `lem:theta-continuity` | PROVED | Online synthesis foundation | Reuse |
| Correct nonautonomous quotient expansion | `lem:nonautonomous-linearization` | PROVED | G5 proof | Reuse |
| Limiting quotient spectral radius | `lem:quotient-radius` | PROVED | Establishes local target rate | Reuse |
| Adapted-norm contraction lemma | `lem:adapted-norm` | PROVED | Local nonlinear proof tool | Reuse |
| Quotient-distance equivalence | `lem:quotient-distance` | PROVED | Converts quotient contraction to orbital metric | Reuse |
| Conditional online orbital convergence and asymptotic rate recovery | `thm:online-rate` | PROVED conditional on edge consistency + sufficiently late local entry | Final ICLR theorem | TSP must remove/derive some antecedents |

### ICLR experimental components

| Component | Current status | What it establishes / is designed to establish | TSP disposition |
|---|---:|---|---|
| E1 geometry \(\to\) transverse spectrum | Protocol + implementation; controlled numerical evidence exists | Numerical geometry-spectrum correspondence | Reuse only as sanity check |
| E2 spectrum \(\to\) local rate | Protocol + implementation; multi-instance numerical evidence exists | Predicted vs observed late-stage contraction | Reuse only as calibration |
| E3 passive Ritz estimation | Protocol + implementation | Trajectory-active dominant-edge tracking under excitation | Expand into safeguard/coupling diagnostics |
| E4 online one-edge synthesis | Protocol + implementation | Empirical approach toward \(q^\star(0,\lambda_+)\) | Becomes component of SafeGeoAGLA |
| E5 signal-scale / near-degenerate STFT | Engine/protocol exists; includes hard \(\lambda_+\approx1\) cases | Transfer and finite-horizon stress testing | Expand substantially for TSP |
| Real-audio block | Engine/protocol prepared | Practical transfer/basin behavior | Major TSP validation block |
| Running-envelope + GLA fallback | Implemented as experimental protection | Practical transient protection; **not a theorem** | Candidate precursor of formal SafeGeoAGLA safeguard |
| Frozen invalid-fit / failure ledger | Implemented protocol | Prevents post-hoc cherry-picking | Keep and extend |

---

## B. Results proved in the project but intentionally deferred from ICLR

### Key finding of this inventory

There is **not** a large hidden stack of completed SafeGeoAGLA theorems outside the ICLR manuscript. Nearly all original mathematical results that have been fully proved and audited are already represented in ICLR (mostly in Appendices A--E).

What is genuinely deferred is mainly:

| Deferred item | Status | Why not in ICLR | SafeGeoAGLA role |
|---|---:|---|---|
| Use of the existing AGLA KL merit framework as a globalization foundation | EXTERNAL FOUNDATION, not our new theorem | Belongs to Nenov et al. convergence theory; ICLR deliberately stays local | Starting point for a new safeguard theorem |
| Practical checkpoint/fallback idea | IMPLEMENTED / NOT THEOREM | Would distract from local-geometry thesis | Must be formalized |
| Basin/failure diagnostics near \(\lambda_+\uparrow1\) | EMPIRICAL / DIAGNOSTIC | ICLR only needs stress-test interpretation | Can become rate--basin study |
| Real-audio reliability analysis | IMPLEMENTATION / EXPERIMENT DEFERRED | Too large for 9-page theory-first paper | Major TSP evidence |
| Comprehensive finite-budget reliability/failure analysis | PROTOCOL / PARTIAL DATA | Not part of asymptotic ICLR claim | Major TSP empirical contribution |

Therefore **"deferred to TSP" must not be described as already proved** unless a new proof is completed. The journal paper needs genuinely new theorems.

---

## C. Open SafeGeoAGLA / TSP gates

| Proposed SafeGeoAGLA result | Current status | Exact missing implication | Priority |
|---|---:|---|---:|
| Safeguarded sufficient-decrease theorem | OPEN GATE | Proposed aggressive geometry step + fallback \(\Rightarrow\) monotone/descent merit inequality | Critical |
| Whole-sequence safeguarded convergence | OPEN GATE | safeguard descent + relative error + KL \(\Rightarrow\) convergence of switched dynamics to a critical point | Critical |
| Safeguard preserves phase equivariance / quotient structure | OPEN GATE (likely tractable) | switched rule must descend to phase quotient without introducing gauge pathology | High |
| Eventual safeguard inactivity | OPEN GATE | regular local regime + sufficiently accurate geometry estimate \(\Rightarrow\) all late geometry steps accepted | **Hero bridge** |
| Local rate preservation under safeguard | OPEN GATE but should follow after inactivity | safeguard cannot degrade asymptotic \(q^\star(0,\lambda_+)\) once inactive | **Hero bridge** |
| Certified basin / acceptance neighborhood | OPEN GATE | explicit neighborhood in which geometry proposal satisfies safeguard | High |
| Rate--basin / aggressiveness tradeoff | OPEN GATE | quantify how accepted basin changes with \(\lambda_+\), projector curvature, and \(\Theta\) | High |
| Dominant-mode excitation preservation | OPEN GATE | adaptive/safeguarded trajectory preserves or generically excites the dominant transverse mode | **Hardest** |
| Automatic Ritz conditioning | OPEN GATE | switched dynamics \(\Rightarrow\) eventual \(H_n\succ0\) / controlled normalized secants | Very high |
| Coupled estimator--optimizer consistency | OPEN GATE | dynamics themselves \(\Rightarrow \widehat\lambda_{+,n}\to\lambda_+\), rather than assuming it | **Hero candidate** |
| Global-to-local transition theorem | OPEN GATE | safeguarded convergence + regular feasible limit \(\Rightarrow\) entry into local geometry regime + sensing + inactivity | **Hero theorem** |
| Unconditional global recovery of the desired PR solution | NOT A TARGET / likely too strong | arbitrary initialization \(\Rightarrow\) desired feasible orbit | Do not promise |
| Uniform guarantee as \(\lambda_+\uparrow1\) | NOT AVAILABLE | uniform basin/rate constants in vanishing transverse gap | Do not promise |
| Finite-budget universal superiority over FGLA | NOT A THEOREM TARGET | asymptotic local advantage \(\not\Rightarrow\) finite-horizon dominance | Empirical stratification only |

---

## D. SafeGeoAGLA scientific-core assembly

The journal paper should **inherit** the ICLR local controller and sensor, but make the new object the safeguarded coupled dynamics:

\[
\text{practical initialization}
\longrightarrow
\text{safeguarded dynamics}
\longrightarrow
\text{regular feasible local regime}
\longrightarrow
\text{trajectory spectral sensing}
\longrightarrow
\text{eventual safeguard inactivity}
\longrightarrow
\text{geometry-designed local rate}.
\]

Recommended modular decomposition:

| SafeGeoAGLA module | Reused result | New result required |
|---|---|---|
| Local geometry model | ICLR geometry--spectrum theorem | None |
| Local target controller | ICLR exact minimax / one-edge design | None |
| Passive spectral sensor | ICLR secant + Ritz machinery | Need excitation/conditioning coupling |
| Globalizer | Existing AGLA merit ideas + GLA/safe fallback | New safeguard descent theorem |
| Transition mechanism | None currently | Eventual acceptance/inactivity theorem |
| End-to-end asymptotics | ICLR conditional online theorem | New global-to-local/coupled theorem |
| Reliability layer | Current experimental fallback/basin diagnostics | Expanded finite-budget + real-audio study |

---

## E. Frozen separation rule for the two papers

### ICLR 2027 owns

**Geometry \(\rightarrow\) spectrum \(\rightarrow\) exact minimax acceleration \(\rightarrow\) passive identifiability boundary \(\rightarrow\) conditional online local rate recovery.**

### IEEE TSP / SafeGeoAGLA must own

**Safeguarded globalization \(\rightarrow\) basin/acceptance transition \(\rightarrow\) coupled spectral sensing \(\rightarrow\) eventual safeguard inactivity \(\rightarrow\) reliable recovery of the geometry-designed local regime.**

The TSP manuscript should not market the ICLR geometry theorem, minimax formula, passive impossibility result, or basic Ritz consistency as new journal contributions.

---

## F. Go / no-go decision

**GO for SafeGeoAGLA research.**

However, the first new theorem should be **Eventual Safeguard Inactivity only after a precise safeguard sufficient-decrease rule is frozen**. A journal manuscript should not be drafted as a finished paper until the safeguard and transition gates are mathematically green.

The strongest realistic TSP configuration is:

\[
\boxed{
\text{safeguarded convergence}
+
\text{explicit excitation/conditioning condition}
+
\text{eventual safeguard inactivity}
+
\text{conditional coupled rate recovery}
+
\text{large-scale finite-budget/real-audio evidence}.
}
\]

The strongest aspirational configuration additionally proves automatic/generic dominant-mode excitation and full coupled estimator consistency.
