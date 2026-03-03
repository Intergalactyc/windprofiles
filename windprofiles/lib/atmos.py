import numpy as np
import pandas as pd
import windprofiles.lib.polar as polar
from windprofiles.lib.stats import KAPPA  # Von Karman constant

STANDARD_GRAVITY = 9.80665  # standard gravitational parameter g in m/s^2
REFERENCE_PRESSURE = 100.0  # reference pressure in kPa
WATER_AIR_MWR = 0.622  # water:air molecular weight ratio
R = (
    8.314462618 / 0.02896968
)  # gas constant of air, equal to universal gas constant divided by molar mass of dry air; result in J/(kg*K)
CP = 1004.68506  # specific heat capacity of air at constant pressure, J/(kg*K)
R_CP = R / CP  # ~ 0.286
T0 = 288.15  # Sea level standard temperature, K
SURFACE_LAYER_CUTOFF = 150.0  # top of surface layer, m

# coefficients for Businger-Dyer dimensionless wind shear computation
ALPHA = 4.7
BETA = 15.0


def pressure_above_msl(value, meters_asl, gravity=STANDARD_GRAVITY):
    """
    Given value of pressure at sea level and height above
        sea level (in meters), as well as optionally a value
        for local gravitational acceleration, returns
        the local value of barometric pressure
    """
    exponent = 1 / R_CP
    coefficient = 1 - ((gravity * meters_asl) / (CP * T0))
    return value * (coefficient**exponent)


def saturation_vapor_pressure(temperature, method="tetens"):
    """
    Saturation vapor pressure in kPa.
    Assumes temperature is in K.
    Default (and currently only) method is Tetens' approximation.
    """
    if method.lower() == "tetens":
        return 0.6113 * np.exp(
            17.2694 * (temperature - 273.15) / (temperature - 35.86)
        )
    else:
        raise Exception(
            f"lib.atmos.saturation_vapor_pressure: Method {method} unrecognized."
        )


def water_partial_pressure(relative_humidity, sat_vapor_pressure):
    """
    Partial pressure of water (e = RH * e_s)
    """
    return relative_humidity * sat_vapor_pressure


actual_vapor_pressure = water_partial_pressure  # alias


def water_air_mixing_ratio(actual_vapor_pressure, barometric_air_pressure):
    """
    Dimensionless mixing ratio of water:air (mass of vapor / mass of dry air) given two pressures of the same units.
    """
    return (
        WATER_AIR_MWR
        * actual_vapor_pressure
        / (barometric_air_pressure - actual_vapor_pressure)
    )


def specific_humidity(mixing_ratio):
    """
    Specific humidity (mass of vapor / total air mass = mass of vapor / (mass of dry air + mass of vapor)) given mixing ratio.
    """
    return mixing_ratio / (1 + mixing_ratio)


def virtual_temperature(temperature, mixing_ratio):
    """
    Virtual temperature in K, from temperature in K and water:air mixing ratio
    """
    return (
        temperature * (1 + (mixing_ratio / WATER_AIR_MWR)) / (1 + mixing_ratio)
    )


def potential_temperature(temperature, barometric_air_pressure):
    """
    Potential temperature in K, from temperature in K and air pressure in kPa.
    """
    return temperature * (REFERENCE_PRESSURE / barometric_air_pressure) ** R_CP


def virtual_potential_temperature(
    potential_temperature, mixing_ratio, approximate=False
):
    """
    Virtual potential temperature in K.
    Requires potential temperature in K and mixing ratio (dimensionless).
    If `approximate`, uses a first order approximation of the exact formula
        which is valid within ~1% for mixing ratios between roughly 0.00-0.20,
        but there isn't much reason to use it.
    """
    if approximate:
        return potential_temperature * (1 + 0.607 * mixing_ratio)
    return (
        potential_temperature
        * (1 + (mixing_ratio / WATER_AIR_MWR))
        / (1 + mixing_ratio)
    )


def dewpoint_temperature(temperature, relative_humidity):
    """
    Given temperature in K and relative humidity decimal value, compute dewpoint temperature in K
    """
    # Currently using a rough approximation. A better approximation is the Magnus formula, not yet implemented here.
    return temperature - 20 * (
        1 - relative_humidity
    )  # often seen as T - 0.2(100-RH), which is for RH in %


