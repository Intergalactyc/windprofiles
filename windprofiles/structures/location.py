from dataclasses import dataclass
from ..lib.geo import local_gravity
from ..data.gmaps import get_elevation, get_timezone


@dataclass
class Location:
    latitude: float
    """Latitude in degrees"""
    longitude: float
    """Longitude in degrees"""
    elevation: float = None
    """Elevation in meters"""
    timezone: str = None
    """
    Local timezone, in representation such as "US/Central" or "America/Los_Angeles"
    (will be used in Pandas' tz_localize/tz_convert where relevant)
    """

    def __post_init__(self):
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
