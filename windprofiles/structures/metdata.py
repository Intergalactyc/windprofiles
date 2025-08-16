import pandas as pd
import pint
import pint_pandas
from collections.abc import Collection
from windprofiles.structures.location import Location
from windprofiles.structures.base import BaseData
from windprofiles.structures.timeseries import TimeSeries


class Boom(BaseData):
    def __init__(self, units: dict, number: int, height: float):
        self.number = number
        """Boom number, uniquely identifying the boom in the tower"""
        self.height = height
        """Height from base of tower"""
        super().__init__(
            metadata={"boom_number": number, "boom_height": height}
        )
        self._slow_data = None
        self._sonic_data = None

    @property
    def slow_data(self):
        return self._slow_data

    @property
    def sonic_data(self):
        return self._sonic_data


class BoomSonicData(TimeSeries):
    def __init__(self, data: pd.DataFrame = pd.DataFrame()):
        super().__init__(data=data)

    def align(self):
        pass


class BoomSlowData(TimeSeries):
    def __init__(
        self,
        data: pd.DataFrame = pd.DataFrame(
            columns=["TEMP", "PRES", "WS", "WD", "W"]
        ),
    ):
        super().__init__(data=data)


class MetTower(BaseData):
    def __init__(self, location: Location, booms: Collection[Boom]):
        self._location = location
        self._booms = {boom.number: boom for boom in booms}
        if len(self._booms) != len(booms):
            raise ValueError("Boom numbers are not unique!")
        for boom in self._booms():
            boom.update_metadata(
                {"height_asl": self._location.elevation + boom.height}
            )

    def add_boom(self, boom: Boom):
        self._booms[boom.number] = boom

    def get_boom(self, number: int) -> Boom:
        """
        Returns the boom with the given number, if it exists, and `None` otherwise.
        """
        return self._booms.get(number)


class WeatherStationData(TimeSeries):
    def __init__(self, location: Location, data: DataFrame):
        pass
