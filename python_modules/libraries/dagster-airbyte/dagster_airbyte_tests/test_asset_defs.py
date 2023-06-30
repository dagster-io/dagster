import re

import pytest
import responses
from dagster import (
    AssetKey,
    FreshnessPolicy,
    TableColumn,
    TableSchema,
    asset,
    build_init_resource_context,
)
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.events import StepMaterializationData
from dagster._core.types.dagster_type import DagsterTypeKind
from dagster._legacy import build_assets_job
from dagster_airbyte import AirbyteCloudResource, airbyte_resource, build_airbyte_assets

from .utils import get_sample_connection_json, get_sample_job_json


@responses.activate
@pytest.mark.parametrize("schema_prefix", ["", "the_prefix_"])
def test_assets(schema_prefix):
    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
            }
        )
    )
    destination_tables = ["foo", "bar"]
    if schema_prefix:
        destination_tables = [schema_prefix + t for t in destination_tables]
    ab_assets = build_airbyte_assets(
        "12345",
        destination_tables=destination_tables,
        asset_key_prefix=["some", "prefix"],
    )

    assert ab_assets[0].keys == {AssetKey(["some", "prefix", t]) for t in destination_tables}
    assert len(ab_assets[0].op.output_defs) == 2

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

    ab_job = build_assets_job(
        "ab_job",
        ab_assets,
        resource_defs={
            "airbyte": airbyte_resource.configured(
                {
                    "host": "some_host",
                    "port": "8000",
                }
            )
        },
    )

    res = ab_job.execute_in_process()

    materializations = [
        event.event_specific_data.materialization
        for event in res.events_for_node("airbyte_sync_12345")
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
def test_assets_with_normalization(schema_prefix, source_asset, freshness_policy):
    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
            }
        )
    )
    destination_tables = ["foo", "bar"]
    if schema_prefix:
        destination_tables = [schema_prefix + t for t in destination_tables]

    bar_normalization_tables = {schema_prefix + "bar_baz", schema_prefix + "bar_qux"}
    ab_assets = build_airbyte_assets(
        "12345",
        destination_tables=destination_tables,
        normalization_tables={destination_tables[1]: bar_normalization_tables},
        asset_key_prefix=["some", "prefix"],
        upstream_assets={AssetKey(source_asset)} if source_asset else None,
        freshness_policy=freshness_policy,
    )

    freshness_policies = ab_assets[0].freshness_policies_by_key
    assert all(freshness_policies[key] == freshness_policy for key in freshness_policies)

    assert ab_assets[0].keys == {AssetKey(["some", "prefix", t]) for t in destination_tables} | {
        AssetKey(["some", "prefix", t]) for t in bar_normalization_tables
    }
    assert len(ab_assets[0].op.output_defs) == 4

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

    ab_job = build_assets_job(
        "ab_job",
        ab_assets,
        source_assets=[SourceAsset(AssetKey(source_asset))] if source_asset else None,
        resource_defs={
            "airbyte": airbyte_resource.configured(
                {
                    "host": "some_host",
                    "port": "8000",
                }
            )
        },
    )

    res = ab_job.execute_in_process()

    materializations = [
        event.event_specific_data.materialization
        for event in res.events_for_node("airbyte_sync_12345")
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
    ab_resource = AirbyteCloudResource(api_key="some_key")
    ab_url = ab_resource.api_base_url

    ab_assets = build_airbyte_assets(
        "12345",
        destination_tables=["foo", "bar"],
        normalization_tables={"bar": {"bar_baz", "bar_qux"}},
        asset_key_prefix=["some", "prefix"],
        group_name="foo",
    )

    ab_job = build_assets_job(
        "ab_job",
        ab_assets,
        resource_defs={"airbyte": ab_resource},
    )

    with responses.RequestsMock() as rsps:
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

        res = ab_job.execute_in_process()

        materializations = [
            event.event_specific_data.materialization
            for event in res.events_for_node("airbyte_sync_12345")
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
        assert ab_assets[0].group_names_by_key == {
            AssetKey(["some", "prefix", "foo"]): "foo",
            AssetKey(["some", "prefix", "bar"]): "foo",
            AssetKey(["some", "prefix", "bar_baz"]): "foo",
            AssetKey(["some", "prefix", "bar_qux"]): "foo",
        }


def test_built_airbyte_asset_with_downstream_asset_errors():
    destination_tables = ["foo", "bar"]
    ab_assets = build_airbyte_assets(
        "12345",
        destination_tables=destination_tables,
        asset_key_prefix=["some", "prefix"],
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Cannot pass a multi_asset AssetsDefinition as an argument to deps."
            " Instead, specify dependencies on the assets created by the multi_asset via AssetKeys"
            " or strings."
            " For the multi_asset airbyte_sync_12345, the available keys are: "
            "{AssetKey(['some', 'prefix', 'bar']), AssetKey(['some', 'prefix', 'foo'])}"
        ),
    ):

        @asset(deps=ab_assets)
        def downstream_of_ab():
            return None


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

    assert len(downstream_of_ab.input_names) == 2
    assert downstream_of_ab.op.ins["some_prefix_foo"].dagster_type.kind == DagsterTypeKind.NOTHING
    assert downstream_of_ab.op.ins["some_prefix_bar"].dagster_type.kind == DagsterTypeKind.NOTHING
