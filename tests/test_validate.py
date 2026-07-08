from pathlib import Path

from migration.extract import read_multinet_boundaries, read_orbis_divisions
from migration.match import match_to_orbis
from migration.validate import validate_crosswalk, validate_geometry

FIXTURES = Path(__file__).parent / "fixtures"


def test_validate_geometry_all_valid_passes():
    gdf = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")

    report = validate_geometry(gdf, id_column="ID")

    assert report.passed
    assert report.feature_count == 3
    assert report.invalid_ids == []


def test_validate_crosswalk_fully_matched_passes():
    multinet = read_multinet_boundaries(FIXTURES / "multinet_state.geojson", "state")
    orbis = read_orbis_divisions(FIXTURES / "orbis_state.geojson", "state")
    crosswalk = match_to_orbis(multinet, orbis, "state", source_vintage="2026-06")

    report = validate_crosswalk(crosswalk)

    assert report.passed
    assert report.matched_count == 1
    assert report.unmatched_count == 0


def test_validate_crosswalk_unmatched_row_fails():
    multinet = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")
    orbis = read_orbis_divisions(FIXTURES / "orbis_county.geojson", "county")
    crosswalk = match_to_orbis(multinet, orbis, "county", source_vintage="2026-06")

    report = validate_crosswalk(crosswalk)

    assert not report.passed
    assert report.unmatched_ids == ["C3"]
