import requests

WIKIDATA_ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"

# Wikidata property P882 ("FIPS 6-4 code"), the standard property for US county FIPS codes.
# wikidata.org is blocked by this development session's network policy, so this has not been
# exercised against a live response here - confirm P882 still holds on the first real run
# (see docs/plan.md).
FIPS_PROPERTY = "P882"


def fetch_fips_code(qid: str) -> str | None:
    response = requests.get(WIKIDATA_ENTITY_URL.format(qid=qid), timeout=10)
    response.raise_for_status()
    entity = response.json()["entities"][qid]

    fips_claims = entity["claims"].get(FIPS_PROPERTY)
    if not fips_claims:
        return None

    return fips_claims[0]["mainsnak"]["datavalue"]["value"]
