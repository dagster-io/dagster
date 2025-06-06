from collections.abc import Sequence
from functools import cached_property
from typing import Optional

from dagster_airbyte import AirbyteCloudWorkspace
from dagster_airbyte.components.workspace_component.component import (
    AirbyteCloudWorkspaceComponent,
)
from dagster_airbyte.translator import (
    AirbyteConnection,
    AirbyteDestination,
    AirbyteStream,
    AirbyteWorkspaceData,
)

from dagster._utils.cached_method import cached_method


class MockAirbyteWorkspace(AirbyteCloudWorkspace):
    @cached_method
    def fetch_airbyte_workspace_data(
        self,
    ) -> AirbyteWorkspaceData:
        """Retrieves all Airbyte content from the workspace and returns it as a AirbyteWorkspaceData object.

        Returns:
            AirbyteWorkspaceData: A snapshot of the Airbyte workspace's content.
        """
        # connections_by_id = {}
        # destinations_by_id = {}

        # client = self.get_client()
        # connections = client.get_connections()["data"]

        # for partial_connection_details in connections:
        #     full_connection_details = client.get_connection_details(
        #         connection_id=partial_connection_details["connectionId"]
        #     )
        #     connection = AirbyteConnection.from_connection_details(
        #         connection_details=full_connection_details
        #     )
        #     connections_by_id[connection.id] = connection

        #     destination_details = client.get_destination_details(
        #         destination_id=connection.destination_id
        #     )
        #     destination = AirbyteDestination.from_destination_details(
        #         destination_details=destination_details
        #     )
        #     destinations_by_id[destination.id] = destination

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


class MockAirbyteComponent(AirbyteCloudWorkspaceComponent):
    @cached_property
    def workspace_resource(self) -> MockAirbyteWorkspace:
        return MockAirbyteWorkspace(**self.workspace.model_dump())