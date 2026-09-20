# ICLR 2027 — Figure Reproduction Scripts

This package contains the Python scripts used in the M3/M4 manuscript
integration for:

1. `Figure_1_geometry_spectrum`
2. `Figure_2_predicted_observed_rates`
3. `Figure_3_estimator_maturation`
4. `Figure_4_rate_robustness`
5. `Figure_M4_composite_evidence`

## Scripts

- `make_publication_figures.py`
  - builds Figures 1, 2, and 4 from the frozen CSV ledgers;
  - copies the frozen audited Student-B estimator-maturation image as Figure 3.

- `make_composite_figure.py`
  - combines the four main figures into the 2x2 composite evidence figure
    used during M4 manuscript integration.

## Required Python packages

```bash
pip install pandas numpy matplotlib
```

## Required inputs

Expected relative paths:

```text
real_audio_audit/geometry_results.csv
real_audio_audit/rate_results.csv
C1_capture_ratio_audit.csv
Online Evaluator_Final_Freeze_Candidate_v1/
└── figures/
    └── Figure_B1_estimator_maturation_traces.png
```

If your folder structure differs, change the path constants at the top of
`make_publication_figures.py`.

## Run

```bash
python make_publication_figures.py
python make_composite_figure.py
```

Outputs are written to `publication_figures/`.

## Scientific provenance notes

- Figure 1 is generated directly from the frozen Student-A geometry ledger.
- Figure 2 is generated directly from the frozen Student-A predicted/observed
  rate ledger.
- Figure 3 deliberately uses the already-audited frozen Student-B maturation
  plot rather than regenerating it from an unspecified alternate trace set.
- Figure 4 recomputes the Online-vs-FGLA win rate directly from the canonical
  C1 ledger and uses the frozen basin-success values 74.94% and 54.87%.
- No parameter retuning, case filtering, or manual result editing is performed
  by these scripts.
