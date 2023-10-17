from typing import Any, Optional

from dagster import (
    Config,
    ConfigurableResource,
    IAttachDifferentObjectToOpContext,
    resource,
)
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from pydantic import Field, root_validator

from .databricks import DatabricksClient


class OauthCredentials(Config):
    """OAuth credentials for Databricks.

    See https://docs.databricks.com/dev-tools/api/latest/authentication.html#oauth-2-0.
    """

    client_id: str = Field(description="OAuth client ID")
    client_secret: str = Field(description="OAuth client secret")


class DatabricksClientResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    """Resource which provides a Python client for interacting with Databricks within an
    op or asset.
    """

    host: str = Field(description="Databricks host, e.g. https://uksouth.azuredatabricks.com")
    token: Optional[str] = Field(default=None, description="Databricks access token")
    oauth_credentials: Optional[OauthCredentials] = Field(
        default=None,
        description=(
            "Databricks OAuth credentials for using a service principal. See"
            " https://docs.databricks.com/en/dev-tools/auth.html#oauth-2-0"
        ),
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description=(
            "DEPRECATED: The Databricks workspace ID, as described in"
            " https://docs.databricks.com/workspace/workspace-details.html#workspace-instance-names-urls-and-ids."
            " This is no longer used and will be removed in a 0.21."
        ),
    )

    @root_validator()
    def has_token_or_oauth_credentials(cls, values):
        token = values.get("token")
        oauth_credentials = values.get("oauth_credentials")
        if not token and not oauth_credentials:
            raise ValueError("Must provide either token or oauth_credentials")
        if token and oauth_credentials:
            raise ValueError("Must provide either token or oauth_credentials, not both")
        return values

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> DatabricksClient:
        if self.oauth_credentials:
            client_id = self.oauth_credentials.client_id
            client_secret = self.oauth_credentials.client_secret
        else:
            client_id = None
            client_secret = None

        return DatabricksClient(
            host=self.host,
            token=self.token,
            oauth_client_id=client_id,
            oauth_client_secret=client_secret,
            workspace_id=self.workspace_id,
        )

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(config_schema=DatabricksClientResource.to_config_schema())
def databricks_client(init_context) -> DatabricksClient:
    return DatabricksClientResource.from_resource_context(init_context).get_client()
