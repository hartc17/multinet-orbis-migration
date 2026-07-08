from collections.abc import Callable

import geopandas as gpd
import pandas as pd

from migration.wikidata import fetch_fips_code


def cross_check_fips(
    crosswalk_df: pd.DataFrame,
    multinet_gdf: gpd.GeoDataFrame,
    orbis_gdf: gpd.GeoDataFrame,
    fips_lookup: Callable[[str], str | None] = fetch_fips_code,
) -> pd.DataFrame:
    multinet_fips = multinet_gdf.set_index("ID")["FIPS_CODE"]
    orbis_wikidata = orbis_gdf.set_index("id")["wikidata"] if "wikidata" in orbis_gdf.columns else {}

    def check(row: pd.Series) -> str:
        if row["match_method"] == "unmatched":
            return "unavailable"

        qid = orbis_wikidata.get(row["gers_id"])
        if not qid:
            return "unavailable"

        wikidata_fips = fips_lookup(qid)
        if wikidata_fips is None:
            return "unavailable"

        return "agree" if wikidata_fips == multinet_fips.get(row["multinet_source_id"]) else "disagree"

    result = crosswalk_df.copy()
    result["fips_cross_check"] = result.apply(check, axis=1)
    return result
