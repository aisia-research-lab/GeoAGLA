from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
import numpy as np
from scipy.io import wavfile
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT/'src'):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from experiments.phase2b_real_audio.run import run

fs=16000
with tempfile.TemporaryDirectory() as td:
    td=Path(td); t=np.arange(8192)/fs
    x1=.55*np.sin(2*np.pi*220*t)+.25*np.sin(2*np.pi*440*t)+.1*np.sin(2*np.pi*880*t)
    x2=np.sin(2*np.pi*(120*t+350*t*t))*(.5+.5*np.sin(2*np.pi*2*t))
    wavfile.write(td/'smoke_harmonic.wav',fs,np.int16(np.clip(x1,-1,1)*32767))
    wavfile.write(td/'smoke_chirp.wav',fs,np.int16(np.clip(x2,-1,1)*32767))
    cfg=json.loads((ROOT/'configs/phase2b_grid.json').read_text())
    cfg['excerpt_length']=1024; cfg['max_files']=2; cfg['n_iter']=100; cfg['power_steps']=120
    cfg['stft_profiles']=[{'id':'smoke_hann','window':'hann','window_length':128,'hop':32,'n_fft':128}]
    cfg['basin_initializations']=[{'kind':'transverse','levels':[0.001]},{'kind':'phase_jitter','levels':[0.05]}]
    cfg['seeds']=[0]
    cfg['gates']['paired_success_online_beat_fraction_min']=0.0
    cfg['gates']['small_basin_success_fraction_min']=0.0
    cp=td/'smoke.json'; cp.write_text(json.dumps(cfg,indent=2))
    run(td,cp,ROOT/'results/phase2b_smoke',max_files=2)
