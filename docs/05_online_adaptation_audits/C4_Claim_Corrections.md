# Task C4 — Final Claim-Discipline Audit

**Document Reference**: `Student B - Final Correction & Audit Handoff.md`  
**Evaluation Scope**: ICLR 2027 — *Geometry Determines Acceleration in Phase Retrieval*  
**Date**: September 2026  
**Status**: COMPLETE (Editing and claim moderation without new computation)

---

## Executive Overview

The final scientific audit identified four claims in prior drafts of the Student B experimental report that were stated more strongly than the experimental evidence strictly establishes. In accordance with the supervisor instructions in Task C4, all four claims have been audited and replaced with moderated, evidence-calibrated language.

---

## Claim-by-Claim Audit & Corrections

### C4.1 Safeguard Reliability

* **Previous Language**:
  > "Absolute safety: the safeguard completely eliminates divergence risk" / "0 / 7176 failures across all experimental phases."
* **Audit Finding**:
  The figure of 7176 was formed by aggregating across heterogeneous, partially overlapping evaluation phases (preliminary pilot runs, multi-horizon tests, signal-scale runs, and basin runs). The rigorously verified, non-overlapping denominator in the full real-audio basin evaluation is exactly **4680 runs**. Claiming "absolute safety" or "complete elimination of risk" extrapolates beyond finite empirical sampling.
* **Approved Replacement Language**:
  > **"No safeguard failure was observed among the 4,680 basin runs in the full real-audio evaluation."**
* **Reporting Rule**:
  Earlier phase results (e.g., zero divergence in the 12 transfer configurations) are reported separately rather than being summed into an inflated composite denominator.

---

### C4.2 Near-Degenerate Real-Audio Geometry

* **Previous Language**:
  > "Near-degeneracy is a natural geometric property of STFT on real audio."
* **Audit Finding**:
  While 81.28% of valid cases in the evaluated dataset satisfied the pre-specified near-degeneracy criterion ($\lambda_+ \ge 0.9999$ or spectral gap $1 - \lambda_+ \le 10^{-4}$), this finding is conditioned on the tested MUSAN subset (speech, music, noise) and the specific STFT window lengths and hop sizes ($W \in \{256, 512\}$, hop $\in \{32, 64\}$). Generalizing to *all* natural acoustic signals or arbitrary transform parameters is unverified.
* **Approved Replacement Language**:
  > **"Near-phase-degenerate geometry was common in the evaluated MUSAN subset under the tested STFT configurations, with 81.28% of valid cases satisfying the pre-specified near-degeneracy criterion."**

---

### C4.3 Six-File Real-Audio Transfer Experiment

* **Previous Language**:
  > "External generalization is proved" / "Divergence risk is completely eliminated on unseen real audio."
* **Audit Finding**:
  The evaluation of 6 held-out WAV files across 2 STFT regimes (hop 32 and hop 64, 12 total test instances) showed zero divergence and monotonic convergence. However, $N=6$ files is an empirical sanity check, not a statistical proof of universal out-of-domain generalization across acoustic domains.
* **Approved Replacement Language**:
  > **"No divergence was observed in the frozen 6-file × 2-STFT-regime transfer evaluation."**
* **Contextual Role**:
  Explicitly designated as a **frozen transfer sanity check**, demonstrating policy robustness across standard speech, music, and noise textures without hyperparameter retuning.

---

### C4.4 Online Adaptation versus Optimal FGLA

* **Previous Language**:
  > "Online is consistently faster than optimal FGLA" / "100% Online beats FGLA."
* **Audit Finding**:
  The multi-horizon empirical win rates in the controlled evaluation are:
  - $H = 60$: **86.7%** (13 / 15)
  - $H = 120$: **46.7%** (7 / 15)
  - $H = 180$: **40.0%** (6 / 15)
  - $H = 360$: **40.0%** (6 / 15)
  Across all multi-horizon configurations, there are **41 instances** where Online does not achieve a faster fitted rate than FGLA. Of these, 53.7% (22 cases) stem from negligible Oracle opportunity ($\Delta_{\rm oracle} < 10^{-4}$ where FGLA is already near-optimal), 22.0% from near-degenerate geometry, and 12.2% from estimator maturation latency at very short horizons.
  Furthermore, on real audio, Online achieves an overall convergence basin rate of **74.94%** versus **54.87%** for FGLA (a +20.07 percentage point improvement in basin diameter).
* **Approved Replacement Language**:
  > **"Online shows a strong early finite-horizon advantage in the controlled multi-horizon experiment, while optimal FGLA becomes highly competitive at longer horizons."**
  > 
  > **"Online substantially improves empirical basin success relative to FGLA, but does not exhibit universal paired-rate superiority."**
* **Core Conceptual Principle**:
  $$\boxed{\textbf{basin robustness} \neq \textbf{paired local-rate superiority}}$$
  Online expands the basin of attraction and prevents stagnation from bad initialization, while FGLA with an optimal fixed momentum parameter achieves an extremely competitive asymptotic rate once inside a well-conditioned local basin.



