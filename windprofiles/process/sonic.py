import pandas as pd
import numpy as np
from multiprocessing import Pool, Queue, Process
import os
import windprofiles.lib.polar as polar
import windprofiles.lib.stats as stats
from windprofiles.user.logs import log_listener, configure_worker
from tqdm import tqdm
import signal

pd.options.mode.chained_assignment = None


def _init(queue):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    configure_worker(queue)


def analyze_directory(
    path: str | os.PathLike,
    analysis,
    logfile,
    rules: dict = None,
    nproc=1,
    index=None,
    limit=None,
    progress=False,
    **kwargs,
) -> pd.DataFrame:
    # analysis should be a function which takes a single arg (to unpack as `filepath, {rules (if not None)}, <kwargs>`) and returns a dict

    dir_path = os.path.abspath(path)
    if rules is None:
        if len(kwargs) == 0:
            directory = [
                os.path.join(dir_path, filename)
                for filename in os.listdir(path)
            ]
        else:
            directory = [
                (os.path.join(dir_path, filename), *kwargs)
                for filename in os.listdir(path)
            ]
    else:
        directory = [
            (os.path.join(dir_path, filename), rules, *kwargs)
            for filename in os.listdir(path)
        ]
    if limit is not None:
        directory = directory[:limit]

    if progress:
        pbar = tqdm(total=len(directory))

    queue = Queue(-1)

    listener = Process(target=log_listener, args=(queue, logfile), daemon=True)
    listener.start()

    pool = Pool(
        processes=max(1, nproc - 1), initializer=_init, initargs=(queue,)
    )
    results = []
    for res in pool.imap(analysis, directory):
        if isinstance(res, list):
            results += res
        elif isinstance(res, dict):
            results.append(res)
        else:
            raise TypeError(f"Unrecognized analysis result type {type(res)}")
        if pbar:
            pbar.update()
            pbar.refresh()
    pool.close()
    pool.join()
    df = pd.DataFrame(results)
    if index is not None and index in df.columns:
        df.set_index(index, inplace=True)
        df.sort_index(ascending=True)
    return df


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
