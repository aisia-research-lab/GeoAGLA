import numpy as np
from pathlib import Path
from scipy.io import wavfile
from experiments.phase2b_real_audio.run import load_audio, _max_rms_excerpt

def test_max_rms_excerpt_prefers_active_region():
    x=np.zeros(1000); x[400:600]=1
    y,s=_max_rms_excerpt(x,200)
    assert y.shape==(200,)
    assert np.mean(y*y)>.9

def test_load_audio_resamples_and_normalizes(tmp_path: Path):
    fs=8000; t=np.arange(4000)/fs; x=.5*np.sin(2*np.pi*440*t)
    p=tmp_path/'a.wav'; wavfile.write(p,fs,np.int16(x*32767))
    y,m=load_audio(p,16000,1024)
    assert len(y)==1024
    assert abs(np.linalg.norm(y)-1)<1e-10
    assert m['target_sample_rate']==16000
