import numpy as np

from experiments.common import preprocess_audio
from geometry_gla.signals import make_signal


def test_synthetic_signal_shape_and_unit_norm():
    x = make_signal("chirp", 256, seed=0)
    assert x.shape == (256,)
    assert np.isfinite(x).all()
    assert abs(np.linalg.norm(x) - 1.0) < 1e-10


def test_preprocess_audio_crops_and_normalizes():
    rng = np.random.default_rng(0)
    raw = rng.normal(size=(8192, 2))
    out = preprocess_audio(raw, sr=16000, excerpt_len=4096)
    assert out.shape == (4096,)
    assert abs(np.linalg.norm(out) - 1.0) < 1e-12


def test_audio_loader_rejects_hash_mismatch():
    import json
    import tempfile
    from pathlib import Path

    from experiments.common import INPUT_DIR, load_audio_records

    first = json.loads((INPUT_DIR / "manifest.json").read_text(encoding="utf-8"))[0]
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / first["path"]).write_bytes(b"not the audited audio file")
        try:
            next(load_audio_records(tmp))
        except ValueError as err:
            assert "SHA256 mismatch" in str(err)
        else:
            raise AssertionError("tampered audio was accepted")
