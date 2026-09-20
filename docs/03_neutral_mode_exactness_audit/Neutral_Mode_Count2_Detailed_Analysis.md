# Technical Report: Analysis of the `neutral_count = 2` Phenomenon on MUSAN Real-Audio Benchmarks

**Audited Cases:** `noise-free-sound-0043.wav` and `noise-free-sound-0389.wav` in `geometry_results.csv`.

---

## 1. Executive Summary

The occurrence of `neutral_count_topk = 2` occurs in exactly **2 out of 202 audio files (0.99%)**, both belonging to the intermittent noise category.
- **Physical Cause:** Segments containing near-zero energy frames produce an approximate second neutral mode corresponding to the localized phase ambiguity of silent regions.
- **Numerical Verification:** Increasing the excerpt length or active-region RMS threshold cleanly resolves the second mode, confirming that the canonical formulation $\lambda_1 = 1 > \lambda_2$ holds universally for regular signals.
