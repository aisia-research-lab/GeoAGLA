"""One-command Phase-2A controlled signal-scale reproduction.

This file bootstraps the repository root and src/ so it also works when executed
without editable installation.  This repairs the Phase-1E-R packaging defect.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT/'src'):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from experiments.phase2a_transfer.run import run

if __name__ == '__main__':
    run(str(ROOT/'configs'/'phase2a_grid.json'), str(ROOT/'results'/'phase2a'))
