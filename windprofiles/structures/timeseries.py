from pandas import DataFrame
from windprofiles.quantities import Variable
from abc import ABC


class TimeSeries:
    # Dataframe with datetime index, timezone awareness, and unit handling
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


class TimeSeriesCollection(ABC):
    def __init__(self, data: TimeSeries | Collection[TimeSeries] = None):
        self._data_by_frequency = (
            {}
        )  # ideally: some way of indexing by frequency?
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
        # Combine all time series together and sort the index
        pass

    @property
    def timeseries(self):
        # Combine all time series together and sort the index
        # Maybe make TimeSeries allow adding? (If frequencies are same and remains aligned, output frequency is the same, otherwise "irregular")
        # Otherwise just have this in df property
        # Maybe can detect to see if result has a consistent frequency (e.g. adding 5Hz + 10Hz is a 10Hz result if aligned, or 5Hz + 5Hz with proper shift could be 10Hz)
        pass

    def add_data(self, data: TimeSeries):
        if not isinstance(data, TimeSeries):
            pass
        freq = data.frequency
        if freq not in self._data_by_frequency:
            self._data_by_frequency[freq] = []
        self._data_by_frequency[freq].append(data)

    def by_frequency(self, freq: int):
        return self._data_by_frequency.get(freq) or []
