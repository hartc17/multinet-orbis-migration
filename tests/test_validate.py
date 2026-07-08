from pathlib import Path

from migration.extract import read_multinet_boundaries
from migration.transform import transform_boundaries
from migration.validate import validate_boundaries

FIXTURES = Path(__file__).parent / "fixtures"


def test_validate_boundaries_matching_counts_passes():
    source = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")
    transformed = transform_boundaries(source, "county", source_vintage="2026-06")

    report = validate_boundaries(source, transformed)

    assert report.passed
    assert report.dropped_count == 0
    assert report.invalid_geometry_ids == []


def test_validate_boundaries_dropped_rows_fails():
    source = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")
    transformed = transform_boundaries(source, "county", source_vintage="2026-06").iloc[:1]

    report = validate_boundaries(source, transformed)

    assert not report.passed
    assert report.dropped_count == 1
