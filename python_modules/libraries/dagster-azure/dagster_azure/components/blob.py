from typing import Optional, Union, cast

import dagster as dg
from dagster._annotations import preview, public
from dagster.components import Component, ComponentLoadContext, Model
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

    account_url: Optional[str] = Field(
        default=None, description="The URL to the blob storage account"
    )

    credential: Optional[
        Union[
            AzureBlobStorageSASTokenCredential,
            AzureBlobStorageKeyCredential,
            AzureBlobStorageDefaultCredential,
            AzureBlobStorageAnonymousCredential,
        ]
    ] = Field(default=None, description="Azure credential configuration")

    resource_key: Optional[str] = Field(
        default=None, description="Resource key for binding to definitions"
    )

    @property
    def resource(self) -> AzureBlobStorageResource:
        return AzureBlobStorageResource(
            account_url=cast("str", self.account_url),
            credential=self.credential or AzureBlobStorageDefaultCredential(),
        )

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
