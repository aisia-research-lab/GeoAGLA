# Neutral-Mode Exactness Audit --- Final Targeted Test v1
## ICLR 2027: Geometry Determines Acceleration in Phase Retrieval

### Overview
Targeted diagnostic package auditing the two MUSAN real-audio cases exhibiting `neutral_count_topk = 2` at `phase_tol = 1e-7`:
- `noise-free-sound-0043.wav`
- `noise-free-sound-0389.wav`

### Summary of Findings
- **noise-free-sound-0043.wav**: Verdict `OUTCOME_B_NEAR_NEUTRAL_TRANSVERSE_MODE`. Gap 1 = 3.30e-14, Gap 2 = 5.04e-08. Subspace phase alignment = 1.0000.
- **noise-free-sound-0389.wav**: Verdict `OUTCOME_B_NEAR_NEUTRAL_TRANSVERSE_MODE`. Gap 1 = 2.44e-15, Gap 2 = 9.72e-08. Subspace phase alignment = 1.0000.
