from typing import Annotated

from dagster_airbyte import AirbyteCloudWorkspace
from dagster_airbyte.components.workspace_component.component import (
    AirbyteWorkspaceComponent,
)
from dagster_airbyte.translator import (
    AirbyteConnection,
    AirbyteDestination,
    AirbyteStream,
    AirbyteWorkspaceData,
)

import dagster as dg
from dagster._utils.cached_method import cached_method
from dagster.components.resolved.base import resolve_fields


class MockAirbyteWorkspace(AirbyteCloudWorkspace):
    @cached_method
    def fetch_airbyte_workspace_data(
        self,
    ) -> AirbyteWorkspaceData:
        """Retrieves all Airbyte content from the workspace and returns it as a AirbyteWorkspaceData object.

        Returns:
            AirbyteWorkspaceData: A snapshot of the Airbyte workspace's content.
        """
        return AirbyteWorkspaceData(
            connections_by_id={
                "my_salesforce_connection": AirbyteConnection(
                    id="my_salesforce_connection",
                    name="salesforce_to_snowflake",
                    streams={
                        name: AirbyteStream(
                            name=name,
                            selected=True,
                            json_schema={
                                "type": "object",
                                "$schema": "http://json-schema.org/draft-07/schema#",
                                "properties": {},
                            },
                        )
                        for name in {"user", "task", "opportunity", "account"}
                    },
                    destination_id="snowflake",
                    stream_prefix=None,
                ),
                "my_hubspot_connection": AirbyteConnection(
                    id="my_hubspot_connection",
                    name="Hubspot to Snowflake",
                    streams={
                        name: AirbyteStream(
                            name=name,
                            selected=True,
                            json_schema={
                                "type": "object",
                                "$schema": "http://json-schema.org/draft-07/schema#",
                                "properties": {},
                            },
                        )
                        for name in {"contact", "company"}
                    },
                    destination_id="snowflake",
                    stream_prefix=None,
                ),
            },
            destinations_by_id={
                "snowflake": AirbyteDestination(
                    id="snowflake", type="snowflake", database="snowflake", schema=None
                )
            },
        )


class MockAirbyteComponent(AirbyteWorkspaceComponent):
    workspace: Annotated[
        MockAirbyteWorkspace,
        dg.Resolver(
            lambda context, model: MockAirbyteWorkspace(
                **resolve_fields(model, MockAirbyteWorkspace, context)
            )
        ),
    ]
