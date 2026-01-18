from unittest.mock import MagicMock, patch

from dagster import asset, materialize_to_memory
from dagster_azure.blob import (
    AzureBlobStorageAnonymousCredential,
    AzureBlobStorageDefaultCredential,
    AzureBlobStorageKeyCredential,
    AzureBlobStorageResource,
    AzureBlobStorageSASTokenCredential,
)

ACCOUNT_URL = "https://example-account.blob.core.windows.net"
SAS_TOKEN = "example-sas-token"
SHARED_KEY = "example-shared-key"


@patch("dagster_azure.blob.resources.BlobServiceClient")
def test_resource_sas_credential(mock_blob_service_client):
    @asset
    def az_asset(azure_blob_resource: AzureBlobStorageResource):
        with azure_blob_resource.get_client():
            mock_blob_service_client.assert_called_once_with(
                account_url=ACCOUNT_URL, credential=SAS_TOKEN
            )

    result = materialize_to_memory(
        [az_asset],
        resources={
            "azure_blob_resource": AzureBlobStorageResource(
                account_url=ACCOUNT_URL,
                credential=AzureBlobStorageSASTokenCredential(token=SAS_TOKEN),
            )
        },
    )

    assert result.success


@patch("dagster_azure.blob.resources.BlobServiceClient")
def test_resource_shared_key_credential(mock_blob_service_client):
    @asset
    def az_asset(azure_blob_resource: AzureBlobStorageResource):
        with azure_blob_resource.get_client():
            mock_blob_service_client.assert_called_once_with(
                account_url=ACCOUNT_URL, credential=SHARED_KEY
            )

    result = materialize_to_memory(
        [az_asset],
        resources={
            "azure_blob_resource": AzureBlobStorageResource(
                account_url=ACCOUNT_URL, credential=AzureBlobStorageKeyCredential(key=SHARED_KEY)
            )
        },
    )

    assert result.success


@patch("dagster_azure.blob.resources.BlobServiceClient")
@patch("dagster_azure.blob.resources.DefaultAzureCredential")
def test_resource_default_credential(mock_default_credential_method, mock_blob_service_client):
    mock_default_credential = MagicMock()
    mock_default_credential_method.return_value = mock_default_credential

    @asset
    def az_asset(azure_blob_resource: AzureBlobStorageResource):
        with azure_blob_resource.get_client():
            mock_blob_service_client.assert_called_once_with(
                account_url=ACCOUNT_URL, credential=mock_default_credential
            )

    result = materialize_to_memory(
        [az_asset],
        resources={
            "azure_blob_resource": AzureBlobStorageResource(
                account_url=ACCOUNT_URL, credential=AzureBlobStorageDefaultCredential()
            )
        },
    )

    assert result.success


@patch("dagster_azure.blob.resources.BlobServiceClient")
def test_resource_anonymous_credential(mock_blob_service_client):
    @asset
    def az_asset(azure_blob_resource: AzureBlobStorageResource):
        with azure_blob_resource.get_client():
            mock_blob_service_client.assert_called_once_with(
                account_url=ACCOUNT_URL, credential=None
            )

    result = materialize_to_memory(
        [az_asset],
        resources={
            "azure_blob_resource": AzureBlobStorageResource(
                account_url=ACCOUNT_URL, credential=AzureBlobStorageAnonymousCredential()
            )
        },
    )

    assert result.success
