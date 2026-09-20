from pathlib import Path
import sys,argparse
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT,ROOT/'src'):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from experiments.phase2a_transfer.wav_run import run

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--audio-dir',required=True); p.add_argument('--max-files',type=int,default=4); p.add_argument('--N',type=int,default=2048); p.add_argument('--n-iter',type=int,default=360); a=p.parse_args()
    run(a.audio_dir,str(ROOT/'results'/'phase2a_real_audio'),a.max_files,a.N,a.n_iter)
