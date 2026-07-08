from pathlib import Path

from migration.extract import read_multinet_boundaries, read_orbis_divisions
from migration.match import match_to_orbis
from migration.validate import validate_crosswalk, validate_geometry

FIXTURES = Path(__file__).parent / "fixtures"


def test_validate_geometry_all_valid_passes():
    gdf = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")

    report = validate_geometry(gdf, id_column="ID")

    assert report.passed
    assert report.feature_count == 2
    assert report.invalid_ids == []


def test_validate_crosswalk_fully_matched_passes():
    multinet = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")
    orbis = read_orbis_divisions(FIXTURES / "orbis_county.geojson", "county")
    crosswalk = match_to_orbis(multinet, orbis, "county", source_vintage="2026-06")

    report = validate_crosswalk(crosswalk)

    assert report.passed
    assert report.matched_count == 2
    assert report.unmatched_count == 0


def test_validate_crosswalk_unmatched_row_fails():
    multinet = read_multinet_boundaries(FIXTURES / "multinet_zip.geojson", "zip")
    orbis = read_orbis_divisions(FIXTURES / "orbis_zip.geojson", "zip")
    crosswalk = match_to_orbis(multinet, orbis, "zip", source_vintage="2026-06")

    report = validate_crosswalk(crosswalk)

    assert not report.passed
    assert report.unmatched_ids == ["Z3"]
