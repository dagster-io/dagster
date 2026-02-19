import dagster as dg
from dagster._annotations import preview, public
from pydantic import Field

from dagster_azure.blob.resources import (
    AzureBlobStorageAnonymousCredential,
    AzureBlobStorageDefaultCredential,
    AzureBlobStorageKeyCredential,
    AzureBlobStorageResource,
    AzureBlobStorageSASTokenCredential,
)


@public
@preview
class AzureBlobStorageResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """Component for Azure Blob Storage Resource.

    Wraps AzureBlobStorageResource for use in YAML-based configuration.

    Example usage in YAML:

    .. code-block:: YAML

        resources:
          - name: blob_storage
            type: dagster_azure.AzureBlobStorageResourceComponent
            attributes:
              account_url: "https://myaccount.blob.core.windows.net"
              credential:
                credential_type: key
                key: "{{ env.AZURE_STORAGE_ACCOUNT_KEY }}"
              resource_key: blob_storage
    """

    account_url: str = Field(description="The URL to the blob storage account")

    credential: (
        AzureBlobStorageSASTokenCredential
        | AzureBlobStorageKeyCredential
        | AzureBlobStorageDefaultCredential
        | AzureBlobStorageAnonymousCredential
    ) = Field(description="Azure credential configuration")

    resource_key: str | None = Field(
        default=None, description="Resource key for binding to definitions"
    )

    @property
    def resource(self) -> AzureBlobStorageResource:
        return AzureBlobStorageResource(
            account_url=self.account_url,
            credential=self.credential,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
