import pytest
import responses
from dagster_airbyte import airbyte_resource
from dagster_airbyte.asset_defs import load_assets_from_airbyte_instance

from dagster import AssetKey, build_init_resource_context, materialize
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema

from .utils import (
    get_instance_connections_json,
    get_instance_operations_json,
    get_instance_workspaces_json,
    get_project_connection_json,
    get_project_job_json,
)


@responses.activate
@pytest.mark.parametrize("use_normalization_tables", [True, False])
@pytest.mark.parametrize("connection_to_group_fn", [None, lambda x: f"{x[0]}_group"])
def test_load_from_instance(use_normalization_tables, connection_to_group_fn):

    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
            }
        )
    )
    ab_instance = airbyte_resource.configured(
        {
            "host": "some_host",
            "port": "8000",
        }
    )

    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/workspaces/list",
        json=get_instance_workspaces_json(),
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/list",
        json=get_instance_connections_json(),
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/operations/list",
        json=get_instance_operations_json(),
        status=200,
    )
    if connection_to_group_fn:
        ab_cacheable_assets = load_assets_from_airbyte_instance(
            ab_instance,
            create_assets_for_normalization_tables=use_normalization_tables,
            connection_to_group_fn=connection_to_group_fn,
        )
    else:
        ab_cacheable_assets = load_assets_from_airbyte_instance(
            ab_instance,
            create_assets_for_normalization_tables=use_normalization_tables,
        )
    ab_assets = ab_cacheable_assets.build_definitions(ab_cacheable_assets.compute_cacheable_data())

    tables = {"dagster_releases", "dagster_tags", "dagster_teams"} | (
        {
            "dagster_releases_assets",
            "dagster_releases_author",
            "dagster_tags_commit",
            "dagster_releases_foo",
        }
        if use_normalization_tables
        else set()
    )

    # Check schema metadata is added correctly to asset def

    assert any(
        out.metadata.get("schema")
        == MetadataValue.table_schema(
            TableSchema(
                columns=[
                    TableColumn(name="commit", type="['null', 'object']"),
                    TableColumn(name="name", type="['null', 'string']"),
                    TableColumn(name="node_id", type="['null', 'string']"),
                    TableColumn(name="repository", type="['string']"),
                    TableColumn(name="tarball_url", type="['null', 'string']"),
                    TableColumn(name="zipball_url", type="['null', 'string']"),
                ]
            )
        )
        for out in ab_assets[0].node_def.output_defs
    )
    # Check schema metadata works for normalization tables too
    if use_normalization_tables:
        assert any(
            out.metadata.get("schema")
            == MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name="sha", type="['null', 'string']"),
                        TableColumn(name="url", type="['null', 'string']"),
                    ]
                )
            )
            for out in ab_assets[0].node_def.output_defs
        )

    assert ab_assets[0].keys == {AssetKey(t) for t in tables}
    assert all(
        [
            ab_assets[0].group_names_by_key.get(AssetKey(t))
            == (
                connection_to_group_fn("GitHub <> snowflake-ben")
                if connection_to_group_fn
                else "github_snowflake_ben"
            )
            for t in tables
        ]
    )
    assert len(ab_assets[0].op.output_defs) == len(tables)

    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/get",
        json=get_project_connection_json(),
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/sync",
        json={"job": {"id": 1}},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs/get",
        json=get_project_job_json(),
        status=200,
    )

    res = materialize(ab_assets)

    materializations = [
        event.event_specific_data.materialization
        for event in res.events_for_node("airbyte_sync_87b7f")
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == len(tables)
    assert {m.asset_key for m in materializations} == {AssetKey(t) for t in tables}
