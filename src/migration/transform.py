import geopandas as gpd

from migration.schema import (
    ADMIN_LEVEL_BY_BOUNDARY_TYPE,
    CODE_COLUMN_BY_BOUNDARY_TYPE,
    ORBIS_COLUMNS,
    BoundaryType,
)


def transform_boundaries(
    gdf: gpd.GeoDataFrame, boundary_type: BoundaryType, source_vintage: str
) -> gpd.GeoDataFrame:
    code_column = CODE_COLUMN_BY_BOUNDARY_TYPE[boundary_type]

    # gers_id/parent_gers_id are left unresolved here: GERS IDs are assigned by Overture/Orbis
    # itself, not derivable from Multinet fields. A later match step (spatial + code join
    # against real Orbis divisions data) is what fills these in.
    orbis = gpd.GeoDataFrame(
        {
            "gers_id": None,
            "multinet_source_id": gdf["ID"],
            "name": gdf["NAME"],
            "boundary_type": boundary_type,
            "admin_level": ADMIN_LEVEL_BY_BOUNDARY_TYPE[boundary_type],
            "code": gdf[code_column],
            "parent_gers_id": None,
            "source_vintage": source_vintage,
            "geometry": gdf["geometry"],
        },
        crs=gdf.crs,
    )

    return orbis[ORBIS_COLUMNS]
