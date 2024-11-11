from typing import Iterator

import pytest
import responses
from dagster_fivetran.resources import (
    FIVETRAN_API_BASE,
    FIVETRAN_API_VERSION,
    FIVETRAN_CONNECTOR_ENDPOINT,
)

# Taken from Fivetran API documentation
# https://fivetran.com/docs/rest-api/api-reference/groups/list-all-groups
SAMPLE_GROUPS = {
    "code": "Success",
    "message": "Operation performed.",
    "data": {
        "items": [{"id": "group_id", "name": "Group_Name", "created_at": "2024-01-01T00:00:00Z"}],
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
                "succeeded_at": "2024-12-01T15:43:29.013729Z",
                "sync_frequency": 360,
                "group_id": "group_id",
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
                "created_at": "2024-12-01T15:43:29.013729Z",
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
        "id": "destination_id",
        "service": "adls",
        "region": "GCP_US_EAST4",
        "networking_method": "Directly",
        "setup_status": "CONNECTED",
        "daylight_saving_time_enabled": True,
        "group_id": "group_id",
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
SAMPLE_CONNECTOR_DETAILS = {
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
        "succeeded_at": "2024-03-17T12:31:40.870504Z",
        "sync_frequency": 1440,
        "group_id": "group_id",
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
        "created_at": "2023-12-01T15:43:29.013729Z",
        "failed_at": "2024-04-01T18:13:25.043659Z",
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
        "connect_card_config": {"redirect_uri": "https://your.site/path", "hide_setup_guide": True},
        "hybrid_deployment_agent_id": "hybrid_deployment_agent_id",
        "config": {"api_key": "your_15five_api_key"},
    },
}


@pytest.fixture(name="connector_id")
def connector_id_fixture() -> str:
    return "connector_id"


@pytest.fixture(name="destination_id")
def destination_id_fixture() -> str:
    return "destination_id"


@pytest.fixture(name="group_id")
def group_id_fixture() -> str:
    return "group_id"


@pytest.fixture(
    name="workspace_data_api_mocks",
)
def workspace_data_api_mocks_fixture(
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
            url=f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}/{FIVETRAN_CONNECTOR_ENDPOINT}/{connector_id}",
            json=SAMPLE_CONNECTOR_DETAILS,
            status=200,
        )

        yield response
