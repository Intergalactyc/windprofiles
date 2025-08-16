from pandas import DataFrame
from windprofiles.structures.base import BaseData


class TimeSeries(BaseData):
    # Dataframe with datetime index, timezone awareness, and per-column units
    def __init__(
        self, data: DataFrame, units: dict, timezone: str, metadata: dict = {}
    ):
        super().__init__(metadata=metadata)
        self._df = data.copy()
        self._tz = timezone  # Timezone of index
        # TODO: set up the datetime index for the dataframe and set timezone for it
        self._units = units
        # TODO: figure out units

    @property
    def df(self):
        return self._df

    def __str__(self):
        return f"TimeSeries<data shape: {self._df.shape}; location: {self._loc}; metadata: {self._metadata}"
