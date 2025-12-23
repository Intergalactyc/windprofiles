import numpy as np
import pandas as pd
from warnings import warn


def correct_directions(df):
    result = df.copy()
    for col in result.columns:
        if col[:3] == "wd_":
            b = col[3]
            ws_col = f"ws_{b}"
            if ws_col in result.columns:
                result.loc[result[ws_col] == 0, col] = pd.NA
            else:
                warn(f"Could not locate column {ws_col}")
    return result


def clean_formatting(df, type="float32"):
    """
    At times when wind speed for a certain height
        is zero, sets the corresponding wind direction
        to NaN (np.nan).
    Also cast data (with '_', o.t. times) to `type`, default float32.
        Disable this by setting `type = None`.
    Finally, fixes duplicates and misordering.
    Assumes that dataframe formatting is already
        otherwise full consistent with guidelines.
    """
    result = df.copy(deep=True)

    for column in result.columns:
        if "_" in column and "time" not in column:
            result[column] = result[column].astype(type)
            columntype, boomStr, *_ = column.split("_")
            if columntype == "ws":
                dircol = f"wd_{boomStr}"
                result.loc[result[column] == 0, dircol] = np.nan

    result = result.sort_values(by="time").set_index("time")
    result = result[~result.index.duplicated(keep="first")]

    return result.reset_index()


def rename_headers(
    df,
    mapper,
    drop_nones: bool = True,
    drop_others: bool = True,
    drop_empty: bool = True,
):
    result = df.copy()
    for col in result.columns:
        col_type, height_str = col.split("_")
        if col_type in mapper:
            if mapper[col_type] is not None:
                new = f"{mapper[col_type]}_{height_str}"
                result.rename(columns={col: new}, inplace=True)
            elif drop_nones:
                result.drop(columns=[col], inplace=True)
        elif drop_others:
            result.drop(columns=[col], inplace=True)
    if drop_empty:
        result.dropna(axis=1, how="all", inplace=True)
    return result
