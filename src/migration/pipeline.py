import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from migration.extract import read_multinet_boundaries, read_orbis_divisions
from migration.fips_check import cross_check_fips
from migration.match import match_to_orbis
from migration.schema import BoundaryType
from migration.validate import (
    CrosswalkValidationReport,
    GeometryValidationReport,
    validate_crosswalk,
    validate_geometry,
)
from migration.wikidata import fetch_fips_code


class InvalidSourceGeometryError(ValueError):
    pass


@dataclass
class PipelineResult:
    crosswalk: pd.DataFrame
    multinet_geometry_report: GeometryValidationReport
    orbis_geometry_report: GeometryValidationReport
    crosswalk_report: CrosswalkValidationReport
    crosswalk_path: Path
    report_path: Path


def run_crosswalk_pipeline(
    multinet_path: Path,
    orbis_path: Path,
    boundary_type: BoundaryType,
    source_vintage: str,
    output_dir: Path,
    run_fips_check: bool = False,
    fips_lookup: Callable[[str], str | None] = fetch_fips_code,
) -> PipelineResult:
    multinet_gdf = read_multinet_boundaries(multinet_path, boundary_type)
    orbis_gdf = read_orbis_divisions(orbis_path, boundary_type)

    multinet_geometry_report = validate_geometry(multinet_gdf, id_column="ID")
    if not multinet_geometry_report.passed:
        raise InvalidSourceGeometryError(
            f"Multinet {boundary_type} source at {multinet_path} has invalid geometry for "
            f"IDs: {multinet_geometry_report.invalid_ids}"
        )

    orbis_geometry_report = validate_geometry(orbis_gdf, id_column="id")
    if not orbis_geometry_report.passed:
        raise InvalidSourceGeometryError(
            f"Orbis {boundary_type} source at {orbis_path} has invalid geometry for "
            f"IDs: {orbis_geometry_report.invalid_ids}"
        )

    crosswalk = match_to_orbis(multinet_gdf, orbis_gdf, boundary_type, source_vintage)
    crosswalk_report = validate_crosswalk(crosswalk)

    if run_fips_check:
        crosswalk = cross_check_fips(crosswalk, multinet_gdf, orbis_gdf, fips_lookup=fips_lookup)

    output_dir.mkdir(parents=True, exist_ok=True)

    crosswalk_path = output_dir / f"{boundary_type}_crosswalk.csv"
    crosswalk.to_csv(crosswalk_path, index=False)

    report = {
        "boundary_type": boundary_type,
        "source_vintage": source_vintage,
        "multinet_geometry": {**asdict(multinet_geometry_report), "passed": multinet_geometry_report.passed},
        "orbis_geometry": {**asdict(orbis_geometry_report), "passed": orbis_geometry_report.passed},
        "crosswalk": {**asdict(crosswalk_report), "passed": crosswalk_report.passed},
    }
    if run_fips_check:
        report["fips_cross_check_summary"] = crosswalk["fips_cross_check"].value_counts().to_dict()

    report_path = output_dir / f"{boundary_type}_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True))

    return PipelineResult(
        crosswalk=crosswalk,
        multinet_geometry_report=multinet_geometry_report,
        orbis_geometry_report=orbis_geometry_report,
        crosswalk_report=crosswalk_report,
        crosswalk_path=crosswalk_path,
        report_path=report_path,
    )
