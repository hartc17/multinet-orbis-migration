from pathlib import Path

import pytest

from migration.extract import read_multinet_boundaries, read_orbis_divisions

FIXTURES = Path(__file__).parent / "fixtures"


def test_read_multinet_boundaries_state_returns_expected_rows():
    gdf = read_multinet_boundaries(FIXTURES / "multinet_state.geojson", "state")

    assert len(gdf) == 1
    assert gdf.iloc[0]["NAME"] == "Texas"


def test_read_multinet_boundaries_county_returns_expected_rows():
    gdf = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")

    assert len(gdf) == 2
    assert set(gdf["PARENT_ID"]) == {"S1"}


def test_read_multinet_boundaries_missing_column_raises(tmp_path):
    bad_file = tmp_path / "bad.geojson"
    bad_file.write_text(
        '{"type": "FeatureCollection", "features": ['
        '{"type": "Feature", "properties": {"NAME": "Texas"}, '
        '"geometry": {"type": "Polygon", "coordinates": '
        "[[[-98, 29], [-96, 29], [-96, 31], [-98, 31], [-98, 29]]]}}]}"
    )

    with pytest.raises(ValueError, match="missing columns"):
        read_multinet_boundaries(bad_file, "state")


def test_read_orbis_divisions_county_returns_expected_rows():
    gdf = read_orbis_divisions(FIXTURES / "orbis_county.geojson", "county")

    assert len(gdf) == 2
    assert set(gdf["admin_level"]) == {2}


def test_read_orbis_divisions_missing_column_raises(tmp_path):
    bad_file = tmp_path / "bad.geojson"
    bad_file.write_text(
        '{"type": "FeatureCollection", "features": ['
        '{"type": "Feature", "properties": {"name": "Texas"}, '
        '"geometry": {"type": "Polygon", "coordinates": '
        "[[[-98, 29], [-96, 29], [-96, 31], [-98, 31], [-98, 29]]]}}]}"
    )

    with pytest.raises(ValueError, match="missing columns"):
        read_orbis_divisions(bad_file, "state")
