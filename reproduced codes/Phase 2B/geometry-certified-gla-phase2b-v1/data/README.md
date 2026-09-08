# Phase-2B real-audio input

Phase-2B intentionally does **not** ship third-party recordings. Put ordinary PCM WAV files in a local folder and pass that folder to the reproduction command. The engine converts stereo to mono, resamples to 16 kHz, removes the mean, selects a deterministic high-RMS excerpt, and normalizes its Euclidean norm.

Recommended first independent run: 4–6 speech/music recordings with diverse spectral structure and at least 0.5 s of non-silent audio each. Keep the original files unchanged; Phase-2B writes only derived numeric diagnostics to `results/phase2b/`.
