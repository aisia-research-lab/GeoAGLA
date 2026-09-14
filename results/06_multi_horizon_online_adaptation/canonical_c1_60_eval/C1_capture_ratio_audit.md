# Task C1 — Audit Report: Canonical Multi-Horizon Ledger and R_capture > 1

## Executive Summary
This audit formally investigates the canonical multi-horizon evaluation ledger ($15\text{ cases} \times 4\text{ horizons} = 60\text{ evaluations}$) and addresses the empirical observation of $R_{\rm capture} > 1$ (such as $\operatorname{median} R_{\rm capture} = 1.9764$ at $H=60$) in accordance with Section 4 (Task F1) of `StudentB_Final_Reconciliation_Assignment_Before_Freeze.md`.

### Key Findings & Mathematical Reconciliation
1. **Zero Denominator Clipping & Zero Negligible Oracle Opportunity**:
   In the canonical multi-horizon ledger:
   - `fraction_negligible_oracle_opportunity = 0.0` across all four horizons ($H \in \{60, 120, 180, 360\}$).
   - `fraction_denominator_clipped = 0.0` across all four horizons.
   Therefore, denominator clipping at $10^{-6}$ and negligible Oracle opportunity ($\Delta_{\rm oracle} < 10^{-4}$) are **not** the mechanisms explaining $R_{\rm capture} > 1$ in this canonical experiment.

2. **Finite-Horizon Fitted-Rate Phenomenon**:
   In the canonical experiment, cases with $R_{\rm capture} > 1$ correspond empirically to:
   $$q_{\rm Online} < q_{\rm Oracle}$$
   over the fitted finite-horizon observation window.

3. **Compatibility with Theoretical Oracle Optimality**:
   Values of $R_{\rm capture} > 1$ must **not** be interpreted as violating the Oracle optimality theorem. The theoretical Oracle result concerns the local asymptotic linearized regime, whereas the empirical contraction factors are estimated from finite nonlinear trajectory windows where transient nonlinear dynamics can temporarily produce fitted slopes steeper than the asymptotic linearized prediction.

---

## Multi-Horizon Summary Table (Canonical Ledger Verification)

| Horizon ($H$) | Cases | Online Wins ($q_{\rm Online} < q_{\rm FGLA}$) | Win Rate (%) | Median $R_{\rm capture}$ | IQR | Fraction $> 1$ | Fraction $[0, 1]$ | Fraction $< 0$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$H=60$** | 15 | **13 / 15** | **86.7%** | **+1.9764** | **3.0234** | **60.0%** (9/15) | **26.7%** (4/15) | **13.3%** (2/15) |
| **$H=120$** | 15 | **7 / 15** | **46.7%** | **-0.0827** | **3.4803** | **20.0%** (3/15) | **26.7%** (4/15) | **53.3%** (8/15) |
| **$H=180$** | 15 | **6 / 15** | **40.0%** | **-0.8199** | **4.5096** | **6.7%** (1/15) | **33.3%** (5/15) | **60.0%** (9/15) |
| **$H=360$** | 15 | **6 / 15** | **40.0%** | **-1.2610** | **2.8045** | **13.3%** (2/15) | **26.7%** (4/15) | **60.0%** (9/15) |

---

## Detailed Empirical Analysis across Horizons

1. **Short Horizon ($H=60$)**:
   - Online exhibits a strong finite-horizon advantage, winning in **13 out of 15 cases (86.7%)**.
   - The median capture ratio is **$+1.9764$**.
   - In 9 cases ($60.0\%$), $R_{\rm capture} > 1.0$ occurs because Online rapidly adapts to active spectral modes within early blocks, producing a transient contraction factor that is temporarily smaller than the asymptotic linearized Oracle rate ($q_{\rm Online} < q_{\rm Oracle}$).
   - Both non-win cases (`h32_w16_h4_f16__s0__e0.0001` and `h32_w16_h4_f16__s2__e0.0001`) are associated with near-degenerate geometry ($\lambda_+ \ge 0.9999$).

2. **Longer Horizons ($H=120, 180, 360$)**:
   - As $H$ lengthens, paired-rate comparisons become mixed ($46.7\%$, $40.0\%$, $40.0\%$).
   - Fixed optimal FGLA operates with ideal momentum from iteration 0, while Online incurs an initial estimation latency ($T_{\rm edge}$) before dynamic momentum engages.
   - Consequently, the canonical multi-horizon experiment demonstrates that **Online geometry adaptation provides robust finite-horizon responsiveness**, while **fixed optimal momentum remains highly competitive in paired local-rate comparisons over extended horizons**.

---

## Approved Scientific Interpretation (Task F1)

> **Values of $R_{\rm capture} > 1$ in the canonical multi-horizon experiment arise when the finite-horizon fitted Online contraction factor is temporarily smaller than the local asymptotic Oracle prediction. Such values should not be interpreted as violating Oracle optimality, because the theoretical Oracle result concerns the local asymptotic linearized regime, whereas the empirical contraction factors are estimated from finite nonlinear trajectory windows.**
