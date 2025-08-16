import pandas as pd
from collections.abc import Collection
from windprofiles.structures.location import Location
from windprofiles.structures.timeseries import TimeSeries


class Boom:
    def __init__(self, number: int, height: float):
        self.number = number
        """Boom number, uniquely identifying the boom in the tower"""
        self.height = height
        """Height from base of tower"""
        self._data: list[MetData] = []

    @property
    def data(self):
        return self._data


class MetData(TimeSeries):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MetTower:
    def __init__(self, location: Location, booms: Collection[Boom] = []):
        self._location = location
        self._booms = {boom.number: boom for boom in booms}
        if len(self._booms) != len(booms):
            raise ValueError("Boom numbers must be unique")

    def add_boom(self, boom: Boom):
        if (n := boom.number) in self._booms:
            raise ValueError(f"Boom {n} already present in tower")
        self._booms[n] = boom

    def get_boom(self, number: int) -> Boom:
        """Returns the boom with the given number, if it exists, and `None` otherwise."""
        return self._booms.get(number)


class WeatherStationData(TimeSeries):
    def __init__(self, location: Location, data: pd.DataFrame):
        pass
