import responses
from dagster_airbyte import AirbyteState, airbyte_resource, build_airbyte_assets

from dagster import MetadataEntry, build_assets_job, build_init_resource_context


@responses.activate
def test_assets():

    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
            }
        )
    )
    ab_assets = build_airbyte_assets("12345", ["foo", "bar"], asset_key_prefix=["some", "prefix"])

    assert len(ab_assets[0].op.output_defs) == 2

    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/get",
        json={
            "name": "xyz",
            "syncCatalog": {
                "streams": [
                    {
                        "stream": {
                            "name": "foo",
                            "jsonSchema": {
                                "properties": {"a": {"type": "str"}, "b": {"type": "int"}}
                            },
                        },
                        "config": {"selected": True},
                    },
                    {
                        "stream": {
                            "name": "bar",
                            "jsonSchema": {
                                "properties": {
                                    "c": {"type": "str"},
                                }
                            },
                        },
                        "config": {"selected": True},
                    },
                    {
                        "stream": {
                            "name": "baz",
                            "jsonSchema": {
                                "properties": {
                                    "d": {"type": "str"},
                                }
                            },
                        },
                        "config": {"selected": True},
                    },
                ]
            },
        },
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
        json={
            "job": {"id": 1, "status": AirbyteState.SUCCEEDED},
            "attempts": [
                {
                    "attempt": {
                        "streamStats": [
                            {
                                "streamName": "foo",
                                "stats": {
                                    "bytesEmitted": 1234,
                                    "recordsCommitted": 4321,
                                },
                            },
                            {
                                "streamName": "bar",
                                "stats": {
                                    "bytesEmitted": 1234,
                                    "recordsCommitted": 4321,
                                },
                            },
                            {
                                "streamName": "baz",
                                "stats": {
                                    "bytesEmitted": 1111,
                                    "recordsCommitted": 1111,
                                },
                            },
                        ]
                    }
                }
            ],
        },
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
        event
        for event in res.events_for_node("airbyte_sync_12345")
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 3
    assert (
        MetadataEntry.text("a,b", "columns")
        in materializations[0].event_specific_data.materialization.metadata_entries
    )
    assert (
        MetadataEntry.int(1234, "bytesEmitted")
        in materializations[0].event_specific_data.materialization.metadata_entries
    )
    assert (
        MetadataEntry.int(4321, "recordsCommitted")
        in materializations[0].event_specific_data.materialization.metadata_entries
    )
