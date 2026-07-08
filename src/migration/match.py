import geopandas as gpd
import pandas as pd

from migration.schema import (
    ADMIN_LEVEL_BY_BOUNDARY_TYPE,
    CROSSWALK_BOUNDARY_TYPES,
    CROSSWALK_COLUMNS,
    BoundaryType,
)

# NAD83 / Conus Albers Equal Area - used only to compute an accurate interior point for the
# spatial match (centroids on unprojected WGS84 degrees are distorted for large polygons like
# whole states). Inputs and crosswalk output stay in MULTINET_CRS/ORBIS_CRS (WGS84).
_MATCH_CRS = "EPSG:5070"


def match_to_orbis(
    multinet_gdf: gpd.GeoDataFrame,
    orbis_gdf: gpd.GeoDataFrame,
    boundary_type: BoundaryType,
    source_vintage: str,
) -> pd.DataFrame:
    if boundary_type not in CROSSWALK_BOUNDARY_TYPES:
        raise ValueError(
            f"Orbis has no crosswalk support for boundary_type={boundary_type!r} "
            f"(supported: {CROSSWALK_BOUNDARY_TYPES})"
        )

    centroids = multinet_gdf[["ID", "geometry"]].to_crs(_MATCH_CRS)
    centroids["geometry"] = centroids.geometry.centroid

    # A real Orbis/Overture divisions extract mixes every admin level (country, region,
    # county, locality, ...) in one dataset, so candidates must be filtered to the level
    # matching this boundary_type before matching, or e.g. a county centroid could just as
    # validly match its containing state polygon.
    same_level = orbis_gdf[orbis_gdf["admin_level"] == ADMIN_LEVEL_BY_BOUNDARY_TYPE[boundary_type]]
    orbis_projected = same_level[["id", "geometry"]].to_crs(_MATCH_CRS)

    joined = gpd.sjoin(
        centroids,
        orbis_projected,
        how="left",
        predicate="within",
    )

    # A centroid can fall within more than one Orbis polygon at shared borders;
    # keep the first match and let validate_crosswalk flag any resulting duplicates.
    joined = joined.drop_duplicates(subset="ID", keep="first")

    crosswalk = pd.DataFrame(
        {
            "multinet_source_id": joined["ID"],
            "boundary_type": boundary_type,
            "gers_id": joined["id"],
            "match_method": joined["id"].notna().map({True: "spatial", False: "unmatched"}),
            "source_vintage": source_vintage,
        }
    )

    return crosswalk[CROSSWALK_COLUMNS].reset_index(drop=True)
