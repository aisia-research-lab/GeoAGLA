# Trace Provenance for Panel C (Passive Edge-Estimator Maturation)

## 1. Provenance Summary
- **Audience / Student:** Bảo
- **Target Gate:** Gate C (G-R4: Panel C raw-data reproduction)
- **Status:** **PASS** (`RAW-DATA-REPRODUCIBLE`)
- **Git Commit:** `5701afe746e4b2d994e62e318950b1345a87348e` (Branch: `bao-10pct-dataset`)
- **Original Experiment Script:** `GeoAGLA_Consolidated/experiments/06_multi_horizon_online_adaptation/04_estimator_maturation_sweep.py`
- **Plotting Script (Package):** `scripts/reproduce_results_and_figures.py` (Panel C generator)

---

## 2. Case Selection Rule
The three representative trajectory traces correspond to the three canonical opportunity regimes:
1. **Low Opportunity ($\Delta_{\rm oracle} < 0.005$):**
   - **Case ID:** `g24_w8_h4_f8__s2__e0.001`
   - **File:** `g24_w8_h4_f8__s2__e0.001_trace.csv`
   - **Config:** STFT `g24_w8_h4_f8` (window=8, hop=4, fft=8)
   - **Seed:** `2`
   - **Initial Error Level ($\epsilon$):** `0.001`
   - **Oracle $\lambda_+$:** `0.9999802815490957`
   - **$\Delta_{\rm oracle}^{\rm obs}$:** `0.0012314`
   - **Maturation Horizon ($T_{1\%}$):** Iteration `12`

2. **Medium Opportunity ($0.005 \le \Delta_{\rm oracle} < 0.02$):**
   - **Case ID:** `h24_w8_h4_f8__s0__e1e-05`
   - **File:** `h24_w8_h4_f8__s0__e1e-05_trace.csv`
   - **Config:** STFT `h24_w8_h4_f8` (window=8, hop=4, fft=8)
   - **Seed:** `0`
   - **Initial Error Level ($\epsilon$):** `1e-05`
   - **Oracle $\lambda_+$:** `0.9997290021630232`
   - **$\Delta_{\rm oracle}^{\rm obs}$:** `0.0062387`
   - **Maturation Horizon ($T_{1\%}$):** Iteration `12`

3. **High Opportunity ($\Delta_{\rm oracle} \ge 0.02$):**
   - **Case ID:** `g32_w16_h4_f16__s1__e0.001`
   - **File:** `g32_w16_h4_f16__s1__e0.001_trace.csv`
   - **Config:** STFT `g32_w16_h4_f16` (window=16, hop=4, fft=16)
   - **Seed:** `1`
   - **Initial Error Level ($\epsilon$):** `0.001`
   - **Oracle $\lambda_+$:** `0.991704965416071`
   - **$\Delta_{\rm oracle}^{\rm obs}$:** `0.0322869`
   - **Maturation Horizon ($T_{1\%}$):** Iteration `12`

**Deterministic Selection Logic:**
The three cases were selected as the first audited run in each opportunity tier encountered in the canonical multi-horizon adaptation ledger (`maturation_ledger.csv`), ensuring zero cherry-picking.

---

## 3. Machine-Readable Schema of Per-Iteration Traces
Each trace file records 180 iterations of the Online algorithm with the passive Ritz estimator:
- `iteration` (int): Algorithm iteration index ($k = 0, \dots, 180$).
- `lambda_hat_raw` (float / null during warmup): Raw Ritz eigenvalue estimate $\hat{\lambda}_+$ from order-$p$ Krylov subspace ($p=3$, warmup=12).
- `lambda_hat_envelope` (float / null during warmup): Stabilized dynamic envelope $\lambda_{\rm env}$ preventing instantaneous downward degradation.
- `lambda_plus_oracle` (float): Exact theoretical transverse spectral radius $\lambda_+$ computed from full Jacobian.
- `edge_rel_error` (float): $|\lambda_{\rm env} - \lambda_+| / \lambda_+$.
- `alpha` (float): Adaptive momentum parameter computed from $\hat{\lambda}_+$.
- `beta` (float): Adaptive feedback parameter.
- `gamma` (float): Adaptive step scale.
- `safeguard_accept` (bool): Whether the candidate spectral estimate passed the Rayleigh quotient and contraction safeguards.
- `orbit_error` (float): Orbit distance $\|c_k - c^*\|_2$.

---

## 4. Full Audit Population (12 Cases)
All 12 audited cases are preserved under `traces/`:
- `g16_w8_h4_f8__s1__e0.0001_trace.csv`
- `g16_w8_h4_f8__s3__e0.001_trace.csv`
- `g24_w8_h4_f8__s0__e0.0001_trace.csv`
- `g24_w8_h4_f8__s2__e0.001_trace.csv`
- `g32_w16_h4_f16__s0__e0.001_trace.csv`
- `g32_w16_h4_f16__s1__e0.001_trace.csv`
- `h16_w8_h4_f8__s3__e1e-05_trace.csv`
- `h24_w8_h4_f8__s0__e1e-05_trace.csv`
- `h24_w8_h4_f8__s2__e0.001_trace.csv`
- `h24_w8_h4_f8__s3__e0.001_trace.csv`
- `h32_w16_h4_f16__s2__e1e-05_trace.csv`
- `h32_w16_h4_f16__s4__e0.001_trace.csv`
