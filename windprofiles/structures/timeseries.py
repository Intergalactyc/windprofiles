from __future__ import annotations
from collections.abc import Collection
import pandas as pd
from windprofiles.quantities import Variable
from abc import ABC


class TimeSeries:
    _units_error = "units must be 'default', 'original', or a dictionary mapping column names to units"

    # Dataframe with datetime index, timezone awareness, and unit handling
    def __init__(
        self,
        data: pd.DataFrame,
        units: dict,
        timezone: str,
        *,
        datetime_format=None,
        start_time=None,
        freq=None,
    ):
        """
        `units` should be a dictionary mapping data column names to units

        `timezone` should be the timezone of the datetime column

        If the datetime column is not of a common format, pass a formatter string with `datetime_format`

        If no datetime column exists in `data`, then a start time `start_time` and frequency `freq`
        (see https://pandas.pydata.org/docs/user_guide/timeseries.html#timeseries-offset-aliases)
        must be provided
        """
        self._warnings = []
        self._df = data.copy()
        self._tz = timezone  # Timezone of index
        self._original_units = units
        self._converted_units = {}
        self._variables_to_columns = {}
        self._columns_to_variables = {}
        # TODO: set up the datetime index for the dataframe and set timezone for it

        explicit_timestamp = False
        for column in self._df.columns:
            if (var := Variable.get(column)) is not None:
                if (
                    existing := self._variables_to_columns.get(var)
                ) is not None:
                    raise ValueError(
                        f"Column '{column}' could not be distinguished from '{existing}' (both parsed as {var.name})"
                    )

                if var is Variable.Timestamp:
                    self._df.index = pd.to_datetime(
                        self._df[column], format=datetime_format
                    )
                    explicit_timestamp = True
                    self._df.drop(column, axis=1)
                    continue

                unit = self._original_units.get(column)

                self._converted_units[column] = var.default_unit
                self._df[column] = var.convert(self._df[column], unit)

                self._variables_to_columns[var] = column
                self._columns_to_variables[column] = var
            else:
                self._warnings.append(
                    f"Dropped column {column} (no matching variable found)"
                )
                self._df.drop(column, axis=1)

        if not explicit_timestamp:
            if not start_time and freq:
                raise TypeError(
                    "Explicit timestamp column not present in data - must provide a start_time and freq"
                )
            self._df.index = pd.date_range(
                start_time,
            )

    def _df_converted(self, to_units: dict):
        out = self._df.copy()
        for column in out.columns:
            var = self._columns_to_variables[column]
            self._variables.get

    @property
    def warnings(self):
        return self._warnings

    @property
    def df(self):
        return self.get_df("default")

    @property
    def units(self):
        return self._converted_units

    def __getitem__(self, key: Variable | str):
        if isinstance(key, Variable):
            var = key
        elif isinstance(key, str):
            var = Variable.get(key)
        if col := self._variables_to_columns.get(var):
            return self._df[col]
        raise KeyError(f"'{key}' is not a variable in the given TimeSeries")

    def get_df(self, units: str | dict = "default"):
        match units:
            case "default":
                return self._df
            case "original":
                return self._df_converted(self._original_units)
            case _:
                if isinstance(units, dict):
                    return self._df_converted(units)
                raise ValueError(TimeSeries._units_error)

    def __str__(self):
        return f"TimeSeries<data shape: {self._df.shape}; units: {self._loc}; index timezone: {self._tz}>"

    def __add__(self, other: TimeSeries) -> TimeSeries:
        pass


class TimeSeriesCollection(ABC):
    def __init__(self, data: TimeSeries | Collection[TimeSeries] = None):
        self._data_by_frequency = {}
        self._all_data = set()
        if data:
            if isinstance(data, TimeSeries):
                self.add_data(data)
            elif isinstance(data, Collection):
                for d in data:
                    self.add_data(d)
            else:
                raise TypeError(
                    f"Cannot construct with data of type {type(data)}"
                )

    @property
    def df(self):
        # Combine all time series together and sort the index, then get its dataframe
        pass

    @property
    def timeseries(self):
        # Combine all time series together and sort the index
        # Maybe make TimeSeries allow adding? (If frequencies are same and remains aligned, output frequency is the same, otherwise "irregular")
        # Otherwise just have this in df property
        # Maybe can detect to see if result has a consistent frequency (e.g. adding 5Hz + 10Hz is a 10Hz result if aligned, or 5Hz + 5Hz with proper shift could be 10Hz)
        return sum(self._all_data)

    def add_data(self, data: TimeSeries, *args, **kwargs):
        if not isinstance(data, TimeSeries):
            if isinstance(data, pd.DataFrame):
                try:
                    ts = TimeSeries(data, *args, **kwargs)
                except TypeError:
                    print(
                        "Could not parse provided DataFrame as TimeSeries: make sure to provide all required arguments (data, units, timezone), or pass a TimeSeries object"
                    )
                    raise
                else:
                    self.add_data(ts)
        freq = data.frequency
        if freq not in self._data_by_frequency:
            self._data_by_frequency[freq] = []
        self._data_by_frequency[freq].append(data)

    def by_frequency(self, freq: int):
        return self._data_by_frequency.get(freq) or []
