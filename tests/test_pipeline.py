import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from migration.pipeline import InvalidSourceGeometryError, run_crosswalk_pipeline

FIXTURES = Path(__file__).parent / "fixtures"


def test_run_crosswalk_pipeline_state_writes_crosswalk_and_report(tmp_path):
    result = run_crosswalk_pipeline(
        multinet_path=FIXTURES / "multinet_state.geojson",
        orbis_path=FIXTURES / "orbis_state.geojson",
        boundary_type="state",
        source_vintage="2026-06",
        output_dir=tmp_path,
    )

    assert result.crosswalk_path == tmp_path / "state_crosswalk.csv"
    assert result.report_path == tmp_path / "state_validation_report.json"
    assert result.crosswalk_path.exists()
    assert result.report_path.exists()
    assert result.crosswalk_report.passed

    written = pd.read_csv(result.crosswalk_path)
    assert written.loc[0, "multinet_source_id"] == "S1"

    report = json.loads(result.report_path.read_text())
    assert report["boundary_type"] == "state"
    assert report["crosswalk"]["matched_count"] == 1
    assert report["multinet_geometry"]["passed"] is True


def test_run_crosswalk_pipeline_county_reports_unmatched_without_raising(tmp_path):
    result = run_crosswalk_pipeline(
        multinet_path=FIXTURES / "multinet_county.geojson",
        orbis_path=FIXTURES / "orbis_county.geojson",
        boundary_type="county",
        source_vintage="2026-06",
        output_dir=tmp_path,
    )

    assert not result.crosswalk_report.passed
    assert result.crosswalk_report.unmatched_ids == ["C3"]

    report = json.loads(result.report_path.read_text())
    assert report["crosswalk"]["unmatched_ids"] == ["C3"]


def test_run_crosswalk_pipeline_is_idempotent(tmp_path):
    run_crosswalk_pipeline(
        FIXTURES / "multinet_county.geojson",
        FIXTURES / "orbis_county.geojson",
        "county",
        "2026-06",
        tmp_path,
    )
    first = (tmp_path / "county_crosswalk.csv").read_text()

    run_crosswalk_pipeline(
        FIXTURES / "multinet_county.geojson",
        FIXTURES / "orbis_county.geojson",
        "county",
        "2026-06",
        tmp_path,
    )
    second = (tmp_path / "county_crosswalk.csv").read_text()

    assert first == second


def test_run_crosswalk_pipeline_with_fips_check_adds_column_and_summary(tmp_path):
    fake_lookup = {"Q27018": "48209", "Q110426": "48453"}.get

    result = run_crosswalk_pipeline(
        multinet_path=FIXTURES / "multinet_county.geojson",
        orbis_path=FIXTURES / "orbis_county.geojson",
        boundary_type="county",
        source_vintage="2026-06",
        output_dir=tmp_path,
        run_fips_check=True,
        fips_lookup=fake_lookup,
    )

    assert "fips_cross_check" in result.crosswalk.columns

    report = json.loads(result.report_path.read_text())
    assert report["fips_cross_check_summary"]["agree"] == 2


def test_run_crosswalk_pipeline_invalid_multinet_geometry_raises(tmp_path):
    bowtie = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
    assert not bowtie.is_valid

    gdf = gpd.GeoDataFrame(
        {"ID": ["S9"], "NAME": ["Bad"], "FIPS_CODE": ["99"], "geometry": [bowtie]},
        crs="EPSG:4326",
    )
    bad_path = tmp_path / "bad_multinet_state.geojson"
    gdf.to_file(bad_path, driver="GeoJSON")

    with pytest.raises(InvalidSourceGeometryError, match="invalid geometry"):
        run_crosswalk_pipeline(
            multinet_path=bad_path,
            orbis_path=FIXTURES / "orbis_state.geojson",
            boundary_type="state",
            source_vintage="2026-06",
            output_dir=tmp_path,
        )

    assert not (tmp_path / "state_crosswalk.csv").exists()
