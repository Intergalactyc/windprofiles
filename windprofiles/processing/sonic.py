import windprofiles.lib.polar as polar
import numpy as np
import pandas as pd
import scipy.integrate as spint


def get_stats(
    df: pd.DataFrame, stat=np.mean, suffix=None, col_types=None
) -> dict:
    result = dict()
    if suffix is None:
        if stat == np.mean:
            suffix = "_mean"
        elif stat == np.median:
            suffix = "_med"
        elif stat == np.std:
            suffix = "_std"
        else:
            suffix = ""
    for col in df.columns:
        ctype = col.split("_")[0]
        if col_types is not None and ctype not in col_types:
            continue
        result_col = col + str(suffix)
        if ctype in {"wd", "propwd"}:
            if stat == np.mean:
                result[result_col] = polar.unit_average_direction(df[col])
            elif stat == np.std:
                result[result_col] = polar.directional_rms(df[col])
            else:
                result[result_col] = pd.NA
        else:
            result[result_col] = stat(df[col])
    return result


def mean_directions(df, booms, prefix: str = "", degrees: bool = True):
    # u should be East, v should be North

    result = {}

    for b in booms:
        ux = df[f"{prefix}u_{b}"]
        uy = df[f"{prefix}v_{b}"]

        uxavg = np.mean(ux)
        uyavg = np.mean(uy)

        result[f"{prefix}wd_{b}_mean"] = polar.polar_wind(
            uxavg, uyavg, degrees
        )[1]

    return result


def align_to_directions(
    df, directions, prefix: str = "", degrees: bool = True
):
    # Given vector-mean wind directions:
    # Convert wind components to streamwise coordinates - that is,
    # Geometrically align the u, v components of wind such that u is oriented
    # in the direction of the mean wind and v is in the crosswind direction (and hence mean-0)
    by_boom = {
        int(s.split("_")[1]): np.deg2rad(d) if degrees else d
        for s, d in directions.items()
    }

    dfc = df.copy()
    for b, d in by_boom.items():
        ux = df[f"{prefix}u_{b}"]
        uy = df[f"{prefix}v_{b}"]

        ux_aligned = ux * np.sin(d) + uy * np.cos(d)
        uy_aligned = ux * np.cos(d) - uy * np.sin(d)
        # ux_aligned = ux * np.cos(d) + uy * np.sin(d)
        # uy_aligned = -ux * np.sin(d) + uy * np.cos(d)

        dfc[f"{prefix}u_{b}"] = ux_aligned
        dfc[f"{prefix}v_{b}"] = uy_aligned

    return dfc

available_cutoff_methods = ["zerocrossing", "efolding", "efoldingtime", "threshold", "total"]
def integral_time_scale(
    ac: pd.Series,
    scale_factor: float = 1.0,
    integration_method: str = "simpson",
    cutoff_method: str = "efolding",
    threshold: float|None = None,
) -> float:
    # typical index is a lag # index, rather than true time index;
    # in this case a correction factor should be passed
    # (e.g. for lags at intervals of 0.05 s, use scale_factor=0.05)
    # Note that "efoldingtime" is special: rather than integrating, it simply
    # returns the time at which the 1/e threshold is met
    INTEGRATION_METHODS = {
        "simpson": spint.simpson,
        "trapezoid": np.trapezoid,
        "trapezoidal": np.trapezoid,
    }
    method = INTEGRATION_METHODS.get(integration_method.lower())
    if method is None:
        raise ValueError(f"Invalid integration method '{integration_method}'")

    cutoff_index = 0
    match cutoff_method.lower():
        case "zerocrossing": # threshold of 0
            cutoff_threshold = 0.0
        case "efolding" | "efoldingtime": # threshold of 1/e
            cutoff_threshold = 1 / np.e
        case "threshold": # use custom specified threshold
            if threshold is None:
                raise ValueError("To use threshold method, a value must be passed")
            cutoff_threshold = threshold
        case "total": # integrate over all lags
            cutoff_index = -1
        case _:
            raise ValueError(f"Invalid cutoff method '{cutoff_method}'")

    # cutoff_index is the integer index at which the cutoff threshold is first met
    # will be -1 if no such crossing is detected
    if cutoff_index == 0:
        try:
            cutoff_index = ac[ac <= cutoff_threshold].index[0]
        except IndexError:
            cutoff_index = -1
        if cutoff_method.lower() == "efoldingtime": # special mode: no integration, just give folding time
            if cutoff_index != -1:
                return scale_factor * cutoff_index
            else:
                return scale_factor * ac.index[-1]
    return scale_factor * method(
        ac.iloc[:cutoff_index], ac.index[:cutoff_index]
    )
