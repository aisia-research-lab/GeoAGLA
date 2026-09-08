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
