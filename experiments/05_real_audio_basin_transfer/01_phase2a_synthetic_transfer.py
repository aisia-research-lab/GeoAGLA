from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import argparse, csv, json, time
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from geometry_gla.operators.stft import hann_window, gaussian_window
from geometry_gla.operators.stft_fft import FFTAnalysisOperator
from geometry_gla.geometry.matrixfree import top_transverse_spectrum, principal_angle_power_check
from geometry_gla.signals import make_signal
from geometry_gla.algorithms.minimax import fgla_opt, oracle_minimax
from geometry_gla.algorithms.agla import run_agla_state
from geometry_gla.algorithms.online_safe import run_online_policy
from geometry_gla.metrics.phase import orbit_distance


def _window(kind, n):
    return gaussian_window(n) if kind == "gaussian" else hann_window(n)


def _rate(errors, fraction=.35, floor=1e-12):
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


def _fixed(c0, cstar, s, op, pars, n_iter, frac, floor):
    tr = run_agla_state(c0, c0, s, op, pars['alpha'], pars['beta'], pars['gamma'], n_iter)
    er = _errors(tr, cstar)
    return tr, er, _rate(er, frac, floor)


def _regularity(cstar, rel_tol):
    a = np.abs(cstar)
    scale = max(float(np.median(a)), 1e-15)
    return float(np.min(a)), float(np.min(a)/scale), bool(np.min(a) > rel_tol*scale)


def _case_signal(cfg, fs):
    x = make_signal(cfg['signal'], cfg['signal_length'], cfg['seed'], fs)
    return np.asarray(x, np.complex128)


