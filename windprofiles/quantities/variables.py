from windprofiles.quantities.structures import (
    Dimension,
    Variable,
)

_v_temperature = Variable(
    "Temperature",
    Dimension.Temperature,
    [
        "t",
        "temp",
        "tmpr",
    ],
)
_v_dewpoint = Variable(
    "Dewpoint",
    Dimension.Temperature,
    [
        "dwpt",
        "dew",
        "tdew",
    ],
)
_v_relative_humidity = Variable(
    "Relative Humidity",
    Dimension.Dimless,
    [
        "rh",
        "rhum",
        "relh",
        "relative_humidity",
    ],
)
_v_wind_direction = Variable(
    "Wind Direction",
    Dimension.Angle,
    [
        "wd",
        "wdir",
        "dir",
    ],
)
