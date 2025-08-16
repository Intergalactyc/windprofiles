# ruff: noqa: E402

import os

from windprofiles.structures.location import Location
from windprofiles.structures.metdata import Boom, MetTower

# Expose data submodules as top-level modules (so one can e.g.
# `import windprofiles.meteostat` rather than `import windprofiles.data.meteostat`)
__path__.insert(0, os.path.join(os.path.dirname(__file__), "data"))
from windprofiles.data import meteostat, gmaps

__version__ = "0.0.1"

__all__ = ["Location", "Boom", "MetTower", "meteostat", "gmaps"]
