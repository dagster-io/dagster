from collections import namedtuple
from collections.abc import Iterator, Mapping, Sequence, Set
from typing import Any, Union

import tableauserverclient as TSC
from dagster import (
    AssetKey,
    AssetObservation,
    AssetSpec,
    Output,
    _check as check,
)

from dagster_tableau.translator import (
    TableauDataSourceMetadataSet,
    TableauTagSet,
    TableauViewMetadataSet,
)


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
            Whether to include published data sources with extracts in materializable assets.

    Returns:
        ParsedTableauAssetSpecs: A named tuple representing the parsed Tableau asset specs
            as `external_asset_specs` and `materializable_asset_specs`.
    """
    data_source_asset_specs = [
        spec for spec in specs if TableauTagSet.extract(spec.tags).asset_type == "data_source"
    ]

    materializable_data_source_asset_specs, non_materializable_data_source_asset_specs = [], []
    for spec in data_source_asset_specs:
        # Embedded data sources with extract can't be refreshed using the "Update Data Source Now" endpoint
        # https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_data_sources.htm#update_data_source_now
        if (
            TableauDataSourceMetadataSet.extract(spec.metadata).has_extracts
            and TableauDataSourceMetadataSet.extract(spec.metadata).is_published
        ):
            materializable_data_source_asset_specs.append(spec)
        else:
            non_materializable_data_source_asset_specs.append(spec)

    view_asset_specs = [
        spec
        for spec in specs
        if TableauTagSet.extract(spec.tags).asset_type in ["dashboard", "sheet"]
    ]

    external_asset_specs = (
        non_materializable_data_source_asset_specs
        if include_data_sources_with_extracts
        else data_source_asset_specs
    )
    materializable_asset_specs = (
        materializable_data_source_asset_specs + view_asset_specs
        if include_data_sources_with_extracts
        else view_asset_specs
    )

    return ParsedTableauAssetSpecs(
        external_asset_specs=external_asset_specs,
        materializable_asset_specs=materializable_asset_specs,
    )


def create_view_asset_event(
    view: TSC.ViewItem, spec: AssetSpec, refreshed_workbook_ids: Set[str]
) -> Iterator[Union[AssetObservation, Output]]:
    asset_key = spec.key
    workbook_id = TableauViewMetadataSet.extract(spec.metadata).workbook_id

    if workbook_id and workbook_id in refreshed_workbook_ids:
        yield from create_asset_output(
            asset_key=asset_key, data=view, additional_metadata={"workbook_id": view.workbook_id}
        )
    else:
        yield from create_asset_observation(
            asset_key=asset_key, data=view, additional_metadata={"workbook_id": view.workbook_id}
        )


def create_data_source_asset_event(
    data_source: TSC.DatasourceItem, spec: AssetSpec, refreshed_data_source_ids: Set[str]
) -> Iterator[Union[AssetObservation, Output]]:
    asset_key = spec.key
    data_source_id = TableauDataSourceMetadataSet.extract(spec.metadata).id

    if data_source_id and data_source_id in refreshed_data_source_ids:
        yield from create_asset_output(
            asset_key=asset_key, data=data_source, additional_metadata={"id": data_source.id}
        )
    else:
        yield from create_asset_observation(
            asset_key=asset_key, data=data_source, additional_metadata={"id": data_source.id}
        )


def create_view_asset_observation(
    view: TSC.ViewItem,
    spec: AssetSpec,
) -> Iterator[AssetObservation]:
    asset_key = spec.key
    yield from create_asset_observation(
        asset_key=asset_key, data=view, additional_metadata={"workbook_id": view.workbook_id}
    )


def create_asset_output(
    asset_key: AssetKey,
    data: Union[TSC.DatasourceItem, TSC.ViewItem],
    additional_metadata: Mapping[str, Any],
) -> Iterator[Output]:
    yield Output(
        value=None,
        output_name="__".join(asset_key.path),
        metadata={
            **additional_metadata,
            "owner_id": data.owner_id,
            "name": data.name,
            "contentUrl": data.content_url,
            "createdAt": data.created_at.strftime("%Y-%m-%dT%H:%M:%S") if data.created_at else None,
            "updatedAt": data.updated_at.strftime("%Y-%m-%dT%H:%M:%S") if data.updated_at else None,
        },
    )


def create_asset_observation(
    asset_key: AssetKey,
    data: Union[TSC.DatasourceItem, TSC.ViewItem],
    additional_metadata: Mapping[str, Any],
) -> Iterator[AssetObservation]:
    yield AssetObservation(
        asset_key=asset_key,
        metadata={
            **additional_metadata,
            "owner_id": data.owner_id,
            "name": data.name,
            "contentUrl": data.content_url,
            "createdAt": data.created_at.strftime("%Y-%m-%dT%H:%M:%S") if data.created_at else None,
            "updatedAt": data.updated_at.strftime("%Y-%m-%dT%H:%M:%S") if data.updated_at else None,
        },
    )
