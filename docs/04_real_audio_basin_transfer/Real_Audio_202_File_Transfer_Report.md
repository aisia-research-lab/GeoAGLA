# Real-Audio 202-File Transfer Report: Population-Scale Basin Evaluation

### Project: *Geometry Determines Acceleration in Phase Retrieval* (ICLR 2027)
### Dataset: MUSAN (Speech, Music, Noise; 202 files, seed 42)

---

## 1. Executive Summary

This report documents the population-scale evaluation across all **202 real-audio files** (54 Music, 44 Speech, 104 Noise) under deterministic STFT profiles.

1. **Theorem 2 (Geometry--Spectrum Correspondence):**
   - Dominant transverse edge matches principal angle cosines with median relative error $1.4439 \times 10^{-3}$ and maximum error $2.8971 \times 10^{-3}$.
2. **Theorem 8 (Rate Hierarchy):**
   - Acceleration hierarchy holds on 173/202 files at $H=360$, and 188/202 at $H=720$.
3. **Basin Robustness:**
   - Online adaptation increases convergence success across random initializations from $54.87\%$ to $74.94\%$ ($+20.07$ percentage points).
