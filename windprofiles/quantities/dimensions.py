from windprofiles.quantities.core import (
    Dimension,
)
from math import pi

_d_temperature = Dimension(
    "Temperature",
    ["t"],
    "K",
)
_d_temperature.register_unit("C", 1, -273.15)
_d_temperature.register_unit(
    "F",
    5 / 9,
    -459.67,
)

_d_fractional = Dimension(
    "Dimensionless",
    ["dimless"],
    "decimal",
)
_d_fractional.register_unit("%", 0.01)

_d_direction = Dimension(
    "Angle",
    ["dir"],
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
