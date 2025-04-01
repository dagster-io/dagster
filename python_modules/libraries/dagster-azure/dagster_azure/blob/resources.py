from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Literal, Union

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dagster import Config, ConfigurableResource
from pydantic import Field


class AzureBlobStorageSASTokenCredential(Config):
    """Authentication using an azure SAS token."""

    credential_type: Literal["sas"] = "sas"

    token: str
    "an azure SAS token"


class AzureBlobStorageKeyCredential(Config):
    """Authentication using an azure shared-key."""

    credential_type: Literal["key"] = "key"
    key: str
    "an azure shared-key"


class AzureBlobStorageDefaultCredential(Config):
    """Authenticate using azure.identity.DefaultAzureCredential."""

    credential_type: Literal["default_azure_credential"] = "default_azure_credential"

    kwargs: dict[str, Any] = {}
    "additional arguments to be passed to azure.identity.DefaultAzureCredential."
    ' e.g. AzureBlobStorageDefaultCredential(kwargs={"exclude_environment_credential": True})'


class AzureBlobStorageAnonymousCredential(Config):
    """For anonymous access to azure blob storage."""

    credential_type: Literal["anonymous"] = "anonymous"


class AzureBlobStorageResource(ConfigurableResource):
    """Resource for interacting with Azure Blob Storage.

    Examples:
        .. code-block:: python

            import os
            from dagster import Definitions, asset, EnvVar
            from dagster_azure.blob import (
                AzureBlobStorageResource,
                AzureBlobStorageKeyCredential,
                AzureBlobStorageDefaultCredential
            )

            @asset
            def my_table(azure_blob_storage: AzureBlobStorageResource):
                with azure_blob_storage.get_client() as blob_storage_client:
                    response = blob_storage_client.list_containers()

            defs = Definitions(
                assets=[my_table],
                resources={
                    "azure_blob_storage": AzureBlobStorageResource(
                        account_url=EnvVar("AZURE_BLOB_STORAGE_ACCOUNT_URL"),
                        credential=AzureBlobStorageDefaultCredential() if os.getenv("DEV") else
                            AzureBlobStorageKeyCredential(key=EnvVar("AZURE_BLOB_STORAGE_KEY"))
                    ),
                },
            )

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

    @classmethod
    def _is_dagster_maintained(cls):
        return True

    def _raw_credential(self) -> Any:
        if self.credential.credential_type == "sas":
            return self.credential.token
        if self.credential.credential_type == "key":
            return self.credential.key
        if self.credential.credential_type == "default_azure_credential":
            return DefaultAzureCredential(**self.credential.kwargs)
        if self.credential.credential_type == "anonymous":
            return None
        raise Exception(
            "Invalid credential type - use one of AzureBlobStorageKeyCredential, "
            " AzureBlobStorageSASTokenCredential, AzureBlobStorageDefaultCredential,"
            " AzureBlobStorageAnonymousCredential"
        )

    @contextmanager
    def get_client(self) -> Generator[BlobServiceClient, None, None]:
        service = BlobServiceClient(account_url=self.account_url, credential=self._raw_credential())

        try:
            yield service
        finally:
            service.close()
