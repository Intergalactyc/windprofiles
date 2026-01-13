import pandas as pd
import windprofiles.lib.atmos as atmos
import windprofiles.lib.stats as stats
import windprofiles.lib.polar as polar
from windprofiles.utilities.classify import (
    TerrainClassifier,
    PolarClassifier,
    StabilityClassifier,
    SingleClassifier,
)
from warnings import warn
from windprofiles.lib.atmos import STANDARD_GRAVITY


def strip_failures(
    df: pd.DataFrame, subset: list[str]
) -> tuple[pd.DataFrame, int]:

    result = df.dropna(axis="rows", how="any", subset=subset) # pyright: ignore[reportArgumentType]

    n_dropped = len(df) - len(result)

    return result, n_dropped


def virtual_potential_temperatures(
    df: pd.DataFrame,
    booms: list[int],
    heights: list[float],
    *,
    substitutions: dict[str,str] = {},
) -> pd.DataFrame:
    """
    Compute virtual potential temperatures at all given heights.
    Creates new columns in the dataframe with the results.
    """
    result = df.copy()

    for b, h in zip(booms, heights):

        rh_str = f"rh_{b}"
        p_str = f"p_{b}"
        t_str = f"t_{b}"

        if rh_str in substitutions.keys():
            rh_str = substitutions[rh_str]
        if p_str in substitutions.keys():
            p_str = substitutions[p_str]
        if t_str in substitutions.keys():
            t_str = substitutions[t_str]

        result[f"vpt_{b}"] = atmos.vpt_from_3(
            relative_humidity=result[rh_str],
            barometric_air_pressure=result[p_str],
            temperature=result[t_str],
        )

    return result


def environmental_lapse_rate(
    df: pd.DataFrame,
    variable: str,
    booms: list[int]|tuple[int],
    heights: list[int|float]|tuple[int|float],
) -> pd.DataFrame:
    """
    Approximate environmental lapse rate of a variable between two heights.
    Creates a new column in the dataframe with the results.
    """

    if (
        type(booms) not in [list, tuple]
        or len(booms) != 2
        or booms[0] == booms[1]
    ):
        raise Exception(f"invalid booms {booms}")
    if (
        type(heights) not in [list, tuple]
        or len(heights) != 2
        or heights[0] == heights[1]
    ):
        raise Exception(f"invalid heights {heights}")
    if type(variable) is not str:
        raise Exception(f"invalid variable {variable}")

    h1 = min(heights)
    h2 = max(heights)
    h1_str = f"{variable}_{booms[heights.index(h1)]}"
    h2_str = f"{variable}_{booms[heights.index(h2)]}"

    result = df.copy()

    if h1_str not in result.columns:
        raise Exception(f"{h1_str} not found in DataFrame columns")
    if h2_str not in result.columns:
        raise Exception(f"{h2_str} not found in DataFrame columns")

    result[f"{variable}_lapse"] = (result[h2_str] - result[h1_str]) / (h2 - h1)

    return result


def bulk_richardson_number(
    df: pd.DataFrame,
    booms: list[int]|tuple[int],
    heights: list[int|float]|tuple[int|float],
    *,
    components: bool = False,
    suffix: str = "",
    gravity: float = STANDARD_GRAVITY,
    colname="Ri_bulk",
) -> pd.DataFrame:
    """
    Compute bulk Richardson number Ri_bulk using data at two heights.
    Creates a new column in the dataframe with the results.
    """

    if (
        type(booms) not in [list, tuple]
        or len(booms) != 2
        or booms[0] == booms[1]
    ):
        raise Exception(f"invalid booms {booms}")
    if (
        type(heights) not in [list, tuple]
        or len(heights) != 2
        or heights[0] == heights[1]
    ):
        raise Exception(f"invalid heights {heights}")

    h_lower = min(heights)
    h_upper = max(heights)

    b_lower = booms[heights.index(h_lower)]
    b_upper = booms[heights.index(h_upper)]

    result = df.copy()
    if components:
        result[colname] = result.apply(
            lambda row: atmos.bulk_richardson_number(
                row[f"vpt_{b_lower}{suffix}"],
                row[f"vpt_{b_upper}{suffix}"],
                h_lower,
                h_upper,
                row[f"u_{b_lower}{suffix}"],
                row[f"u_{b_upper}{suffix}"],
                row[f"v_{b_lower}{suffix}"],
                row[f"v_{b_upper}{suffix}"],
                components=True,
                gravity=gravity,
            ),
            axis=1,
        )
    else:
        result[colname] = result.apply(
            lambda row: atmos.bulk_richardson_number(
                row[f"vpt_{b_lower}{suffix}"],
                row[f"vpt_{b_upper}{suffix}"],
                h_lower,
                h_upper,
                row[f"ws_{b_lower}{suffix}"],
                row[f"ws_{b_upper}{suffix}"],
                row[f"wd_{b_lower}{suffix}"],
                row[f"wd_{b_upper}{suffix}"],
                gravity=gravity,
            ),
            axis=1,
        )

    return result


