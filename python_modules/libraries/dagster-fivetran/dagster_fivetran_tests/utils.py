import base64

import responses
from dagster._utils.merger import deep_merge_dicts
from responses import matchers

DEFAULT_CONNECTOR_ID = "some_connector"
DEFAULT_CONNECTOR_ID_2 = "some_other_connector"


def get_sample_connector_response(**kwargs):
    return deep_merge_dicts(
        {
            "code": "Success",
            "data": {
                "id": DEFAULT_CONNECTOR_ID,
                "group_id": "some_group",
                "service": "some_service",
                "service_version": 1,
                "schema": "some_service.some_name",
                "connected_by": "some_user",
                "created_at": "2021-01-01T00:00:00.0Z",
                "succeeded_at": "2021-01-01T01:00:00.0Z",
                "failed_at": None,
                "paused": False,
                "pause_after_trial": False,
                "sync_frequency": 360,
                "schedule_type": "auto",
                "status": {
                    "setup_state": "connected",
                    "sync_state": "scheduled",
                    "update_state": "on_schedule",
                    "is_historical_sync": False,
                    "tasks": [],
                    "warnings": [],
                },
                "config": {
                    "auth_type": "OAuth",
                },
                "source_sync_details": {"last_synced": "2021-10-27T16:58:40.035Z"},
            },
        },
        kwargs,
    )


def get_sample_connector_schema_config(tables):
    schemas = {schema_name for schema_name, table_name in tables}

    return {
        "code": "Success",
        "data": {
            "enable_new_by_default": False,
            "schemas": {
                schema: {
                    "name_in_destination": schema,
                    "enabled": True,
                    "tables": {
                        t: {"name_in_destination": t, "enabled": True}
                        for s, t in tables
                        if s == schema
                    },
                }
                for schema in schemas
            },
        },
    }


# Set schema names if you want to reuse this on multiple connectors for the same fivetran service
# without getting duplicate asset keys.
def get_complex_sample_connector_schema_config(
    schema_name_1: str = "xyz1",
    schema_name_2: str = "abc",
    schema_name_3: str = "qwerty",
):
    return {
        "code": "Success",
        "data": {
            "enable_new_by_default": False,
            "schemas": {
                "schema_1": {
                    "name_in_destination": schema_name_1,
                    "enabled": True,
                    "tables": {
                        "table_1": {
                            "name_in_destination": "abc1",
                            "enabled": True,
                            "enabled_patch_settings": {"allowed": True},
                            "columns": {
                                "column_1": {
                                    "name_in_destination": "column_1",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason_code": "SYSTEM_COLUMN",
                                        "reason": (
                                            "The column does not support exclusion as it is a"
                                            " Primary Key"
                                        ),
                                    },
                                },
                                "column_2": {
                                    "name_in_destination": "column_2",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {"allowed": True},
                                },
                                "column_3": {
                                    "name_in_destination": "column_3",
                                    "enabled": True,
                                    "hashed": True,
                                    "enabled_patch_settings": {"allowed": True},
                                },
                            },
                        },
                        "table_2": {
                            "name_in_destination": "abc2",
                            "enabled": True,
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason_code": "SYSTEM_TABLE",
                            },
                        },
                    },
                },
                "schema_2": {
                    "name_in_destination": schema_name_2,
                    "enabled": True,
                    "tables": {
                        "table_1": {
                            "name_in_destination": "xyz",
                            "enabled": True,
                            "enabled_patch_settings": {"allowed": True},
                            "columns": {
                                "column_1": {"name_in_destination": "column_1", "enabled": False},
                            },
                        },
                        "table_2": {
                            "name_in_destination": "fed",
                            "enabled": False,
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason_code": "OTHER",
                                "reason": "Permission denied",
                            },
                        },
                    },
                },
                "schema_3": {
                    "name_in_destination": schema_name_3,
                    "enabled": False,
                    "tables": {
                        "table_1": {
                            "name_in_destination": "bar",
                            "enabled": True,
                            "enabled_patch_settings": {"allowed": True},
                            "columns": {
                                "name_in_destination": "column_1",
                                "column_1": {"enabled": False},
                            },
                        },
                        "table_2": {
                            "name_in_destination": "fed",
                            "enabled": True,
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason_code": "OTHER",
                                "reason": "Permission denied",
                            },
                        },
                    },
                },
            },
        },
    }


def get_sample_update_response():
    return {
        "code": "Success",
        "message": "Connector has been updated",
        "data": get_sample_connector_response()["data"],
    }


def get_sample_sync_response():
    return {
        "code": "Success",
        "message": "Sync has been successfully triggered for connector with id 'some_connector'",
    }


def get_sample_resync_response():
    return {"code": "Success", "message": "Re-sync has been triggered successfully"}


def get_sample_groups_response():
    return {
        "items": [
            {
                "id": "some_group",
            }
        ]
    }


def get_sample_connectors_response():
    return {
        "items": [
            {
                "id": DEFAULT_CONNECTOR_ID,
                "service": "some_service",
                "schema": "some_service.some_name",
            }
        ]
    }


def get_sample_connectors_response_multiple():
    return {
        "items": [
            {
                "id": DEFAULT_CONNECTOR_ID,
                "service": "some_service",
                "schema": "some_service.some_name",
            },
            {
                "id": DEFAULT_CONNECTOR_ID_2,
                "service": "some_other_service",
                "schema": "some_other_service.some_name",
                "status": {
                    "setup_state": "connected",
                },
            },
            {
                "id": "FAKE",
                "service": "some_fake_service",
                "schema": "some_fake_service.some_name",
                "status": {
                    "setup_state": "broken",
                },
            },
        ]
    }


def get_sample_destination_details_response():
    return {
        "data": {
            "service": "snowflake",
            "config": {"database": "example_database"},
        }
    }


def get_sample_columns_response():
    return {
        "columns": {
            "column_1": {
                "name_in_destination": "column_1",
                "enabled": True,
                "hashed": False,
                "enabled_patch_settings": {
                    "allowed": False,
                    "reason_code": "SYSTEM_COLUMN",
                    "reason": ("The column does not support exclusion as it is a Primary Key"),
                },
            },
            "column_2": {
                "name_in_destination": "column_2_renamed",
                "enabled": True,
                "hashed": False,
                "enabled_patch_settings": {"allowed": True},
            },
            "column_3": {
                "name_in_destination": "column_3",
                "enabled": True,
                "hashed": True,
                "enabled_patch_settings": {"allowed": True},
            },
        },
    }


def mock_responses(ft_resource, multiple_connectors=False):
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
