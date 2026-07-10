from dataclasses import dataclass, field

import geopandas as gpd
import pandas as pd


@dataclass
class GeometryValidationReport:
    feature_count: int
    invalid_ids: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.invalid_ids


def validate_geometry(gdf: gpd.GeoDataFrame, id_column: str) -> GeometryValidationReport:
    invalid_mask = ~gdf.geometry.is_valid
    invalid_ids = gdf.loc[invalid_mask, id_column].tolist()

    return GeometryValidationReport(feature_count=len(gdf), invalid_ids=invalid_ids)


@dataclass
class CrosswalkValidationReport:
    source_count: int
    matched_count: int
    unmatched_ids: list[str] = field(default_factory=list)
    duplicate_gers_ids: list[str] = field(default_factory=list)

    @property
    def unmatched_count(self) -> int:
        return len(self.unmatched_ids)

    @property
    def passed(self) -> bool:
        return not self.unmatched_ids and not self.duplicate_gers_ids


def validate_crosswalk(crosswalk_df: pd.DataFrame) -> CrosswalkValidationReport:
    unmatched = crosswalk_df[crosswalk_df["match_method"] == "unmatched"]

    matched = crosswalk_df[crosswalk_df["match_method"] != "unmatched"]
    duplicate_gers_ids = matched.loc[
        matched["gers_id"].duplicated(keep=False), "gers_id"
    ].unique().tolist()

    return CrosswalkValidationReport(
        source_count=len(crosswalk_df),
        matched_count=len(matched),
        unmatched_ids=unmatched["multinet_source_id"].tolist(),
        duplicate_gers_ids=duplicate_gers_ids,
    )
