from dagster_airbyte import AirbyteState

from dagster.utils.merger import deep_merge_dicts


def get_sample_connection_json(**kwargs):
    return deep_merge_dicts(
        {
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
                    {
                        "stream": {
                            "name": "qux",
                            "jsonSchema": {
                                "properties": {
                                    "e": {"type": "str"},
                                }
                            },
                        },
                        "config": {"selected": False},
                    },
                ]
            },
        },
        kwargs,
    )


def get_sample_job_json(schema_prefix=""):
    return {
        "job": {"id": 1, "status": AirbyteState.SUCCEEDED},
        "attempts": [
            {
                "attempt": {
                    "streamStats": [
                        {
                            "streamName": schema_prefix + "foo",
                            "stats": {
                                "bytesEmitted": 1234,
                                "recordsCommitted": 4321,
                            },
                        },
                        {
                            "streamName": schema_prefix + "bar",
                            "stats": {
                                "bytesEmitted": 1234,
                                "recordsCommitted": 4321,
                            },
                        },
                        {
                            "streamName": schema_prefix + "baz",
                            "stats": {
                                "bytesEmitted": 1111,
                                "recordsCommitted": 1111,
                            },
                        },
                    ]
                }
            }
        ],
    }
