import numpy as np
import pandas as pd
import windprofiles.lib.polar as polar
import warnings


def shadowing_merge(df, speeds, directions, angles, width=30, drop_old=True):
    """
    Merges multiple sets of data at a shared height, accounting
        for tower shadowing effects.
    `speeds` and `directions` should be the names of the columns of
        `df` containing the wind speeds and directions to combine.
    `angles` should be the center wind direction from which
        shadowing occurs for their respective boom (data set).
    `speeds`, `directions`, and `angles` must be iterables
        of the same length.
    At each time, if the wind direction reported by boom `i` is
        within width/2 of its corresponding shadowing angle,
        then its data will be considered shadowed and neither its
        speed or direction will be used. Data from all booms which
        are not shadowed will be (vector) averaged to form the
        resulting wind speed and direction at that time.
    Returns two columns: merged wind speeds and merged wind directions.
    """
    if not (len(speeds) == len(directions) == len(angles)):
        raise Exception(
            f"Mismatched lengths for speeds/directions/angles (given lengths {len(speeds)}/{len(directions)}/{len(angles)})"
        )
    nBooms = len(speeds)
    radius = width / 2
    raw_deviations = [
        (df[dir] - ang) % 360 for dir, ang in zip(directions, angles)
    ]
    indexer = [
        col.apply(lambda d: min(360 - d, d) > radius) for col in raw_deviations
    ]
    n_shadowed = [len(indexer[i]) - indexer[i].sum() for i in range(nBooms)]
    uList = []
    vList = []
    for i in range(nBooms):
        _spd, _dir, _ang = speeds[i], directions[i], angles[i]
        raw_deviations = (df[_dir] - _ang) % 360
        corr_deviations = raw_deviations.apply(lambda d: min(360 - d, d))
        u, v = polar.wind_components(df[_spd], df[_dir])
        u[corr_deviations < radius] = np.nan # type: ignore
        v[corr_deviations < radius] = np.nan # type: ignore
        uList.append(u)
        vList.append(v)
    # We want the mean(np.nan...) -> np.nan behavior and expect to see it sometimes, so we'll filter the error
    warnings.filterwarnings(action="ignore", message="Mean of empty slice")
    uMeans = np.nanmean(np.stack(uList), axis=0)
    vMeans = np.nanmean(np.stack(vList), axis=0)
    sMeans = np.sqrt(uMeans * uMeans + vMeans * vMeans)
    dMeans = (np.rad2deg(np.arctan2(uMeans, vMeans)) + 360) % 360
    if drop_old:
        df.drop(columns=speeds + directions, inplace=True)
    return sMeans, dMeans, [int(n) for n in n_shadowed]


def resample(
    df: pd.DataFrame,
    all_booms: list[int],
    window_size_minutes: int,
    how: str = "mean",
    drms: bool = False,
    pti: bool = False,
    turbulence_reference: int = -1,
) -> pd.DataFrame:

    to_resample = df.copy(deep=True)
    window = f"{window_size_minutes}min"

    for b in all_booms:
        to_resample[f"x_{b}"], to_resample[f"y_{b}"] = polar.wind_components(
            to_resample[f"ws_{b}"], to_resample[f"wd_{b}"]
        )

    rsmp = to_resample.resample(window)
    if how == "mean":
        resampled = rsmp.mean()
    elif how == "median":
        resampled = rsmp.median()
    else:
        raise Exception(f"Unrecognized resampling method {how}")
    if pti:
        stds = rsmp.std()
    if drms:  # directional RMS per height
        drms_dict = dict()
        for b in all_booms:
            drms_dict[b] = rsmp[f"wd_{b}"].agg(polar.directional_rms)

    resampled.dropna(axis=0, how="all", inplace=True)

    for b in all_booms:
        if pti:
            # Compute pseudo-turbulence intensities 'pti_{b}' per height as (mean of wind speeds) / (mean wind speed [direct magnitude average])
            # mean wind speed used is that at height `turbulence_reference` (or at local height if turbulence_reference == -1)
            ref = (
                b
                if (
                    type(turbulence_reference) is not int
                    or turbulence_reference < 0
                )
                else turbulence_reference
            )
            if ref not in all_booms:
                raise Exception(
                    f"In pseudo-TI calculation, unrecognized reference boom {ref}"
                )
            resampled[f"pti_{b}"] = (
                stds[f"ws_{b}"] / resampled[f"ws_{ref}"]
            )  # divide by raw average wind speed, before vector averaging

        if drms:
            # Get directional RMS that was computed above
            resampled[f"drms_{b}"] = drms_dict[b]

        # Find vector averages
        resampled[f"ws_{b}"] = np.sqrt(
            resampled[f"x_{b}"] ** 2 + resampled[f"y_{b}"] ** 2
        )
        resampled[f"wd_{b}"] = (
            np.rad2deg(np.arctan2(resampled[f"x_{b}"], resampled[f"y_{b}"]))
            + 360
        ) % 360
        resampled.drop(columns=[f"x_{b}", f"y_{b}"], inplace=True)

    return resampled
