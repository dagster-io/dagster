import threading
from typing import Any

from dagster import Config, ConfigurableResource, IAttachDifferentObjectToOpContext, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from databricks.sdk.core import CredentialsStrategy
from pydantic import Field, PrivateAttr, model_validator

from dagster_databricks.databricks import DatabricksClient

# Thread-local used to smuggle credentials_strategy into model_post_init.
# CredentialsStrategy is not a Dagster-serializable config type and cannot be a Pydantic
# field on ConfigurableResource. __init__ stores it here before calling super().__init__()
# so that model_post_init (which fires during Pydantic construction) can inspect it for
# the no-credentials check. The thread-local is cleaned up before __init__ returns.
_init_local = threading.local()


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
      a serializable config type, it is accepted as a constructor argument rather than
      a Dagster config field.
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

    # CredentialsStrategy is not a Dagster-serializable config type, so it cannot be
    # declared as a Pydantic Field on a ConfigurableResource. It is accepted via __init__
    # and stored as a private attribute, invisible to Dagster's config schema machinery.
    _credentials_strategy: CredentialsStrategy | None = PrivateAttr(default=None)

    def __init__(
        self,
        credentials_strategy: CredentialsStrategy | None = None,
        **kwargs,
    ):
        # Stash credentials_strategy in a thread-local before calling super().__init__(),
        # so that model_post_init can inspect it during Pydantic construction.
        _init_local.credentials_strategy = credentials_strategy
        try:
            super().__init__(**kwargs)
        finally:
            del _init_local.credentials_strategy
        # Write into __pydantic_private__ directly rather than using object.__setattr__.
        # object.__setattr__ would place the value in __dict__, shadowing the PrivateAttr
        # entry in __pydantic_private__ and causing model_copy() to silently produce a
        # copy with _credentials_strategy=None.
        if self.__pydantic_private__ is not None:
            self.__pydantic_private__["_credentials_strategy"] = credentials_strategy

    @model_validator(mode="before")
    def validate_no_multiple_serializable_credentials(
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        token = values.get("token")
        oauth_credentials = values.get("oauth_credentials")
        azure_credentials = values.get("azure_credentials")
        present = [True for v in [token, oauth_credentials, azure_credentials] if v is not None]
        if len(present) > 1:
            raise ValueError(
                "Must provide one of token, oauth_credentials, or azure_credentials, not multiple"
            )
        # Zero serializable credentials is intentionally allowed here — credentials_strategy
        # may be supplied via the constructor. The model_post_init below enforces that at
        # least one auth method is present once all paths are visible.
        return values

    def model_post_init(self, __context: Any) -> None:
        credentials_strategy = getattr(_init_local, "credentials_strategy", None)
        has_serializable = (
            self.token is not None
            or self.oauth_credentials is not None
            or self.azure_credentials is not None
        )
        if credentials_strategy is not None and has_serializable:
            raise ValueError(
                "Cannot combine credentials_strategy with token, oauth_credentials, or azure_credentials"
            )
        if not (has_serializable or credentials_strategy is not None):
            raise ValueError(
                "Must provide one of token, oauth_credentials, azure_credentials, or"
                " credentials_strategy"
            )
        super().model_post_init(__context)

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
            credentials_strategy=self._credentials_strategy,
        )

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(config_schema=DatabricksClientResource.to_config_schema())
def databricks_client(init_context) -> DatabricksClient:
    return DatabricksClientResource.from_resource_context(init_context).get_client()
