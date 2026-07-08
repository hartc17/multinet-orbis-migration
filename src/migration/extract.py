from pathlib import Path

import geopandas as gpd

from migration.schema import (
    MULTINET_CRS,
    MULTINET_REQUIRED_COLUMNS,
    ORBIS_CRS,
    ORBIS_REQUIRED_COLUMNS,
    BoundaryType,
)


def read_multinet_boundaries(path: Path, boundary_type: BoundaryType) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)

    required = MULTINET_REQUIRED_COLUMNS[boundary_type]
    missing = [col for col in required if col not in gdf.columns]
    if missing:
        raise ValueError(f"Multinet {boundary_type} source at {path} is missing columns: {missing}")

    if gdf.crs is None or gdf.crs.to_string() != MULTINET_CRS:
        raise ValueError(
            f"Multinet {boundary_type} source at {path} has CRS {gdf.crs}, expected {MULTINET_CRS}"
        )

    return gdf


def read_orbis_divisions(path: Path, boundary_type: BoundaryType) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)

    required = ORBIS_REQUIRED_COLUMNS[boundary_type]
    missing = [col for col in required if col not in gdf.columns]
    if missing:
        raise ValueError(f"Orbis {boundary_type} source at {path} is missing columns: {missing}")

    if gdf.crs is None or gdf.crs.to_string() != ORBIS_CRS:
        raise ValueError(
            f"Orbis {boundary_type} source at {path} has CRS {gdf.crs}, expected {ORBIS_CRS}"
        )

    return gdf
