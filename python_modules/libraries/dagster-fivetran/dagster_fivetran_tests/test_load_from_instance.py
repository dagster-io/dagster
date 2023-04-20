from typing import Any

import pytest
import responses
from dagster import (
    AssetIn,
    AssetKey,
    InputContext,
    IOManager,
    OutputContext,
    asset,
    io_manager,
)
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster._core.execution.with_resources import with_resources
from dagster_fivetran import FivetranResource
from dagster_fivetran.asset_defs import (
    FivetranConnectionMetadata,
    load_assets_from_fivetran_instance,
)

from dagster_fivetran_tests.utils import (
    DEFAULT_CONNECTOR_ID,
    DEFAULT_CONNECTOR_ID_2,
    get_complex_sample_connector_schema_config,
    get_sample_connector_response,
    get_sample_connectors_response,
    get_sample_connectors_response_multiple,
    get_sample_groups_response,
    get_sample_sync_response,
    get_sample_update_response,
)


@responses.activate
@pytest.mark.parametrize("connector_to_group_fn", [None, lambda x: f"{x[0]}_group"])
@pytest.mark.parametrize("filter_connector", [True, False])
@pytest.mark.parametrize(
    "connector_to_asset_key_fn",
    [
        None,
        lambda conn, name: AssetKey([*conn.name.split("."), *name.split(".")]),
    ],
)
@pytest.mark.parametrize("multiple_connectors", [True, False])
def test_load_from_instance(
    connector_to_group_fn, filter_connector, connector_to_asset_key_fn, multiple_connectors
):
    load_calls = []

    @io_manager
    def test_io_manager(_context) -> IOManager:
        class TestIOManager(IOManager):
            def handle_output(self, context: OutputContext, obj) -> None:
                assert context.dagster_type.is_nothing
                return

            def load_input(self, context: InputContext) -> Any:
                load_calls.append(context.asset_key)
                return None

        return TestIOManager()

    ft_resource = FivetranResource(api_key="some_key", api_secret="some_secret")

    with responses.RequestsMock() as rsps:
        rsps.add(
            method=rsps.GET,
            url=ft_resource.api_base_url + "groups",
            json=get_sample_groups_response(),
            status=200,
        )
        rsps.add(
            method=rsps.GET,
            url=ft_resource.api_base_url + "groups/some_group/connectors",
            json=get_sample_connectors_response_multiple()
            if multiple_connectors
            else get_sample_connectors_response(),
            status=200,
        )
        rsps.add(
            rsps.GET,
            f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID}/schemas",
            json=get_complex_sample_connector_schema_config(),
        )
        if multiple_connectors:
            rsps.add(
                rsps.GET,
                f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID_2}/schemas",
                json=get_complex_sample_connector_schema_config(),
            )

        if connector_to_group_fn:
            ft_cacheable_assets = load_assets_from_fivetran_instance(
                ft_resource,
                connector_to_group_fn=connector_to_group_fn,
                connector_filter=(lambda _: False) if filter_connector else None,
                connector_to_asset_key_fn=connector_to_asset_key_fn,
                connector_to_io_manager_key_fn=(lambda _: "test_io_manager"),
            )
        else:
            ft_cacheable_assets = load_assets_from_fivetran_instance(
                ft_resource,
                connector_filter=(lambda _: False) if filter_connector else None,
                connector_to_asset_key_fn=connector_to_asset_key_fn,
                io_manager_key="test_io_manager",
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
                FivetranConnectionMetadata("some_service.some_name", "", "=", []),
                ".".join(t.path),
            )
            for t in tables
        }

    # Set up a downstream asset to consume the xyz output table
    xyz_asset_key = (
        connector_to_asset_key_fn(
            FivetranConnectionMetadata("some_service.some_name", "", "=", []),
            "abc.xyz",
        )
        if connector_to_asset_key_fn
        else AssetKey(["abc", "xyz"])
    )

    @asset(ins={"xyz": AssetIn(key=xyz_asset_key)})
    def downstream_asset(xyz):
        return

    all_assets = [downstream_asset] + ft_assets

    # Check schema metadata is added correctly to asset def
    assert any(
        out.metadata.get("table_schema")
        == MetadataValue.table_schema(
            TableSchema(
                columns=[
                    TableColumn(name="column_1", type="any"),
                    TableColumn(name="column_2", type="any"),
                    TableColumn(name="column_3", type="any"),
                ]
            )
        )
        for out in ft_assets[0].node_def.output_defs
    )

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
    fivetran_sync_job = build_assets_job(
        name="fivetran_assets_job",
        assets=all_assets,
    )

    with responses.RequestsMock() as rsps:
        api_prefixes = [
            f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID}",
        ]
        if multiple_connectors:
            api_prefixes.append(f"{ft_resource.api_connector_url}{DEFAULT_CONNECTOR_ID_2}")
        for api_prefix in api_prefixes:
            rsps.add(rsps.PATCH, api_prefix, json=get_sample_update_response())
            rsps.add(rsps.POST, f"{api_prefix}/force", json=get_sample_sync_response())
            # connector schema
            rsps.add(
                rsps.GET, f"{api_prefix}/schemas", json=get_complex_sample_connector_schema_config()
            )
            # initial state
            rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
            # n polls before updating
            for _ in range(2):
                rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
            # final state will be updated
            rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response(data=final_data))

        result = fivetran_sync_job.execute_in_process()
        asset_materializations = [
            event
            for event in result.events_for_node("fivetran_sync_some_connector")
            if event.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(asset_materializations) == 3
        asset_keys = set(
            mat.event_specific_data.materialization.asset_key for mat in asset_materializations
        )
        assert asset_keys == tables

        # Validate IO manager is called to retrieve the xyz asset which our downstream asset depends on
        assert load_calls == [xyz_asset_key]
