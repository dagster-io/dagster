from typing import Sequence, Tuple

from dagster import AssetSpec

from dagster_tableau.translator import TableauTagSet


def parse_tableau_external_and_materializable_asset_specs(
    specs: Sequence[AssetSpec],
) -> Tuple[Sequence[AssetSpec], Sequence[AssetSpec]]:
    external_asset_specs = [
        spec for spec in specs if TableauTagSet.extract(spec.tags).asset_type == "data_source"
    ]

    materializable_asset_specs = [
        spec
        for spec in specs
        if TableauTagSet.extract(spec.tags).asset_type in ["dashboard", "sheet"]
    ]

    return external_asset_specs, materializable_asset_specs
