from dataclasses import dataclass, field

import geopandas as gpd


@dataclass
class ValidationReport:
    source_count: int
    output_count: int
    invalid_geometry_ids: list[str] = field(default_factory=list)

    @property
    def dropped_count(self) -> int:
        return self.source_count - self.output_count

    @property
    def passed(self) -> bool:
        return self.dropped_count == 0 and not self.invalid_geometry_ids


def validate_boundaries(
    source_gdf: gpd.GeoDataFrame, transformed_gdf: gpd.GeoDataFrame
) -> ValidationReport:
    invalid_mask = ~transformed_gdf.geometry.is_valid
    invalid_ids = transformed_gdf.loc[invalid_mask, "multinet_source_id"].tolist()

    return ValidationReport(
        source_count=len(source_gdf),
        output_count=len(transformed_gdf),
        invalid_geometry_ids=invalid_ids,
    )
