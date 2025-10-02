from functools import reduce
import pandas as pd


def dict_checksum(d: dict, verbose: bool = False) -> int:
    result = abs(
        reduce(lambda x, y: x ^ y, [hash(item) for item in d.items()])
    )
    if verbose:
        print(result)
    return result


def dataframe_checksum(df: pd.DataFrame, verbose: bool = False) -> int:
    result = int(pd.util.hash_pandas_object(df).sum())
    if verbose:
        print(result)
    return result
