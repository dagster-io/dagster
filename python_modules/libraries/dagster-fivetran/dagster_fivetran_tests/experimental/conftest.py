from collections.abc import Iterator, Mapping
from typing import Any
from unittest.mock import patch

import pytest
import responses
from dagster_fivetran.resources import (
    FIVETRAN_API_BASE,
    FIVETRAN_API_VERSION,
    FIVETRAN_CONNECTOR_ENDPOINT,
)
from dagster_fivetran.types import FivetranOutput

TEST_MAX_TIME_STR = "2024-12-01T15:45:29.013729Z"
TEST_PREVIOUS_MAX_TIME_STR = "2024-12-01T15:43:29.013729Z"

TEST_ACCOUNT_ID = "test_account_id"
TEST_API_KEY = "test_api_key"
TEST_API_SECRET = "test_api_secret"
TEST_ANOTHER_ACCOUNT_ID = "test_another_account_id"

TEST_SCHEMA_NAME = "schema_name_in_destination_1"
TEST_TABLE_NAME = "table_name_in_destination_1"
TEST_SECOND_SCHEMA_NAME = "schema_name_in_destination_2"
TEST_SECOND_TABLE_NAME = "table_name_in_destination_2"
TEST_ANOTHER_TABLE_NAME = "another_table_name_in_destination_1"

