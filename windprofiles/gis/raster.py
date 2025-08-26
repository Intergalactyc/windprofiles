from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.features import geometry_mask
from affine import Affine
from shapely.geometry import Polygon, mapping
from pyproj import Transformer
from os import PathLike
from windprofiles.gis.polygons import circular_region


@dataclass
class Raster:
    data: np.ndarray
    transform: Affine
    meta: dict[str, Any]

    @classmethod
    def from_file(cls, raster_path: str | PathLike):
        return cls.from_files([raster_path])

    @classmethod
    def from_files(cls, raster_paths: list[str | PathLike]) -> Raster:
        """
        Load one or multiple rasters into a single Raster object.
        All rasters must share the same CRS.
        The rasters are combined as a mosaic.
        """
        if not raster_paths:
            raise ValueError("raster_paths is empty")

        src_files = [rasterio.open(p) for p in raster_paths]
        try:
            base_crs = src_files[0].crs
            if any(src.crs != base_crs for src in src_files):
                raise ValueError(
                    "All rasters must have the same CRS before merging."
                )

            nodata_value = src_files[0].nodata
            first_dtype = src_files[0].dtypes[0]

            # For float rasters with no nodata, use NaN
            if nodata_value is None and np.issubdtype(
                np.dtype(first_dtype), np.floating
            ):
                nodata_value: Optional[float] = np.nan

            mosaic, out_transform = merge(src_files, nodata=nodata_value)

            out_meta = src_files[0].meta.copy()
            out_meta.update(
                {
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_transform,
                    "count": 1,
                    "dtype": str(mosaic.dtype),
                    "nodata": nodata_value,
                    "crs": base_crs,
                }
            )

            return cls(data=mosaic[0], transform=out_transform, meta=out_meta)
        finally:
            for s in src_files:
                s.close()

    def _values_in_geometry(
        self, geom: Polygon, all_touched: bool = False
    ) -> np.ndarray:
        """
        Extract values from Raster.data that fall inside 'geom' (in Raster CRS).
        Returns a 1D array of values.
        """
        mask_in = geometry_mask(
            [mapping(geom)],
            out_shape=self.data.shape,
            transform=self.transform,
            all_touched=all_touched,
            invert=True,
        )
        return self.data[mask_in]

    def transform_point(self, latitude: float, longitude: float):
        crs = self.meta["crs"]
        transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        return transformer.transform(longitude, latitude)

    def circular_region_around(
        self, latitude: float, longitude: float, *args, **kwargs
    ):
        return circular_region(
            *self.transform_point(latitude, longitude), *args, **kwargs
        )

    def stats_in_region(
        self, geom: Polygon, *, all_touched: bool = False
    ) -> dict[str, Optional[float]]:
        """
        Compute statistics within a certain region.
        """

        # Extract values from in-memory mosaic
        vals = self._values_in_geometry(geom, all_touched=all_touched)

        # Handle nodata and NaN
        if vals.size == 0:
            return {"min": None, "max": None, "mean": None, "std": None}

        nodata = self.meta.get("nodata", None)
        if nodata is None:
            if np.issubdtype(vals.dtype, np.floating):
                valid = vals[~np.isnan(vals)]
            else:
                valid = vals
        else:
            if isinstance(nodata, float) and np.isnan(nodata):
                valid = vals[~np.isnan(vals)]
            else:
                valid = vals[vals != nodata]

        if valid.size == 0:
            return {"min": None, "max": None, "mean": None, "std": None}

        return {
            "min": float(np.min(valid)),
            "max": float(np.max(valid)),
            "mean": float(np.mean(valid)),
            "std": float(np.std(valid)),
        }
