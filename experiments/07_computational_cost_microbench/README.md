# 07. Computational Cost & Isolated Microbenchmarks

Scripts evaluating execution overhead, profiling Ritz iterations, and decoupling algorithmic cost from OS-level load:
- `01_computational_cost_and_crosscheck.py`: Complete pipeline timing and crosscheck audit.
- `02_runtime_provenance_and_profiling.py`: High-resolution profiling across signal lengths and iterations.
- `03_isolated_ritz_microbench.py`: Isolated benchmarking of the 3x3 Rayleigh-Ritz eigensolver showing ~0.038 ms/update (0.0048 ms/iteration, ~0.28% overhead).
