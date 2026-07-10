from pathlib import Path

import pandas as pd
import pytest

from migration.extract import read_multinet_boundaries, read_orbis_divisions
from migration.match import match_to_orbis

FIXTURES = Path(__file__).parent / "fixtures"

# Real Overture GERS IDs (release 2026-06-17.0) - see docs/plan.md.
HAYS_GERS_ID = "a8853873-6cc9-42ea-a484-2df7eeb94d52"
TRAVIS_GERS_ID = "9bf0b1da-9566-4acf-bdea-6687626f05cd"


def test_match_to_orbis_county_matches_by_spatial_containment():
    multinet = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")
    orbis = read_orbis_divisions(FIXTURES / "orbis_county.geojson", "county")

    crosswalk = match_to_orbis(multinet, orbis, "county", source_vintage="2026-06")

    by_id = crosswalk.set_index("multinet_source_id")
    assert by_id.loc["C1", "gers_id"] == HAYS_GERS_ID
    assert by_id.loc["C1", "match_method"] == "spatial"
    assert by_id.loc["C2", "gers_id"] == TRAVIS_GERS_ID
    assert (crosswalk["source_vintage"] == "2026-06").all()


def test_match_to_orbis_flags_unmatched_county():
    # El Paso County (C3) is present in the Multinet fixture but deliberately absent from
    # the Orbis fixture, to exercise the unmatched path.
    multinet = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")
    orbis = read_orbis_divisions(FIXTURES / "orbis_county.geojson", "county")

    crosswalk = match_to_orbis(multinet, orbis, "county", source_vintage="2026-06")

    by_id = crosswalk.set_index("multinet_source_id")
    assert by_id.loc["C3", "match_method"] == "unmatched"
    assert pd.isna(by_id.loc["C3", "gers_id"])


def test_match_to_orbis_zip_unsupported_raises():
    multinet = read_multinet_boundaries(FIXTURES / "multinet_zip.geojson", "zip")

    with pytest.raises(ValueError, match="no crosswalk support"):
        match_to_orbis(multinet, multinet, "zip", source_vintage="2026-06")
