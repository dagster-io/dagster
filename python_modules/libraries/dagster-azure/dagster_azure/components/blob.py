"""Azure Blob Storage Resource Component for dagster-dg."""

from typing import Optional, Union

import dagster as dg
from dagster.components import Component, Model
from dagster._annotations import public, preview
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
class AzureBlobStorageResourceComponent(Component, dg.Resolvable, Model):
    """Component for Azure Blob Storage Resource.

    Wraps AzureBlobStorageResource for use in YAML-based configuration.

    Example usage in YAML:

    .. code-block:: YAML

        resources:
          - name: blob_storage
            type: dagster_azure.AzureBlobStorageResourceComponent
            attributes:
              account_url: ${AZURE_STORAGE_ACCOUNT_URL}
              credential:
                credential_type: key
                key: ${AZURE_STORAGE_ACCOUNT_KEY}
              resource_key: blob_storage
    """

    account_url: str = Field(
        description=(
            "The URL to the blob storage account. Any other entities included"
            " in the URL path (e.g. container or blob) will be discarded. This URL can be optionally"
            " authenticated with a SAS token."
        ),
    )

    credential: Union[
        AzureBlobStorageKeyCredential,
        AzureBlobStorageSASTokenCredential,
        AzureBlobStorageDefaultCredential,
        AzureBlobStorageAnonymousCredential,
    ] = Field(
        discriminator="credential_type",
        description=(
            "The credential used to authenticate to the storage account. One of:"
            " AzureBlobStorageSASTokenCredential,"
            " AzureBlobStorageKeyCredential,"
            " AzureBlobStorageDefaultCredential,"
            " AzureBlobStorageAnonymousCredential"
        ),
    )

    resource_key: Optional[str] = Field(
        default=None, description="Resource key for binding to definitions."
    )

    @property
    def resource(self) -> AzureBlobStorageResource:
        """Return the underlying AzureBlobStorageResource."""
        return AzureBlobStorageResource(
            account_url=self.account_url,
            credential=self.credential,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
