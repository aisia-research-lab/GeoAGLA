"""Optional real-WAV extension for Phase-2A.

This is deliberately separate from the deterministic controlled gate. It uses a
short signal-scale excerpt from user-supplied WAV files and never downloads data.
"""
from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import argparse, json
from pathlib import Path
import numpy as np
from scipy.io import wavfile

from geometry_gla.operators.stft import hann_window
from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.geometry.matrixfree import top_transverse_spectrum, principal_angle_power_check
from geometry_gla.algorithms.minimax import fgla_opt
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.metrics.phase import orbit_distance


def _mono_float(path: Path):
    fs,raw=wavfile.read(path)
    raw=np.asarray(raw); dtype=raw.dtype
    if raw.ndim>1: x=np.mean(raw.astype(float),axis=1)
    else: x=raw.astype(float)
    if np.issubdtype(dtype, np.integer):
        mx=np.iinfo(dtype).max
        x=x/max(float(mx),1.0)
    x=x-np.mean(x)
    n=np.linalg.norm(x)
    return int(fs), x/n if n>0 else x


def _excerpt(x,N):
    if len(x)>=N:
        start=(len(x)-N)//2; return x[start:start+N]
    y=np.zeros(N,float); y[:len(x)]=x; return y


def _rate(e,fraction=.35,floor=1e-12):
    e=np.asarray(e,float); idx=np.where(np.isfinite(e)&(e>floor))[0]; idx=idx[idx>=5]
    if len(idx)<10:return None
    n=max(10,int(np.ceil(fraction*len(idx)))); sel=idx[-n:]
    return float(np.exp(np.polyfit(sel,np.log(e[sel]),1)[0]))


def run(audio_dir, out_dir='results/phase2a_real_audio', max_files=4, N=2048, n_iter=360):
    paths=sorted(Path(audio_dir).glob('*.wav'))[:max_files]
    if not paths: raise FileNotFoundError(f'no .wav files found in {audio_dir}')
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); rows=[]
    op=FFTAnalysisOperator(N,hann_window(256),32,256)
    for i,p in enumerate(paths):
        fs,x=_mono_float(p); x=_excerpt(x,N).astype(np.complex128); x/=max(np.linalg.norm(x),1e-15)
        cstar=op.analyze(x); med=max(float(np.median(np.abs(cstar))),1e-15); minrel=float(np.min(np.abs(cstar))/med)
        if minrel<=1e-12:
            rows.append({'file':p.name,'status':'SKIP_IRREGULAR','min_rel_coeff':minrel}); continue
        spec=top_transverse_spectrum(cstar,op,k=6,eig_tol=1e-9); lp=spec['lambda_plus']
        geom=principal_angle_power_check(cstar,op,lp,seed=100+i,n_steps=500)
        rng=np.random.default_rng(900+i); z=rng.normal(size=N)+1j*rng.normal(size=N)
        zph=1j*x*op.frame_sqrt; zph/=np.linalg.norm(zph); z-=zph*np.real(np.vdot(zph,z)); z/=np.linalg.norm(z)
        v=op.q_analyze(z); v/=np.linalg.norm(v); c0=cstar+1e-3*v; s=np.abs(cstar)
        fg=fgla_opt(lp); ftr=run_agla_state(c0,c0,s,op,fg['alpha'],0.0,1.0,n_iter); fe=np.asarray([orbit_distance(q,cstar) for q in ftr])
        rr=run_online_policy(c0,c0,s,op,n_iter=n_iter,warmup=12,block_size=8,memory=3,margin=0.0,policy='dynamic_envelope',alpha_safe=0,beta_safe=0,gamma_safe=1,K_safe=.25,descent_a=1e-4)
        oe=np.asarray([orbit_distance(q,cstar) for q in rr['trajectory']]); qf=_rate(fe); qo=_rate(oe); blocks=rr['blocks']; edges=[b['edge_state'] for b in blocks if b.get('edge_state') is not None]
        rows.append({'file':p.name,'status':'OK','sample_rate':fs,'N':N,'lambda_plus':lp,'geometry_rel_error':geom['relative_error'],'final_edge_rel_error':float(abs(edges[-1]-lp)/lp) if edges else None,'q_online':qo,'q_fgla':qf,'ratio':float(qo/qf) if qo and qf else None,'beats':bool(qo and qf and qo<qf),'late_reject_fraction':float(np.mean([not b['candidate_accepted'] for b in blocks[-10:]])),'fallback_e1_failures':int(sum(not b['fallback_e1_pass'] for b in blocks if not b['candidate_accepted']))})
        print('Phase-2A WAV',p.name,rows[-1])
    ok=[r for r in rows if r['status']=='OK']
    summary={'n_files':len(paths),'n_regular':len(ok),'beat_fraction':float(np.mean([r['beats'] for r in ok])) if ok else None,'median_ratio':float(np.median([r['ratio'] for r in ok])) if ok else None,'median_edge_rel_error':float(np.median([r['final_edge_rel_error'] for r in ok])) if ok else None,'max_geometry_rel_error':float(np.max([r['geometry_rel_error'] for r in ok])) if ok else None,'fallback_e1_failures':int(sum(r['fallback_e1_failures'] for r in ok))}
    (out/'wav_results.json').write_text(json.dumps(rows,indent=2)); (out/'summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2)); return summary


def main():
    p=argparse.ArgumentParser(); p.add_argument('--audio-dir',required=True); p.add_argument('--out',default='results/phase2a_real_audio'); p.add_argument('--max-files',type=int,default=4); p.add_argument('--N',type=int,default=2048); p.add_argument('--n-iter',type=int,default=360); a=p.parse_args(); run(a.audio_dir,a.out,a.max_files,a.N,a.n_iter)
if __name__=='__main__': main()