def veer(
    df: pd.DataFrame,
    booms: list[int]|tuple[int],
    *,
    suffix: str = "",
    colname="veer",
) -> pd.DataFrame:  #
    """
    Compute signed veer in wind direction between two booms.
    If vertical turning is CW, return +, if it is CCW, return -.
    Creates a new column in the dataframe with the results.
    """
    # May expect large discontinuities when veer is significant

    if (
        type(booms) not in [list, tuple]
        or len(booms) != 2
        or booms[0] == booms[1]
    ):
        raise Exception(f"invalid booms {booms}")

    b_lower = min(booms)
    b_upper = max(booms)

    result = df.copy()
    result[colname] = polar.series_signed_angular_distance(
        result[f"wd_{b_upper}"], result[f"wd_{b_lower}"]
    )

    return result


def classifications(
    df: pd.DataFrame,
    *,
    terrain_classifier: PolarClassifier | TerrainClassifier | None = None,
    stability_classifier: SingleClassifier | StabilityClassifier | None = None,
) -> pd.DataFrame:
    """
    Classify terrain and/or stability for each timestamp in a dataframe.
    Creates a new column in the dataframe for each type of result.
    """
    if terrain_classifier is None and stability_classifier is None:
        warn("Neither terrain nor stability classifier passed")

    result = df.copy()

    if terrain_classifier is not None:
        result["terrain"] = terrain_classifier.classify_rows(result)
    if stability_classifier is not None:
        result["stability"] = stability_classifier.classify_rows(result)

    return result


def power_law_fits(
    df: pd.DataFrame,
    booms: list[int],
    heights: list[int],
    minimum_present: int = 2,
    columns: list[str] = ["beta", "alpha"],
    suffix: str = "",
):
    """
    Fit power law u(z) = A z ^ B to each timestamp in a dataframe.
    Creates new columns columns[0] and column[1] for the coefficients
        A and B ('beta' and 'alpha' by default) respectively.
    """

    if type(minimum_present) is not int or minimum_present < 2:
        raise Exception(f"invalid argument {minimum_present=}")
    if len(heights) < minimum_present:
        raise Exception("insufficient number of heights provided")
    if type(columns) not in [tuple, list] or len(columns) != 2:
        raise Exception(
            "'columns' must be a tuple or list of two column names for the multiplicative coefficient and power, respectively"
        )

    result = df.copy()

    result[["A_PRIMITIVE", "B_PRIMITIVE"]] = result.apply(
        lambda row: stats.power_fit(
            heights,
            [row[f"ws_{b}{suffix}"] for b in booms],
            require=minimum_present,
        ),
        axis=1,
        result_type="expand",
    )

    if columns[0] is None:
        result.drop(columns=["A_PRIMITIVE"], inplace=True)
    elif type(columns[0]) is str:
        result.rename(columns={"A_PRIMITIVE": columns[0]}, inplace=True)
    if columns[1] is None:
        result.drop(columns=["B_PRIMITIVE"], inplace=True)
    elif type(columns[1]) is str:
        result.rename(columns={"B_PRIMITIVE": columns[1]}, inplace=True)

    return result
