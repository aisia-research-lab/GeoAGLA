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
