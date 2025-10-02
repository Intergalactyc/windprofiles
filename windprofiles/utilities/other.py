import pandas as pd
from tqdm import tqdm
import datetime

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def test_frame_discrepancy_by_row(
    df1, df2, silent=False, details=False, exact=False, progress=False
):
    """
    Apply pandas.testing.assert_frame_equal row-by-row to determine mismatch
        locations between two dataframes.
    Boolean options (all default False):
        `silent` to prevent printing
        `details` to print details after every occurrence (may be a lot)
        `exact` to determine the value of `check_exact` passed to the pandas
            function (if it remains the default value of False, then floats will
            be checked to be within default tolerance rather than exactly)
        `progress` to show a tqdm progress bar; you probably shouldn't combine
            this with `details`
    Aside: This was used for comparing old results to those outputted by updated code
        and finding an error in the old shadowing-mean-computation function.
    """
    if df1.shape != df2.shape:
        raise ("Mismatch in shapes")
    caught_rows = []
    n_total = df1.shape[0]
    iterator = tqdm(range(n_total)) if progress else range(n_total)
    for i in iterator:
        try:
            pd.testing.assert_frame_equal(
                pd.DataFrame(df1.iloc[i, :]),
                pd.DataFrame(df2.iloc[i, :]),
                check_exact=exact,
            )
        except AssertionError as e:
            caught_rows.append(i)
            if details:
                print(f"In row {i}:")
                print(e, "\n")
    if not silent:
        n = len(caught_rows)
        print(
            f"\n\n\n\n\n{n} data points affected ({100*n/n_total:.2f}%)\n\n\n\n\n"
        )
    return caught_rows


def time_to_hours(dt: datetime.datetime):
    return dt.hour + dt.minute / 60 + dt.second / 3600


def get_monthly_breakdown(
    df: pd.DataFrame, column: str, ignore: list = []
) -> tuple[pd.DataFrame]:
    """
    Given a dataframe df with a datetime column 'time' as well as the name of a column
        of interest, returns the breakdown of the amount of entries with each value
        in that column, both as number (breakdown, first return value) and fraction of total
        (proportions, second return value)
    """
    classes = [cls for cls in df[column].unique() if cls not in ignore]
    breakdown = pd.DataFrame(index=MONTHS, columns=classes)
    proportions = breakdown.copy()
    for i, mon in enumerate(MONTHS, 1):
        df_mon = df[df["time"].dt.month == i]
        total = len(df_mon)
        for cls in classes:
            df_cls = df_mon[df_mon[column] == cls]
            count = len(df_cls)
            breakdown.loc[mon, cls] = count
            proportions.loc[mon, cls] = count / total
    return breakdown, proportions
