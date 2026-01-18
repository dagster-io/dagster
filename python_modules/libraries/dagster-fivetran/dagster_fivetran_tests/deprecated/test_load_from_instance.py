import pytest
import responses
from dagster import AssetKey, EnvVar
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster._core.definitions.tags import has_kind
from dagster._core.instance_for_test import environ
from dagster_fivetran import FivetranResource
from dagster_fivetran.asset_defs import (
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    load_assets_from_fivetran_instance,
)

from dagster_fivetran_tests.deprecated.utils import mock_responses


class CustomDagsterFivetranTranslator(DagsterFivetranTranslator):
    def get_asset_spec(self, props: FivetranConnectorTableProps) -> AssetSpec:
        asset_spec = super().get_asset_spec(props)
        return asset_spec.replace_attributes(
            key=asset_spec.key.with_prefix("my_prefix"),
            metadata={"foo": "bar", **asset_spec.metadata},
            group_name="custom_group_name",
        )


@responses.activate
@pytest.mark.parametrize(
    ("translator, custom_prefix, custom_metadata, custom_group_name"),
    [
        (DagsterFivetranTranslator, [], {}, None),
        (CustomDagsterFivetranTranslator, ["my_prefix"], {"foo": "bar"}, "custom_group_name"),
    ],
)
def test_load_from_instance_with_translator(
    translator, custom_prefix, custom_metadata, custom_group_name
) -> None:
    with environ({"FIVETRAN_API_KEY": "some_key", "FIVETRAN_API_SECRET": "some_secret"}):
        ft_resource = FivetranResource(
            api_key=EnvVar("FIVETRAN_API_KEY"), api_secret=EnvVar("FIVETRAN_API_SECRET")
        )

        mock_responses(ft_resource)

        ft_cacheable_assets = load_assets_from_fivetran_instance(
            ft_resource,
            poll_interval=10,
            poll_timeout=600,
            translator=translator,
        )
        ft_assets = ft_cacheable_assets.build_definitions(
            ft_cacheable_assets.compute_cacheable_data()
        )

        # Create set of expected asset keys
        tables = {
            AssetKey([*custom_prefix, "xyz1", "abc2"]),
            AssetKey([*custom_prefix, "xyz1", "abc1"]),
            AssetKey([*custom_prefix, "abc", "xyz"]),
        }

        # Check schema metadata is added correctly to asset def
        assets_def = ft_assets[0]

        assert any(
            metadata.get("dagster/column_schema")
            == (
                TableSchema(
                    columns=[
                        TableColumn(name="column_1", type=""),
                        TableColumn(name="column_2", type=""),
                        TableColumn(name="column_3", type=""),
                    ]
                )
            )
            for key, metadata in assets_def.metadata_by_key.items()
        ), str(assets_def.metadata_by_key)

        for key, metadata in assets_def.metadata_by_key.items():
            assert metadata.get("dagster/table_name") == (
                "example_database." + ".".join(key.path[-2:])
            )
            assert has_kind(assets_def.tags_by_key[key], "snowflake")

        for key, value in custom_metadata.items():
            assert all(metadata[key] == value for metadata in assets_def.metadata_by_key.values())
        assert ft_assets[0].keys == tables
        assert all(
            [
                ft_assets[0].group_names_by_key.get(t)
                == (custom_group_name or "some_service_some_name")
                for t in tables
            ]
        ), str(ft_assets[0].group_names_by_key)
        assert len(ft_assets[0].op.output_defs) == len(tables)
