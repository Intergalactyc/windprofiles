import pandas as pd
import numpy as np
from multiprocessing import Pool
import os
import windprofiles.lib.polar as polar
from tqdm import tqdm
import signal


def _init():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def analyze_directory(
    path: str | os.PathLike,
    analysis,
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

    pool = Pool(processes=nproc, initializer=_init)
    results = []
    try:
        for res in pool.imap(analysis, directory):
            if isinstance(res, list):
                results += res
            elif isinstance(res, dict):
                results.append(res)
            else:
                raise TypeError(
                    f"Unrecognized analysis result type {type(res)}"
                )
            if pbar:
                pbar.update()
                pbar.refresh()
    except KeyboardInterrupt:
        pool.terminate()
    else:
        pool.close()
    finally:
        pool.join()
    print(f"Completed analysis of directory {path}")
    df = pd.DataFrame(results)
    if index is not None and index in df.columns:
        df.set_index(index, inplace=True)
        df.sort_index(ascending=True)
    return df


# def compute_fluxes(df: pd.DataFrame, booms: list[int]) -> pd.DataFrame:
#     # u', v', w', u'v', u'w'


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
            else:
                result[result_col] = pd.NA
        else:
            result[result_col] = stat(df[col])
    return result
