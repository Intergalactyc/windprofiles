import numpy as np
import pandas as pd
import windprofiles.lib.atmos as atmos


STANDARD_UNITS = {
    "p": "kPa",  # pressure
    "t": "K",  # temperature
    "rh": "decimal",  # relative humidity
    "ws": "m/s",  # wind speed
    "wd": (
        "degrees",
        "N",
        "CW",
    ),  # wind direction [angle measure, zero point, orientation]
}


def _convert_pressure(series, from_unit, gravity=atmos.STANDARD_GRAVITY):
    """
    Conversion of pressure units
    If input has format "{unit}_{number}asl", interpreted
        as sea-level pressure and converted to pressure
        at height of <number> meters
    """
    if "_" in from_unit:
        from_unit, masl = from_unit.split("_")
        meters_asl = float(masl[:-3])
        series = atmos.pressure_above_msl(series, meters_asl, gravity=gravity)
    match from_unit:
        case "kPa":
            return series
        case "mmHg":
            return series * 0.13332239
        case "inHg":
            return series * 3.38639
        case "mBar" | "mb":
            return series / 10.0
        case _:
            raise Exception(f"Unrecognized pressure unit {from_unit}")


def _convert_temperature(series, from_unit):
    """
    Conversion of temperature units
    """
    match from_unit:
        case "K":
            return series
        case "C":
            return series + 273.15
        case "F":
            return (series - 32) * (5 / 9) + 273.15
        case _:
            raise Exception(f"Unrecognized temperature unit {from_unit}")


def _convert_humidity(series, from_unit):
    """
    Relative humidity conversions.
    Does not account for other types of humidity -
        just for switching between percent [%] (0-100)
        and decimal (0-1) scales
    """
    match from_unit:
        case "decimal":
            return series
        case ".":
            return series
        case "%":
            return series / 100.0
        case "percent":
            return series / 100.0
        case _:
            raise Exception(f"Unrecognized humidity unit {from_unit}")


def _convert_speed(series, from_unit):
    """
    Conversion of wind speed units
    """
    match from_unit:
        case "m/s":
            return series
        case "mph":
            return series / 2.23694
        case "mi/hr":
            return series / 2.23694
        case "mi/h":
            return series / 2.23694
        case _:
            raise Exception(f"Unrecognized wind speed unit {from_unit}")


def _convert_direction(series, from_unit):
    """
    Conversion of wind direction
    """
    measure, zero, orient = from_unit

    # Convert measure to degrees (possibly from radians)
    if measure in ["rad", "radians"]:
        series = np.rad2deg(series)
    elif measure not in ["deg", "degrees"]:
        raise Exception(f"Unrecognized angle measure {measure}")

    # Convert orientation to clockwise (possibly from counterclockwise)
    if orient.lower() in ["ccw", "counterclockwise"]:
        series = (-series) % 360
    elif orient.lower() not in ["cw", "clockwise"]:
        raise Exception(f"Unrecognized angle orientation {orient}")

    # Align zero point to north
    if type(zero) is str:
        # From cardinal direction
        match zero.lower():
            case "n":
                return series
            case "w":
                return (series - 90) % 360
            case "s":
                return (series - 180) % 360
            case "e":
                return (series - 270) % 360
    elif type(zero) in [int, float]:
        # From degrees offset
        return (series - zero) % 360
    else:
        raise Exception(f"Unrecognized zero type {type(zero)} for {zero}")


def convert_dataframe_units(df, from_units, gravity=atmos.STANDARD_GRAVITY):
    """
    Public function for converting units for all
    (commonly formatted) columns in dataframe based
    on a dictionary of units formatted in the same
    way as the STANDARDS
    """

    result = df.copy(deep=True)

    conversions_by_type = {
        "p": _convert_pressure,
        "t": _convert_temperature,
        "ts": _convert_temperature,
        "rh": _convert_humidity,
        "wd": _convert_direction,
        "ws": _convert_speed,
        "u": _convert_speed,
        "v": _convert_speed,
        "w": _convert_speed,
        "ux": _convert_speed,
        "uy": _convert_speed,
        "uz": _convert_speed,
        "propu": _convert_speed,
        "propv": _convert_speed,
        "propw": _convert_speed,
        "propwd": _convert_direction,
        "propws": _convert_speed,
    }

    for column in result.columns:
        if "_" in column and "time" not in column:
            column_type = column.split("_")[0]
            if column_type in conversions_by_type.keys():
                conversion = conversions_by_type[column_type]
                if column_type == "p":
                    result[column] = conversion(
                        series=result[column],
                        from_unit=from_units[column_type],
                        gravity=gravity,
                    )
                else:
                    result[column] = conversion(
                        series=result[column],
                        from_unit=from_units[column_type],
                    )

    return result


def convert_timezone(
    df: pd.DataFrame, source_timezone: str, target_timezone: str
):
    result = df.copy()
    result.index = df.index.tz_localize(source_timezone).tz_convert(  # type: ignore
        target_timezone
    )
    return result
