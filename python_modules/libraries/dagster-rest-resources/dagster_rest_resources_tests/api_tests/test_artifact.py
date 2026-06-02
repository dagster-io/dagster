from pathlib import Path
from unittest.mock import Mock

import pytest
from dagster_rest_resources.api.artifact import DgApiArtifactApi
from dagster_rest_resources.s3_client import S3Client
from dagster_rest_resources.schemas.artifact import (
    DgApiArtifactDownloadResult,
    DgApiArtifactUploadResult,
)
from dagster_rest_resources.schemas.exception import S3Error


class TestActionUpload:
    def test_upload(self, tmp_path: Path):
        upload_file = tmp_path / "test-file.bin"
        upload_file.write_bytes(b"test content")
        client = Mock(spec=S3Client)

        result = DgApiArtifactApi(client).action_upload(key="test-file.bin", path=upload_file)

        client.upload.assert_called_once()
        key_arg, scope_arg, file_arg = client.upload.call_args[0]
        assert key_arg == "test-file.bin"
        assert scope_arg is None
        assert file_arg.name == str(upload_file.resolve())
        assert file_arg.mode == "rb"

        assert result == DgApiArtifactUploadResult(key="test-file.bin", deployment=None)

    def test_upload_with_deployment(self, tmp_path: Path):
        upload_file = tmp_path / "test-file.bin"
        upload_file.write_bytes(b"test content")
        client = Mock(spec=S3Client)

        result = DgApiArtifactApi(client).action_upload(
            key="test-file.bin", path=upload_file, deployment="prod"
        )

        client.upload.assert_called_once()
        key_arg, scope_arg, file_arg = client.upload.call_args[0]
        assert key_arg == "test-file.bin"
        assert scope_arg == "prod"
        assert file_arg.name == str(upload_file.resolve())
        assert file_arg.mode == "rb"

        assert result == DgApiArtifactUploadResult(key="test-file.bin", deployment="prod")

    def test_upload_file_not_found_raises(self, tmp_path: Path):
        client = Mock(spec=S3Client)

        with pytest.raises(FileNotFoundError, match="Upload path does not exist"):
            DgApiArtifactApi(client).action_upload(key="missing.bin", path=tmp_path / "missing.bin")

        client.upload.assert_not_called()

    def test_upload_client_error_raises_s3_error(self, tmp_path: Path):
        upload_file = tmp_path / "test-file.bin"
        upload_file.write_bytes(b"test content")
        client = Mock(spec=S3Client)
        client.upload.side_effect = Exception()

        with pytest.raises(S3Error, match="Error uploading file"):
            DgApiArtifactApi(client).action_upload(key="test-file.bin", path=upload_file)


class TestActionDownload:
    def test_download(self, tmp_path: Path):
        dest = tmp_path / "test-file.bin"
        client = Mock(spec=S3Client)
        client.download.return_value = b"test content"

        result = DgApiArtifactApi(client).action_download(key="test-file.bin", path=dest)

        client.download.assert_called_once_with("test-file.bin", None)
        assert result == DgApiArtifactDownloadResult(
            key="test-file.bin", path=str(dest), deployment=None
        )

    def test_download_with_deployment(self, tmp_path: Path):
        dest = tmp_path / "test-file.bin"
        client = Mock(spec=S3Client)
        client.download.return_value = b"test content"

        result = DgApiArtifactApi(client).action_download(
            key="test-file.bin", path=dest, deployment="prod"
        )

        client.download.assert_called_once_with("test-file.bin", "prod")
        assert result == DgApiArtifactDownloadResult(
            key="test-file.bin", path=str(dest), deployment="prod"
        )

    def test_download_writes_content_to_path(self, tmp_path: Path):
        dest = tmp_path / "test-dir" / "test-file.bin"
        client = Mock(spec=S3Client)
        client.download.return_value = b"test content"

        DgApiArtifactApi(client).action_download(key="test-file.bin", path=dest)

        assert dest.read_bytes() == b"test content"

    def test_download_client_error_raises_s3_error(self, tmp_path: Path):
        dest = tmp_path / "test-file.bin"
        client = Mock(spec=S3Client)
        client.download.side_effect = Exception()

        with pytest.raises(S3Error, match="Error downloading file"):
            DgApiArtifactApi(client).action_download(key="test-file.bin", path=dest)
