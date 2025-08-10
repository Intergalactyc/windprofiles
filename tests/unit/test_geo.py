from pytest import approx
from windprofiles.lib.geo import local_gravity


def test_local_gravity():
    assert local_gravity(45, 5000) == approx(9.79077, 5e-6)
