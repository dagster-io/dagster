from typing import Any, Literal, Union

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


def _resolve(val: str):
    if isinstance(val, str) and val.startswith("{{ env.") and val.endswith(" }}"):
        return dg.EnvVar(val[7:-3].strip())
    return val


class SASCredentialModel(Model):
    credential_type: Literal["sas"]
    sas_token: str


class KeyCredentialModel(Model):
    credential_type: Literal["key"]
    key: str


class DefaultCredentialModel(Model):
    credential_type: Literal["default_azure_credential"]
    kwargs: dict = {}


class AnonymousCredentialModel(Model):
    credential_type: Literal["anonymous"]


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
    account_url: str = Field(description="The URL to the blob storage account.")

    credential: Union[
        SASCredentialModel,
        KeyCredentialModel,
        DefaultCredentialModel,
        AnonymousCredentialModel,
    ] = Field(description="The credential used to authenticate.")

    resource_key: str = Field(
        default="blob_storage", description="Resource key for binding to definitions."
    )

    def build_resource(self, context: ComponentLoadContext) -> AzureBlobStorageResource:
        cred: Any = AzureBlobStorageDefaultCredential()

        if self.credential.credential_type == "sas":
            cred = AzureBlobStorageSASTokenCredential(token=_resolve(self.credential.sas_token))
        elif self.credential.credential_type == "key":
            cred = AzureBlobStorageKeyCredential(key=_resolve(self.credential.key))
        elif self.credential.credential_type == "default_azure_credential":
            cred = AzureBlobStorageDefaultCredential(kwargs=self.credential.kwargs)
        elif self.credential.credential_type == "anonymous":
            cred = AzureBlobStorageAnonymousCredential()

        return AzureBlobStorageResource(
            account_url=_resolve(self.account_url),
            credential=cred,
        )

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions(resources={self.resource_key: self.build_resource(context)})
