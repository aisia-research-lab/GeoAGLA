# Geometry-Certified Acceleration of Griffin–Lim Phase Retrieval

Reproducibility repository — **Phase-1C v1**.

This package contains the complete Phase-1B smoke-test engine plus the Phase-1C multi-instance H1/H2 verification grid.

Start here: [`PHASE1C_README.md`](PHASE1C_README.md).

Quick reproduction:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
python reproduce/run_phase1c.py
```

Phase-1B remains independently runnable with:

```bash
python reproduce/run_phase1b.py
```

---

## Phase-1D extension

The repository now includes `Phase-1D — Online Dominant Spectral-Edge Identification Engine v1`.
See `PHASE1D_README.md`, `PHASE1D_VERIFICATION_REPORT.md`, and `Phase-1D_Reproduction_Guide_v1.md`.

Run:

```bash
python reproduce/run_phase1d.py
```

## Phase-1E

Phase-1E adds a safeguarded online-λ+ acceleration prototype. The bundled v1
reference run is intentionally reported as **YELLOW**: checkpoint safety diagnostics
pass, while the frozen H4 online-vs-FGLA performance gate requires a repair cycle.
See `PHASE1E_VERIFICATION_REPORT.md`.

## Phase-1E-R

Phase-1E-R decomposes the online rate-realization delay without weakening the Phase-1E safeguard. Run `python reproduce/run_phase1er.py`. See `PHASE1ER_VERIFICATION_REPORT.md`.
