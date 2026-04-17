from typing import Any

from dagster import Config, ConfigurableResource, IAttachDifferentObjectToOpContext, resource
from dagster._config.pythonic_config.resource import ResourceDependency
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from databricks.sdk.core import CredentialsStrategy
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

    Supports four mutually exclusive authentication methods:

    - **PAT**: Provide ``token``.
    - **OAuth M2M**: Provide ``oauth_credentials`` (client ID + secret).
    - **Azure service principal**: Provide ``azure_credentials``.
    - **Custom CredentialsStrategy**: Pass a ``credentials_strategy`` instance to the
      constructor. This supports any authentication flow backed by the Databricks SDK's
      ``CredentialsStrategy`` protocol, including OIDC federation, external IdP token
      exchange, and other custom auth flows. Because ``CredentialsStrategy`` is not
      a serializable config type, it is accepted as a constructor argument and stored
      outside of Dagster's config schema machinery.

    Examples:

    .. code-block:: python

        from dagster import job
        from dagster_databricks import DatabricksClientResource
        from my_auth import MyCredentialsStrategy

        @job(
            resource_defs={
                "databricks": DatabricksClientResource(
                    host="https://my-workspace.cloud.databricks.com",
                    credentials_strategy=MyCredentialsStrategy(),
                )
            }
        )
        def my_job():
            ...
    """

    host: str | None = Field(
        description="Databricks host, e.g. https://uksouth.azuredatabricks.com", default=None
    )
    token: str | None = Field(default=None, description="Databricks access token")
    oauth_credentials: OauthCredentials | None = Field(
        default=None,
        description=(
            "Databricks OAuth credentials for using a service principal. See"
            " https://docs.databricks.com/en/dev-tools/auth.html#oauth-2-0"
        ),
    )
    azure_credentials: AzureServicePrincipalCredentials | None = Field(
        default=None,
        description=(
            "Azure service principal credentials. See"
            " https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth#requirements-for-oauth-u2m-authentication-setup"
        ),
    )
    workspace_id: str | None = Field(
        default=None,
        description=(
            "DEPRECATED: The Databricks workspace ID, as described in"
            " https://docs.databricks.com/workspace/workspace-details.html#workspace-instance-names-urls-and-ids."
            " This is no longer used and will be removed in a 0.21."
        ),
    )
    credentials_strategy: ResourceDependency[CredentialsStrategy | None] = None

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
        # Zero serializable credentials is allowed here — credentials_strategy may be
        # supplied via the constructor. Enforcement of at least one auth method is done
        # in get_client() where credentials_strategy is visible.
        return values

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> DatabricksClient:
        credentials_strategy: CredentialsStrategy | None = self.credentials_strategy

        has_serializable_credentials = (
            self.token is not None
            or self.oauth_credentials is not None
            or self.azure_credentials is not None
        )

        if has_serializable_credentials and credentials_strategy is not None:
            raise ValueError(
                "Can only provide one of token, oauth_credentials, azure_credentials, or"
                " credentials_strategy, not multiple"
            )

        if not has_serializable_credentials and credentials_strategy is None:
            raise ValueError(
                "Must provide one of token, oauth_credentials, azure_credentials, or"
                " credentials_strategy"
            )

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
            credentials_strategy=credentials_strategy,
        )

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(config_schema=DatabricksClientResource.to_config_schema())
def databricks_client(init_context) -> DatabricksClient:
    with DatabricksClientResource.from_resource_context_cm(init_context) as resource:
        return resource.get_client()
