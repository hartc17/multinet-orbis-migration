from typing import Literal

BoundaryType = Literal["state", "county", "zip"]

BOUNDARY_TYPES: tuple[BoundaryType, ...] = ("state", "county", "zip")

# Placeholder field names until a real Multinet sample/spec is obtained (see docs/plan.md Milestone 1).
# Do not treat these as authoritative TomTom Multinet column names.
MULTINET_REQUIRED_COLUMNS: dict[BoundaryType, list[str]] = {
    "state": ["ID", "NAME", "FIPS_CODE", "geometry"],
    "county": ["ID", "NAME", "FIPS_CODE", "PARENT_ID", "geometry"],
    "zip": ["ID", "NAME", "ZIP_CODE", "PARENT_ID", "geometry"],
}

MULTINET_CRS = "EPSG:4326"

# Orbis is built on the Overture Maps Foundation "divisions" schema. These field names and
# values are CONFIRMED against real Overture open data (release 2026-06-17.0,
# theme=divisions, type=division_area, read directly from Overture's public S3 bucket since
# Orbis's own docs are unreachable - see docs/plan.md). `id` is the GERS ID itself, formatted
# as a UUID string, not a separately-named or differently-shaped field.
#
# CONFIRMED GAP: Overture's divisions theme has no zip/postal-code-equivalent boundary
# anywhere in Texas (admin_level only goes 0=country, 1=region/state, 2=county; the only
# subtypes present are country/region/county/locality/neighborhood/microhood/macrohood).
# Zip is therefore excluded from CROSSWALK_BOUNDARY_TYPES until/unless a different Orbis
# data source for postal boundaries is confirmed (see docs/plan.md).
CROSSWALK_BOUNDARY_TYPES: tuple[BoundaryType, ...] = ("state", "county")

ORBIS_REQUIRED_COLUMNS: dict[BoundaryType, list[str]] = {
    "state": ["id", "subtype", "admin_level", "geometry"],
    "county": ["id", "subtype", "admin_level", "geometry"],
}

ORBIS_CRS = "EPSG:4326"

ADMIN_LEVEL_BY_BOUNDARY_TYPE: dict[BoundaryType, int] = {
    "state": 1,
    "county": 2,
}

CODE_COLUMN_BY_BOUNDARY_TYPE: dict[BoundaryType, str] = {
    "state": "FIPS_CODE",
    "county": "FIPS_CODE",
    "zip": "ZIP_CODE",
}

CROSSWALK_COLUMNS: list[str] = [
    "multinet_source_id",
    "boundary_type",
    "gers_id",
    "match_method",
    "source_vintage",
]
