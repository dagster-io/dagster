import sys
from typing import Any

import pytest
import responses
from dagster import (
    AssetKey,
    EnvVar,
    FreshnessPolicy,
    InputContext,
    IOManager,
    OutputContext,
    asset,
    io_manager,
    materialize,
)
from dagster._check import ParameterCheckError
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.execution.context.init import build_init_resource_context
from dagster._core.execution.with_resources import with_resources
from dagster._core.instance_for_test import environ
from dagster_airbyte import AirbyteCloudResource, AirbyteResource, airbyte_resource
from dagster_airbyte.asset_defs import AirbyteConnectionMetadata, load_assets_from_airbyte_instance

from dagster_airbyte_tests.utils import (
    get_instance_connections_json,
    get_instance_operations_json,
    get_instance_workspaces_json,
    get_project_connection_json,
    get_project_job_json,
)

TEST_FRESHNESS_POLICY = FreshnessPolicy(maximum_lag_minutes=60)


@pytest.fixture(name="airbyte_instance", params=[True, False], scope="module")
def airbyte_instance_fixture(request):
    with environ({"AIRBYTE_HOST": "some_host"}):
        if request.param:
            yield AirbyteResource(host=EnvVar("AIRBYTE_HOST"), port="8000", poll_interval=0)
        else:
            yield airbyte_resource(
                build_init_resource_context(
                    {"host": "some_host", "port": "8000", "poll_interval": 0}
                )
            )


