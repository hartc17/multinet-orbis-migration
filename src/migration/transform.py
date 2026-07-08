import geopandas as gpd

from migration.schema import CODE_COLUMN_BY_BOUNDARY_TYPE, ORBIS_COLUMNS, BoundaryType


def transform_boundaries(
    gdf: gpd.GeoDataFrame, boundary_type: BoundaryType, source_vintage: str
) -> gpd.GeoDataFrame:
    code_column = CODE_COLUMN_BY_BOUNDARY_TYPE[boundary_type]

    orbis = gpd.GeoDataFrame(
        {
            "orbis_id": gdf["ID"],
            "boundary_name": gdf["NAME"],
            "boundary_type": boundary_type,
            "code": gdf[code_column],
            "parent_orbis_id": gdf["PARENT_ID"] if "PARENT_ID" in gdf.columns else None,
            "source_vintage": source_vintage,
            "geometry": gdf["geometry"],
        },
        crs=gdf.crs,
    )

    return orbis[ORBIS_COLUMNS]
