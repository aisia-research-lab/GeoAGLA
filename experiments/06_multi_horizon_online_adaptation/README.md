# 06. Multi-Horizon Online Adaptation & Scientific Audit Pipeline

This directory contains the sequential scripts establishing online adaptation, horizon sensitivity, and rigorous scientific reconciliation:
- `01_phase1d_online_edge_tracking.py`: Ritz eigensolver online tracking of the leading edge mode.
- `02_phase1e_safeguarded_acceleration.py`: Safe momentum acceleration with residual fallback triggers.
- `03_phase1er_repair_and_horizon_policy.py`: Failure mode decomposition and switching horizon policy.
- `04_estimator_maturation_sweep.py`: Online Ritz convergence delay (m* = 10..15) analysis.
- `05_multi_horizon_and_failure_taxonomy.py`: Multi-horizon (K=30, 50, 100, 200) evaluation and failure classification.
- `06_signal_scale_validation.py`: Scale-invariance evaluation under dynamic ranges.
- `07_c1_canonical_capture_ratio_audit.py`: Canonical 60-eval C1 audit under exact condition q_online < q_fgla.
- `08_c2_signal_scale_censoring.py`: Censoring check for scale artifacts.
- `09_c4_claim_discipline_checker.py`: Claim consistency auditor.
- `10_package_and_report.py`: Bundle packager for scientific verification.
