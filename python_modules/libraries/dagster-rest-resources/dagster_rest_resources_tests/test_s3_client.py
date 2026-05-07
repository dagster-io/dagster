import io
from unittest.mock import Mock, patch

import pytest
from dagster_rest_resources.s3_client import S3Client

_HTTPX_CLIENT_PATCH = "dagster_rest_resources.s3_client.httpx.Client"

_BASE_URL = "https://dagster.cloud/api"
_HEADERS = {"Dagster-Cloud-Api-Token": "test-token"}


class TestUpload:
    @patch(_HTTPX_CLIENT_PATCH)
    def test_upload(self, MockClient):
        mock_http = MockClient.return_value.__enter__.return_value
        presigned_url_response = Mock()
        presigned_url_response.json.return_value = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {"key": "uploads/test-key"},
        }
        upload_response = Mock()
        mock_http.post.side_effect = [presigned_url_response, upload_response]
        f = io.BytesIO(b"test content")

        S3Client(base_url=_BASE_URL, headers=_HEADERS).upload("test-key", None, f)

        mock_http.post.assert_any_call(
            url=f"{_BASE_URL}/gen_artifact_post",
            headers=_HEADERS,
            json={"key": "test-key"},
        )
        mock_http.post.assert_called_with(
            "https://s3.amazonaws.com/bucket",
            data={"key": "uploads/test-key"},
            files={"file": f},
        )
        presigned_url_response.raise_for_status.assert_called_once()
        upload_response.raise_for_status.assert_called_once()

    @patch(_HTTPX_CLIENT_PATCH)
    def test_with_deployment(self, MockClient):
        mock_http = MockClient.return_value.__enter__.return_value
        presigned_url_response = Mock()
        presigned_url_response.json.return_value = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {},
        }
        mock_http.post.side_effect = [presigned_url_response, Mock()]

        S3Client(base_url=_BASE_URL, headers=_HEADERS).upload(
            "test-key", "prod", io.BytesIO(b"test content")
        )

        mock_http.post.assert_any_call(
            url=f"{_BASE_URL}/gen_artifact_post",
            headers={**_HEADERS, "Dagster-Cloud-Deployment": "prod"},
            json={"key": "test-key"},
        )

    @patch(_HTTPX_CLIENT_PATCH)
    def test_presigned_url_failure_raises(self, MockClient):
        mock_http = MockClient.return_value.__enter__.return_value
        mock_http.post.return_value.raise_for_status.side_effect = Exception("403 Forbidden")

        with pytest.raises(Exception, match="403 Forbidden"):
            S3Client(base_url=_BASE_URL, headers=_HEADERS).upload("test-key", None, io.BytesIO(b""))

    @patch(_HTTPX_CLIENT_PATCH)
    def test_upload_failure_raises(self, MockClient):
        mock_http = MockClient.return_value.__enter__.return_value
        presigned_url_response = Mock()
        presigned_url_response.json.return_value = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {},
        }
        upload_response = Mock()
        upload_response.raise_for_status.side_effect = Exception("403 Forbidden")
        mock_http.post.side_effect = [presigned_url_response, upload_response]

        with pytest.raises(Exception, match="403 Forbidden"):
            S3Client(base_url=_BASE_URL, headers=_HEADERS).upload("test-key", None, io.BytesIO(b""))


class TestDownload:
    @patch(_HTTPX_CLIENT_PATCH)
    def test_download(self, MockClient):
        mock_http = MockClient.return_value.__enter__.return_value
        presigned_url_response = Mock()
        presigned_url_response.json.return_value = {
            "url": "https://s3.amazonaws.com/bucket/test-key"
        }
        mock_http.post.return_value = presigned_url_response
        download_response = Mock()
        download_response.content = b"test content"
        mock_http.get.return_value = download_response

        result = S3Client(base_url=_BASE_URL, headers=_HEADERS).download("test-key", None)

        assert result == b"test content"
        mock_http.post.assert_called_once_with(
            url=f"{_BASE_URL}/gen_artifact_get",
            headers=_HEADERS,
            json={"key": "test-key"},
        )
        mock_http.get.assert_called_once_with(url="https://s3.amazonaws.com/bucket/test-key")
        download_response.raise_for_status.assert_called_once()

    @patch(_HTTPX_CLIENT_PATCH)
    def test_with_deployment(self, MockClient):
        mock_http = MockClient.return_value.__enter__.return_value
        presigned_url_response = Mock()
        presigned_url_response.json.return_value = {
            "url": "https://s3.amazonaws.com/bucket/test-key"
        }
        mock_http.post.return_value = presigned_url_response

        S3Client(base_url=_BASE_URL, headers=_HEADERS).download("test-key", "prod")

        mock_http.post.assert_called_once_with(
            url=f"{_BASE_URL}/gen_artifact_get",
            headers={**_HEADERS, "Dagster-Cloud-Deployment": "prod"},
            json={"key": "test-key"},
        )

    @patch(_HTTPX_CLIENT_PATCH)
    def test_presigned_url_failure_raises(self, MockClient):
        mock_http = MockClient.return_value.__enter__.return_value
        mock_http.post.return_value.raise_for_status.side_effect = Exception("403 Forbidden")

        with pytest.raises(Exception, match="403 Forbidden"):
            S3Client(base_url=_BASE_URL, headers=_HEADERS).download("test-key", None)

    @patch(_HTTPX_CLIENT_PATCH)
    def test_download_failure_raises(self, MockClient):
        mock_http = MockClient.return_value.__enter__.return_value
        presigned_url_response = Mock()
        presigned_url_response.json.return_value = {
            "url": "https://s3.amazonaws.com/bucket/test-key"
        }
        mock_http.post.return_value = presigned_url_response
        download_response = Mock()
        download_response.raise_for_status.side_effect = Exception("403 Forbidden")
        mock_http.get.return_value = download_response

        with pytest.raises(Exception, match="403 Forbidden"):
            S3Client(base_url=_BASE_URL, headers=_HEADERS).download("test-key", None)
