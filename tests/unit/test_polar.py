import numpy as np
import pandas as pd
from pytest import approx

from windprofiles.lib.polar import (
    bearing_to_vector,
    directional_rms,
    polar_wind,
    unit_average_direction,
    vector_to_bearing,
    wind_components,
)
from windprofiles.processing.sonic import mean_directions


def test_polar_wind_toward_bearing_axis_aligned():
    # polar_wind has no meteorological assumption: it's the plain compass
    # bearing (CW of N) that an (east, north) vector points TOWARD.
    assert polar_wind(0.0, 1.0)[1] == approx(0.0)     # points N
    assert polar_wind(1.0, 0.0)[1] == approx(90.0)    # points E
    assert polar_wind(0.0, -1.0)[1] == approx(180.0)  # points S
    assert polar_wind(-1.0, 0.0)[1] == approx(270.0)  # points W


def test_wind_components_polar_wind_round_trip():
    rng = np.random.default_rng(0)
    speed = pd.Series(rng.uniform(0.1, 20, 25))
    toward = rng.uniform(0, 360, 25)
    u, v = wind_components(speed, pd.Series(toward))
    speed_out, toward_out = polar_wind(u, v)
    assert np.allclose(speed_out, speed, atol=1e-9)
    assert np.allclose((toward_out - toward + 180) % 360 - 180, 0, atol=1e-7)


def test_bearing_to_vector_from_bearing_axis_aligned():
    # A "south wind" (FROM 180) points due north; a "west wind" (FROM 270)
    # points due east - the two axis-aligned cases that pin down the sign
    # convention of a correct FROM-bearing-to-vector conversion.
    u, v = bearing_to_vector(1.0, 180.0)  # wind FROM the south -> points N
    assert (u, v) == approx((0.0, 1.0), abs=1e-9)
    u, v = bearing_to_vector(1.0, 270.0)  # wind FROM the west -> points E
    assert (u, v) == approx((1.0, 0.0), abs=1e-9)


def test_vector_to_bearing_matches_ground_truth():
    assert vector_to_bearing(0.0, 1.0)[1] == approx(180.0)   # points N -> FROM S
    assert vector_to_bearing(1.0, 0.0)[1] == approx(270.0)   # points E -> FROM W
    assert vector_to_bearing(0.0, -1.0)[1] == approx(0.0)    # points S -> FROM N
    assert vector_to_bearing(-1.0, 0.0)[1] == approx(90.0)   # points W -> FROM E


def test_bearing_to_vector_vector_to_bearing_round_trip():
    rng = np.random.default_rng(1)
    speed = pd.Series(rng.uniform(0.1, 20, 25))
    from_bearing = rng.uniform(0, 360, 25)
    u, v = bearing_to_vector(speed, pd.Series(from_bearing))
    speed_out, from_out = vector_to_bearing(u, v)
    assert np.allclose(speed_out, speed, atol=1e-9)
    assert np.allclose((from_out - from_bearing + 180) % 360 - 180, 0, atol=1e-7)


def test_unit_average_direction_is_circular_not_naive():
    # Naive arithmetic mean of {350, 10} is 180 - physically backwards (the true
    # average of two directions straddling due-north is north). Compared mod 360
    # since the degrees<->radians round trip can land exactly on 360 instead of 0.
    assert unit_average_direction(pd.Series([350.0, 10.0])) % 360 == approx(0.0, abs=1e-9)
    assert unit_average_direction(pd.Series([0.0, 90.0])) == approx(45.0, abs=1e-9)


def test_directional_rms_invariant_under_reflection_and_rotation():
    rng = np.random.default_rng(2)
    directions = pd.Series(rng.uniform(0, 360, 200))

    baseline = directional_rms(directions)
    reflected = directional_rms((180 - directions) % 360)  # a reflection
    rotated = directional_rms((directions + 137.0) % 360)  # an arbitrary uniform rotation

    assert reflected == approx(baseline, abs=1e-9)
    assert rotated == approx(baseline, abs=1e-9)


def test_mean_directions_matches_ground_truth_bearing():
    # Several samples of (east, north) "blows-toward" velocity, non-trivial
    # (non-axis-aligned) values, at a single boom.
    east = pd.Series([1.0, 2.0, -0.5, 0.3])
    north = pd.Series([3.0, 1.0, 2.0, -0.2])
    df = pd.DataFrame({"u_1": east, "v_1": north})

    result = mean_directions(df, booms=[1])

    toward_true = np.degrees(np.arctan2(east.mean(), north.mean())) % 360
    from_true = (toward_true + 180) % 360
    assert result["wd_1_mean"] == approx(from_true, abs=1e-9)
