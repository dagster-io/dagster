import base64
from typing import Any

import pytest
import responses
from dagster import (
    AssetIn,
    AssetKey,
    EnvVar,
    InputContext,
    IOManager,
    OutputContext,
    asset,
    io_manager,
)
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster._core.definitions.tags import has_kind
from dagster._core.execution.with_resources import with_resources
from dagster._core.instance_for_test import environ
from dagster_fivetran import FivetranResource
from dagster_fivetran.asset_defs import (
    FivetranConnectionMetadata,
    load_assets_from_fivetran_instance,
)
from responses import matchers

from dagster_fivetran_tests.utils import (
    DEFAULT_CONNECTOR_ID,
    DEFAULT_CONNECTOR_ID_2,
    get_complex_sample_connector_schema_config,
    get_sample_columns_response,
    get_sample_connector_response,
    get_sample_connectors_response,
    get_sample_connectors_response_multiple,
    get_sample_destination_details_response,
    get_sample_groups_response,
    get_sample_sync_response,
    get_sample_update_response,
)


@responses.activate
@pytest.mark.parametrize(
    "connector_to_group_fn", [None, lambda x: f"{x[0]}_group"], ids=("default", "custom")
)
@pytest.mark.parametrize("filter_connector", [True, False])
@pytest.mark.parametrize(
    "connector_to_asset_key_fn",
    [
        None,
        lambda conn, name: AssetKey([*conn.name.split("."), *name.split(".")]),
    ],
    ids=("default", "custom"),
)
@pytest.mark.parametrize("multiple_connectors", [True, False])
@pytest.mark.parametrize("destination_ids", [None, [], ["some_group"]])
def test_load_from_instance(
    connector_to_group_fn,
    filter_connector,
    connector_to_asset_key_fn,
    multiple_connectors,
    destination_ids,
) -> None:
    with environ({"FIVETRAN_API_KEY": "some_key", "FIVETRAN_API_SECRET": "some_secret"}):
        load_calls = []

        @io_manager
        def test_io_manager(_context) -> IOManager:
            class TestIOManager(IOManager):
                def handle_output(self, context: OutputContext, obj) -> None:
                    return

                def load_input(self, context: InputContext) -> Any:
                    load_calls.append(context.asset_key)
                    return None

            return TestIOManager()

        ft_resource = FivetranResource(
            api_key=EnvVar("FIVETRAN_API_KEY"), api_secret=EnvVar("FIVETRAN_API_SECRET")
        )

        b64_encoded_auth_str = base64.b64encode(b"some_key:some_secret").decode("utf-8")
        expected_auth_header = {"Authorization": f"Basic {b64_encoded_auth_str}"}

        responses.add(
            method=responses.GET,
            url=ft_resource.api_base_url + "groups",
            json=get_sample_groups_response(),
            status=200,
            match=[matchers.header_matcher(expected_auth_header)],
        )
        responses.add(
            method=responses.GET,
            url=ft_resource.api_base_url + "destinations/some_group",
            json=(get_sample_destination_details_response()),
            status=200,
            match=[matchers.header_matcher(expected_auth_header)],
        )
        responses.add(
            method=responses.GET,
            url=ft_resource.api_base_url + "groups/some_group/connectors",
            json=(
                get_sample_connectors_response_multiple()
                if multiple_connectors
                else get_sample_connectors_response()
            ),
            status=200,
            match=[matchers.header_matcher(expected_auth_header)],
        )

        responses.add(
            responses.GET,
            f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID}/schemas",
            json=get_complex_sample_connector_schema_config(),
        )
        if multiple_connectors:
            responses.add(
                responses.GET,
                f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID_2}/schemas",
                json=get_complex_sample_connector_schema_config("_xyz1", "_abc"),
            )

        if connector_to_group_fn:
            ft_cacheable_assets = load_assets_from_fivetran_instance(
                ft_resource,
                connector_to_group_fn=connector_to_group_fn,
                connector_filter=(lambda _: False) if filter_connector else None,
                connector_to_asset_key_fn=connector_to_asset_key_fn,
                connector_to_io_manager_key_fn=(lambda _: "test_io_manager"),
                poll_interval=10,
                poll_timeout=600,
            )
        else:
            ft_cacheable_assets = load_assets_from_fivetran_instance(
                ft_resource,
                connector_filter=(lambda _: False) if filter_connector else None,
                connector_to_asset_key_fn=connector_to_asset_key_fn,
                io_manager_key="test_io_manager",
                poll_interval=10,
                poll_timeout=600,
            )
        ft_assets = ft_cacheable_assets.build_definitions(
            ft_cacheable_assets.compute_cacheable_data()
        )
        ft_assets = with_resources(ft_assets, {"test_io_manager": test_io_manager})
        if filter_connector:
            assert len(ft_assets) == 0
            return

        # Create set of expected asset keys
        tables = {
            AssetKey(["xyz1", "abc2"]),
            AssetKey(["xyz1", "abc1"]),
            AssetKey(["abc", "xyz"]),
        }
        if connector_to_asset_key_fn:
            tables = {
                connector_to_asset_key_fn(
                    FivetranConnectionMetadata(
                        "some_service.some_name",
                        "",
                        "=",
                        {},
                        database="example_database",
                        service="snowflake",
                    ),
                    ".".join(t.path),
                )
                for t in tables
            }

        # Set up a downstream asset to consume the xyz output table
        xyz_asset_key = (
            connector_to_asset_key_fn(
                FivetranConnectionMetadata(
                    "some_service.some_name",
                    "",
                    "=",
                    {},
                    database="example_database",
                    service="snowflake",
                ),
                "abc.xyz",
            )
            if connector_to_asset_key_fn
            else AssetKey(["abc", "xyz"])
        )

        @asset(ins={"xyz": AssetIn(key=xyz_asset_key)})
        def downstream_asset(xyz):
            return

        all_assets = [downstream_asset] + ft_assets  # type: ignore

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
            assert metadata.get("dagster/relation_identifier") == (
                "example_database." + ".".join(key.path[-2:])
            )
            assert has_kind(assets_def.tags_by_key[key], "snowflake")

        assert ft_assets[0].keys == tables
        assert all(
            [
                ft_assets[0].group_names_by_key.get(t)
                == (
                    connector_to_group_fn("some_service.some_name")
                    if connector_to_group_fn
                    else "some_service_some_name"
                )
                for t in tables
            ]
        )
        assert len(ft_assets[0].op.output_defs) == len(tables)

        # Kick off a run to materialize all assets
        final_data = {"succeeded_at": "2021-01-01T02:00:00.0Z"}

        api_prefixes = [(f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID}", tuple())]
        if multiple_connectors:
            api_prefixes.append(
                (f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID_2}", ("_xyz1", "_abc"))
            )

        for api_prefix, schema_args in api_prefixes:
            responses.add(responses.PATCH, api_prefix, json=get_sample_update_response())
            responses.add(responses.POST, f"{api_prefix}/force", json=get_sample_sync_response())

            # connector schema
            responses.add(
                responses.GET,
                f"{api_prefix}/schemas",
                # json=get_complex_sample_connector_schema_config(),
                json=get_complex_sample_connector_schema_config(*schema_args),
            )
            # initial state
            responses.add(responses.GET, api_prefix, json=get_sample_connector_response())
            # n polls before updating
            for _ in range(2):
                responses.add(responses.GET, api_prefix, json=get_sample_connector_response())
            # final state will be updated
            responses.add(
                responses.GET, api_prefix, json=get_sample_connector_response(data=final_data)
            )

            for schema, table in [
                ("schema_1", "table_1"),
                ("schema_1", "table_2"),
                ("schema_2", "table_1"),
            ]:
                responses.add(
                    responses.GET,
                    f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID}/schemas/{schema}/tables/{table}/columns",
                    json=get_sample_columns_response(),
                )
                if multiple_connectors:
                    responses.add(
                        responses.GET,
                        f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID_2}/schemas/{schema}/tables/{table}/columns",
                        json=get_sample_columns_response(),
                    )
        result = materialize(all_assets)
        asset_materializations = [
            event
            for event in result.events_for_node("fivetran_sync_some_connector")
            if event.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(asset_materializations) == 3

        # Check that we correctly pull runtime schema metadata from the API
        for mat in asset_materializations:
            schema = mat.materialization.metadata.get("dagster/column_schema")
            assert schema == MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name="column_1", type=""),
                        TableColumn(name="column_2_renamed", type=""),
                        TableColumn(name="column_3", type=""),
                    ]
                )
            ), f"{mat.asset_key} {schema}"

        asset_keys = set(
            mat.event_specific_data.materialization.asset_key  # type: ignore
            for mat in asset_materializations
        )
        assert asset_keys == tables

        # Validate IO manager is called to retrieve the xyz asset which our downstream asset depends on
        assert load_calls == [xyz_asset_key]
