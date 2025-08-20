from __future__ import annotations
from dataclasses import dataclass
from windprofiles.lib.geo import local_gravity
from windprofiles.data.gmaps import get_elevation, get_timezone
from geopy.distance import geodesic
from abc import ABC


@dataclass
class Location:
    latitude: float
    """Latitude in degrees"""
    longitude: float
    """Longitude in degrees"""
    elevation: float = None
    """Elevation ASL in meters"""
    timezone: str = None
    """
    Local timezone, in representation such as "US/Central" or "America/Los_Angeles"
    (may be used in Pandas' tz_localize/tz_convert where relevant)
    """
    is_unknown: bool = False

    def __post_init__(self):
        if self.is_unknown:
            if self.elevation is None:
                self.elevation = 0.0
            self.g = 9.80665
        else:
            if self.elevation is None:
                elev = get_elevation(self.latitude, self.longitude)
                if elev is None:
                    raise ValueError(
                        "Could not determine elevation from latitude and longitude: check API key/connection or input manually."
                    )
                self.elevation = elev
            if self.timezone is None:
                tz = get_timezone(self.latitude, self.longitude)
                if tz is None:
                    raise ValueError(
                        "Could not determine timezone from latitude and longitude: check API key/connection or input manually."
                    )
                self.timezone = tz
            self.g = local_gravity(self.latitude, self.elevation)
        self.distance = self._distance

    @property
    def coords(self):
        return (self.latitude, self.longitude)

    @staticmethod
    def unknown() -> Location:
        return Location(None, None, is_unknown=True)

    @staticmethod
    def distance(
        first: Location,
        second: Location,
    ) -> float:
        """Returns: distance between locations in meters"""
        return geodesic(first.coords, second.coords).m

    def _distance(self, other: Location, *args, **kwargs) -> float:
        return Location.distance(self, other, *args, **kwargs)

    def __str__(self):
        if self.is_unknown:
            return "UnknownLocation<>"
        return f"Location<latitude: {self.latitude}; longitude: {self.longitude}; elevation: {self.elevation}; timezone: {self.timezone}; local gravity: {self.g}"


class LocalizedData(ABC):
    def __init__(self, location: Location):
        if not isinstance(location, Location):
            raise TypeError("location must be a Location object")
        self._location = location

    @property
    def location(self) -> Location:
        return self._location
