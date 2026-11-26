"""Safeguarded online geometry-adaptive Griffin-Lim accelerator (NumPy reference)."""
from __future__ import annotations
import numpy as np
from geometry_gla.algorithms.minimax import oracle_minimax
from geometry_gla.estimators.ritz import ritz_largest
from geometry_gla.operators.projections import griffin_lim_map
from geometry_gla.safeguards.checkpoint import checkpoint_accept, restricted_merit_gradient_norm


def _align_pair(q: np.ndarray, g: np.ndarray, ref_q: np.ndarray | None):
    if ref_q is None: return q.copy(),g.copy()
    inn=np.vdot(ref_q,q)
    if abs(inn)==0: return q.copy(),g.copy()
    phase=np.exp(-1j*np.angle(inn))
    return phase*q,phase*g


def _edge_from_history(qhist, ghist, memory, svd_rtol, cond_max):
    if len(qhist)<memory+1: return None
    ss=[]; yy=[]
    start=max(1,len(qhist)-memory)
    for j in range(start,len(qhist)):
        ss.append(qhist[j]-qhist[j-1]); yy.append(ghist[j]-ghist[j-1])
    if not ss: return None
    r=ritz_largest(ss,yy,svd_rtol=svd_rtol,cond_max=cond_max)
    return r if r['accepted'] else None


def _one_step(t,tp,s,op,alpha,beta,gamma):
    delta=t-tp; c=t+alpha*delta; d=t+beta*delta; g=griffin_lim_map(c,s,op)
    tn=(1-gamma)*d+gamma*g
    return tn,c,g


def _run_block(t,tp,s,op,alpha,beta,gamma,K):
    states=[t.copy()]; queries=[]; images=[]
    cur=t.copy(); prev=tp.copy()
    for _ in range(K):
        new,q,g=_one_step(cur,prev,s,op,alpha,beta,gamma)
        queries.append(q); images.append(g); states.append(new.copy())
        prev,cur=cur,new
    return cur,prev,np.asarray(states),queries,images


