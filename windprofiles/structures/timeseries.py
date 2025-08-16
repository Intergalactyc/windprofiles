from pandas import DataFrame
from windprofiles.quantities import Variable


class TimeSeries:
    # Dataframe with datetime index and timezone awareness
    def __init__(
        self,
        data: DataFrame,
        units: dict,
        timezone: str,
    ):
        """`units` should be a dictionary mapping data column names to units"""
        self._df = data.copy()
        self._tz = timezone  # Timezone of index
        # TODO: set up the datetime index for the dataframe and set timezone for it

        for column in data.columns:
            unit = units.get(column)
            if (var := Variable.get(column)) is not None:
                var.convert(data[column], "unit")
            else:
                pass

    @property
    def df(self):
        return self._df

    def __str__(self):
        return f"TimeSeries<data shape: {self._df.shape}; units: {self._loc}; index timezone: {self._tz}>"
