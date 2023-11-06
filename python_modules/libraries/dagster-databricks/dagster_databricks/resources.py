from typing import Any, Optional

from dagster import (
    Config,
    ConfigurableResource,
    IAttachDifferentObjectToOpContext,
    resource,
)
from dagster._config.pythonic_config.pydantic_compat_layer import compat_model_validator
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from pydantic import Field

from .databricks import DatabricksClient


class OauthCredentials(Config):
    """OAuth credentials for Databricks.

    See https://docs.databricks.com/dev-tools/api/latest/authentication.html#oauth-2-0.
    """

    client_id: str = Field(description="OAuth client ID")
    client_secret: str = Field(description="OAuth client secret")


class AzureSpCredentials(Config):
    """Azure service principal credentials for Databricks."""

    azure_tenant_id: str = Field(description="Azure tenant ID")
    azure_client_id: str = Field(description="Azure service principal client ID")
    azure_client_secret: str = Field(description="Azure service principal client secret")


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
    azure_sp_credentials: Optional[AzureSpCredentials] = Field(
        default=None,
        description="Databricks azure service principal credentials for using a service principal.",
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description=(
            "DEPRECATED: The Databricks workspace ID, as described in"
            " https://docs.databricks.com/workspace/workspace-details.html#workspace-instance-names-urls-and-ids."
            " This is no longer used and will be removed in a 0.21."
        ),
    )

    @compat_model_validator(mode="before")
    def has_auth_credentials(cls, values):
        token = values.get("token")
        oauth_credentials = values.get("oauth_credentials")
        azure_sp_credentials = values.get("azure_sp_credentials")
        if (
            len(
                [
                    auth_type
                    for auth_type in [token, oauth_credentials, azure_sp_credentials]
                    if auth_type is not None
                ]
            )
            != 1
        ):
            raise ValueError(
                "Must provide either databricks_token, oauth_credentials or azure_sp_credentials,"
                " but cannot provide multiple of them"
            )
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
        if self.azure_sp_credentials:
            azure_tenant_id = self.azure_sp_credentials.azure_tenant_id
            azure_client_id = self.azure_sp_credentials.azure_client_id
            azure_client_secret = self.azure_sp_credentials.azure_client_secret
        else:
            azure_tenant_id = None
            azure_client_id = None
            azure_client_secret = None

        return DatabricksClient(
            host=self.host,
            token=self.token,
            oauth_client_id=client_id,
            oauth_client_secret=client_secret,
            azure_tenant_id=azure_tenant_id,
            azure_client_id=azure_client_id,
            azure_client_secret=azure_client_secret,
            workspace_id=self.workspace_id,
        )

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(config_schema=DatabricksClientResource.to_config_schema())
def databricks_client(init_context) -> DatabricksClient:
    return DatabricksClientResource.from_resource_context(init_context).get_client()