@pytest.mark.skipif(sys.version_info >= (3, 12), reason="something with py3.12 and sqlite")
@responses.activate
@pytest.mark.parametrize("use_normalization_tables", [True, False])
@pytest.mark.parametrize(
    "connection_to_group_fn, connection_meta_to_group_fn",
    [(None, lambda meta: f"{meta.name[0]}_group"), (None, None), (lambda x: f"{x[0]}_group", None)],
)
@pytest.mark.parametrize("filter_connection", [True, False])
@pytest.mark.parametrize(
    "connection_to_asset_key_fn", [None, lambda conn, name: AssetKey([f"{conn.name[0]}_{name}"])]
)
@pytest.mark.parametrize(
    "connection_to_freshness_policy_fn", [None, lambda _: TEST_FRESHNESS_POLICY]
)
@pytest.mark.parametrize(
    "connection_to_auto_materialize_policy_fn", [None, lambda _: AutoMaterializePolicy.lazy()]
)
def test_load_from_instance(
    use_normalization_tables,
    connection_to_group_fn,
    connection_meta_to_group_fn,
    filter_connection,
    connection_to_asset_key_fn,
    connection_to_freshness_policy_fn,
    connection_to_auto_materialize_policy_fn,
    airbyte_instance: AirbyteResource,
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

    base_url = "http://some_host:8000/api/v1"
    responses.add(
        method=responses.POST,
        url=base_url + "/workspaces/list",
        json=get_instance_workspaces_json(),
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=base_url + "/connections/list",
        json=get_instance_connections_json(),
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=base_url + "/operations/list",
        json=get_instance_operations_json(),
        status=200,
    )
    if connection_to_group_fn:
        ab_cacheable_assets = load_assets_from_airbyte_instance(
            airbyte_instance,
            create_assets_for_normalization_tables=use_normalization_tables,
            connection_to_group_fn=connection_to_group_fn,
            connection_meta_to_group_fn=connection_meta_to_group_fn,
            connection_filter=(lambda _: False) if filter_connection else None,
            connection_to_io_manager_key_fn=(lambda _: "test_io_manager"),
            connection_to_asset_key_fn=connection_to_asset_key_fn,
            connection_to_freshness_policy_fn=connection_to_freshness_policy_fn,
            connection_to_auto_materialize_policy_fn=connection_to_auto_materialize_policy_fn,
        )
    else:
        ab_cacheable_assets = load_assets_from_airbyte_instance(
            airbyte_instance,
            create_assets_for_normalization_tables=use_normalization_tables,
            connection_filter=(lambda _: False) if filter_connection else None,
            io_manager_key="test_io_manager",
            connection_meta_to_group_fn=connection_meta_to_group_fn,
            connection_to_asset_key_fn=connection_to_asset_key_fn,
            connection_to_freshness_policy_fn=connection_to_freshness_policy_fn,
            connection_to_auto_materialize_policy_fn=connection_to_auto_materialize_policy_fn,
        )
    ab_assets = ab_cacheable_assets.build_definitions(ab_cacheable_assets.compute_cacheable_data())
    ab_assets = list(with_resources(ab_assets, {"test_io_manager": test_io_manager}))

    if connection_to_asset_key_fn:

        @asset
        def downstream_asset(G_dagster_tags):
            return

    else:

        @asset
        def downstream_asset(dagster_tags):
            return

    all_assets = [downstream_asset] + ab_assets

    if filter_connection:
        assert len(ab_assets) == 0
        return

    tables = {
        "dagster_releases",
        "dagster_tags",
        "dagster_teams",
        "dagster_array_test",
        "dagster_unknown_test",
    } | (
        {
            "dagster_releases_assets",
            "dagster_releases_author",
            "dagster_tags_commit",
            "dagster_releases_foo",
            "dagster_array_test_author",
        }
        if use_normalization_tables
        else set()
    )

    if connection_to_asset_key_fn:
        tables = {
            connection_to_asset_key_fn(
                AirbyteConnectionMetadata(
                    "Github <> snowflake-ben", "", use_normalization_tables, []
                ),
                t,
            ).path[0]
            for t in tables
        }

    # Check schema metadata is added correctly to asset def

    assert any(
        out.metadata.get("table_schema")
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
            out.metadata.get("table_schema")
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
            ab_assets[0].specs_by_key[AssetKey(t)].group_name
            == (
                connection_meta_to_group_fn(
                    AirbyteConnectionMetadata("GitHub <> snowflake-ben", "", False, [])
                )
                if connection_meta_to_group_fn
                else (
                    connection_to_group_fn("GitHub <> snowflake-ben")
                    if connection_to_group_fn
                    else "github_snowflake_ben"
                )
            )
            for t in tables
        ]
    )
    assert len(ab_assets[0].op.output_defs) == len(tables)

    expected_freshness_policy = TEST_FRESHNESS_POLICY if connection_to_freshness_policy_fn else None
    freshness_policies = {spec.key: spec.freshness_policy for spec in ab_assets[0].specs}
    assert all(freshness_policies[key] == expected_freshness_policy for key in freshness_policies)

    expected_auto_materialize_policy = (
        AutoMaterializePolicy.lazy() if connection_to_auto_materialize_policy_fn else None
    )
    auto_materialize_policies_by_key = {
        spec.key: spec.auto_materialize_policy for spec in ab_assets[0].specs
    }
    if expected_auto_materialize_policy:
        assert auto_materialize_policies_by_key
    assert all(
        auto_materialize_policies_by_key[key] == expected_auto_materialize_policy
        for key in auto_materialize_policies_by_key
    )

    responses.add(
        method=responses.POST,
        url=base_url + "/connections/get",
        json=get_project_connection_json(),
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=base_url + "/connections/sync",
        json={"job": {"id": 1}},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=base_url + "/jobs/get",
        json=get_project_job_json(),
        status=200,
    )

    res = materialize(all_assets)

    materializations = [
        event.event_specific_data.materialization  # type: ignore[attr-defined]
        for event in res.events_for_node("airbyte_sync_87b7f")
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == len(tables)
    assert {m.asset_key for m in materializations} == {AssetKey(t) for t in tables}

    assert load_calls == [
        AssetKey("G_dagster_tags" if connection_to_asset_key_fn else "dagster_tags")
    ]


def test_load_from_instance_cloud() -> None:
    airbyte_cloud_instance = AirbyteCloudResource(
        client_id="some_client_id", client_secret="some_client_secret", poll_interval=0
    )

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="load_assets_from_airbyte_instance is not yet supported for AirbyteCloudResource",
    ):
        load_assets_from_airbyte_instance(airbyte_cloud_instance)  # type: ignore


def test_load_from_instance_with_downstream_asset_errors():
    ab_cacheable_assets = load_assets_from_airbyte_instance(
        AirbyteResource(host="some_host", port="8000", poll_interval=0)
    )

    with pytest.raises(
        ParameterCheckError,
        match='Param "asset" is not one of ',
    ):

        @asset(deps=[ab_cacheable_assets])
        def downstream_of_ab():
            return None