def run_safeguarded_online(
    t0,t_minus1,s,op,*,n_iter=180,warmup=12,block_size=4,memory=3,
    margin=0.003,lambda_ceiling=1-1e-8,svd_rtol=1e-9,cond_max=1e10,
    alpha_safe=0.0,beta_safe=0.0,gamma_safe=1.0,K_safe=0.25,descent_a=1e-4,
    estimator_bias=0.0,
):
    """Run online edge synthesis with rollback checkpoint safeguard.

    `estimator_bias` is a hostile-test hook. It perturbs the passive estimate
    before parameter synthesis but does not alter the safeguard.
    """
    t=np.asarray(t0,dtype=np.complex128).copy(); tp=np.asarray(t_minus1,dtype=np.complex128).copy()
    committed=[t.copy()]; qhist=[]; ghist=[]; logs=[]; n_done=0; prev_D=0.0

    # Safe warmup, while collecting passive map pairs.
    for _ in range(min(warmup,n_iter)):
        new,q,g=_one_step(t,tp,s,op,alpha_safe,beta_safe,gamma_safe)
        ref=qhist[-1] if qhist else None; qa,ga=_align_pair(q,g,ref)
        qhist.append(qa); ghist.append(ga)
        tp,t=t,new; committed.append(t.copy()); n_done+=1

    block_id=0
    edge_envelope=None
    while n_done<n_iter:
        K=min(block_size,n_iter-n_done); block_id+=1
        estres=_edge_from_history(qhist,ghist,memory,svd_rtol,cond_max)
        if estres is None:
            raw=None; synth=None; pars={'alpha':0.0,'beta':0.0,'gamma':1.0,'q':None}; proposal='safe_no_estimate'
        else:
            raw_current=float(estres['estimate'])
            edge_envelope = raw_current if edge_envelope is None else max(edge_envelope, raw_current)
            raw=float(edge_envelope); synth=float(np.clip(raw+estimator_bias+margin,1e-8,lambda_ceiling))
            pars=oracle_minimax(0.0,synth); proposal='online'
        start_t=t.copy(); start_tp=tp.copy()
        cand_t,cand_tp,cand_states,cand_q,cand_g=_run_block(t,tp,s,op,pars['alpha'],pars['beta'],pars['gamma'],K)
        check=checkpoint_accept(start_t,start_tp,cand_t,cand_tp,cand_states,s,
                                alpha_safe=alpha_safe,K_safe=K_safe,descent_a=descent_a)
        rejected=not check['accepted']
        if rejected:
            end_t,end_tp,states,qs,gs=_run_block(start_t,start_tp,s,op,alpha_safe,beta_safe,gamma_safe,K)
            fallback_check=checkpoint_accept(start_t,start_tp,end_t,end_tp,states,s,
                                             alpha_safe=alpha_safe,K_safe=K_safe,descent_a=descent_a)
            # If a nominal safe block fails the strict diagnostic inequality,
            # commit it anyway but expose the event; this prevents silently
            # claiming a theorem property that was not observed.
            safe_e1=bool(fallback_check['accepted'])
        else:
            end_t,end_tp,states,qs,gs=cand_t,cand_tp,cand_states,cand_q,cand_g; fallback_check=None; safe_e1=True
        # Commit accepted/fallback trajectory and only its estimator information.
        ref=qhist[-1] if qhist else None
        for q,g in zip(qs,gs):
            qa,ga=_align_pair(q,g,ref); qhist.append(qa); ghist.append(ga); ref=qa
        for z in states[1:]: committed.append(z.copy())
        D=float(check['path_size'] if not rejected else fallback_check['path_size'])
        grad=restricted_merit_gradient_norm(end_t,end_tp,s,op,alpha_safe=alpha_safe,K_safe=K_safe)
        denom=D+prev_D; e2_ratio=float(grad/denom) if denom>1e-15 else float('inf')
        logs.append({'block':block_id,'start_iter':n_done,'end_iter':n_done+K,'proposal':proposal,
                     'raw_estimate':raw,'synth_edge':synth,'alpha':pars['alpha'],'beta':pars['beta'],'gamma':pars['gamma'],
                     'candidate_accepted':not rejected,'candidate_phi_start':check['phi_start'],'candidate_phi_end':check['phi_end'],
                     'candidate_path_size':check['path_size'],'candidate_descent_slack':check['descent_slack'],
                     'fallback_e1_pass':safe_e1,'committed_path_size':D,'e2_grad_norm':grad,'e2_ratio':e2_ratio})
        t,tp=end_t,end_tp; prev_D=D; n_done+=K
    return {'trajectory':np.asarray(committed),'blocks':logs,'query_history':qhist,'image_history':ghist}


