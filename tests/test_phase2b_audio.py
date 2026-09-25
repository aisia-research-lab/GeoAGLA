import numpy as np
from pathlib import Path
from scipy.io import wavfile
import sys
import tempfile

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root / "src") not in sys.path:
    sys.path.insert(0, str(_repo_root / "src"))

from geometry_gla.signals import load_audio, _max_rms_excerpt


def test_max_rms_excerpt_prefers_active_region():
    x = np.zeros(1000)
    x[400:600] = 1.0
    y, s = _max_rms_excerpt(x, 200)
    assert y.shape == (200,)
    assert np.mean(y * y) > 0.9
    assert 350 <= s <= 450


def _run_test_load_audio(tmp_dir: Path):
    fs = 8000
    t = np.arange(4000) / fs
    x = 0.5 * np.sin(2 * np.pi * 440 * t)
    p = tmp_dir / "test_a.wav"
    wavfile.write(p, fs, np.int16(x * 32767))

    y, m = load_audio(p, 16000, 1024)
    assert len(y) == 1024
    assert abs(np.linalg.norm(y) - 1.0) < 1e-10
    assert m["target_sample_rate"] == 16000
    assert m["excerpt_length"] == 1024


def test_load_audio_resamples_and_normalizes(tmp_path: Path | None = None):
    if tmp_path is None:
        with tempfile.TemporaryDirectory() as td:
            _run_test_load_audio(Path(td))
    else:
        _run_test_load_audio(tmp_path)
