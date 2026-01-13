from windprofiles.data.gmaps import get_elevation
from pytest import approx, mark


@mark.api
def test_elevation():
    assert get_elevation(28.3922, -80.6077) == approx(9.8, 1.0)