def run_online_policy(
    t0,t_minus1,s,op,*,n_iter=180,warmup=12,block_size=8,memory=3,
    margin=0.0,lambda_ceiling=1-1e-8,svd_rtol=1e-9,cond_max=1e10,
    alpha_safe=0.0,beta_safe=0.0,gamma_safe=1.0,K_safe=0.25,descent_a=1e-4,
    policy='dynamic_envelope', update_rel_tol=0.0, ema_eta=0.25,
    oracle_edge=None, estimator_bias=0.0,
):
    """Safeguarded online edge-synthesis policy runner.

    Supported edge-update policies:
      dynamic_raw       : current Ritz edge at every block;
      dynamic_envelope  : running maximum of accepted Ritz estimates;
      freeze_first      : freeze first accepted Ritz edge after warmup;
      freeze_calibrated : extend warmup calibration to 2*warmup, then freeze;
      thresholded       : update only if relative edge change exceeds update_rel_tol;
      ema               : exponential moving average damping by ema_eta;
      oracle_frozen     : frozen supplied oracle_edge (oracle diagnostic control).

    All non-oracle policies are passive. Local convergence safeguarding is
    enforced via the fixed checkpoint merit and GLA rollback mechanism.
    """
    t=np.asarray(t0,dtype=np.complex128).copy(); tp=np.asarray(t_minus1,dtype=np.complex128).copy()
    committed=[t.copy()]; qhist=[]; ghist=[]; logs=[]; n_done=0; prev_D=0.0
    calibration = min(n_iter, 2*warmup if policy=='freeze_calibrated' else warmup)
    for _ in range(calibration):
        new,q,g=_one_step(t,tp,s,op,alpha_safe,beta_safe,gamma_safe)
        ref=qhist[-1] if qhist else None; qa,ga=_align_pair(q,g,ref)
        qhist.append(qa); ghist.append(ga); tp,t=t,new; committed.append(t.copy()); n_done+=1

    edge_state=None; frozen=False; block_id=0
    while n_done<n_iter:
        K=min(block_size,n_iter-n_done); block_id+=1
        estres=_edge_from_history(qhist,ghist,memory,svd_rtol,cond_max)
        raw_current=float(estres['estimate']) if estres is not None else None
        changed=False
        if policy=='oracle_frozen':
            if oracle_edge is None: raise ValueError('oracle_edge required')
            edge_state=float(oracle_edge); frozen=True
        elif raw_current is not None:
            if policy=='dynamic_raw': edge_state=raw_current; changed=True
            elif policy=='dynamic_envelope':
                new=raw_current if edge_state is None else max(edge_state,raw_current); changed=(edge_state is None or new!=edge_state); edge_state=new
            elif policy in ('freeze_first','freeze_calibrated'):
                if not frozen: edge_state=raw_current; frozen=True; changed=True
            elif policy=='thresholded':
                if edge_state is None: edge_state=raw_current; changed=True
                elif abs(raw_current-edge_state)/max(1e-12,abs(edge_state)) >= update_rel_tol: edge_state=raw_current; changed=True
            elif policy=='ema':
                if edge_state is None: edge_state=raw_current; changed=True
                else: edge_state=(1-ema_eta)*edge_state+ema_eta*raw_current; changed=True
            else: raise ValueError(policy)
        if edge_state is None:
            synth=None; pars={'alpha':0.0,'beta':0.0,'gamma':1.0,'q':None}; proposal='safe_no_estimate'
        else:
            synth=float(np.clip(edge_state+estimator_bias+margin,1e-8,lambda_ceiling)); pars=oracle_minimax(0.0,synth); proposal=policy
        start_t=t.copy(); start_tp=tp.copy()
        cand_t,cand_tp,cand_states,cand_q,cand_g=_run_block(t,tp,s,op,pars['alpha'],pars['beta'],pars['gamma'],K)
        check=checkpoint_accept(start_t,start_tp,cand_t,cand_tp,cand_states,s,alpha_safe=alpha_safe,K_safe=K_safe,descent_a=descent_a)
        rejected=not check['accepted']
        if rejected:
            end_t,end_tp,states,qs,gs=_run_block(start_t,start_tp,s,op,alpha_safe,beta_safe,gamma_safe,K)
            fallback_check=checkpoint_accept(start_t,start_tp,end_t,end_tp,states,s,alpha_safe=alpha_safe,K_safe=K_safe,descent_a=descent_a)
            safe_e1=bool(fallback_check['accepted'])
        else:
            end_t,end_tp,states,qs,gs=cand_t,cand_tp,cand_states,cand_q,cand_g; fallback_check=None; safe_e1=True
        ref=qhist[-1] if qhist else None
        for q,g in zip(qs,gs):
            qa,ga=_align_pair(q,g,ref); qhist.append(qa); ghist.append(ga); ref=qa
        for z in states[1:]: committed.append(z.copy())
        D=float(check['path_size'] if not rejected else fallback_check['path_size'])
        grad=restricted_merit_gradient_norm(end_t,end_tp,s,op,alpha_safe=alpha_safe,K_safe=K_safe)
        denom=D+prev_D; e2_ratio=float(grad/denom) if denom>1e-15 else float('inf')
        logs.append({'block':block_id,'start_iter':n_done,'end_iter':n_done+K,'proposal':proposal,'raw_current':raw_current,
                     'edge_state':edge_state,'edge_changed':changed,'synth_edge':synth,'alpha':pars['alpha'],'beta':pars['beta'],'gamma':pars['gamma'],
                     'candidate_accepted':not rejected,'candidate_phi_start':check['phi_start'],'candidate_phi_end':check['phi_end'],
                     'candidate_path_size':check['path_size'],'candidate_descent_slack':check['descent_slack'],'fallback_e1_pass':safe_e1,
                     'committed_path_size':D,'e2_grad_norm':grad,'e2_ratio':e2_ratio})
        t,tp=end_t,end_tp; prev_D=D; n_done+=K
    return {'trajectory':np.asarray(committed),'blocks':logs,'query_history':qhist,'image_history':ghist}
