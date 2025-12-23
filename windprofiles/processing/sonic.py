import windprofiles.lib.polar as polar
import windprofiles.lib.stats as stats
import numpy as np
import pandas as pd


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
        if ctype == "wd":
            if stat == np.mean:
                result[result_col] = polar.unit_average_direction(df[col])
            elif stat == np.std:
                result[result_col] = polar.directional_rms(df[col])
            else:
                result[result_col] = pd.NA
        else:
            result[result_col] = stat(df[col])
    return result


def mean_directions(df, booms, degrees: bool = True):
    # u should be East, v should be North

    result = {}

    for b in booms:
        ux = df[f"u_{b}"]
        uy = df[f"v_{b}"]

        uxavg = np.mean(ux)
        uyavg = np.mean(uy)

        result[f"wd_{b}_mean"] = polar.polar_wind(uxavg, uyavg, degrees)[0]

    return result


def align_to_directions(df, directions, degrees: bool = True):
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
        ux = df[f"u_{b}"]
        uy = df[f"v_{b}"]

        ux_aligned = ux * np.cos(d) + uy * np.sin(d)
        uy_aligned = -ux * np.sin(d) + uy * np.cos(d)

        dfc[f"u_{b}"] = ux_aligned
        dfc[f"v_{b}"] = uy_aligned

    return dfc


def compute_autocorrs(
    df: pd.DataFrame, columns: list, maxlag: float = 0.5
) -> pd.DataFrame:
    num_lags = int(len(df) * maxlag)
    lags = range(num_lags)
    result = pd.DataFrame(index=lags)
    for col in columns:
        result[col] = stats.autocorrelations(df[col], lags=lags)
    return result


def integral_scales(autocorrs: pd.DataFrame):
    pass
