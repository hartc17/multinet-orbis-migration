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

# Placeholder Orbis schema until the real target schema is obtained (see docs/plan.md Milestone 1).
ORBIS_COLUMNS: list[str] = [
    "orbis_id",
    "boundary_name",
    "boundary_type",
    "code",
    "parent_orbis_id",
    "source_vintage",
    "geometry",
]

ORBIS_CRS = "EPSG:4326"

CODE_COLUMN_BY_BOUNDARY_TYPE: dict[BoundaryType, str] = {
    "state": "FIPS_CODE",
    "county": "FIPS_CODE",
    "zip": "ZIP_CODE",
}
