import numpy as np
from experiments.h1_geometry.run import build_case
from geometry_gla.geometry.jacobian import jacobian_matrix_on_range
from geometry_gla.geometry.principal_angles import principal_angle_spectrum


def test_jacobian_principal_angle_identity():
    op,c=build_case(seed=11)
    J,_=jacobian_matrix_on_range(c,op)
    vals=np.sort(np.linalg.eigvalsh(J))
    geom,_=principal_angle_spectrum(op.T,c)
    assert np.linalg.norm(J-J.T)<1e-10
    assert vals.size==geom.size
    rel=np.linalg.norm(vals-geom)/(np.linalg.norm(vals)+1e-15)
    assert rel<1e-9
