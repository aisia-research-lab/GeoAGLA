import numpy as np
from geometry_gla.estimators.ritz import ritz_largest, estimate_edge_series


def test_exact_ritz_on_invariant_subspace():
    J=np.diag([0.2,0.6,0.9])
    S=[np.array([1,0,0],complex),np.array([0,1,0],complex),np.array([0,0,1],complex)]
    Y=[J@s for s in S]
    r=ritz_largest(S,Y)
    assert r['accepted']
    assert abs(r['estimate']-0.9)<1e-12


def test_power_trajectory_edge_estimation():
    J=np.diag([0.25,0.55,0.82,0.94])
    x=np.array([1.0,-.2,.4,.7]); tr=[x.copy()]
    for _ in range(120):
        x=J@x; tr.append(x.copy())
    ser=estimate_edge_series(np.asarray(tr,dtype=complex),1)
    ok=[r for r in ser if r['accepted']]
    assert abs(ok[-1]['estimate']-.94)<1e-5


def test_hidden_mode_nonidentifiability():
    JA=np.diag([.2,.5,.8,.9]); JB=np.diag([.2,.5,.8,.99]); x=np.array([1.,.2,-.5,0.])
    ta=[x.copy()]; tb=[x.copy()]
    for _ in range(30):
        xA=JA@ta[-1]; xB=JB@tb[-1]; ta.append(xA); tb.append(xB)
    assert np.max(np.abs(np.asarray(ta)-np.asarray(tb)))==0
