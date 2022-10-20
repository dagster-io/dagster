from dagster_airbyte import AirbyteState

from dagster._utils.merger import deep_merge_dicts


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


def get_sample_job_list_json(schema_prefix=""):
    return {
        "jobs": [
            {
                "job": {"id": 1, "status": AirbyteState.SUCCEEDED},
                "attempts": [
                    {
                        "streamStats": [
                            {
                                "streamName": schema_prefix + "foo",
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
                ],
            }
        ]
    }


def get_project_connection_json(**kwargs):
    return deep_merge_dicts(
        {
            "name": "GitHub <> snowflake-ben",
            "prefix": "dagster_",
            "syncCatalog": {
                "streams": [
                    {
                        "stream": {
                            "name": "releases",
                            "jsonSchema": {
                                "type": "object",
                                "$schema": "http://json-schema.org/draft-07/schema#",
                                "properties": {
                                    "id": {"type": ["null", "integer"]},
                                    "url": {"type": ["null", "string"]},
                                    "body": {"type": ["null", "string"]},
                                    "name": {"type": ["null", "string"]},
                                    "draft": {"type": ["null", "boolean"]},
                                    "assets": {
                                        "type": ["null", "array"],
                                        "items": {
                                            "type": ["null", "object"],
                                            "properties": {
                                                "id": {"type": ["null", "integer"]},
                                                "url": {"type": ["null", "string"]},
                                                "name": {"type": ["null", "string"]},
                                                "size": {"type": ["null", "integer"]},
                                                "label": {"type": ["null", "string"]},
                                                "state": {"type": ["null", "string"]},
                                                "node_id": {"type": ["null", "string"]},
                                                "created_at": {
                                                    "type": ["null", "string"],
                                                    "format": "date-time",
                                                },
                                                "updated_at": {
                                                    "type": ["null", "string"],
                                                    "format": "date-time",
                                                },
                                                "uploader_id": {"type": ["null", "integer"]},
                                                "content_type": {"type": ["null", "string"]},
                                                "download_count": {"type": ["null", "integer"]},
                                                "browser_download_url": {
                                                    "type": ["null", "string"]
                                                },
                                            },
                                        },
                                    },
                                    "author": {
                                        "type": ["null", "object"],
                                        "properties": {
                                            "id": {"type": ["null", "integer"]},
                                            "url": {"type": ["null", "string"]},
                                            "type": {"type": ["null", "string"]},
                                            "login": {"type": ["null", "string"]},
                                            "node_id": {"type": ["null", "string"]},
                                            "html_url": {"type": ["null", "string"]},
                                            "gists_url": {"type": ["null", "string"]},
                                            "repos_url": {"type": ["null", "string"]},
                                            "avatar_url": {"type": ["null", "string"]},
                                            "events_url": {"type": ["null", "string"]},
                                            "site_admin": {"type": ["null", "boolean"]},
                                            "gravatar_id": {"type": ["null", "string"]},
                                            "starred_url": {"type": ["null", "string"]},
                                            "followers_url": {"type": ["null", "string"]},
                                            "following_url": {"type": ["null", "string"]},
                                            "organizations_url": {"type": ["null", "string"]},
                                            "subscriptions_url": {"type": ["null", "string"]},
                                            "received_events_url": {"type": ["null", "string"]},
                                        },
                                    },
                                    "node_id": {"type": ["null", "string"]},
                                    "html_url": {"type": ["null", "string"]},
                                    "tag_name": {"type": ["null", "string"]},
                                    "assets_url": {"type": ["null", "string"]},
                                    "created_at": {
                                        "type": ["null", "string"],
                                        "format": "date-time",
                                    },
                                    "prerelease": {"type": ["null", "boolean"]},
                                    "repository": {"type": ["string"]},
                                    "upload_url": {"type": ["null", "string"]},
                                    "tarball_url": {"type": ["null", "string"]},
                                    "zipball_url": {"type": ["null", "string"]},
                                    "published_at": {
                                        "type": ["null", "string"],
                                        "format": "date-time",
                                    },
                                    "target_commitish": {"type": ["null", "string"]},
                                    "foo": {
                                        "oneOf": [
                                            {
                                                "type": ["null", "object"],
                                                "properties": {"bar": {"type": "string"}},
                                            },
                                            {
                                                "type": ["null", "object"],
                                                "properties": {"baz": {"type": "string"}},
                                            },
                                        ]
                                    },
                                },
                            },
                            "supportedSyncModes": ["full_refresh", "incremental"],
                            "sourceDefinedCursor": True,
                            "defaultCursorField": ["created_at"],
                            "sourceDefinedPrimaryKey": [["id"]],
                        },
                        "config": {
                            "syncMode": "full_refresh",
                            "cursorField": ["created_at"],
                            "destinationSyncMode": "append",
                            "primaryKey": [["id"]],
                            "aliasName": "releases",
                            "selected": True,
                        },
                    },
                    {
                        "stream": {
                            "name": "tags",
                            "jsonSchema": {
                                "type": "object",
                                "$schema": "http://json-schema.org/draft-07/schema#",
                                "properties": {
                                    "name": {"type": ["null", "string"]},
                                    "commit": {
                                        "type": ["null", "object"],
                                        "properties": {
                                            "sha": {"type": ["null", "string"]},
                                            "url": {"type": ["null", "string"]},
                                        },
                                    },
                                    "node_id": {"type": ["null", "string"]},
                                    "repository": {"type": ["string"]},
                                    "tarball_url": {"type": ["null", "string"]},
                                    "zipball_url": {"type": ["null", "string"]},
                                },
                            },
                            "supportedSyncModes": ["full_refresh"],
                            "defaultCursorField": [],
                            "sourceDefinedPrimaryKey": [["repository"], ["name"]],
                        },
                        "config": {
                            "syncMode": "full_refresh",
                            "cursorField": [],
                            "destinationSyncMode": "append",
                            "primaryKey": [["repository"], ["name"]],
                            "aliasName": "tags",
                            "selected": True,
                        },
                    },
                    {
                        "stream": {
                            "name": "teams",
                            "jsonSchema": {
                                "type": "object",
                                "$schema": "http://json-schema.org/draft-07/schema#",
                                "properties": {
                                    "id": {"type": ["null", "integer"]},
                                    "url": {"type": ["null", "string"]},
                                    "name": {"type": ["null", "string"]},
                                    "slug": {"type": ["null", "string"]},
                                    "parent": {
                                        "type": ["null", "object"],
                                        "properties": {},
                                        "additionalProperties": True,
                                    },
                                    "node_id": {"type": ["null", "string"]},
                                    "privacy": {"type": ["null", "string"]},
                                    "html_url": {"type": ["null", "string"]},
                                    "permission": {"type": ["null", "string"]},
                                    "repository": {"type": ["null", "string"]},
                                    "description": {"type": ["null", "string"]},
                                    "members_url": {"type": ["null", "string"]},
                                    "organization": {"type": ["null", "string"]},
                                    "repositories_url": {"type": ["null", "string"]},
                                },
                            },
                            "supportedSyncModes": ["full_refresh"],
                            "defaultCursorField": [],
                            "sourceDefinedPrimaryKey": [["id"]],
                        },
                        "config": {
                            "syncMode": "full_refresh",
                            "cursorField": [],
                            "destinationSyncMode": "append",
                            "primaryKey": [["id"]],
                            "aliasName": "teams",
                            "selected": True,
                        },
                    },
                ]
            },
        },
        kwargs,
    )


def get_project_job_json():
    return {
        "job": {"id": 1, "status": AirbyteState.SUCCEEDED},
        "attempts": [
            {
                "attempt": {
                    "streamStats": [
                        {
                            "streamName": "dagster_teams",
                            "stats": {
                                "recordsEmitted": 3,
                                "bytesEmitted": 1493,
                                "recordsCommitted": 3,
                            },
                        },
                        {
                            "streamName": "dagster_tags",
                            "stats": {
                                "recordsEmitted": 622,
                                "bytesEmitted": 289815,
                                "recordsCommitted": 622,
                            },
                        },
                        {
                            "streamName": "dagster_releases",
                            "stats": {
                                "recordsEmitted": 119,
                                "bytesEmitted": 620910,
                                "recordsCommitted": 119,
                            },
                        },
                    ],
                }
            }
        ],
    }


def get_instance_workspaces_json():
    return {
        "workspaces": [
            {
                "workspaceId": "b49ed3cd-7bb4-4f11-b8ba-95b4a5f7bc75",
            }
        ]
    }


def get_instance_connections_json():
    return {
        "connections": [
            {
                "connectionId": "87b7fe85-a22c-420e-8d74-b30e7ede77df",
                "name": "GitHub <> snowflake-ben",
                "prefix": "dagster_",
                "sourceId": "4b8fc3cc-efce-41d7-8654-05c3fc03485e",
                "destinationId": "028fc82d-3a27-4fef-94a6-a22fbd45bac4",
                "operationIds": ["f39dbcd0-a6dc-4319-9ae4-28937997b48a"],
                "syncCatalog": {
                    "streams": [
                        {
                            "stream": {
                                "name": "releases",
                                "jsonSchema": {
                                    "type": "object",
                                    "$schema": "http://json-schema.org/draft-07/schema#",
                                    "properties": {
                                        "id": {"type": ["null", "integer"]},
                                        "url": {"type": ["null", "string"]},
                                        "body": {"type": ["null", "string"]},
                                        "name": {"type": ["null", "string"]},
                                        "draft": {"type": ["null", "boolean"]},
                                        "assets": {
                                            "type": ["null", "array"],
                                            "items": {
                                                "type": ["null", "object"],
                                                "properties": {
                                                    "id": {"type": ["null", "integer"]},
                                                    "url": {"type": ["null", "string"]},
                                                    "name": {"type": ["null", "string"]},
                                                    "size": {"type": ["null", "integer"]},
                                                    "label": {"type": ["null", "string"]},
                                                    "state": {"type": ["null", "string"]},
                                                    "node_id": {"type": ["null", "string"]},
                                                    "created_at": {
                                                        "type": ["null", "string"],
                                                        "format": "date-time",
                                                    },
                                                    "updated_at": {
                                                        "type": ["null", "string"],
                                                        "format": "date-time",
                                                    },
                                                    "uploader_id": {"type": ["null", "integer"]},
                                                    "content_type": {"type": ["null", "string"]},
                                                    "download_count": {"type": ["null", "integer"]},
                                                    "browser_download_url": {
                                                        "type": ["null", "string"]
                                                    },
                                                },
                                            },
                                        },
                                        "author": {
                                            "type": ["null", "object"],
                                            "properties": {
                                                "id": {"type": ["null", "integer"]},
                                                "url": {"type": ["null", "string"]},
                                                "type": {"type": ["null", "string"]},
                                                "login": {"type": ["null", "string"]},
                                                "node_id": {"type": ["null", "string"]},
                                                "html_url": {"type": ["null", "string"]},
                                                "gists_url": {"type": ["null", "string"]},
                                                "repos_url": {"type": ["null", "string"]},
                                                "avatar_url": {"type": ["null", "string"]},
                                                "events_url": {"type": ["null", "string"]},
                                                "site_admin": {"type": ["null", "boolean"]},
                                                "gravatar_id": {"type": ["null", "string"]},
                                                "starred_url": {"type": ["null", "string"]},
                                                "followers_url": {"type": ["null", "string"]},
                                                "following_url": {"type": ["null", "string"]},
                                                "organizations_url": {"type": ["null", "string"]},
                                                "subscriptions_url": {"type": ["null", "string"]},
                                                "received_events_url": {"type": ["null", "string"]},
                                            },
                                        },
                                        "node_id": {"type": ["null", "string"]},
                                        "html_url": {"type": ["null", "string"]},
                                        "tag_name": {"type": ["null", "string"]},
                                        "assets_url": {"type": ["null", "string"]},
                                        "created_at": {
                                            "type": ["null", "string"],
                                            "format": "date-time",
                                        },
                                        "prerelease": {"type": ["null", "boolean"]},
                                        "repository": {"type": ["string"]},
                                        "upload_url": {"type": ["null", "string"]},
                                        "tarball_url": {"type": ["null", "string"]},
                                        "zipball_url": {"type": ["null", "string"]},
                                        "published_at": {
                                            "type": ["null", "string"],
                                            "format": "date-time",
                                        },
                                        "target_commitish": {"type": ["null", "string"]},
                                        "foo": {
                                            "oneOf": [
                                                {
                                                    "types": ["null", "object"],
                                                    "properties": {"bar": {"type": "string"}},
                                                },
                                                {
                                                    "type": ["null", "object"],
                                                    "properties": {"baz": {"type": "string"}},
                                                },
                                            ]
                                        },
                                    },
                                },
                                "supportedSyncModes": ["full_refresh", "incremental"],
                                "sourceDefinedCursor": True,
                                "defaultCursorField": ["created_at"],
                                "sourceDefinedPrimaryKey": [["id"]],
                            },
                            "config": {
                                "syncMode": "incremental",
                                "cursorField": ["created_at"],
                                "destinationSyncMode": "append_dedup",
                                "primaryKey": [["id"]],
                                "aliasName": "releases",
                                "selected": True,
                            },
                        },
                        {
                            "stream": {
                                "name": "tags",
                                "jsonSchema": {
                                    "type": "object",
                                    "$schema": "http://json-schema.org/draft-07/schema#",
                                    "properties": {
                                        "name": {"type": ["null", "string"]},
                                        "commit": {
                                            "type": ["null", "object"],
                                            "properties": {
                                                "sha": {"type": ["null", "string"]},
                                                "url": {"type": ["null", "string"]},
                                            },
                                        },
                                        "node_id": {"type": ["null", "string"]},
                                        "repository": {"type": ["string"]},
                                        "tarball_url": {"type": ["null", "string"]},
                                        "zipball_url": {"type": ["null", "string"]},
                                    },
                                },
                                "supportedSyncModes": ["full_refresh"],
                                "defaultCursorField": [],
                                "sourceDefinedPrimaryKey": [["repository"], ["name"]],
                            },
                            "config": {
                                "syncMode": "full_refresh",
                                "cursorField": [],
                                "destinationSyncMode": "append",
                                "primaryKey": [["repository"], ["name"]],
                                "aliasName": "tags",
                                "selected": True,
                            },
                        },
                        {
                            "stream": {
                                "name": "teams",
                                "jsonSchema": {
                                    "type": "object",
                                    "$schema": "http://json-schema.org/draft-07/schema#",
                                    "properties": {
                                        "id": {"type": ["null", "integer"]},
                                        "url": {"type": ["null", "string"]},
                                        "name": {"type": ["null", "string"]},
                                        "slug": {"type": ["null", "string"]},
                                        "parent": {
                                            "type": ["null", "object"],
                                            "properties": {},
                                            "additionalProperties": True,
                                        },
                                        "node_id": {"type": ["null", "string"]},
                                        "privacy": {"type": ["null", "string"]},
                                        "html_url": {"type": ["null", "string"]},
                                        "permission": {"type": ["null", "string"]},
                                        "repository": {"type": ["null", "string"]},
                                        "description": {"type": ["null", "string"]},
                                        "members_url": {"type": ["null", "string"]},
                                        "organization": {"type": ["null", "string"]},
                                        "repositories_url": {"type": ["null", "string"]},
                                    },
                                },
                                "supportedSyncModes": ["full_refresh"],
                                "defaultCursorField": [],
                                "sourceDefinedPrimaryKey": [["id"]],
                            },
                            "config": {
                                "syncMode": "full_refresh",
                                "cursorField": [],
                                "destinationSyncMode": "append",
                                "primaryKey": [["id"]],
                                "aliasName": "teams",
                                "selected": True,
                            },
                        },
                    ]
                },
                "scheduleType": "manual",
                "status": "active",
            },
        ]
    }


def get_instance_operations_json():
    return {
        "operations": [
            {
                "workspaceId": "b49ed3cd-7bb4-4f11-b8ba-95b4a5f7bc75",
                "operationId": "f39dbcd0-a6dc-4319-9ae4-28937997b48a",
                "name": "Normalization",
                "operatorConfiguration": {
                    "operatorType": "normalization",
                    "normalization": {"option": "basic"},
                },
            }
        ]
    }
