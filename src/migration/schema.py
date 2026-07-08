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

# Orbis is built on the Overture Maps Foundation "divisions" schema (division/division_area/
# division_boundary), identified by GERS IDs (stable 128-bit identifiers) and a numeric
# admin_level hierarchy field (confirmed via Overture's public schema docs, 2026-07-08 research).
# Overture assigns GERS IDs itself; this pipeline does not mint them. `gers_id` here is
# therefore the id we expect to receive back from an Orbis lookup/match, not one we generate.
# `subtype` and the exact code/postal representation are NOT yet confirmed against real
# Orbis output and must be revisited once real Orbis data is obtained (see docs/plan.md).
ORBIS_COLUMNS: list[str] = [
    "gers_id",
    "multinet_source_id",
    "name",
    "boundary_type",
    "admin_level",
    "code",
    "parent_gers_id",
    "source_vintage",
    "geometry",
]

ORBIS_CRS = "EPSG:4326"

# Placeholder until real Orbis divisions data confirms the actual admin_level values used
# for state/county/zip in the US (see docs/plan.md).
ADMIN_LEVEL_BY_BOUNDARY_TYPE: dict[BoundaryType, int] = {
    "state": 1,
    "county": 2,
    "zip": 3,
}

CODE_COLUMN_BY_BOUNDARY_TYPE: dict[BoundaryType, str] = {
    "state": "FIPS_CODE",
    "county": "FIPS_CODE",
    "zip": "ZIP_CODE",
}
