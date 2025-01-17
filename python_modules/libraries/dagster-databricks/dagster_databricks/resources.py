from typing import Any, Optional

from dagster import Config, ConfigurableResource, IAttachDifferentObjectToOpContext, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from pydantic import Field, model_validator

from dagster_databricks.databricks import DatabricksClient


class OauthCredentials(Config):
    """OAuth credentials for Databricks.

    See https://docs.databricks.com/dev-tools/api/latest/authentication.html#oauth-2-0.
    """

    client_id: str = Field(description="OAuth client ID")
    client_secret: str = Field(description="OAuth client secret")


class AzureServicePrincipalCredentials(Config):
    """Azure service principal credentials for Azure Databricks.

    See https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth#--azure-service-principal-authentication.
    """

    azure_client_id: str = Field(description="The client ID of the Azure service principal")
    azure_client_secret: str = Field(description="The client secret of the Azure service principal")
    azure_tenant_id: str = Field(description="The tenant ID of the Azure service principal")


class DatabricksClientResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    """Resource which provides a Python client for interacting with Databricks within an
    op or asset.
    """

    host: Optional[str] = Field(
        description="Databricks host, e.g. https://uksouth.azuredatabricks.com", default=None
    )
    token: Optional[str] = Field(default=None, description="Databricks access token")
    oauth_credentials: Optional[OauthCredentials] = Field(
        default=None,
        description=(
            "Databricks OAuth credentials for using a service principal. See"
            " https://docs.databricks.com/en/dev-tools/auth.html#oauth-2-0"
        ),
    )
    azure_credentials: Optional[AzureServicePrincipalCredentials] = Field(
        default=None,
        description=(
            "Azure service principal credentials. See"
            " https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth#requirements-for-oauth-u2m-authentication-setup"
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

    @model_validator(mode="before")
    def has_token_or_oauth_credentials(cls, values: dict[str, Any]) -> dict[str, Any]:
        token = values.get("token")
        oauth_credentials = values.get("oauth_credentials")
        azure_credentials = values.get("azure_credentials")
        present = [True for v in [token, oauth_credentials, azure_credentials] if v is not None]
        if len(present) > 1:
            raise ValueError(
                "Must provide one of token or oauth_credentials or azure_credentials, not multiple"
            )
        elif not len(present):
            raise ValueError("Must provide one of token or oauth_credentials or azure_credentials")
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
            azure_client_id = self.azure_credentials.azure_client_id
            azure_client_secret = self.azure_credentials.azure_client_secret
            azure_tenant_id = self.azure_credentials.azure_tenant_id
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
            azure_tenant_id=azure_tenant_id,
        )

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(config_schema=DatabricksClientResource.to_config_schema())
def databricks_client(init_context) -> DatabricksClient:
    return DatabricksClientResource.from_resource_context(init_context).get_client()