def vpt_from_3(relative_humidity, barometric_air_pressure, temperature):
    """
    Full 'pipeline' to compute virtual potential temperature in K, given
        relative humidity in [0,1], air pressure in kPa, and temperature in K.
    """
    svp = saturation_vapor_pressure(temperature)  # saturation vapor pressure
    avp = (
        relative_humidity * svp
    )  # actual vapor pressure (water partial pressure)
    w = water_air_mixing_ratio(
        actual_vapor_pressure=avp,
        barometric_air_pressure=barometric_air_pressure,
    )
    pT = potential_temperature(
        temperature=temperature,
        barometric_air_pressure=barometric_air_pressure,
    )
    vpT = virtual_potential_temperature(
        potential_temperature=pT, mixing_ratio=w, approximate=False
    )
    return vpT


def bulk_richardson_number(
    vpt_lower: float | pd.Series,
    vpt_upper: float | pd.Series,
    height_lower: float,
    height_upper: float,
    ws_lower: float | pd.Series,
    ws_upper: float | pd.Series,
    wd_lower: float | pd.Series,
    wd_upper: float | pd.Series,
    *,
    components: bool = False,
    gravity=STANDARD_GRAVITY,
) -> float:
    """
    Compute the bulk Richardson number Ri_bulk using data at two heights
    """
    delta_vpt = vpt_upper - vpt_lower
    delta_z = height_upper - height_lower

    if components:
        u_lower, u_upper = ws_lower, ws_upper
        v_lower, v_upper = wd_lower, wd_upper
    else:
        u_lower, v_lower = polar.wind_components(ws_lower, wd_lower)
        u_upper, v_upper = polar.wind_components(ws_upper, wd_upper)

    delta_u = u_upper - u_lower
    delta_v = v_upper - v_lower

    shear_sq = delta_u**2 + delta_v**2

    vpt_avg = (vpt_upper + vpt_lower) / 2

    ri = np.where(
        shear_sq == 0,
        np.nan,
        (gravity * delta_vpt * delta_z) / (vpt_avg * shear_sq),
    )

    if isinstance(vpt_lower, pd.Series):
        return pd.Series(ri, index=vpt_lower.index)

    return ri


def friction_velocity(
    wu_covariance: float | pd.Series, wv_covariance: float | pd.Series
):
    return (
        wu_covariance * wu_covariance + wv_covariance * wv_covariance
    ) ** 0.25


def obukhov_length(
    u_star: float | pd.Series,
    vpt: float | pd.Series,
    vpt_flux: float | pd.Series,
    gravity=STANDARD_GRAVITY,
):
    return -(u_star**3) * vpt / (KAPPA * gravity * vpt_flux)


def businger_dyer_phi(z_over_L):
    # Dimensionless wind shear function
    phi_stable = 1 + ALPHA * z_over_L
    phi_unstable = (1 - BETA * z_over_L) ** (-1 / 4)
    return np.where(z_over_L >= 0, phi_stable, phi_unstable)


def most_wind_gradient(u_star, L, z, method="businger dyer"):
    # L should be Obukhov length
    # uses MOST + Businger-Dyer relationship to estimate the vertical gradient of horizontal wind speed, du/dz
    # assume u is aligned with the mean horizontal wind direction
    match (m := method.lower().replace("-", " ").replace("_", " ")):
        case "businger dyer":
            phi = businger_dyer_phi
        case _:
            raise ValueError(
                f"Wind shear function method '{method}' ('{m}') unrecognized"
            )
    return u_star / (KAPPA * z) * phi(z / L)


def _finite_difference(h1, h2, u_minus, u, u_plus):
    num = (h1**2 * u_plus) - (h2**2 * u_minus) + (h2**2 - h1**2) * u
    den = h1 * h2 * (h1 + h2)
    return num / den


def _oneway_finite_difference_wind_gradient(
    z0: int | float,
    z1: int | float,
    u0,
    u1,
    wd0,
    wd1,
    log_method: bool,
    degrees: bool,
):
    c0 = np.log(z0) if log_method else z0
    c1 = np.log(z1) if log_method else z1
    h = c1 - c0

    if wd0 is not None and wd1 is not None:
        if isinstance(wd0, (float, int)):
            _d = polar.signed_angular_distance(wd1, wd0, degrees=degrees)
        else:
            _d = polar.series_signed_angular_distance(
                wd1, wd0, degrees=degrees
            )
        V1, U1 = polar.wind_components(u1, _d, degrees=degrees)
        dU_dz = (U1 - u0) / h
        dV_dz = V1 / h
        if log_method:
            dU_dz /= z0
            dV_dz /= z0
        return dU_dz, dV_dz

    derivative = (u1 - u0) / h
    return (derivative / z0) if log_method else derivative


