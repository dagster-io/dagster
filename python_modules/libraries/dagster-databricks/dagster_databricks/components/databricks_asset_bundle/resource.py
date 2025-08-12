from dagster import ConfigurableResource
from dagster_shared.utils import cached_method
from databricks.sdk import WorkspaceClient
from pydantic import Field


class DatabricksWorkspace(ConfigurableResource):
    """Represents a workspace in Databricks and provides utilities
    to interact with the Databricks SDK.
    """

    host: str = Field(description="The host used to connect to the Databricks Workspace.")
    token: str = Field(description="The token used to connect to Databricks Workspace.")

    @cached_method
    def get_client(self) -> WorkspaceClient:
        return WorkspaceClient(
            host=self.host,
            token=self.token,
        )
