from typing import overload, Union

import numpy as np
import pandas as pd

# numbers.Number can't be used here: numpy ufuncs don't accept it
# (no __array_ufunc__ in typeshed) and typeshed doesn't model float/int as
# subtypes of it, so it fails static checks on nearly every line. This
# covers the same "any real scalar" intent, including numpy float dtypes.
Scalar = Union[int, float, np.floating]


@overload
def wind_components(
    speed: Scalar, direction: Scalar, degrees: bool = True
) -> tuple[float, float]: ...
@overload
def wind_components(
    speed: pd.Series, direction: pd.Series, degrees: bool = True
) -> tuple[pd.Series, pd.Series]: ...
@overload
def wind_components(
    speed: np.ndarray, direction: np.ndarray, degrees: bool = True
) -> tuple[np.ndarray, np.ndarray]: ...
def wind_components(
    speed: Scalar|pd.Series|np.ndarray, direction: Scalar|pd.Series|np.ndarray, degrees: bool = True
) -> tuple[Scalar|pd.Series|np.ndarray, Scalar|pd.Series|np.ndarray]:
    """
    Pure polar-to-Cartesian conversion, exact inverse of polar_wind.

    Given a magnitude and a TOWARD-bearing (degrees clockwise of N that the
    resulting vector points toward - NOT the meteorological "wind FROM"
    convention), return u, v (east, north) Cartesian components.
    Apply generally to vectors. Can be used with numerical types or pd.Series.

    This has no built-in meteorological assumption - it doesn't know or care
    whether `direction` came from a real, reported wind direction. If you
    have an actual measured/reported wind direction (the usual case - e.g. a
    station's "WD" field, or anything meaning "wind is blowing FROM this
    compass heading"), use bearing_to_vector instead, which handles the
    FROM/TOWARD distinction for you.
    """
    direction_rad = np.deg2rad(direction) if degrees else direction
    u = speed * np.sin(direction_rad)
    v = speed * np.cos(direction_rad)
    if isinstance(speed, (int, float, np.floating)):
        if speed == 0:
            u = 0.0
            v = 0.0
    elif isinstance(speed, (pd.Series, np.ndarray)):
        u[speed == 0] = 0.0
        v[speed == 0] = 0.0
    else:
        raise Exception(
            f"windprofiles.lib.polar.wind_components - unknown speed array type {type(speed)}"
        )
    return u, v


def polar_wind(u, v, degrees: bool = True):
    """
    Pure Cartesian-to-polar conversion, exact inverse of wind_components.

    Given u, v (east, north) Cartesian components of a vector, return its
    magnitude and the TOWARD-bearing (degrees clockwise of N that the vector
    points toward) - NOT the meteorological "wind FROM" convention.

    This has no built-in meteorological assumption - the returned direction
    is not a reportable "wind direction" (a real wind direction is a FROM
    bearing). If u, v are actual (east, north) wind velocity components and
    you want the standard meteorological wind direction, use
    vector_to_bearing instead, which handles the FROM/TOWARD distinction for
    you. This function (and wind_components) exist for generic polar-math
    uses where "direction" isn't a compass bearing at all - e.g. projecting
    a scalar onto a rotated reference frame via a relative angular offset.
    """
    speed = np.sqrt(u * u + v * v)
    direction = (
        np.rad2deg(np.arctan2(u, v)) % 360
        if degrees
        else np.arctan2(u, v) % (2 * np.pi)
    )
    return speed, direction


def bearing_to_vector(speed, from_bearing, degrees: bool = True):
    """
    Given a wind speed and a genuine meteorological wind direction (degrees
    clockwise of N that the wind is blowing FROM - the standard convention
    for a reported/measured wind direction, e.g. a station's "WD" field),
    return u, v (east, north) Cartesian "blows-toward" components.

    Exact inverse of vector_to_bearing. Use this (not wind_components
    directly) whenever `from_bearing` is an actual wind direction rather
    than a generic angle.
    """
    mod = 360 if degrees else 2 * np.pi
    toward_bearing = (from_bearing + mod / 2) % mod
    return wind_components(speed, toward_bearing, degrees=degrees)


def vector_to_bearing(u, v, degrees: bool = True):
    """
    Given u, v (east, north) Cartesian "blows-toward" wind velocity
    components, return the wind speed and the standard meteorological wind
    direction (degrees clockwise of N that the wind is blowing FROM).

    Exact inverse of bearing_to_vector. Use this (not polar_wind directly)
    whenever u, v are genuine wind velocity components and you want a
    reportable wind direction.
    """
    mod = 360 if degrees else 2 * np.pi
    speed, toward_bearing = polar_wind(u, v, degrees=degrees)
    from_bearing = (toward_bearing + mod / 2) % mod
    return speed, from_bearing


