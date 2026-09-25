# Reproduce Package: One-Command Reproduction Scripts

The `reproduce/` package provides standalone, one-command CLI runners for each experiment in the **ICLR 2027 Experimental Protocol**:
**S0, E1, E2, E3, E4, E5, E6, E7, E10**, as well as the master end-to-end pipeline and manuscript verification scripts.

---

## 1. Canonical Experiment Launchers (S0, E1–E7, E10)

| Experiment | Script | Description |
| :--- | :--- | :--- |
| **S0** | `run_s0_linear_modal.py` | Linear modal dynamics smoke test (scalar recurrence $\rho = \lambda_+$). |
| **E1** | `run_e1_geometry_spectrum.py` | Geometry-spectrum correspondence ($\cos^2\theta \leftrightarrow \lambda_\pm$). |
| **E2** | `run_e2_oracle_rates.py` | Local rate prediction (GLA < FGLA < Oracle minimax rate $\rho^*$). |
| **E3** | `run_e3_ritz_estimator.py` | Passive Rayleigh-Ritz dominant-edge tracking ($p \in \{1, 3, 5\}$). |
| **E4** | `run_e4_online_horizon.py` | Online dynamics, safeguarding & finite-horizon adaptation ($H \in \{30, 60, 120, 200, 360\}$). |
| **E5** | `run_e5_real_audio_basin.py` | Real-audio basin transfer and robustness across MUSAN recordings. |
| **E6** | `run_e6_gate_a_heldout.py` | Geometry-opportunity Gate A 90-case ledger, 36 held-out cases & neutral mode audit. |
| **E7** | `run_e7_microbench.py` | Computational cost microbenchmarking (isolated $3 \times 3$ Ritz eigensolver). |
| **E10** | `run_e10_mechanism_ablation.py` | Robustness mechanism ablation suite (E10, E10-R locked, E10-R2 canonical, E10-R2F archive). |

---

## 2. Master Execution & Verification Scripts

| Target | Script | Description |
| :--- | :--- | :--- |
| **Full Suite** | `run_all_experiments.py` | Master end-to-end execution running S0, E1-E7, E10 in sequence (~47s). |
| **Publication Figures** | `run_verification_and_figures.py` | Reproduces publication panels A-D (400 DPI) and validates 20/20 numerical claims. |
| **Final Freeze** | `run_final_freeze_reconciliation.py` | Final scientific freeze reconciliation & 16-item diagnostic checklist verification. |
| **Long Horizon** | `run_final_patch_horizon_audit.py` | Near-neutral patch and 29-case long-horizon audit ($H \in \{360, 720, 1440\}$). |

---

## 3. Legacy Phase Aliases (Maintained for Backward Compatibility)

For reproducibility across existing notebooks and historical run logs:
- `run_phase1b.py`: Linear modal dynamics + H1 + H2.
- `run_phase1c.py`: Multi-STFT grid sweep.
- `run_phase1d.py`: Online Ritz dominant-edge tracking.
- `run_phase1e.py`: Safeguarded online acceleration.
- `run_phase1er.py`: Horizon policy switching & envelope damping.
- `run_phase2a.py`: Operator isometry & synthetic transfer.
- `run_phase2b_smoke.py`: Fast 15s smoke test without external audio.
- `run_phase2b_checkpointed.py`: Resumable batch runner with deadline control.
- `run_e10_ablation.py`: E10 6-variant ablation runner.
- `run_e10r_locked.py`: E10-R locked evaluation runner.
- `run_e10r2f_archive.py`: E10-R2F forensic archive runner.

---

## 4. Usage Examples

```bash
# Run Experiment S0:
python reproduce/run_s0_linear_modal.py

# Run Experiment E1:
python reproduce/run_e1_geometry_spectrum.py

# Run Experiment E2:
python reproduce/run_e2_oracle_rates.py

# Run Experiment E3:
python reproduce/run_e3_ritz_estimator.py

# Run Experiment E4:
python reproduce/run_e4_online_horizon.py

# Run Experiment E5 (Synthetic isometry test):
python reproduce/run_e5_real_audio_basin.py --stft-fft

# Run Experiment E6 (Gate A step 1):
python reproduce/run_e6_gate_a_heldout.py --step 1

# Run Experiment E7:
python reproduce/run_e7_microbench.py

# Run Experiment E10 (Forensic archive):
python reproduce/run_e10_mechanism_ablation.py --archive

# Run Complete End-to-End Suite:
python reproduce/run_all_experiments.py

# Re-generate Publication Figures and Verify Paper Numbers:
python reproduce/run_verification_and_figures.py
```
