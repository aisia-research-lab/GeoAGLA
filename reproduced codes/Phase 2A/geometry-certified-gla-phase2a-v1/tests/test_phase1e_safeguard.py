import numpy as np
from geometry_gla.safeguards.checkpoint import fixed_checkpoint_merit, checkpoint_accept
from geometry_gla.operators.stft import periodic_stft_matrix, gaussian_window, AnalysisOperator
from geometry_gla.operators.projections import griffin_lim_map
from geometry_gla.algorithms.online_safe import run_safeguarded_online


def test_fixed_merit_is_parameter_independent_object():
    T=periodic_stft_matrix(16,gaussian_window(8),4,8); op=AnalysisOperator(T)
    rng=np.random.default_rng(7); x=rng.normal(size=16)+1j*rng.normal(size=16); c=op.analyze(x); s=np.abs(c)
    t=c+1e-3*op.project_range(rng.normal(size=op.coeff_dim)+1j*rng.normal(size=op.coeff_dim)); tp=c.copy()
    a=fixed_checkpoint_merit(t,tp,s,alpha_safe=0.0,K_safe=.25)
    b=fixed_checkpoint_merit(t,tp,s,alpha_safe=0.0,K_safe=.25)
    assert np.isfinite(a) and abs(a-b)<1e-15


def test_safe_gla_step_decreases_frozen_merit_locally():
    T=periodic_stft_matrix(16,gaussian_window(8),4,8); op=AnalysisOperator(T)
    rng=np.random.default_rng(8); x=rng.normal(size=16)+1j*rng.normal(size=16); c=op.analyze(x); s=np.abs(c)
    v=op.project_range(rng.normal(size=op.coeff_dim)+1j*rng.normal(size=op.coeff_dim)); v/=np.linalg.norm(v)
    t=c+1e-4*v; tp=t.copy(); tn=griffin_lim_map(t,s,op)
    chk=checkpoint_accept(t,tp,tn,t,np.asarray([t,tn]),s,K_safe=.25,descent_a=1e-4)
    assert chk['accepted']


def test_hostile_estimator_bias_cannot_bypass_checkpoint_logic():
    T=periodic_stft_matrix(16,gaussian_window(8),4,8); op=AnalysisOperator(T)
    rng=np.random.default_rng(9); x=rng.normal(size=16)+1j*rng.normal(size=16); c=op.analyze(x); s=np.abs(c)
    v=op.project_range(rng.normal(size=op.coeff_dim)+1j*rng.normal(size=op.coeff_dim)); v/=np.linalg.norm(v)
    r=run_safeguarded_online(c+1e-3*v,c+1e-3*v,s,op,n_iter=40,warmup=8,block_size=4,memory=3,margin=0,
                             estimator_bias=-0.1,K_safe=.25,descent_a=1e-4)
    assert len(r['trajectory'])==41
    assert all('candidate_accepted' in b for b in r['blocks'])
