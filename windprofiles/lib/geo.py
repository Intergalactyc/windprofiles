import numpy as np


def local_gravity(latitude, elevation, *, latitude_degrees: bool=True):
    """
    Given latitude in degrees and elevation in m,
    returns theoretical local gravity in m/s^2.
    If latitude is passed as radians rather than degrees,
    then specify latitude_degress = False.
    """
    rad = np.deg2rad(latitude) if latitude_degrees else latitude_degrees
    IGF = 9.780327 * (
        1 + 0.0053024 * np.sin(rad) ** 2 - 0.0000058 * np.sin(2 * rad) ** 2
    )
    FAC = -3.086e-6 * elevation
    return IGF + FAC

def coriolis(latitude, *, latitude_degrees: bool=True, Omega=7.2921e-5):
    """
    Given latitude in degrees (and globe angular velocity Omega in rad/s),
    returns coriolis parameter in rad/s.
    If latitude is passed as radians rather than degrees,
    then specify latitude_degress = False.
    """
    rad = np.deg2rad(latitude) if latitude_degrees else latitude_degrees
    return 2 * Omega * np.sin(rad)