# 04. Neutral Mode Exactness Audit

Audit scripts verifying that the leading eigenvalue of the linearized GLA operator is identically 1.0 (phase gauge symmetry) and that the sub-dominant mode is strictly separated by the spectral gap:
- `01_run_neutral_mode_audit.py`: Full neutral mode tolerance sweep and solver stability audit across audio signals.
