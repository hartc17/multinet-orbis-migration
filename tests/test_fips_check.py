from pathlib import Path

from migration.extract import read_multinet_boundaries, read_orbis_divisions
from migration.fips_check import cross_check_fips
from migration.match import match_to_orbis

FIXTURES = Path(__file__).parent / "fixtures"


def _crosswalk():
    multinet = read_multinet_boundaries(FIXTURES / "multinet_county.geojson", "county")
    orbis = read_orbis_divisions(FIXTURES / "orbis_county.geojson", "county")
    crosswalk = match_to_orbis(multinet, orbis, "county", source_vintage="2026-06")
    return multinet, orbis, crosswalk


def test_cross_check_fips_agrees_when_wikidata_matches_multinet():
    multinet, orbis, crosswalk = _crosswalk()

    fake_lookup = {"Q27018": "48209", "Q110426": "48453"}.get
    result = cross_check_fips(crosswalk, multinet, orbis, fips_lookup=fake_lookup)

    by_id = result.set_index("multinet_source_id")
    assert by_id.loc["C1", "fips_cross_check"] == "agree"
    assert by_id.loc["C2", "fips_cross_check"] == "agree"


def test_cross_check_fips_disagrees_when_wikidata_differs():
    multinet, orbis, crosswalk = _crosswalk()

    fake_lookup = {"Q27018": "00000", "Q110426": "48453"}.get
    result = cross_check_fips(crosswalk, multinet, orbis, fips_lookup=fake_lookup)

    by_id = result.set_index("multinet_source_id")
    assert by_id.loc["C1", "fips_cross_check"] == "disagree"
    assert by_id.loc["C2", "fips_cross_check"] == "agree"


def test_cross_check_fips_unavailable_for_unmatched_and_missing_lookup():
    multinet, orbis, crosswalk = _crosswalk()

    result = cross_check_fips(crosswalk, multinet, orbis, fips_lookup=lambda qid: None)

    by_id = result.set_index("multinet_source_id")
    assert by_id.loc["C3", "fips_cross_check"] == "unavailable"
    assert by_id.loc["C1", "fips_cross_check"] == "unavailable"
