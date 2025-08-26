from shapely.geometry import Point, Polygon
import math
import numpy as np


def circular_region(
    cx: float,
    cy: float,
    radius: float,
    *,
    sector_start: float = None,
    sector_end: float = None,
    segments: int = 128,
) -> Polygon:
    """
    Circlular polygon centered at (cx, cy). By default a full circle; if
    `sector_start` and `sector_end` angles (degrees CCW of +X (East)) are
    provided, a sector (approximated with `segments` segments) is given.
    """

    if sector_start is None and sector_end is None:
        # Just a circle
        return Point(cx, cy).buffer(radius)

    if sector_start is None or sector_end is None:
        # For a sector, start & end both need be specified
        raise ValueError("Sector must be specified with both start and end")

    # Normalize to [0, 360)
    sector_start = sector_start % 360
    sector_end = sector_end % 360
    if sector_end < sector_start:
        sector_end += 360

    start_rad = math.radians(sector_start)
    stop_rad = math.radians(sector_end)

    points = [(cx, cy)]
    for a in np.linspace(start_rad, stop_rad, segments):
        x = cx + radius * math.cos(a)
        y = cy + radius * math.sin(a)
        points.append((x, y))
    points.append((cx, cy))

    return Polygon(points)