def polar_average(magnitudes, directions, degrees: bool = True):
    """
    Computes true vector average of vectors provided in polar form.
    Convention-agnostic: `directions` may be in any consistent angular
    convention (TOWARD-bearing, FROM-bearing, or otherwise) and the result
    will be a vector average expressed in that same convention.
    """
    if (type(magnitudes) not in [int, float]) and (
        len(magnitudes) != len(directions)
    ):
        raise Exception(
            f"lib.polar.polar_average: mismatched lengths of magnitudes/directions ({len(magnitudes)/len(directions)})"
        )

    directions_rad = np.deg2rad(directions) if degrees else directions

    xs = magnitudes * np.sin(
        directions_rad
    )  # the polar_wind function uses this swapped convention, so as we are calling it here, we must also use that convention for consistency.
    ys = magnitudes * np.cos(directions_rad)

    # nanmean rather than mean: a single NaN (from either magnitudes or
    # directions, propagated through the multiplication above) would
    # otherwise silently NaN out the whole average instead of just being
    # excluded from it.
    xavg = np.nanmean(xs)
    yavg = np.nanmean(ys)

    return polar_wind(xavg, yavg, degrees=degrees)


def unit_average_direction(directions, degrees: bool = True):
    """
    Computes unit vector (circular) average of directions - NOT a naive
    arithmetic mean, which breaks near the 0/360 wraparound (e.g. the
    circular mean of 350 and 10 is 0, not 180). Convention-agnostic: works
    the same whether `directions` are FROM-bearings, TOWARD-bearings, or any
    other consistent angular convention, and returns a result in that same
    convention.
    """
    return polar_average(magnitudes=1, directions=directions, degrees=degrees)[
        1
    ]


def angular_distance(theta, phi, degrees: bool = True):
    """
    Given two numerical angles theta and phi, computes
    the angular distance (minimal angle) between them.
    Convention-agnostic: since this only depends on the difference between
    theta and phi, it gives the same result regardless of which consistent
    angular convention (FROM-bearing, TOWARD-bearing, etc.) they're both
    expressed in.
    """
    mod = 360 if degrees else 2 * np.pi
    d0 = (theta - phi) % mod
    return min(mod - d0, d0)


def signed_angular_distance(
    theta, phi, degrees: bool = True, reverse: bool = False
):
    """Convention-agnostic (see angular_distance) - depends only on the
    difference between theta and phi."""
    flip_sign = -1 if reverse else 1
    mod = 360 if degrees else 2 * np.pi
    d0 = (theta - phi) % mod
    d1 = mod - d0
    if (
        d0 > d1
    ):  # If theta is counterclockwise of phi (ASSUMING ANGLES ARE CW CONVENTIONED), sign negative (positive if reverse)
        return -1 * flip_sign * d1
    return (
        flip_sign * d0
    )  # If theta is clockwise of phi, sign positive (negative if reverse)


def series_angular_distance(theta, phi, degrees: bool = True):
    """
    Extension of angular_distance to pd.Series and dimension-1 np.Array.
    Convention-agnostic (see angular_distance).
    """
    mod = 360 if degrees else 2 * np.pi
    d0 = (theta - phi) % mod
    return np.minimum(mod - d0, d0)


def series_signed_angular_distance(
    theta, phi, degrees: bool = True, reverse: bool = False
):
    """
    Extension of signed_angular_distance to pd.Series and dimension-1 np.Array.
    Convention-agnostic (see angular_distance).
    """
    flip_sign = -1 if reverse else 1
    mod = 360 if degrees else 2 * np.pi
    d0 = (theta - phi) % mod
    d1 = mod - d0
    return flip_sign * np.where(d1 < d0, -d1, d0)


def directional_rms(directions, degrees: bool = True):
    """
    Using the Yamartino double-pass method (Yamartino (1984) eq. 1,
    see https://doi.org/10.1175/1520-0450(1984)023%3C1362:ACOSPE%3E2.0.CO;2),
    compute the RMS of wind direction.

    Convention-agnostic and, further, provably invariant under any global
    reflection or rotation of `directions` (e.g. swapping FROM<->TOWARD
    convention, or any other consistent relabeling) - angular spread about
    the mean is unaffected by which convention the underlying angles use, so
    this function's output does not depend on getting that convention right.
    """
    mean_direction = unit_average_direction(directions, degrees=degrees)
    deviations = series_angular_distance(directions, mean_direction)
    variance = np.nanmean(deviations * deviations) - (np.nanmean(deviations)) ** 2
    return variance**0.5
