import pandas as pd
from collections.abc import Collection
from windprofiles.structures.location import Location, LocalizedData
from windprofiles.structures.timeseries import TimeSeries, TimeSeriesCollection
from windprofiles.quantities import Dimension


class Boom(TimeSeriesCollection):
    def __init__(self, number: int, height: float, height_unit: str = "m"):
        self.number = number
        """Boom number, uniquely identifying the boom in the tower"""
        self.height = Dimension.Height.convert_from(height, height_unit)
        """Height from base of tower (converted to height default unit)"""


class MetTower(LocalizedData):
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


class WeatherStation(TimeSeriesCollection, LocalizedData):
    def __init__(self, location: Location, data: pd.DataFrame = None):
        super().__init__(location=location, data=data)

    # TODO: change how windprofiles.data things create WeatherStation
