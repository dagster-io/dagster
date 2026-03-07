from collections.abc import Sequence
from functools import cached_property

from dagster_fivetran.asset_defs import (
    AssetSpec,
    ConnectorSelectorFn,
    DagsterFivetranTranslator,
)
from dagster_fivetran.components.workspace_component.component import (
    FivetranAccountComponent,
)
from dagster_fivetran.resources import FivetranConnector, FivetranWorkspace
from dagster_fivetran.translator import (
    FivetranDestination,
    FivetranSchema,
    FivetranSchemaConfig,
    FivetranTable,
    FivetranWorkspaceData,
)

from dagster._utils.cached_method import cached_method


class MockFivetranWorkspace(FivetranWorkspace):
    @cached_method
    def fetch_fivetran_workspace_data(
        self,
    ) -> FivetranWorkspaceData:
        return FivetranWorkspaceData(
            connectors_by_id={
                "123": FivetranConnector(
                    id="123",
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
                "123": FivetranSchemaConfig(
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


class MockFivetranComponent(FivetranAccountComponent):
    @cached_property
    def workspace_resource(self) -> MockFivetranWorkspace:
        return MockFivetranWorkspace(**self.workspace.model_dump())
