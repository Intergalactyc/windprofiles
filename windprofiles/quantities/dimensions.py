from windprofiles.quantities.core import (
    Dimension,
)
from math import pi

_d_temperature = Dimension(
    "Temperature",
    ["T"],
    "K",
)
_d_temperature.register_unit("C", 1, -273.15)
_d_temperature.register_unit("°C", 1, -273.15)
_d_temperature.register_unit(
    "F",
    5 / 9,
    -459.67,
)
_d_temperature.register_unit(
    "°F",
    5 / 9,
    -459.67,
)
_d_temperature.register_unit("R", 5 / 9)

_d_pressure = Dimension("Pressure", [], "kPa")
_d_pressure.register_unit("Pa", 0.001)
_d_pressure.register_unit("N/m^2", 1),
_d_pressure.register_unit("atm", 101.325)
_d_pressure.register_unit("mmHg", 0.133322368)
_d_pressure.register_unit("psi", 6.89475729)

_d_fractional = Dimension(
    "Dimensionless",
    ["Dimless", "Fractional"],
    "decimal",
)
_d_fractional.register_unit("%", 0.01)
_d_fractional.register_unit("1", 1)
_d_fractional.register_unit("unitless", 1)

_d_specific = Dimension("Specific", [], "g/g")
_d_specific.register_unit("kg/kg", 1)
_d_specific.register_unit("g/kg", 1000)

_d_density = Dimension("Density", [], "g/L")
_d_density.register_unit("g/m^3", 1)

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
