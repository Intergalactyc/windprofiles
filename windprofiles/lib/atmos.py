import numpy as np
from windprofiles.lib.polar import wind_components
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

# coefficients for dimensionless wind shear computation
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
        raise (
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
        return potential_temperature * (1 + 0.61 * mixing_ratio)
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
    )  # often seen as T - 0.2(100-RH), this is for RH in %


def vpt_from_3(relative_humidity, barometric_air_pressure, temperature):
    """
    Full 'pipeline' to compute virtual potential temperature in K, given
        relative humidity in [0,1], air pressure in kPa, and temperature in K.
    """
    svp = saturation_vapor_pressure(temperature)  # saturation vapor pressure
    avp = relative_humidity * svp  # actual vapor pressure
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
    vpt_lower: float,
    vpt_upper: float,
    height_lower: float,
    height_upper: float,
    ws_lower: float,
    ws_upper: float,
    wd_lower: float,
    wd_upper: float,
    *,
    components: bool = False,
    gravity=STANDARD_GRAVITY,
) -> float:
    """
    Compute the bulk Richardson number Ri_bulk using data at two heights
    """
    delta_vpt = vpt_upper - vpt_lower
    delta_z = height_upper - height_lower

    if components:  # instead of ws's pass u's, instead of wd's pass v's
        u_lower = ws_lower
        u_upper = ws_upper
        v_lower = wd_lower
        v_upper = wd_upper
    else:
        u_lower, v_lower = wind_components(ws_lower, wd_lower)
        u_upper, v_upper = wind_components(ws_upper, wd_upper)

    delta_u = u_upper - u_lower
    delta_v = v_upper - v_lower

    shear_term = delta_u * delta_u + delta_v * delta_v

    if shear_term == 0:
        return np.nan

    vpt_avg = (vpt_upper + vpt_lower) / 2

    ri = gravity * delta_vpt * delta_z / (vpt_avg * shear_term)

    return ri


def obukhov_length(u_star, vpt, vpt_flux, gravity=STANDARD_GRAVITY):
    return -(u_star**3) * vpt / (KAPPA * gravity * vpt_flux)


# def phi(z_over_L):
#     # Dimensionless wind shear function
#     if z_over_L >= 0: # stable
#         # case z/L == 0 is neutral, returns 1 in either formula
#         return 1 + ALPHA * z_over_L
#     # otherwise, unstable
#     return (1 - BETA * z_over_L)**(-1/4)


# def wind_gradient(u_star, L, z):
#     # L should be Obukhov length
#     # uses Businger-Dyer relationship to estimate the vertical gradient of horizontal wind speed, du/dz
#     # assume u is aligned with the mean horizontal wind direction
#     return u_star / (KAPPA * z) * phi(z / L)


# def flux_richardson_number(u_star, momt_flux, vpt, vpt_flux, L, g=STANDARD_GRAVITY):
#     windgrad = wind_gradient(u_star, vpt, vpt_flux)
#     Rif = (g / vpt) * vpt_flux / (momt_flux * windgrad)
#     return Rif