def finite_difference_wind_gradient(
    z_minus: int | float,
    z: int | float,
    z_plus: int | float,
    u_minus,
    u,
    u_plus,
    wd_minus=None,
    wd=None,
    wd_plus=None,
    log_method: bool | str = "auto",
    degrees: bool = True,
):
    # given mean wind speed at three heights, approximates the vertical gradient of horizontal wind speed, du/dz
    # uses asymmetric central finite differencing
    # if one of the other heights is the same as the central height, use one-direction finite differencing instead (forward/backward differencing, depending on order)
    # if mean wind directions are provided, the result is a tuple of both u and v wind gradients, *where u is mean-wind aligned to the center height*
    # if log_method is True, transforms into log space first
    # if log_method is "auto", then if all z values given are below 150 m, True, else False
    # assumes z_plus > z > z_minus
    if log_method == "auto":
        log_method = z_plus < SURFACE_LAYER_CUTOFF
    if not isinstance(log_method, bool):
        raise ValueError("log_method must be True, False, or 'auto'")
    if z == z_minus and z == z_plus:
        raise ValueError("All three heights cannot be the same")

    if z == z_minus or z == z_plus:  # handle forward/backward difference case
        z0, u0, wd0 = z, u, wd
        z1, u1, wd1 = (
            (z_plus, u_plus, wd_plus)
            if z == z_minus
            else (z_minus, u_minus, wd_minus)
        )
        return _oneway_finite_difference_wind_gradient(
            z0, z1, u0, u1, wd0, wd1, log_method=log_method, degrees=degrees
        )

    c_m = np.log(z_minus) if log_method else z_minus
    c = np.log(z) if log_method else z
    c_p = np.log(z_plus) if log_method else z_plus
    h1 = c - c_m
    h2 = c_p - c

    if wd_minus is not None and wd is not None and wd_plus is not None:
        if isinstance(wd, (float, int)):
            d_m = polar.signed_angular_distance(wd_minus, wd, degrees=degrees)
            d_p = polar.signed_angular_distance(wd_plus, wd, degrees=degrees)
        else:  # pd.Series, np.array
            d_m = polar.series_signed_angular_distance(
                wd_minus, wd, degrees=degrees
            )
            d_p = polar.series_signed_angular_distance(
                wd_plus, wd, degrees=degrees
            )

        # V is latitudinal wrt center height, U is longitudinal (mean wind dir)
        V_m, U_m = polar.wind_components(u_minus, d_m, degrees=degrees)
        V_p, U_p = polar.wind_components(u_plus, d_p, degrees=degrees)

        dU_dz = _finite_difference(h1, h2, U_m, u, U_p)
        dV_dz = _finite_difference(h1, h2, V_m, 0.0, V_p)

        if log_method:
            # if log_method: results are dUi/dlnz, convert to dUi/dz by dividing by z
            dU_dz /= z
            dV_dz /= z

        return dU_dz, dV_dz

    derivative = _finite_difference(h1, h2, u_minus, u, u_plus)
    # if log_method: result is du/dlnz, convert to du/dz by dividing by z
    return (derivative / z) if log_method else derivative


def flux_richardson_number(
    vpt,
    heat_flux,
    u_momt_flux,
    grad_u,
    v_momt_flux=None,
    grad_v=None,
    gravity=STANDARD_GRAVITY,
):
    # heat_flux should be w'vpt' mean (m*K/s)
    # u_momt_flux should be w'u' mean (m^2/s^2), v_momt_flux (w'v' mean) may also be provided
    # vpt should be mean virtual potential temperature (K)
    # grad_u should be local vertical gradient of mean wind speed, grad_v may also be provided
    num = (gravity / vpt) * heat_flux
    den = u_momt_flux * grad_u
    if v_momt_flux is not None and grad_v is not None:
        den += v_momt_flux * grad_v
    return num / den
