from typing import TYPE_CHECKING, Optional

from dagster import ConfigurableResource
from obstore.store import AzureStore
from pydantic import Field

if TYPE_CHECKING:
    from obstore.store import AzureConfig, RetryConfig


class AzureServicePrincipal(ConfigurableResource):
    client_id: str = Field("Client ID of Azure Service principal.")
    client_secret: str = Field("Client secret of Azure Service principal.")
    tenant_id: str = Field("Tenant ID of the service principal.")


class AzureObjectStore(ConfigurableResource):
    storage_account: str = Field(
        description="Storage account to use when creating the Azure Store."
    )
    access_key: Optional[str] = Field(
        description="Storage access key to use when creating the Azure Store."
    )
    service_principal: Optional[AzureServicePrincipal] = Field(
        default=None,
        description="Service principal credentials to use when creating the Azure store.",
    )
    sas_token: Optional[str] = Field(
        default=None,
        description="Path of service account key to authenticate, for the Azure Store.",
    )
    use_azure_cli: bool = Field(
        default=False, description="Whether to use Azure CLI to authenticate to Azure."
    )
    allow_http: bool = Field(
        default=False, description="Whether to allow http connections. By default, https is used."
    )
    allow_invalid_certificates: bool = Field(
        default=False,
        description="Whether to allow invalid certificates. By default, valid certs are required.",
    )

    def create_store(
        self, container: str, timeout: str = "60s", retry_config: Optional["RetryConfig"] = None
    ) -> AzureStore:
        """Creates an Azure object store."""
        config: AzureConfig = {}
        if self.access_key:
            config["access_key"] = self.access_key

        if self.service_principal:
            config["client_id"] = self.service_principal.client_id
            config["client_secret"] = self.service_principal.client_secret
            config["tenant_id"] = self.service_principal.tenant_id

        if self.sas_token:
            config["sas_token"] = self.sas_token

        if self.use_azure_cli:
            config["use_azure_cli"] = self.use_azure_cli

        return AzureStore.from_env(
            container=container,
            config=config,
            client_options={
                "timeout": timeout,
                "allow_http": self.allow_http,
                "allow_invalid_certificates": self.allow_invalid_certificates,
            },
            retry_config=retry_config,
        )
