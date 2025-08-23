from windprofiles.quantities.core import (
    Dimension,
)
from math import pi

_d_temperature = Dimension(
    "Temperature", ["T"], "K", default_unit_aliases=["Kelvin"]
)
_d_temperature.register_unit(
    "°C", 1, -273.15, aliases=["degC", "C", "Celsius"]
)
_d_temperature.register_unit(
    "°F", 5 / 9, -459.67, aliases=["degF", "F", "Fahrenheit"]
)
_d_temperature.register_unit("R", 5 / 9, aliases=["degR", "R", "Rankine"])

_d_pressure = Dimension(
    "Pressure",
    [],
    "kPa",
    default_unit_aliases=["N/m^2", "kilopascal", "kilopascals"],
)
_d_pressure.register_unit("Pa", 0.001, aliases=["pascal"])
_d_pressure.register_unit("atm", 101.325)
_d_pressure.register_unit("mmHg", 0.133322368)
_d_pressure.register_unit("psi", 6.89475729)

_d_distance = Dimension(
    "Distance",
    ["Height", "Length", "Width"],
    "m",
    default_unit_aliases=["meter", "meters"],
)
_d_distance.register_unit("km", 1000, aliases=["kilometer", "kilometers"])
_d_distance.register_unit("ft", 0.3048, aliases=["foot", "feet"])
_d_distance.register_unit("mi", 1609.34, aliases=["mile", "miles"])
_d_distance.register_unit("yd", 0.9144, aliases=["yard", "yards", "yds"])

_d_speed = Dimension(
    "Speed",
    ["Velocity"],
    "m/s",
    default_unit_aliases=["meters per second"],
)
_d_speed.register_unit(
    "mi/h", 0.44704, aliases=["mi/hr", "mph", "miles per hour"]
)
_d_speed.register_unit(
    "ft/s",
    0.3048,
    aliases=["feet/s", "ft/sec", "feet/sec", "feet per second", "fps"],
)

_d_timestamp = Dimension(
    "Timestamp", [], None
)  # Special dimension (only for use in Variable.Timestamp recognition)

_d_time = Dimension(
    "Time",
    [],
    "s",
    default_unit_aliases=["second", "seconds", "sec"],
)
_d_time.register_unit("min", 60, aliases=["minute", "minutes"])
_d_time.register_unit("hr", 3600, aliases=["hour", "hrs", "hours"])

_d_fractional = Dimension(
    "Dimensionless",
    ["Dimless", "Fractional", "Specific"],
    "decimal",
    default_unit_aliases=["1", "unitless", "g/g", "kg/kg"],
)
_d_fractional.register_unit("%", 0.01)
_d_fractional.register_unit("g/kg", 0.001)

_d_density = Dimension("Density", [], "g/L", default_unit_aliases=["g/m^3"])
_d_density.register_unit("kg/L", 1000, aliases=["kg/m^3"])

_d_direction = Dimension(
    "Angle",
    ["Direction"],
    "degCW-N",
)
for zero, zval in [
    ("N", 0),
    ("E", 90),
    ("S", 180),
    ("W", 270),
]:
    _d_direction.register_unit(
        f"radCW-{zero}",
        factor=None,
        converter=lambda x: (x * 180 / pi + zval) % 360,
        inverse_converter=lambda x: ((x - zval) * pi / 180) % (2 * pi),
        ignore_existing=True,
    )
    _d_direction.register_unit(
        f"radCCW-{zero}",
        factor=None,
        converter=lambda x: (-x * 180 / pi + zval) % 360,
        inverse_converter=lambda x: ((-x - zval) * pi / 180) % (2 * pi),
    )
    _d_direction.register_unit(
        f"degCW-{zero}",
        factor=None,
        converter=lambda x: (x + zval) % 360,
        inverse_converter=lambda x: (x - zval) % 360,
    )
    _d_direction.register_unit(
        f"degCCW-{zero}",
        factor=None,
        converter=lambda x: (-x + zval) % 360,
        inverse_converter=lambda x: (-x - zval) % 360,
    )
