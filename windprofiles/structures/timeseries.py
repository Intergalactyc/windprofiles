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
        self._original_units = units
        self._converted_units = {}
        self._variables = {}
        # TODO: set up the datetime index for the dataframe and set timezone for it

        for column in data.columns:
            if (var := Variable.get(column)) is not None:
                unit = units.get(column)
                data[column] = var.convert(data[column], unit)
                if (existing := self._variables.get(var)) is not None:
                    raise ValueError(
                        f"Column '{column}' could not be distinguished from '{existing}' (both parsed as {var.name})"
                    )
                self._variables[var] = column

    @property
    def df(self):
        return self._df

    def __str__(self):
        return f"TimeSeries<data shape: {self._df.shape}; units: {self._loc}; index timezone: {self._tz}>"
