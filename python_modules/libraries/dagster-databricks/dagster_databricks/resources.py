from enum import Enum
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


class ClientType(Enum):
    """OAuth client type.

    See https://docs.databricks.com/dev-tools/api/latest/authentication.html#oauth-2-0.
    """

    PUBLIC = "PUBLIC"
    CONFIDENTIAL = "CONFIDENTIAL"


class OauthCredentials(Config):
    """OAuth credentials for Databricks.

    See https://docs.databricks.com/dev-tools/api/latest/authentication.html#oauth-2-0.
    """

    client_id: str = Field(description="OAuth client ID")
    client_secret: str = Field(description="OAuth client secret")


class AzureOauthCredentials(Config):
    """OAuth credentials for Azure Databricks.

    See https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth#--azure-service-principal-authentication.
    """

    arm_client_id: str = Field(description="The client ID of the Azure service principal")
    arm_client_secret: str = Field(description="The client secret of the Azure service principal")
    arm_tenant_id: str = Field(description="The tenant ID of the Azure service principal")


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
    azure_credentials: Optional[AzureOauthCredentials] = Field(default=None, description="Azure service principal. See See See https://docs.databricks.com/dev-tools/api/latest/authentication.html#oauth-2-0")
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
        azure_credentials = values.get("azure_oauth_credentials")
        if not any([token, oauth_credentials, azure_credentials]):
            raise ValueError("Must provide either token or oauth_credentials or azure_oauth_credentials")
        if all([token, oauth_credentials, azure_credentials]):
            raise ValueError("Must provide one of token or oauth_credentials or azure_oauth_credentials, not all")

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

        if self.azure_credentials:
            azure_client_id = self.azure_credentials.arm_client_id
            azure_client_secret = self.azure_credentials.arm_client_secret
            azure_tenant_id = self.azure_credentials.arm_tenant_id
        else:
            azure_client_id = None
            azure_client_secret = None
            azure_tenant_id = None

        return DatabricksClient(
            host=self.host,
            token=self.token,
            oauth_client_id=client_id,
            oauth_client_secret=client_secret,
            workspace_id=self.workspace_id,
            azure_client_id=azure_client_id,
            azure_client_secret=azure_client_secret,
            azure_tenant_id=azure_tenant_id
        )

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(config_schema=DatabricksClientResource.to_config_schema())
def databricks_client(init_context) -> DatabricksClient:
    return DatabricksClientResource.from_resource_context(init_context).get_client()
