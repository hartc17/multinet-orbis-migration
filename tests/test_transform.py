from pathlib import Path

from migration.extract import read_multinet_boundaries
from migration.transform import transform_boundaries

FIXTURES = Path(__file__).parent / "fixtures"


def test_transform_boundaries_state_maps_to_orbis_schema():
    source = read_multinet_boundaries(FIXTURES / "multinet_state.geojson", "state")

    result = transform_boundaries(source, "state", source_vintage="2026-06")

    row = result.iloc[0]
    assert row["orbis_id"] == "S1"
    assert row["boundary_name"] == "Texas"
    assert row["boundary_type"] == "state"
    assert row["code"] == "48"
    assert row["parent_orbis_id"] is None
    assert row["source_vintage"] == "2026-06"


def test_transform_boundaries_zip_uses_zip_code_as_code():
    source = read_multinet_boundaries(FIXTURES / "multinet_zip.geojson", "zip")

    result = transform_boundaries(source, "zip", source_vintage="2026-06")

    assert set(result["code"]) == {"78640", "78704"}
    assert set(result["parent_orbis_id"]) == {"C1", "C2"}
