import numpy as np
import pandas as pd


def remove_data(
    df: pd.DataFrame, periods: dict, silent: bool = False
) -> tuple[pd.DataFrame, tuple[int, int]]:
    """
    Removes data within certain specified datetime intervals.
    Removal can be complete (specify 'ALL') or partial (specify
        list of integer booms).
    See kcc.py's `removal_periods` for an example of proper
        format for `periods`.
    If silent == False then #s of total and partial removals
        will be printed.
    """
    result = df.copy()

    total_removals = 0
    partial_removals = 0

    for interval, which_booms in periods.items():

        removal_start, removal_end = interval
        indices = result.loc[
            result["time"].between(
                removal_start, removal_end, inclusive="both"
            )
        ].index

        if (
            type(which_booms) is str and which_booms.lower() == "all"
        ):  # if all data is to be removed, just drop the full row entry
            result.drop(index=indices, inplace=True)
            total_removals += len(indices)
        elif (
            type(which_booms) is list
        ):  # otherwise, just set data from the selected booms to NaN
            datatypes = ["p", "ws", "wd", "t", "rh"]
            for b in which_booms:
                for d in datatypes:
                    selection = f"{d}_{b}"
                    if selection in result.columns:
                        result.loc[indices, selection] = np.nan
            partial_removals += len(indices)
        else:
            raise Exception(
                "Unrecognized removal-height specification in given periods",
                periods,
            )

    result.set_index("time", inplace=True)

    return result, (total_removals, partial_removals)


def rolling_outlier_removal(
    df: pd.DataFrame,
    window_size_minutes: int = 30,
    window_size_observations: int|None = None,
    sigma: int = 5,
    column_types=["ws", "t", "p", "rh"],
    silent: bool = False,
    remove_if_any: bool = True,
) -> tuple[pd.DataFrame, int | dict]:
    """
    Eliminate data where values from columns of types `column_types` are more than
        `sigma` (default 5) standard deviations from a rolling mean, rolling in a
        window of width `window_size_minutes` (default 30) minutes.
    Unable to handle wind direction - don't try to apply it to 'wd'.
    """
    result = df.copy(deep=True)
    window = (
        f"{window_size_minutes}min"
        if window_size_observations is None
        else window_size_observations
    )
    eliminations = 0 if remove_if_any else dict()

    for column in result.columns:
        column_type = column.split("_")[0]
        if column_type in column_types:
            rolling_mean = result[column].rolling(window=window).mean()
            rolling_std = result[column].rolling(window=window).std()
            threshold = sigma * rolling_std
            outliers = np.abs(result[column] - rolling_mean) > threshold
            if remove_if_any:
                eliminations += result[outliers].shape[0] # type: ignore
                result = result[~outliers]
            else:
                eliminations[column] = result[outliers].shape[0] # type: ignore
                result.loc[outliers, column] = pd.NA

    return result, eliminations


def flagged_removal(
    df: pd.DataFrame,
    flags: str | list[str],
    silent: bool = False,
    drop_cols=True,
):
    """
    For each column listed in `flags`, remove rows from `df` where that column is True
    """

    original_size = len(df)
    result = df.copy()

    if type(flags) is str:
        flags = [flags]

    for flag in flags:
        print(result[flag])
        result.drop(result[result[flag]].index, inplace=True)

    result.drop(columns=flags, inplace=True)

    removals = original_size - len(result)

    return result, removals


def strip_missing_data(
    df: pd.DataFrame,
    necessary: list[int],
    minimum: int = 4,
    silent: bool = False,
):
    """
    Remove rows where there are fewer than `minimum` wind speed columns or where
        wind speeds are missing at any of the `necessary` booms
    """
    result = df.copy()

    cols = result.columns

    necessarys = [f"ws_{b}" for b in necessary]
    ws_cols = []
    for col in cols:
        if "ws_" in col:
            ws_cols.append(col)

    removed = 0
    iterable = result.iterrows()
    for index, row in iterable:
        drop = False
        for necessary in necessarys: # type: ignore # TODO: figure out why the type error
            if pd.isna(row[necessary]): # type: ignore # TODO: figure out why the type error
                drop = True
                break
        count = 0
        for col in ws_cols:
            if not pd.isna(row[col]):
                count += 1
        if drop or count < minimum:
            result.drop(index=index, inplace=True)
            removed += 1

    return result, removed
