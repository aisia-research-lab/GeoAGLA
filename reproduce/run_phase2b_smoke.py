from __future__ import annotations
import importlib.util, json, sys, tempfile
from pathlib import Path
import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))

# Dynamic import of sweep module
_sweep_path = ROOT / "experiments" / "05_real_audio_basin_transfer" / "03_phase2b_real_audio_basin_sweep.py"
_spec = importlib.util.spec_from_file_location("phase2b_sweep", _sweep_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
run = _mod.run

def main():
    print("=== Phase-2B Smoke Test (Synthetic Dual-Signal) ===")
    fs = 16000
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        t = np.arange(8192) / fs
        x1 = 0.55 * np.sin(2 * np.pi * 220 * t) + 0.25 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.sin(2 * np.pi * 880 * t)
        x2 = np.sin(2 * np.pi * (120 * t + 350 * t * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 2 * t))
        wavfile.write(td / 'harmonic.wav', fs, np.int16(x1 / max(np.max(np.abs(x1)), 1e-9) * 32767))
        wavfile.write(td / 'chirp.wav', fs, np.int16(x2 / max(np.max(np.abs(x2)), 1e-9) * 32767))

        out = ROOT / 'results' / '02_phase2_transfer' / 'phase2b_smoke'
        res = run(str(td), str(ROOT / 'configs' / 'phase2b_grid.json'), str(out))
        print("Smoke test finished with gate:", res.get("phase2b_gate", "UNKNOWN"))

if __name__ == '__main__':
    main()
