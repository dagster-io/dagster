from collections.abc import Mapping, Sequence
from functools import cached_property
from typing import Any, Optional

from dagster_fivetran.asset_defs import (
    AssetSpec,
    ConnectorSelectorFn,
    DagsterFivetranTranslator,
)
from dagster_fivetran.components.workspace_component.component import (
    FivetranWorkspaceComponent,
)
from dagster_fivetran.resources import (
    FivetranClient,
    FivetranConnector,
    FivetranWorkspace,
    load_fivetran_asset_specs,
)
from dagster_fivetran.translator import (
    FivetranDestination,
    FivetranSchema,
    FivetranSchemaConfig,
    FivetranTable,
    FivetranWorkspaceData,
)
from dagster_fivetran.types import FivetranOutput

from dagster._utils.cached_method import cached_method

TEST_MAX_TIME_STR = "2024-12-01T15:45:29.013729Z"
TEST_PREVIOUS_MAX_TIME_STR = "2024-12-01T15:43:29.013729Z"


def get_sample_connection_details(
    succeeded_at: str, failed_at: str, paused: bool = False
) -> Mapping[str, Any]:
    return {
        "code": "Success",
        "message": "Operation performed.",
        "data": {
            "id": "promotion_secretory",
            "service": "15five",
            "schema": "schema.table",
            "paused": paused,
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
            "group_id": "snowflake_group",
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


class MockFivetranClient:
    def sync_and_poll(self, connector_id: str) -> FivetranOutput:
        return FivetranOutput(
            connector_details=get_sample_connection_details(
                succeeded_at=TEST_MAX_TIME_STR, failed_at=TEST_PREVIOUS_MAX_TIME_STR
            )["data"],
            schema_config={
                "enable_new_by_default": True,
                "schema_change_handling": "ALLOW_ALL",
                "schemas": {
                    "salesforce": {
                        "name_in_destination": "salesforce",
                        "enabled": True,
                        "tables": {
                            "campaign": {
                                "sync_mode": "SOFT_DELETE",
                                "name_in_destination": "campaign",
                                "enabled": True,
                            },
                            "opportunity": {
                                "sync_mode": "SOFT_DELETE",
                                "name_in_destination": "opportunity",
                                "enabled": True,
                            },
                            "task": {
                                "sync_mode": "SOFT_DELETE",
                                "name_in_destination": "task",
                                "enabled": True,
                            },
                            "user": {
                                "sync_mode": "SOFT_DELETE",
                                "name_in_destination": "user",
                                "enabled": True,
                            },
                        },
                    }
                },
            },
        )


class MockFivetranWorkspace(FivetranWorkspace):
    @cached_method
    def load_asset_specs(
        self,
        dagster_fivetran_translator: Optional[DagsterFivetranTranslator] = None,
        connector_selector_fn: Optional[ConnectorSelectorFn] = None,
    ) -> Sequence[AssetSpec]:
        return load_fivetran_asset_specs(
            workspace=self,
            dagster_fivetran_translator=dagster_fivetran_translator
            or DagsterFivetranTranslator(),
            connector_selector_fn=connector_selector_fn,
        )

    @cached_method
    def get_client(self):
        return MockFivetranClient()

    @cached_method
    def fetch_fivetran_workspace_data(
        self,
    ) -> FivetranWorkspaceData:
        return FivetranWorkspaceData(
            connectors_by_id={
                "promotion_secretory": FivetranConnector(
                    id="promotion_secretory",
                    name="salesforce_warehouse_sync",
                    service="snowflake",
                    group_id="snowflake_group",
                    setup_state="test_setup_state",
                    sync_state="test_sync_state",
                    paused=False,
                    succeeded_at=None,
                    failed_at=None,
                ),
                "456": FivetranConnector(
                    id="456",
                    name="hubspot_warehouse_sync",
                    service="snowflake",
                    group_id="snowflake_group",
                    setup_state="test_setup_state",
                    sync_state="test_sync_state",
                    paused=False,
                    succeeded_at=None,
                    failed_at=None,
                ),
            },
            destinations_by_id={
                "snowflake_group": FivetranDestination(
                    id="snowflake_group",
                    database="test_database",
                    service="snowflake",
                )
            },
            schema_configs_by_connector_id={
                "promotion_secretory": FivetranSchemaConfig(
                    schemas={
                        "salesforce": FivetranSchema(
                            enabled=True,
                            name_in_destination="salesforce",
                            tables={
                                "user": FivetranTable(
                                    enabled=True,
                                    name_in_destination="user",
                                    columns=None,
                                ),
                                "task": FivetranTable(
                                    enabled=True,
                                    name_in_destination="task",
                                    columns=None,
                                ),
                                "opportunity": FivetranTable(
                                    enabled=True,
                                    name_in_destination="opportunity",
                                    columns=None,
                                ),
                                "campaign": FivetranTable(
                                    enabled=True,
                                    name_in_destination="campaign",
                                    columns=None,
                                ),
                            },
                        )
                    }
                ),
                "456": FivetranSchemaConfig(
                    schemas={
                        "hubspot": FivetranSchema(
                            enabled=True,
                            name_in_destination="hubspot",
                            tables={
                                "contact": FivetranTable(
                                    enabled=True,
                                    name_in_destination="contact",
                                    columns=None,
                                ),
                                "company": FivetranTable(
                                    enabled=True,
                                    name_in_destination="company",
                                    columns=None,
                                ),
                            },
                        )
                    }
                ),
            },
        )


class MockFivetranComponent(FivetranWorkspaceComponent):
    @cached_property
    def workspace_resource(self) -> MockFivetranWorkspace:
        return MockFivetranWorkspace(**self.workspace.model_dump())
