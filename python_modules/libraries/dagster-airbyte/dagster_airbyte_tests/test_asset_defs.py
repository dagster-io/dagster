import pytest
import responses
from dagster_airbyte import airbyte_resource, build_airbyte_assets

from dagster import AssetKey, MetadataEntry, TableColumn, TableSchema, build_init_resource_context
from dagster._legacy import build_assets_job

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
    assert MetadataEntry("bytesEmitted", value=1234) in materializations[0].metadata_entries
    assert MetadataEntry("recordsCommitted", value=4321) in materializations[0].metadata_entries
    assert (
        MetadataEntry(
            "schema",
            value=TableSchema(
                columns=[
                    TableColumn(name="a", type="str"),
                    TableColumn(name="b", type="int"),
                ]
            ),
        )
        in materializations[0].metadata_entries
    )
