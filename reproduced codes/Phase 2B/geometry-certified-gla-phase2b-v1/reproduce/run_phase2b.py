from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT/'src'):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from experiments.phase2b_real_audio.run import main
if __name__=='__main__': main()
