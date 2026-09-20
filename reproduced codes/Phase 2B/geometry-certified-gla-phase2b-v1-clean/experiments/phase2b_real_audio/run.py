from __future__ import annotations
import argparse, csv, json, math, time
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import resample_poly

from geometry_gla.operators.stft import hann_window, gaussian_window
from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.geometry.matrixfree import top_transverse_spectrum, principal_angle_power_check
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.metrics.phase import orbit_distance


def _window(kind: str, n: int):
    return gaussian_window(n) if kind == 'gaussian' else hann_window(n)


def _to_float(raw: np.ndarray) -> np.ndarray:
    a = np.asarray(raw)
    if a.ndim > 1:
        a = np.mean(a.astype(np.float64), axis=1)
    else:
        a = a.astype(np.float64)
    if np.issubdtype(raw.dtype, np.integer):
        info = np.iinfo(raw.dtype)
        scale = max(abs(info.min), abs(info.max))
        a /= max(float(scale), 1.0)
    return a


def _resample(x: np.ndarray, fs: int, target_fs: int) -> np.ndarray:
    if fs == target_fs:
        return np.asarray(x, float)
    g = math.gcd(int(fs), int(target_fs))
    return resample_poly(x, target_fs // g, fs // g)


def _max_rms_excerpt(x: np.ndarray, N: int) -> tuple[np.ndarray, int]:
    x = np.asarray(x, float)
    if len(x) < N:
        y = np.zeros(N, float); y[:len(x)] = x
        return y, 0
    hop = max(1, N // 4)
    starts = list(range(0, len(x) - N + 1, hop))
    if starts[-1] != len(x)-N:
        starts.append(len(x)-N)
    best_s, best_e = 0, -1.0
    for s in starts:
        z = x[s:s+N]
        e = float(np.mean(z*z))
        if e > best_e:
            best_s, best_e = s, e
    return x[best_s:best_s+N].copy(), best_s


def load_audio(path: Path, target_fs: int, N: int):
    fs, raw = wavfile.read(path)
    x = _to_float(raw)
    x = _resample(x, int(fs), target_fs)
    x = x - float(np.mean(x))
    excerpt, start = _max_rms_excerpt(x, N)
    rms = float(np.sqrt(np.mean(excerpt**2)))
    peak = float(np.max(np.abs(excerpt))) if len(excerpt) else 0.0
    nrm = float(np.linalg.norm(excerpt))
    if nrm > 0:
        excerpt = excerpt / nrm
    return excerpt.astype(np.complex128), {
        'source_sample_rate': int(fs), 'target_sample_rate': int(target_fs),
        'source_num_samples': int(len(raw)), 'resampled_num_samples': int(len(x)),
        'excerpt_start_resampled': int(start), 'excerpt_length': int(N),
        'excerpt_rms_before_norm': rms, 'excerpt_peak_before_norm': peak,
    }


def _rate(errors, fraction=.35, floor=1e-11):
    e = np.asarray(errors, float)
    idx = np.where(np.isfinite(e) & (e > floor))[0]
    idx = idx[idx >= 5]
    if len(idx) < 10:
        return None
    n = max(10, int(np.ceil(fraction * len(idx))))
    sel = idx[-n:]
    slope, _ = np.polyfit(sel, np.log(e[sel]), 1)
    return float(np.exp(slope))


def _errors(tr, cstar):
    return np.asarray([orbit_distance(z, cstar) for z in tr], float)


def _magnitude_residual(c, s):
    return float(np.linalg.norm(np.abs(c)-s) / max(np.linalg.norm(s), 1e-15))


def _fixed(c0, cstar, s, op, pars, n_iter, frac, floor):
    tr = run_agla_state(c0, c0, s, op, pars['alpha'], pars['beta'], pars['gamma'], n_iter)
    er = _errors(tr, cstar)
    return tr, er, _rate(er, frac, floor)


def _remove_phase_signal(z, xstar, op):
    zp = 1j * xstar * op.frame_sqrt
    zp /= max(np.linalg.norm(zp), 1e-15)
    z = z - zp * np.real(np.vdot(zp, z))
    return z / max(np.linalg.norm(z), 1e-15)


def _init_state(kind, level, seed, cstar, s, xstar, op):
    rng = np.random.default_rng(seed)
    if kind == 'transverse':
        z = rng.normal(size=op.signal_dim) + 1j*rng.normal(size=op.signal_dim)
        z = _remove_phase_signal(z, xstar, op)
        v = op.q_analyze(z); v /= max(np.linalg.norm(v), 1e-15)
        c0 = cstar + float(level)*v
    elif kind == 'phase_jitter':
        noise = rng.normal(size=cstar.size)
        # Remove mean phase shift so the perturbation is transverse to global phase at first order.
        w = np.maximum(s, 1e-15)**2
        noise -= float(np.sum(w*noise)/np.sum(w))
        raw = s * np.exp(1j*(np.angle(cstar) + float(level)*noise))
        c0 = op.project_range(raw)
    else:
        raise ValueError(kind)
    return np.asarray(c0, np.complex128)


def _near_zero_stats(cstar, thresholds):
    a = np.abs(cstar); med = max(float(np.median(a)), 1e-15)
    out = {'min_abs_coeff': float(np.min(a)), 'median_abs_coeff': med,
           'min_rel_coeff': float(np.min(a)/med)}
    for t in thresholds:
        out[f'fraction_rel_below_{t:g}'] = float(np.mean(a < float(t)*med))
    return out


def _success(initial_error, final_error, final_mag_res, cfg):
    S = cfg['basin_success']
    return bool(final_error <= S['final_orbit_ratio_max']*max(initial_error,1e-15)
                and final_mag_res <= S['final_magnitude_residual_max'])


def run(audio_dir, config_path='configs/phase2b_grid.json', out_dir='results/phase2b', max_files=None):
    C = json.loads(Path(config_path).read_text())
    paths = sorted([p for p in Path(audio_dir).rglob('*') if p.is_file() and p.suffix.lower()=='.wav'])
    if max_files is None: max_files = C['max_files']
    paths = paths[:int(max_files)]
    if not paths:
        raise FileNotFoundError(f'No WAV files found in {audio_dir}')
    out = Path(out_dir); (out/'figures').mkdir(parents=True, exist_ok=True)
    manifest=[]; geometry=[]; basin=[]; traces=[]; t0_all=time.time()

    for fi, path in enumerate(paths):
        xstar, meta = load_audio(path, C['target_sample_rate'], C['excerpt_length'])
        manifest.append({'file': path.name, **meta})
        if np.linalg.norm(xstar) <= 1e-15:
            geometry.append({'file':path.name,'status':'SKIP_SILENT'}); continue
        for pi, P in enumerate(C['stft_profiles']):
            op = FFTAnalysisOperator(C['excerpt_length'], _window(P['window'],P['window_length']),P['hop'],P['n_fft'])
            cstar=op.analyze(xstar); s=np.abs(cstar); nz=_near_zero_stats(cstar,C['near_zero_thresholds'])
            regular = nz['min_rel_coeff'] > C['exact_zero_relative_tol']
            grow={'file':path.name,'profile':P['id'],'window':P['window'],'W':P['window_length'],'hop':P['hop'],'n_fft':P['n_fft'],**nz}
            if not regular:
                grow.update({'status':'SKIP_IRREGULAR','reason':'coefficient at/under exact-zero relative tolerance'})
                geometry.append(grow); continue
            try:
                spec=top_transverse_spectrum(cstar,op,k=C['eig_k'],phase_tol=C['phase_tol'],eig_tol=C['eig_tol'])
                lp=float(spec['lambda_plus'])
                geom=principal_angle_power_check(cstar,op,lp,seed=700+31*fi+pi,n_steps=C['power_steps'])
            except Exception as exc:
                grow.update({'status':'GEOMETRY_FAIL','reason':repr(exc)}); geometry.append(grow); continue
            grow.update({'status':'OK','neutral_count_topk':spec['neutral_count_topk'],'lambda_plus':lp,
                         'spectral_gap_to_phase':spec['spectral_gap_to_phase'],'geometry_lambda_power':geom['lambda_power'],
                         'geometry_rel_error':geom['relative_error']})
            geometry.append(grow)
            fg=fgla_opt(lp); oo=oracle_minimax(0.0,lp)
            for init in C['basin_initializations']:
                for level in init['levels']:
                    for seed in C['seeds']:
                        c0=_init_state(init['kind'],level,10000*fi+100*pi+10*seed+int(round(1000*level)),cstar,s,xstar,op)
                        init_err=float(orbit_distance(c0,cstar)); init_mag=_magnitude_residual(c0,s)
                        fgtr,fge,qf=_fixed(c0,cstar,s,op,fg,C['n_iter'],C['rate_tail_fraction'],C['rate_floor'])
                        otr,oe,qo=_fixed(c0,cstar,s,op,oo,C['n_iter'],C['rate_tail_fraction'],C['rate_floor'])
                        rr=run_online_policy(c0,c0,s,op,n_iter=C['n_iter'],warmup=C['warmup'],block_size=C['block_size'],memory=C['memory'],margin=C['margin'],lambda_ceiling=C['lambda_ceiling'],svd_rtol=C['svd_rtol'],cond_max=C['cond_max'],alpha_safe=C['alpha_safe'],beta_safe=C['beta_safe'],gamma_safe=C['gamma_safe'],K_safe=C['K_safe'],descent_a=C['descent_a'],policy='dynamic_envelope')
                        one=_errors(rr['trajectory'],cstar); qn=_rate(one,C['rate_tail_fraction'],C['rate_floor'])
                        blocks=rr['blocks']; late=blocks[-min(C['late_block_count'],len(blocks)):]
                        edges=np.asarray([b['edge_state'] for b in blocks if b.get('edge_state') is not None],float)
                        fm_on=_magnitude_residual(rr['trajectory'][-1],s); fm_fg=_magnitude_residual(fgtr[-1],s); fm_or=_magnitude_residual(otr[-1],s)
                        son=_success(init_err,float(one[-1]),fm_on,C); sfg=_success(init_err,float(fge[-1]),fm_fg,C); sor=_success(init_err,float(oe[-1]),fm_or,C)
                        row={'file':path.name,'profile':P['id'],'init_kind':init['kind'],'level':float(level),'seed':int(seed),
                             'lambda_plus':lp,'spectral_gap_to_phase':spec['spectral_gap_to_phase'],'initial_orbit_error':init_err,'initial_magnitude_residual':init_mag,
                             'q_online':qn,'q_fgla':qf,'q_oracle0':qo,'q_ratio_online_fgla':float(qn/qf) if qn and qf else None,
                             'beats_fgla':bool(qn and qf and qn<qf),'final_orbit_online':float(one[-1]),'final_orbit_fgla':float(fge[-1]),'final_orbit_oracle':float(oe[-1]),
                             'final_mag_online':fm_on,'final_mag_fgla':fm_fg,'final_mag_oracle':fm_or,'success_online':son,'success_fgla':sfg,'success_oracle':sor,
                             'reject_fraction':float(np.mean([not b['candidate_accepted'] for b in blocks])) if blocks else 0.0,
                             'late_reject_fraction':float(np.mean([not b['candidate_accepted'] for b in late])) if late else 0.0,
                             'fallback_e1_failures':int(sum(not b['fallback_e1_pass'] for b in blocks if not b['candidate_accepted'])),
                             'final_edge_rel_error':float(abs(edges[-1]-lp)/lp) if len(edges) else None,
                             'median_edge_rel_error_last5':float(np.median(np.abs(edges[-5:]-lp)/lp)) if len(edges) else None}
                        basin.append(row)
                        if len(traces)<6:
                            traces.append({'label':f"{path.name}/{P['id']}/{init['kind']}/{level:g}/s{seed}",'online':one.tolist(),'fgla':fge.tolist(),'oracle':oe.tolist()})
            print('Phase-2B',path.name,P['id'],'lambda+',round(lp,8),'geom',geom['relative_error'])

    (out/'audio_manifest.json').write_text(json.dumps(manifest,indent=2))
    (out/'geometry_results.json').write_text(json.dumps(geometry,indent=2,allow_nan=True))
    (out/'basin_results.json').write_text(json.dumps(basin,indent=2,allow_nan=True))
    for name, rows in [('geometry_results.csv',geometry),('basin_results.csv',basin)]:
        if rows:
            with (out/name).open('w',newline='') as f:
                fields=sorted(set().union(*(r.keys() for r in rows))); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    gok=[r for r in geometry if r.get('status')=='OK']
    if not gok:
        summary={'phase2b_gate':'RED','reason':'no regular real-audio geometry cases','n_files':len(paths)}
        (out/'summary.json').write_text(json.dumps(summary,indent=2)); return summary
    paired=[r for r in basin if r['success_online'] and r['success_fgla'] and r['q_ratio_online_fgla'] is not None]
    small=[r for r in basin if (r['init_kind']=='transverse' and r['level']<=0.01) or (r['init_kind']=='phase_jitter' and r['level']<=0.15)]
    ratios=np.asarray([r['q_ratio_online_fgla'] for r in paired],float) if paired else np.asarray([])
    edges=np.asarray([r['final_edge_rel_error'] for r in basin if r['final_edge_rel_error'] is not None],float)
    G=C['gates']
    geom_max=float(np.max([r['geometry_rel_error'] for r in gok]))
    edge_med=float(np.median(edges)) if edges.size else float('inf')
    small_succ=float(np.mean([r['success_online'] for r in small])) if small else 0.0
    on_succ=float(np.mean([r['success_online'] for r in basin])) if basin else 0.0
    fg_succ=float(np.mean([r['success_fgla'] for r in basin])) if basin else 0.0
    beat=float(np.mean([r['beats_fgla'] for r in paired])) if paired else 0.0
    medratio=float(np.median(ratios)) if ratios.size else float('inf')
    late=float(np.mean([r['late_reject_fraction'] for r in basin])) if basin else 1.0
    e1=int(sum(r['fallback_e1_failures'] for r in basin))
    passes={
        'G2B_A_real_audio_geometry_pass': bool(geom_max<=G['geometry_relative_error_max']),
        'G2B_B_active_edge_tracking_pass': bool(edge_med<=G['edge_relative_error_median_max']),
        'G2B_C_small_basin_pass': bool(small_succ>=G['small_basin_success_fraction_min']),
        'G2B_D_basin_nonshrink_pass': bool(on_succ+G['online_basin_deficit_vs_fgla_max']>=fg_succ),
        'G2B_E_paired_rate_pass': bool(len(paired)>0 and beat>=G['paired_success_online_beat_fraction_min'] and medratio<G['paired_success_median_q_ratio_max']),
        'G2B_F_safeguard_pass': bool(late<=G['late_reject_fraction_mean_max'] and e1<=G['fallback_e1_failures_max']),
    }
    summary={'profile':C['profile'],'n_files':len(paths),'n_geometry_cases':len(gok),'n_basin_runs':len(basin),'n_paired_success_runs':len(paired),
             'max_geometry_relative_error':geom_max,'median_final_edge_relative_error':edge_med,
             'small_basin_online_success_fraction':small_succ,'overall_online_success_fraction':on_succ,'overall_fgla_success_fraction':fg_succ,
             'paired_success_online_beat_fraction':beat,'paired_success_median_q_ratio':medratio,
             'paired_success_p90_q_ratio':float(np.percentile(ratios,90)) if ratios.size else None,
             'mean_late_reject_fraction':late,'fallback_e1_failures':e1,
             'near_phase_degenerate_fraction':float(np.mean([r['lambda_plus']>=0.9999 for r in gok])),
             **passes}
    summary['phase2b_gate']='GREEN' if all(passes.values()) else 'YELLOW'
    summary['runtime_sec']=float(time.time()-t0_all)
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=True))

    # Initialization summary for diagnosis.
    groups=[]
    for kind in sorted(set(r['init_kind'] for r in basin)):
        for level in sorted(set(r['level'] for r in basin if r['init_kind']==kind)):
            z=[r for r in basin if r['init_kind']==kind and r['level']==level]
            pair=[r for r in z if r['success_online'] and r['success_fgla'] and r['q_ratio_online_fgla'] is not None]
            groups.append({'init_kind':kind,'level':level,'n':len(z),'online_success_fraction':float(np.mean([r['success_online'] for r in z])),
                           'fgla_success_fraction':float(np.mean([r['success_fgla'] for r in z])),
                           'paired_beat_fraction':float(np.mean([r['beats_fgla'] for r in pair])) if pair else None,
                           'paired_median_q_ratio':float(np.median([r['q_ratio_online_fgla'] for r in pair])) if pair else None})
    (out/'initialization_summary.json').write_text(json.dumps(groups,indent=2,allow_nan=True))

    # Figures.
    labels=[f"{r['file']}\n{r['profile']}" for r in gok]
    x=np.arange(len(gok))
    fig,ax=plt.subplots(figsize=(max(8,1.1*len(gok)),4.8)); ax.bar(x,[r['geometry_rel_error'] for r in gok]); ax.axhline(G['geometry_relative_error_max'],linestyle='--'); ax.set_yscale('log'); ax.set_xticks(x,labels,rotation=35,ha='right'); ax.set_ylabel('relative error'); ax.set_title('2B-D1 — Real-audio tangent geometry transfer'); fig.tight_layout(); fig.savefig(out/'figures'/'2B_D1_real_audio_geometry.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.5,4.8));
    for kind in sorted(set(g['init_kind'] for g in groups)):
        z=[g for g in groups if g['init_kind']==kind]; ax.plot([g['level'] for g in z],[g['online_success_fraction'] for g in z],marker='o',label=f'{kind} online'); ax.plot([g['level'] for g in z],[g['fgla_success_fraction'] for g in z],marker='x',label=f'{kind} FGLA')
    ax.set_xscale('log'); ax.set_ylim(-.02,1.02); ax.set_xlabel('initialization level'); ax.set_ylabel('basin success fraction'); ax.set_title('2B-D2 — Real-audio basin profile'); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(out/'figures'/'2B_D2_basin_profile.png',dpi=180); plt.close(fig)
    if paired:
        fig,ax=plt.subplots(figsize=(7.5,4.8)); ax.hist([r['q_ratio_online_fgla'] for r in paired],bins=min(12,max(4,len(paired)//2))); ax.axvline(1.0,linestyle='--'); ax.set_xlabel('q_online / q_FGLA'); ax.set_ylabel('count'); ax.set_title('2B-D3 — Paired-success local rate transfer'); fig.tight_layout(); fig.savefig(out/'figures'/'2B_D3_rate_ratio.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5));
    for t in traces: ax.semilogy(t['online'],label=t['label'])
    ax.set_xlabel('iteration'); ax.set_ylabel('orbit error'); ax.set_title('2B-D4 — Representative safeguarded online trajectories'); ax.legend(fontsize=6); fig.tight_layout(); fig.savefig(out/'figures'/'2B_D4_trajectories.png',dpi=180); plt.close(fig)

    print(json.dumps(summary,indent=2)); return summary


def main():
    p=argparse.ArgumentParser(description='Phase-2B real-audio basin and geometry validation')
    p.add_argument('--audio-dir',required=True)
    p.add_argument('--config',default='configs/phase2b_grid.json')
    p.add_argument('--out',default='results/phase2b')
    p.add_argument('--max-files',type=int,default=None)
    a=p.parse_args(); run(a.audio_dir,a.config,a.out,a.max_files)

if __name__=='__main__': main()
