from migration.wikidata import fetch_fips_code


def test_fetch_fips_code_returns_value_when_present(mocker):
    fake_response = mocker.Mock()
    fake_response.json.return_value = {
        "entities": {
            "Q27018": {"claims": {"P882": [{"mainsnak": {"datavalue": {"value": "48209"}}}]}}
        }
    }
    mocker.patch("migration.wikidata.requests.get", return_value=fake_response)

    assert fetch_fips_code("Q27018") == "48209"
    fake_response.raise_for_status.assert_called_once()


def test_fetch_fips_code_missing_property_returns_none(mocker):
    fake_response = mocker.Mock()
    fake_response.json.return_value = {"entities": {"Q1": {"claims": {}}}}
    mocker.patch("migration.wikidata.requests.get", return_value=fake_response)

    assert fetch_fips_code("Q1") is None
