from collections import namedtuple
from collections.abc import Sequence

from dagster import (
    AssetSpec,
    _check as check,
)

from dagster_tableau.translator import TableauDataSourceMetadataSet, TableauTagSet


class ParsedTableauAssetSpecs(
    namedtuple("_ParsedTableauAssetSpecs", ["external_asset_specs", "materializable_asset_specs"])
):
    """Used to represent the parsed Tableau asset specs
    as returned by the `parse_tableau_external_and_materializable_asset_specs` function below.
    """

    def __new__(cls, external_asset_specs, materializable_asset_specs):
        return super().__new__(
            cls,
            external_asset_specs=check.list_param(
                external_asset_specs, "external_asset_specs", AssetSpec
            ),
            materializable_asset_specs=check.list_param(
                materializable_asset_specs, "materializable_asset_specs", AssetSpec
            ),
        )


def parse_tableau_external_and_materializable_asset_specs(
    specs: Sequence[AssetSpec],
    include_data_sources_with_extracts: bool = False,
) -> ParsedTableauAssetSpecs:
    """Parses a list of Tableau AssetSpecs provided as input and return two lists of AssetSpecs,
    one for the Tableau external assets and another one for the Tableau materializable assets.

    In Tableau, data sources are considered external assets,
    while sheets and dashboards are considered materializable assets.

    Args:
        specs (Sequence[AssetSpec]): The asset specs of the assets in the Tableau workspace.
        include_data_sources_with_extracts (bool):
            Whether to include data sources with extracts in materializable assets.

    Returns:
        ParsedTableauAssetSpecs: A named tuple representing the parsed Tableau asset specs
            as `external_asset_specs` and `materializable_asset_specs`.
    """
    data_source_asset_specs = [
        spec for spec in specs if TableauTagSet.extract(spec.tags).asset_type == "data_source"
    ]

    extract_asset_specs, non_extract_asset_specs = [], []
    for spec in data_source_asset_specs:
        if TableauDataSourceMetadataSet.extract(spec.metadata).has_extracts:
            extract_asset_specs.append(spec)
        else:
            non_extract_asset_specs.append(spec)

    view_asset_specs = [
        spec
        for spec in specs
        if TableauTagSet.extract(spec.tags).asset_type in ["dashboard", "sheet"]
    ]

    external_asset_specs = (
        non_extract_asset_specs if include_data_sources_with_extracts else data_source_asset_specs
    )
    materializable_asset_specs = (
        view_asset_specs + extract_asset_specs
        if include_data_sources_with_extracts
        else view_asset_specs
    )

    return ParsedTableauAssetSpecs(
        external_asset_specs=external_asset_specs,
        materializable_asset_specs=materializable_asset_specs,
    )