# Taken from Fivetran API documentation
# https://fivetran.com/docs/rest-api/api-reference/groups/list-all-groups
SAMPLE_GROUPS = {
    "code": "Success",
    "message": "Operation performed.",
    "data": {
        "items": [
            {
                "id": "my_group_destination_id",
                "name": "Group_Name",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ],
        "nextCursor": "cursor_value",
    },
}

# Taken from Fivetran API documentation
# https://fivetran.com/docs/rest-api/api-reference/groups/list-all-connectors-in-group
SAMPLE_CONNECTORS_FOR_GROUP = {
    "code": "Success",
    "message": "Operation performed.",
    "data": {
        "items": [
            {
                "id": "connector_id",
                "service": "adls",
                "schema": "gsheets.table",
                "paused": False,
                "status": {
                    "tasks": [
                        {
                            "code": "resync_table_warning",
                            "message": "Resync Table Warning",
                            "details": "string",
                        }
                    ],
                    "warnings": [
                        {
                            "code": "resync_table_warning",
                            "message": "Resync Table Warning",
                            "details": "string",
                        }
                    ],
                    "schema_status": "ready",
                    "update_state": "delayed",
                    "setup_state": "connected",
                    "sync_state": "scheduled",
                    "is_historical_sync": False,
                    "rescheduled_for": "2024-12-01T15:43:29.013729Z",
                },
                "config": {"property1": {}, "property2": {}},
                "daily_sync_time": "14:00",
                "succeeded_at": "2024-12-01T15:45:29.013729Z",
                "sync_frequency": 360,
                "group_id": "my_group_destination_id",
                "connected_by": "user_id",
                "setup_tests": [
                    {
                        "title": "Test Title",
                        "status": "PASSED",
                        "message": "Test Passed",
                        "details": "Test Details",
                    }
                ],
                "source_sync_details": {},
                "service_version": 0,
                "created_at": "2024-12-01T15:41:29.013729Z",
                "failed_at": "2024-12-01T15:43:29.013729Z",
                "private_link_id": "string",
                "proxy_agent_id": "string",
                "networking_method": "Directly",
                "connect_card": {
                    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkIjp7ImxvZ2luIjp0cnVlLCJ1c2VyIjoiX2FjY291bnR3b3J0aHkiLCJhY2NvdW50IjoiX21vb25iZWFtX2FjYyIsImdyb3VwIjoiX21vb25iZWFtIiwiY29ubmVjdG9yIjoiY29iYWx0X2VsZXZhdGlvbiIsIm1ldGhvZCI6IlBiZkNhcmQiLCJpZGVudGl0eSI6ZmFsc2V9LCJpYXQiOjE2Njc4MzA2MzZ9.YUMGUbzxW96xsKJLo4bTorqzx8Q19GTrUi3WFRFM8BU",
                    "uri": "https://fivetran.com/connect-card/setup?auth=eyJ0eXAiOiJKV1QiLCJh...",
                },
                "pause_after_trial": False,
                "data_delay_threshold": 0,
                "data_delay_sensitivity": "LOW",
                "schedule_type": "auto",
                "local_processing_agent_id": "string",
                "connect_card_config": {
                    "redirect_uri": "https://your.site/path",
                    "hide_setup_guide": True,
                },
                "hybrid_deployment_agent_id": "string",
            }
        ],
        "nextCursor": "cursor_value",
    },
}

# Taken from Fivetran API documentation
# https://fivetran.com/docs/rest-api/api-reference/destinations/destination-details
SAMPLE_DESTINATION_DETAILS = {
    "code": "Success",
    "message": "Operation performed.",
    "data": {
        "id": "my_group_destination_id",
        "service": "adls",
        "region": "GCP_US_EAST4",
        "networking_method": "Directly",
        "setup_status": "CONNECTED",
        "daylight_saving_time_enabled": True,
        "group_id": "my_group_destination_id",
        "time_zone_offset": "+3",
        "setup_tests": [
            {
                "title": "Test Title",
                "status": "PASSED",
                "message": "Test Passed",
                "details": "Test Details",
            }
        ],
        "local_processing_agent_id": "local_processing_agent_id",
        "private_link_id": "private_link_id",
        "hybrid_deployment_agent_id": "hybrid_deployment_agent_id",
        "config": {
            "tenant_id": "service_principal_tenant_id",
            "auth_type": "PERSONAL_ACCESS_TOKEN | OAUTH2",
            "storage_account_name": "adls_storage_account_name",
            "connection_type": "Directly | PrivateLink | SshTunnel | ProxyAgent",
            "catalog": "string",
            "should_maintain_tables_in_databricks": True,
            "http_path": "string",
            "oauth2_secret": "string",
            "snapshot_retention_period": "RETAIN_ALL_SNAPSHOTS | ONE_WEEK | TWO_WEEKS | FOUR_WEEKS | SIX_WEEKS",
            "server_host_name": "string",
            "client_id": "service_principal_client_id",
            "prefix_path": "adls_container_path_prefix",
            "container_name": "adls_container_name",
            "port": 0,
            "databricks_connection_type": "Directly | PrivateLink | SshTunnel | ProxyAgent",
            "secret_value": "service_principal_secret_value",
            "oauth2_client_id": "string",
            "personal_access_token": "string",
        },
    },
}


# Taken from Fivetran API documentation
# https://fivetran.com/docs/rest-api/api-reference/connectors/connector-details
# The sample is parameterized to test the poll method
def get_sample_connection_details(succeeded_at: str, failed_at: str) -> Mapping[str, Any]:
    return {
        "code": "Success",
        "message": "Operation performed.",
        "data": {
            "id": "connector_id",
            "service": "15five",
            "schema": "schema.table",
            "paused": False,
            "status": {
                "tasks": [
                    {
                        "code": "resync_table_warning",
                        "message": "Resync Table Warning",
                        "details": "string",
                    }
                ],
                "warnings": [
                    {
                        "code": "resync_table_warning",
                        "message": "Resync Table Warning",
                        "details": "string",
                    }
                ],
                "schema_status": "ready",
                "update_state": "delayed",
                "setup_state": "connected",
                "sync_state": "scheduled",
                "is_historical_sync": False,
                "rescheduled_for": "2024-12-01T15:43:29.013729Z",
            },
            "daily_sync_time": "14:00",
            "succeeded_at": succeeded_at,
            "sync_frequency": 1440,
            "group_id": "my_group_destination_id",
            "connected_by": "user_id",
            "setup_tests": [
                {
                    "title": "Test Title",
                    "status": "PASSED",
                    "message": "Test Passed",
                    "details": "Test Details",
                }
            ],
            "source_sync_details": {},
            "service_version": 0,
            "created_at": "2024-12-01T15:41:29.013729Z",
            "failed_at": failed_at,
            "private_link_id": "private_link_id",
            "proxy_agent_id": "proxy_agent_id",
            "networking_method": "Directly",
            "connect_card": {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkIjp7ImxvZ2luIjp0cnVlLCJ1c2VyIjoiX2FjY291bnR3b3J0aHkiLCJhY2NvdW50IjoiX21vb25iZWFtX2FjYyIsImdyb3VwIjoiX21vb25iZWFtIiwiY29ubmVjdG9yIjoiY29iYWx0X2VsZXZhdGlvbiIsIm1ldGhvZCI6IlBiZkNhcmQiLCJpZGVudGl0eSI6ZmFsc2V9LCJpYXQiOjE2Njc4MzA2MzZ9.YUMGUbzxW96xsKJLo4bTorqzx8Q19GTrUi3WFRFM8BU",
                "uri": "https://fivetran.com/connect-card/setup?auth=eyJ0eXAiOiJKV1QiLCJh...",
            },
            "pause_after_trial": False,
            "data_delay_threshold": 0,
            "data_delay_sensitivity": "NORMAL",
            "schedule_type": "auto",
            "local_processing_agent_id": "local_processing_agent_id",
            "connect_card_config": {
                "redirect_uri": "https://your.site/path",
                "hide_setup_guide": True,
            },
            "hybrid_deployment_agent_id": "hybrid_deployment_agent_id",
            "config": {"api_key": "your_15five_api_key"},
        },
    }


# Taken from Fivetran API documentation
# https://fivetran.com/docs/rest-api/api-reference/connector-schema/connector-schema-config
# The sample is parameterized to test the sync and poll materialization method
def get_sample_schema_config_for_connector(table_name: str) -> Mapping[str, Any]:
    return {
        "code": "Success",
        "message": "Operation performed.",
        "data": {
            "enable_new_by_default": True,
            "schemas": {
                "property1": {
                    "name_in_destination": "schema_name_in_destination_1",
                    "enabled": True,
                    "tables": {
                        "property1": {
                            "sync_mode": "SOFT_DELETE",
                            "name_in_destination": table_name,
                            "enabled": True,
                            "columns": {
                                "property1": {
                                    "name_in_destination": "column_name_in_destination_1",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason": "...",
                                        "reason_code": "SYSTEM_COLUMN",
                                    },
                                    "is_primary_key": True,
                                },
                                "property2": {
                                    "name_in_destination": "column_name_in_destination_2",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason": "...",
                                        "reason_code": "SYSTEM_COLUMN",
                                    },
                                    "is_primary_key": True,
                                },
                            },
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason": "...",
                                "reason_code": "SYSTEM_TABLE",
                            },
                            "supports_columns_config": True,
                        },
                        "property2": {
                            "sync_mode": "SOFT_DELETE",
                            "name_in_destination": "table_name_in_destination_2",
                            "enabled": True,
                            "columns": {
                                "property1": {
                                    "name_in_destination": "column_name_in_destination_1",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason": "...",
                                        "reason_code": "SYSTEM_COLUMN",
                                    },
                                    "is_primary_key": True,
                                },
                                "property2": {
                                    "name_in_destination": "column_name_in_destination_2",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason": "...",
                                        "reason_code": "SYSTEM_COLUMN",
                                    },
                                    "is_primary_key": True,
                                },
                            },
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason": "...",
                                "reason_code": "SYSTEM_TABLE",
                            },
                            "supports_columns_config": True,
                        },
                    },
                },
                "property2": {
                    "name_in_destination": "schema_name_in_destination_2",
                    "enabled": True,
                    "tables": {
                        "property1": {
                            "sync_mode": "SOFT_DELETE",
                            "name_in_destination": "table_name_in_destination_1",
                            "enabled": True,
                            "columns": {
                                "property1": {
                                    "name_in_destination": "column_name_in_destination_1",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason": "...",
                                        "reason_code": "SYSTEM_COLUMN",
                                    },
                                    "is_primary_key": True,
                                },
                                "property2": {
                                    "name_in_destination": "column_name_in_destination_2",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason": "...",
                                        "reason_code": "SYSTEM_COLUMN",
                                    },
                                    "is_primary_key": True,
                                },
                            },
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason": "...",
                                "reason_code": "SYSTEM_TABLE",
                            },
                            "supports_columns_config": True,
                        },
                        "property2": {
                            "sync_mode": "SOFT_DELETE",
                            "name_in_destination": "table_name_in_destination_2",
                            "enabled": True,
                            "columns": {
                                "property1": {
                                    "name_in_destination": "column_name_in_destination_1",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason": "...",
                                        "reason_code": "SYSTEM_COLUMN",
                                    },
                                    "is_primary_key": True,
                                },
                                "property2": {
                                    "name_in_destination": "column_name_in_destination_2",
                                    "enabled": True,
                                    "hashed": False,
                                    "enabled_patch_settings": {
                                        "allowed": False,
                                        "reason": "...",
                                        "reason_code": "SYSTEM_COLUMN",
                                    },
                                    "is_primary_key": True,
                                },
                            },
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason": "...",
                                "reason_code": "SYSTEM_TABLE",
                            },
                            "supports_columns_config": True,
                        },
                    },
                },
            },
            "schema_change_handling": "ALLOW_ALL",
        },
    }


SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR = get_sample_schema_config_for_connector(
    table_name=TEST_TABLE_NAME
)

# We change the name of the original example to test the sync and poll materialization method
ALTERED_SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR = get_sample_schema_config_for_connector(
    table_name=TEST_ANOTHER_TABLE_NAME
)

SAMPLE_SUCCESS_MESSAGE = {"code": "Success", "message": "Operation performed."}

SAMPLE_SOURCE_TABLE_COLUMNS_CONFIG = {
    "code": "Success",
    "message": "Operation performed.",
    "data": {
        "columns": {
            "property1": {
                "name_in_destination": "column_name_in_destination_1",
                "enabled": True,
                "hashed": False,
                "enabled_patch_settings": {
                    "allowed": False,
                    "reason": "...",
                    "reason_code": "SYSTEM_COLUMN",
                },
                "is_primary_key": True,
            },
            "property2": {
                "name_in_destination": "column_name_in_destination_2",
                "enabled": True,
                "hashed": False,
                "enabled_patch_settings": {
                    "allowed": False,
                    "reason": "...",
                    "reason_code": "SYSTEM_COLUMN",
                },
                "is_primary_key": True,
            },
        }
    },
}


def get_fivetran_connector_api_url(connector_id: str) -> str:
    return (
        f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}/{FIVETRAN_CONNECTOR_ENDPOINT}/{connector_id}"
    )


