import pytest
import responses
from dagster import (
    AssetKey,
    AutoMaterializePolicy,
    FreshnessPolicy,
    TableColumn,
    TableSchema,
    asset,
    build_init_resource_context,
)
from dagster._core.definitions.materialize import materialize_to_memory
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.events import StepMaterializationData
from dagster_airbyte import AirbyteCloudResource, airbyte_resource, build_airbyte_assets

from dagster_airbyte_tests.utils import get_sample_connection_json, get_sample_job_json


@responses.activate
@pytest.mark.parametrize("schema_prefix", ["", "the_prefix_"])
@pytest.mark.parametrize("auto_materialize_policy", [None, AutoMaterializePolicy.lazy()])
def test_assets(schema_prefix, auto_materialize_policy, monkeypatch):
    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
                "poll_interval": 0,
            }
        )
    )
    destination_tables = ["foo", "bar"]
    if schema_prefix:
        destination_tables = [schema_prefix + t for t in destination_tables]
    connection_id = "12345"
    ab_assets = build_airbyte_assets(
        connection_id=connection_id,
        destination_tables=destination_tables,
        asset_key_prefix=["some", "prefix"],
        auto_materialize_policy=auto_materialize_policy,
    )
    ab_assets_name = f"airbyte_sync_{connection_id.replace('-', '_')}"

    assert ab_assets[0].keys == {AssetKey(["some", "prefix", t]) for t in destination_tables}
    assert len(ab_assets[0].op.output_defs) == 2

    assert all(
        spec.auto_materialize_policy == auto_materialize_policy for spec in ab_assets[0].specs
    )

    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/get",
        json=get_sample_connection_json(prefix=schema_prefix),
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
        json=get_sample_job_json(schema_prefix=schema_prefix),
        status=200,
    )

    res = materialize_to_memory(
        ab_assets,
        resources={
            "airbyte": airbyte_resource.configured(
                {
                    "host": "some_host",
                    "port": "8000",
                    "poll_interval": 0,
                }
            )
        },
    )

    materializations = [
        event.event_specific_data.materialization  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
        for event in res.events_for_node(ab_assets_name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 3
    assert {m.asset_key for m in materializations} == {
        AssetKey(["some", "prefix", schema_prefix + "foo"]),
        AssetKey(["some", "prefix", schema_prefix + "bar"]),
        AssetKey(["some", "prefix", schema_prefix + "baz"]),
    }
    assert materializations[0].metadata["bytesEmitted"] == MetadataValue.int(1234)
    assert materializations[0].metadata["recordsCommitted"] == MetadataValue.int(4321)
    assert materializations[0].metadata["schema"] == MetadataValue.table_schema(
        TableSchema(
            columns=[
                TableColumn(name="a", type="str"),
                TableColumn(name="b", type="int"),
            ]
        )
    )


@responses.activate
@pytest.mark.parametrize("schema_prefix", ["", "the_prefix_"])
@pytest.mark.parametrize("source_asset", [None, "my_source_asset_key"])
@pytest.mark.parametrize("freshness_policy", [None, FreshnessPolicy(maximum_lag_minutes=60)])
@pytest.mark.parametrize("auto_materialize_policy", [None, AutoMaterializePolicy.lazy()])
def test_assets_with_normalization(
    schema_prefix, source_asset, freshness_policy, auto_materialize_policy
):
    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
                "poll_interval": 0,
            }
        )
    )
    destination_tables = ["foo", "bar"]
    if schema_prefix:
        destination_tables = [schema_prefix + t for t in destination_tables]

    bar_normalization_tables = {schema_prefix + "bar_baz", schema_prefix + "bar_qux"}
    connection_id = "12345"
    ab_assets = build_airbyte_assets(
        connection_id=connection_id,
        destination_tables=destination_tables,
        normalization_tables={destination_tables[1]: bar_normalization_tables},
        asset_key_prefix=["some", "prefix"],
        deps=[AssetKey(source_asset)] if source_asset else None,
        freshness_policy=freshness_policy,
        auto_materialize_policy=auto_materialize_policy,
    )
    ab_assets_name = f"airbyte_sync_{connection_id.replace('-', '_')}"

    assert all(spec.freshness_policy == freshness_policy for spec in ab_assets[0].specs)

    assert ab_assets[0].keys == {AssetKey(["some", "prefix", t]) for t in destination_tables} | {
        AssetKey(["some", "prefix", t]) for t in bar_normalization_tables
    }
    assert len(ab_assets[0].op.output_defs) == 4

    assert all(
        spec.auto_materialize_policy == auto_materialize_policy for spec in ab_assets[0].specs
    )

    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/get",
        json=get_sample_connection_json(prefix=schema_prefix),
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
        json=get_sample_job_json(schema_prefix=schema_prefix),
        status=200,
    )

    source_assets = [SourceAsset(AssetKey(source_asset))] if source_asset else []
    res = materialize_to_memory(
        [*ab_assets, *source_assets],
        selection=ab_assets,
        resources={
            "airbyte": airbyte_resource.configured(
                {
                    "host": "some_host",
                    "port": "8000",
                    "poll_interval": 0,
                }
            )
        },
    )

    materializations = [
        event.event_specific_data.materialization  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
        for event in res.events_for_node(ab_assets_name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 5
    assert {m.asset_key for m in materializations} == {
        AssetKey(["some", "prefix", schema_prefix + "foo"]),
        AssetKey(["some", "prefix", schema_prefix + "bar"]),
        AssetKey(["some", "prefix", schema_prefix + "baz"]),
        # Normalized materializations are there
        AssetKey(["some", "prefix", schema_prefix + "bar_baz"]),
        AssetKey(["some", "prefix", schema_prefix + "bar_qux"]),
    }
    assert materializations[0].metadata["bytesEmitted"] == MetadataValue.int(1234)
    assert materializations[0].metadata["recordsCommitted"] == MetadataValue.int(4321)
    assert materializations[0].metadata["schema"].value == TableSchema(
        columns=[
            TableColumn(name="a", type="str"),
            TableColumn(name="b", type="int"),
        ]
    )

    # No metadata for normalized materializations, for now
    assert not materializations[3].metadata


def test_assets_cloud() -> None:
    ab_resource = AirbyteCloudResource(
        client_id="some_client_id", client_secret="some_client_secret", poll_interval=0
    )
    ab_url = ab_resource.api_base_url

    connection_id = "12345"
    ab_assets = build_airbyte_assets(
        connection_id=connection_id,
        destination_tables=["foo", "bar"],
        normalization_tables={"bar": {"bar_baz", "bar_qux"}},
        asset_key_prefix=["some", "prefix"],
        group_name="foo",
    )
    ab_assets_name = f"airbyte_sync_{connection_id.replace('-', '_')}"

    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.POST,
            f"{ab_url}/applications/token",
            json={"access_token": "some_access_token"},
        )
        rsps.add(
            rsps.POST,
            f"{ab_url}/jobs",
            json={"jobId": 1, "status": "pending", "jobType": "sync"},
        )

        rsps.add(
            rsps.GET,
            f"{ab_url}/jobs/1",
            json={"jobId": 1, "status": "running", "jobType": "sync"},
        )
        rsps.add(
            rsps.GET,
            f"{ab_url}/jobs/1",
            json={"jobId": 1, "status": "succeeded", "jobType": "sync"},
        )

        res = materialize_to_memory(
            ab_assets,
            resources={"airbyte": ab_resource},
        )

        materializations = [
            event.event_specific_data.materialization
            for event in res.events_for_node(ab_assets_name)
            if event.event_type_value == "ASSET_MATERIALIZATION"
            and isinstance(event.event_specific_data, StepMaterializationData)
        ]
        assert len(materializations) == 4
        assert {m.asset_key for m in materializations} == {
            AssetKey(["some", "prefix", "foo"]),
            AssetKey(["some", "prefix", "bar"]),
            AssetKey(["some", "prefix", "bar_baz"]),
            AssetKey(["some", "prefix", "bar_qux"]),
        }
        assert {spec.key: spec.group_name for spec in ab_assets[0].specs} == {
            AssetKey(["some", "prefix", "foo"]): "foo",
            AssetKey(["some", "prefix", "bar"]): "foo",
            AssetKey(["some", "prefix", "bar_baz"]): "foo",
            AssetKey(["some", "prefix", "bar_qux"]): "foo",
        }


def test_built_airbyte_asset_with_downstream_asset_via_definition():
    destination_tables = ["foo", "bar"]
    ab_assets = build_airbyte_assets(
        "12345",
        destination_tables=destination_tables,
        asset_key_prefix=["some", "prefix"],
    )

    @asset(deps=ab_assets)
    def downstream_of_ab():
        return None

    assert len(downstream_of_ab.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert downstream_of_ab.op.ins["some_prefix_foo"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream_of_ab.op.ins["some_prefix_bar"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]


def test_built_airbyte_asset_with_downstream_asset():
    destination_tables = ["foo", "bar"]
    ab_assets = build_airbyte_assets(  # noqa: F841
        "12345",
        destination_tables=destination_tables,
        asset_key_prefix=["some", "prefix"],
    )

    @asset(deps=[AssetKey(["some", "prefix", "foo"]), AssetKey(["some", "prefix", "bar"])])
    def downstream_of_ab():
        return None

    assert len(downstream_of_ab.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert downstream_of_ab.op.ins["some_prefix_foo"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream_of_ab.op.ins["some_prefix_bar"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]


def test_built_airbyte_asset_table_name():
    destination_tables = ["foo", "bar"]

    ab_assets = build_airbyte_assets(
        "12345",
        destination_tables=destination_tables,
        normalization_tables={"foo": {"baz"}},
    )

    # Check relation identifier metadata is added correctly to asset def
    assets_def = ab_assets[0]
    for metadata in assets_def.metadata_by_key.values():
        assert metadata.get("dagster/table_name") is None

    ab_assets = build_airbyte_assets(
        "12345",
        destination_tables=destination_tables,
        destination_database="test_database",
        destination_schema="test_schema",
    )

    table_names = {"test_database.test_schema.foo", "test_database.test_schema.bar"}

    # Check relation identifier metadata is added correctly to asset def
    assets_def = ab_assets[0]
    for key, metadata in assets_def.metadata_by_key.items():
        # Extract the table name from the asset key
        table_name = key.path[-1]
        assert metadata["dagster/table_name"] in table_names
        assert table_name in metadata["dagster/table_name"]

    ab_assets = build_airbyte_assets(
        "12345",
        destination_tables=destination_tables,
        destination_database="test_database",
        destination_schema="test_schema",
        normalization_tables={"foo": {"baz"}},
    )

    table_names.add("test_database.test_schema.foo.baz")

    # Check relation identifier metadata is added correctly to asset def
    assets_def = ab_assets[0]
    for key, metadata in assets_def.metadata_by_key.items():
        # Extract the table name from the asset key
        table_name = key.path[-1]
        assert metadata["dagster/table_name"] in table_names
        assert table_name in metadata["dagster/table_name"]
