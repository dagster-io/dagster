from unittest import mock

from dagster_azure.adls2 import ADLS2Resource, ADLS2SASToken
from dagster_azure.adls2.utils import (
    _create_url as adls2_create_url,
    create_adls2_client,
)
from dagster_azure.blob.utils import (
    _create_url as blob_create_url,
    create_blob_client,
)


class TestCreateUrl:
    def test_default_suffix(self):
        assert adls2_create_url("myaccount", "dfs") == "https://myaccount.dfs.core.windows.net/"

    def test_custom_suffix(self):
        assert (
            adls2_create_url("myaccount", "dfs", "core.usgovcloudapi.net")
            == "https://myaccount.dfs.core.usgovcloudapi.net/"
        )

    def test_blob_default_suffix(self):
        assert blob_create_url("myaccount", "blob") == "https://myaccount.blob.core.windows.net/"

    def test_blob_custom_suffix(self):
        assert (
            blob_create_url("myaccount", "blob", "core.usgovcloudapi.net")
            == "https://myaccount.blob.core.usgovcloudapi.net/"
        )


class TestCreateAdls2Client:
    @mock.patch("dagster_azure.adls2.utils.DataLakeServiceClient")
    def test_default_endpoint(self, mock_client):
        create_adls2_client("myaccount", "fake-cred")
        mock_client.assert_called_once_with("https://myaccount.dfs.core.windows.net/", "fake-cred")

    @mock.patch("dagster_azure.adls2.utils.DataLakeServiceClient")
    def test_govcloud_endpoint(self, mock_client):
        create_adls2_client("myaccount", "fake-cred", endpoint_suffix="core.usgovcloudapi.net")
        mock_client.assert_called_once_with(
            "https://myaccount.dfs.core.usgovcloudapi.net/", "fake-cred"
        )


class TestCreateBlobClient:
    @mock.patch("dagster_azure.blob.utils.BlobServiceClient")
    def test_default_endpoint(self, mock_client):
        create_blob_client("myaccount", "fake-cred")
        mock_client.assert_called_once_with("https://myaccount.blob.core.windows.net/", "fake-cred")

    @mock.patch("dagster_azure.blob.utils.BlobServiceClient")
    def test_govcloud_endpoint(self, mock_client):
        create_blob_client("myaccount", "fake-cred", endpoint_suffix="core.usgovcloudapi.net")
        mock_client.assert_called_once_with(
            "https://myaccount.blob.core.usgovcloudapi.net/", "fake-cred"
        )


class TestADLS2ResourceEndpointSuffix:
    @mock.patch("dagster_azure.adls2.resources.create_adls2_client")
    def test_default_suffix(self, mock_create):
        resource = ADLS2Resource(
            storage_account="myaccount",
            credential=ADLS2SASToken(token="fake-token"),
        )
        _ = resource.adls2_client
        mock_create.assert_called_once_with("myaccount", "fake-token", "core.windows.net")

    @mock.patch("dagster_azure.adls2.resources.create_adls2_client")
    def test_govcloud_suffix(self, mock_create):
        resource = ADLS2Resource(
            storage_account="myaccount",
            credential=ADLS2SASToken(token="fake-token"),
            endpoint_suffix="core.usgovcloudapi.net",
        )
        _ = resource.adls2_client
        mock_create.assert_called_once_with("myaccount", "fake-token", "core.usgovcloudapi.net")

    @mock.patch("dagster_azure.adls2.resources.create_blob_client")
    def test_blob_client_uses_suffix(self, mock_create):
        resource = ADLS2Resource(
            storage_account="myaccount",
            credential=ADLS2SASToken(token="fake-token"),
            endpoint_suffix="core.usgovcloudapi.net",
        )
        _ = resource.blob_client
        mock_create.assert_called_once_with("myaccount", "fake-token", "core.usgovcloudapi.net")