def run(config_path='configs/phase2a_grid.json', out_dir='results/phase2a'):
    C = json.loads(Path(config_path).read_text())
    out = Path(out_dir); (out/'figures').mkdir(parents=True, exist_ok=True)
    rows=[]; horizon_rows=[]; traces=[]; t0_all=time.time()

    for cfg in C['cases']:
        t0=time.time()
        op = FFTAnalysisOperator(cfg['signal_length'], _window(cfg['window'], cfg['window_length']), cfg['hop'], cfg['n_fft'])
        xstar = _case_signal(cfg, C['sample_rate'])
        cstar = op.analyze(xstar); s=np.abs(cstar)
        minmag, minrel, regular = _regularity(cstar, C['near_zero_relative_tol'])
        if not regular:
            rows.append({'case':cfg['id'],'status':'SKIP_IRREGULAR','min_abs_coeff':minmag,'min_rel_coeff':minrel})
            print('Phase-2A SKIP irregular', cfg['id']); continue

        spec = top_transverse_spectrum(cstar, op, k=C['eig_k'], phase_tol=C['phase_tol'], eig_tol=C['eig_tol'])
        lp=float(spec['lambda_plus'])
        geom = principal_angle_power_check(cstar, op, lp, seed=cfg['seed']+101, n_steps=C['power_steps'])

        # Isometric random transverse perturbation; explicitly remove phase orbit direction.
        rng=np.random.default_rng(cfg['seed']+202)
        z=rng.normal(size=op.signal_dim)+1j*rng.normal(size=op.signal_dim)
        zphase=1j*xstar*op.frame_sqrt; zphase/=np.linalg.norm(zphase)
        z -= zphase*np.real(np.vdot(zphase,z)); z/=np.linalg.norm(z)
        v=op.q_analyze(z); v/=np.linalg.norm(v)

        for eps in C['perturbations']:
            c0=cstar+eps*v
            fg=fgla_opt(lp); oo=oracle_minimax(0.0,lp)
            fgtr,fge,qf=_fixed(c0,cstar,s,op,fg,C['n_iter'],C['rate_tail_fraction'],C['rate_floor'])
            otr,oe,qo=_fixed(c0,cstar,s,op,oo,C['n_iter'],C['rate_tail_fraction'],C['rate_floor'])
            rr=run_online_policy(c0,c0,s,op,n_iter=C['n_iter'],warmup=C['warmup'],block_size=C['block_size'],memory=C['memory'],margin=C['margin'],lambda_ceiling=C['lambda_ceiling'],svd_rtol=C['svd_rtol'],cond_max=C['cond_max'],alpha_safe=C['alpha_safe'],beta_safe=C['beta_safe'],gamma_safe=C['gamma_safe'],K_safe=C['K_safe'],descent_a=C['descent_a'],policy='dynamic_envelope')
            one=_errors(rr['trajectory'],cstar); qonline=_rate(one,C['rate_tail_fraction'],C['rate_floor'])
            blocks=rr['blocks']; late=blocks[-min(C['late_block_count'],len(blocks)):]
            edges=np.asarray([b['edge_state'] for b in blocks if b.get('edge_state') is not None],float)
            row={
                'case':cfg['id'],'status':'OK','signal':cfg['signal'],'N':cfg['signal_length'],'window':cfg['window'],'W':cfg['window_length'],'hop':cfg['hop'],'n_fft':cfg['n_fft'],'epsilon':eps,
                'min_abs_coeff':minmag,'min_rel_coeff':minrel,'neutral_count_topk':spec['neutral_count_topk'],'lambda_plus':lp,'spectral_gap_to_phase':spec['spectral_gap_to_phase'],
                'geometry_lambda_power':geom['lambda_power'],'geometry_rel_error':geom['relative_error'],
                'final_edge_rel_error':float(abs(edges[-1]-lp)/lp) if len(edges) else None,'median_edge_rel_error_last5':float(np.median(np.abs(edges[-5:]-lp)/lp)) if len(edges) else None,
                'q_fgla':qf,'q_oracle0':qo,'q_online':qonline,'q_ratio_online_fgla':float(qonline/qf) if qonline and qf else None,'beats_fgla':bool(qonline and qf and qonline<qf),
                'reject_fraction':float(np.mean([not b['candidate_accepted'] for b in blocks])) if blocks else 0.0,
                'late_reject_fraction':float(np.mean([not b['candidate_accepted'] for b in late])) if late else 0.0,
                'fallback_e1_failures':int(sum(not b['fallback_e1_pass'] for b in blocks if not b['candidate_accepted'])),
                'final_error_online':float(one[-1]),'final_error_fgla':float(fge[-1]),'final_error_oracle':float(oe[-1]),
                'runtime_sec':float(time.time()-t0)
            }
            rows.append(row)
            for H in C['horizons']:
                if H > C['n_iter']: continue
                qo_h=_rate(oe[:H+1],C['rate_tail_fraction'],C['rate_floor'])
                qf_h=_rate(fge[:H+1],C['rate_tail_fraction'],C['rate_floor'])
                qn_h=_rate(one[:H+1],C['rate_tail_fraction'],C['rate_floor'])
                horizon_rows.append({'case':cfg['id'],'epsilon':eps,'n_iter':H,'q_online':qn_h,'q_fgla':qf_h,'q_oracle0':qo_h,'ratio':float(qn_h/qf_h) if qn_h and qf_h else None,'beats':bool(qn_h and qf_h and qn_h<qf_h)})
            if len(traces)<4:
                traces.append({'case':cfg['id'],'online':one.tolist(),'fgla':fge.tolist(),'oracle':oe.tolist(),'blocks':blocks})
        print('Phase-2A',cfg['id'],'lambda+',lp,'geom err',geom['relative_error'],'time',round(time.time()-t0,2),'s')

    ok=[r for r in rows if r.get('status')=='OK']
    if not ok:
        raise RuntimeError('no regular Phase-2A cases completed')
    ratios=np.asarray([r['q_ratio_online_fgla'] for r in ok if r['q_ratio_online_fgla'] is not None])
    edge=np.asarray([r['final_edge_rel_error'] for r in ok if r['final_edge_rel_error'] is not None])
    geomerr=np.asarray([r['geometry_rel_error'] for r in ok])
    G=C['gates']
    g_geom=bool(np.max(geomerr)<=G['geometry_relative_error_max'])
    g_edge=bool(np.median(edge)<=G['edge_relative_error_median_max'])
    beat=float(np.mean([r['beats_fgla'] for r in ok]))
    medratio=float(np.median(ratios))
    g_perf=bool(beat>=G['online_beat_fraction_min'] and medratio<G['online_median_ratio_max'])
    late=float(np.mean([r['late_reject_fraction'] for r in ok])); e1=int(sum(r['fallback_e1_failures'] for r in ok))
    g_safe=bool(late<=G['late_reject_fraction_mean_max'] and e1<=G['fallback_e1_failures_max'])
    summary={
        'profile':C['profile'],'n_cases_total':len(C['cases']),'n_regular_runs':len(ok),'n_irregular_skipped':len(rows)-len(ok),
        'max_geometry_relative_error':float(np.max(geomerr)),'median_final_edge_relative_error':float(np.median(edge)),
        'online_beat_fraction_vs_fgla':beat,'median_q_ratio_online_vs_fgla':medratio,'p90_q_ratio_online_vs_fgla':float(np.percentile(ratios,90)),
        'mean_late_reject_fraction':late,'fallback_e1_failures':e1,
        'G2A_geometry_transfer_pass':g_geom,'G2B_active_edge_tracking_pass':g_edge,'G2C_online_rate_transfer_pass':g_perf,'G2D_safeguard_transfer_pass':g_safe,
        'phase2a_controlled_gate':'GREEN' if g_geom and g_edge and g_perf and g_safe else 'YELLOW',
        'real_audio_gate':'PENDING — default package uses deterministic license-free audio-like signals; run optional WAV extension before publication claims.',
        'runtime_sec':float(time.time()-t0_all)
    }
    (out/'case_results.json').write_text(json.dumps(rows,indent=2,allow_nan=True))
    (out/'horizon_audit.json').write_text(json.dumps(horizon_rows,indent=2,allow_nan=True))
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=True))
    with (out/'case_results.csv').open('w',newline='') as f:
        fields=sorted(set().union(*(r.keys() for r in rows))); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    # Aggregate horizon summary
    hs=[]
    for H in C['horizons']:
        z=[r for r in horizon_rows if r['n_iter']==H and r['ratio'] is not None]
        if z:
            hs.append({'n_iter':H,'n':len(z),'beat_fraction':float(np.mean([r['beats'] for r in z])),'median_ratio':float(np.median([r['ratio'] for r in z])),'p90_ratio':float(np.percentile([r['ratio'] for r in z],90))})
    (out/'horizon_summary.json').write_text(json.dumps(hs,indent=2))

    # Figures
    fig,ax=plt.subplots(figsize=(7.6,4.8)); x=np.arange(len(ok)); ax.bar(x,[r['geometry_rel_error'] for r in ok]); ax.axhline(G['geometry_relative_error_max'],linestyle='--'); ax.set_yscale('log'); ax.set_xticks(x,[r['case'] for r in ok],rotation=35,ha='right'); ax.set_ylabel('relative error'); ax.set_title('2A-D1 — Matrix-free tangent geometry transfer'); fig.tight_layout(); fig.savefig(out/'figures'/'2A_D1_geometry_transfer.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.6,4.8)); ax.bar(x,[r['final_edge_rel_error'] for r in ok]); ax.axhline(G['edge_relative_error_median_max'],linestyle='--'); ax.set_yscale('log'); ax.set_xticks(x,[r['case'] for r in ok],rotation=35,ha='right'); ax.set_ylabel('final relative edge error'); ax.set_title('2A-D2 — Passive active-edge tracking at signal scale'); fig.tight_layout(); fig.savefig(out/'figures'/'2A_D2_edge_tracking.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.2,4.6)); ax.plot([h['n_iter'] for h in hs],[h['beat_fraction'] for h in hs],marker='o'); ax.axhline(G['online_beat_fraction_min'],linestyle='--'); ax.set_ylim(0,1.05); ax.set_xlabel('iteration horizon'); ax.set_ylabel('fraction Online beating FGLA-opt'); ax.set_title('2A-D3 — Rate realization versus horizon'); fig.tight_layout(); fig.savefig(out/'figures'/'2A_D3_horizon_transfer.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.6,4.8));
    for t in traces:
        ax.semilogy(t['online'],label=f"{t['case']} online")
    ax.set_xlabel('iteration'); ax.set_ylabel('orbit error'); ax.set_title('2A-D4 — Safeguarded online trajectories'); ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(out/'figures'/'2A_D4_online_trajectories.png',dpi=180); plt.close(fig)

    print(json.dumps(summary,indent=2)); return summary


def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',default='configs/phase2a_grid.json'); p.add_argument('--out',default='results/phase2a'); a=p.parse_args(); run(a.config,a.out)
if __name__=='__main__': main()