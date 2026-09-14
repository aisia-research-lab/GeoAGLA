# 03. Geometry Opportunity & Gate A Heldout Evaluation (E6)

This directory implements the full Gate A evaluation pipeline:
- `01_build_e6_ledger.py`: Builds E6 case ledger from STFT parameter grid.
- `02_analyze_geometry_opportunity.py`: Computes Oracle opportunity Delta_oracle and rank correlation with geometric indicators.
- `03_freeze_heldout_grid.py`: Creates frozen hash-verified manifest for heldout evaluation.
- `04_run_heldout_experiments.py`: Runs execution over heldout configurations.
- `05_validate_results.py`: Runs integrity verification and assertion checks.
- `06_make_tables.py`: Generates publication LaTeX tables.
- `07_generate_gate_a_report.py`: Compiles summary audit report.
- `common.py`: Shared utilities for evaluation and metric computation.
