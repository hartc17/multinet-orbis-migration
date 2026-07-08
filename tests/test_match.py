from pathlib import Path

import pandas as pd

from migration.extract import read_multinet_boundaries, read_orbis_divisions
from migration.match import match_to_orbis

FIXTURES = Path(__file__).parent / "fixtures"


def test_match_to_orbis_county_matches_by_spatial_containment():
    multinet = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")
    orbis = read_orbis_divisions(FIXTURES / "orbis_county.geojson", "county")

    crosswalk = match_to_orbis(multinet, orbis, "county", source_vintage="2026-06")

    by_id = crosswalk.set_index("multinet_source_id")
    assert by_id.loc["C1", "gers_id"] == "08syn-county-hays-0001"
    assert by_id.loc["C1", "match_method"] == "spatial"
    assert by_id.loc["C2", "gers_id"] == "08syn-county-travis-0001"
    assert (crosswalk["source_vintage"] == "2026-06").all()


def test_match_to_orbis_zip_flags_unmatched():
    multinet = read_multinet_boundaries(FIXTURES / "multinet_zip.geojson", "zip")
    orbis = read_orbis_divisions(FIXTURES / "orbis_zip.geojson", "zip")

    crosswalk = match_to_orbis(multinet, orbis, "zip", source_vintage="2026-06")

    by_id = crosswalk.set_index("multinet_source_id")
    assert by_id.loc["Z3", "match_method"] == "unmatched"
    assert pd.isna(by_id.loc["Z3", "gers_id"])
    assert by_id.loc["Z1", "match_method"] == "spatial"
    assert by_id.loc["Z2", "match_method"] == "spatial"