@pytest.fixture(name="connector_id")
def connector_id_fixture() -> str:
    return "connector_id"


@pytest.fixture(name="destination_id")
def destination_id_fixture() -> str:
    return "my_group_destination_id"


@pytest.fixture(name="group_id")
def group_id_fixture() -> str:
    return "my_group_destination_id"


@pytest.fixture(
    name="fetch_workspace_data_api_mocks",
)
def fetch_workspace_data_api_mocks_fixture(
    connector_id: str, destination_id: str, group_id: str
) -> Iterator[responses.RequestsMock]:
    with responses.RequestsMock() as response:
        response.add(
            method=responses.GET,
            url=f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}/groups",
            json=SAMPLE_GROUPS,
            status=200,
        )

        response.add(
            method=responses.GET,
            url=f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}/groups/{group_id}/connectors",
            json=SAMPLE_CONNECTORS_FOR_GROUP,
            status=200,
        )

        response.add(
            method=responses.GET,
            url=f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}/destinations/{destination_id}",
            json=SAMPLE_DESTINATION_DETAILS,
            status=200,
        )

        response.add(
            method=responses.GET,
            url=f"{get_fivetran_connector_api_url(connector_id)}/schemas",
            json=SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR,
            status=200,
        )

        yield response


@pytest.fixture(
    name="all_api_mocks",
)
def all_api_mocks_fixture(
    connector_id: str,
    destination_id: str,
    group_id: str,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> Iterator[responses.RequestsMock]:
    test_connector_api_url = get_fivetran_connector_api_url(connector_id)
    fetch_workspace_data_api_mocks.add(
        method=responses.GET,
        url=test_connector_api_url,
        json=get_sample_connection_details(
            succeeded_at=TEST_MAX_TIME_STR, failed_at=TEST_PREVIOUS_MAX_TIME_STR
        ),
        status=200,
    )
    fetch_workspace_data_api_mocks.add(
        method=responses.PATCH,
        url=test_connector_api_url,
        json=get_sample_connection_details(
            succeeded_at=TEST_MAX_TIME_STR, failed_at=TEST_PREVIOUS_MAX_TIME_STR
        ),
        status=200,
    )
    fetch_workspace_data_api_mocks.add(
        method=responses.POST,
        url=f"{test_connector_api_url}/force",
        json=SAMPLE_SUCCESS_MESSAGE,
        status=200,
    )
    fetch_workspace_data_api_mocks.add(
        method=responses.POST,
        url=f"{test_connector_api_url}/resync",
        json=SAMPLE_SUCCESS_MESSAGE,
        status=200,
    )
    fetch_workspace_data_api_mocks.add(
        method=responses.POST,
        url=f"{test_connector_api_url}/schemas/tables/resync",
        json=SAMPLE_SUCCESS_MESSAGE,
        status=200,
    )
    fetch_workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{test_connector_api_url}/schemas/{TEST_SCHEMA_NAME}/tables/{TEST_TABLE_NAME}/columns",
        json=SAMPLE_SOURCE_TABLE_COLUMNS_CONFIG,
        status=200,
    )
    yield fetch_workspace_data_api_mocks


@pytest.fixture(name="sync_and_poll")
def sync_and_poll_fixture():
    with patch("dagster_fivetran.resources.FivetranClient.sync_and_poll") as mocked_function:
        # Fivetran output where all sync'd tables match the workspace data that was used to create the assets def
        expected_fivetran_output = FivetranOutput(
            connector_details=get_sample_connection_details(
                succeeded_at=TEST_MAX_TIME_STR, failed_at=TEST_PREVIOUS_MAX_TIME_STR
            )["data"],
            schema_config=SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR["data"],
        )
        # Fivetran output where a table is missing and an unexpected table is sync'd,
        # compared to the workspace data that was used to create the assets def
        unexpected_fivetran_output = FivetranOutput(
            connector_details=get_sample_connection_details(
                succeeded_at=TEST_MAX_TIME_STR, failed_at=TEST_PREVIOUS_MAX_TIME_STR
            )["data"],
            schema_config=ALTERED_SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR["data"],
        )
        mocked_function.side_effect = [expected_fivetran_output, unexpected_fivetran_output]
        yield mocked_function
