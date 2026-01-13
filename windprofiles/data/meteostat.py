from datetime import datetime
from windprofiles.utilities.location import Location
from meteostat import Stations, Hourly, Daily, Monthly # TODO: update to meteostat>=2.0.0 (API overhaul, these won't work)
from pandas import DataFrame


def get_weather_data(
    location: Location, period: tuple[datetime, datetime], frequency="hourly"
) -> DataFrame:
    start, end = period
    if end <= start:
        raise ValueError("end timestamp must be after start timestamp")
    if location.latitude is None or location.longitude is None:
        raise ValueError("Location must have a latitude and longitude")
    station = Stations().nearby(location.latitude, location.longitude).fetch(1)
    match frequency:
        case "hourly":
            data = (
                Hourly(station, start, end)
                .fetch()
                .reset_index()[
                    [
                        "time",
                        "temp",
                        "wspd",
                        "wdir",
                        "pres",
                        "rhum",
                        "prcp",
                        "snow",
                    ]
                ]
            )
            data.rename(
                columns={
                    "temp": "t",
                    "rhum": "rh",
                    "wdir": "wd",
                    "wspd": "ws",
                    "pres": "p",
                }
            )
        case "daily":
            data = (
                Daily(station, start, end)
                .fetch()
                .reset_index()[
                    ["time", "tavg", "wspd", "wdir", "pres", "prcp", "snow"]
                ]
            )
            data.rename(
                columns={
                    "tavg": "t",
                    "wdir": "wd",
                    "wspd": "ws",
                    "pres": "p",
                }
            )
        case "monthly":
            data = (
                Monthly(station, start, end)
                .fetch()
                .reset_index()[["time", "tavg", "wspd", "pres", "prcp"]]
            )
            data.rename(
                columns={
                    "tavg": "t",
                    "wdir": "wd",
                    "wspd": "ws",
                    "pres": "p",
                }
            )
        case _:
            raise ValueError(
                f"Frequency '{frequency}' is invalid (must be 'hourly', 'daily', or 'monthly')"
            )
    station = station.iloc[0]
    return data
    # return WeatherStation(
    #     df=data,
    #     station_wmo_id=station.get("wmo"),
    #     station_icao_id=station.get("icao"),
    #     station_name=station.get("name"),
    #     units={
    #         "t": "C",
    #         "prcp": "mm",
    #         "snow": "mm",
    #         "p": "hPa",
    #         "ws": "km/h",
    #         "wd": "CW-N",
    #         "rh": "%",
    #     },
    #     timezone="UTC",
    #     location=Location(
    #         latitude=station["latitude"],
    #         longitude=station["longitude"],
    #         elevation=station["elevation"],
    #         timezone=station["timezone"],
    #     ),
    # )
