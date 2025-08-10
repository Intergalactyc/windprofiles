import numpy as np


def local_gravity(latitude, elevation):
    """
    Given latitude in degrees and elevation in m,
    returns theoretical local gravity in m/s^2
    """
    rad = np.deg2rad(latitude)
    IGF = 9.780327 * (
        1 + 0.0053024 * np.sin(rad) ** 2 - 0.0000058 * np.sin(2 * rad) ** 2
    )
    FAC = -3.086e-6 * elevation
    return IGF + FAC
