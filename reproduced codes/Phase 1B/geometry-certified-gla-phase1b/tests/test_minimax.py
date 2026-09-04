import numpy as np
from geometry_gla.algorithms.minimax import oracle_minimax, fgla_opt, modal_radius


def test_oracle_strictly_beats_fgla_examples():
    for lm,lp in [(0,.2),(0,.5),(.1,.5),(.5,.8),(.8,.95)]:
        o=oracle_minimax(lm,lp); f=fgla_opt(lp)
        assert 0 < o["q"] < f["q"] < lp < 1
        grid=np.linspace(lm,lp,101)
        worst=max(modal_radius(x,o["alpha"],o["beta"],o["gamma"]) for x in grid)
        assert abs(worst-o["q"]) < 1e-7


def test_endpoint_equioscillation():
    lm,lp=.2,.7
    o=oracle_minimax(lm,lp)
    assert abs(modal_radius(lp,o["alpha"],o["beta"],o["gamma"])-o["q"])<1e-8
    assert abs(modal_radius(lm,o["alpha"],o["beta"],o["gamma"])-o["q"])<1e-8
