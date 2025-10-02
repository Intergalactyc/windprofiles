# ruff: noqa: E402

import os
from windprofiles.utilities.location import Location
from windprofiles.utilities.classify import (
    TerrainClassifier,
    StabilityClassifier,
    CoordinateRegion,
)
from windprofiles.user.args import Parser

# Expose data submodules as top-level modules (so one can e.g.
# `import windprofiles.meteostat` rather than `import windprofiles.data.meteostat`)
__path__.insert(0, os.path.join(os.path.dirname(__file__), "data"))
from windprofiles.data import meteostat, gmaps

__version__ = "0.0.1"

__all__ = [
    "TerrainClassifier",
    "StabilityClassifier",
    "CoordinateRegion",
    "Location",
    "Parser",
    "meteostat",
    "gmaps",
]
