import numpy as np
from pytest import approx

from windprofiles.lib.atmos import bulk_richardson_number
from windprofiles.lib.polar import wind_components


def test_bulk_richardson_number_invariant_to_bearing_convention():
    # Ri_bulk only depends on the squared magnitude of the (u_upper-u_lower,
    # v_upper-v_lower) difference vector, which is invariant to any
    # consistent rotation/reflection applied identically at both heights -
    # so the result should be identical whether the two heights' genuine
    # wind directions are converted to (u,v) via the old, "wrong-looking"
    # direct wind_components call (which treats a FROM-bearing as a TOWARD-
    # bearing) or the new, correct bearing_to_vector call - both apply the
    # *same* systematic convention to both heights.
    vpt_lower, vpt_upper = 295.0, 297.5
    height_lower, height_upper = 10.0, 47.0
    ws_lower, ws_upper = 4.2, 6.8
    wd_lower, wd_upper = 137.0, 152.5  # genuine FROM-bearings

    ri_new = bulk_richardson_number(
        vpt_lower, vpt_upper, height_lower, height_upper,
        ws_lower, ws_upper, wd_lower, wd_upper,
    )

    # replicate the old (pre-fix) code path directly: wind_components fed a
    # FROM-bearing as if it were a TOWARD-bearing
    u_lower_old, v_lower_old = wind_components(ws_lower, wd_lower)
    u_upper_old, v_upper_old = wind_components(ws_upper, wd_upper)
    ri_old = bulk_richardson_number(
        vpt_lower, vpt_upper, height_lower, height_upper,
        u_lower_old, u_upper_old, v_lower_old, v_upper_old,
        components=True,
    )

    assert float(ri_new) == approx(float(ri_old), abs=1e-9)


def test_bulk_richardson_number_matches_manual_formula():
    vpt_lower, vpt_upper = 295.0, 297.5
    height_lower, height_upper = 10.0, 47.0
    ws_lower, ws_upper = 4.2, 6.8
    wd_lower, wd_upper = 137.0, 152.5

    ri = bulk_richardson_number(
        vpt_lower, vpt_upper, height_lower, height_upper,
        ws_lower, ws_upper, wd_lower, wd_upper,
    )

    # independent reference: standard Ri_bulk formula computed from scratch
    # using the textbook FROM-bearing -> velocity relationship
    # (u = -speed*sin(from_rad), v = -speed*cos(from_rad))
    def uv(speed, from_bearing_deg):
        rad = np.deg2rad(from_bearing_deg)
        return -speed * np.sin(rad), -speed * np.cos(rad)

    u_l, v_l = uv(ws_lower, wd_lower)
    u_u, v_u = uv(ws_upper, wd_upper)
    shear_sq = (u_u - u_l) ** 2 + (v_u - v_l) ** 2
    g = 9.80665
    expected = g * (vpt_upper - vpt_lower) * (height_upper - height_lower) / (((vpt_upper + vpt_lower) / 2) * shear_sq)

    assert float(ri) == approx(expected, abs=1e-9)
