"""Artifact endpoints - REST interface for upload/download via presigned S3 URLs."""

from dataclasses import dataclass
from pathlib import Path

from dagster_rest_resources.s3_client import S3Client
from dagster_rest_resources.schemas.artifact import (
    DgApiArtifactDownloadResult,
    DgApiArtifactUploadResult,
)
from dagster_rest_resources.schemas.exception import S3Error


@dataclass(frozen=True)
class DgApiArtifactApi:
    _client: S3Client

    def action_upload(
        self,
        path: Path,
        key: str,
        deployment: str | None = None,
    ) -> DgApiArtifactUploadResult:
        try:
            with path.resolve(strict=True).open("rb") as f:
                self._client.upload(key, deployment, f)

            return DgApiArtifactUploadResult(
                key=key,
                deployment=deployment,
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Upload path does not exist: {path}")
        except Exception as e:
            raise S3Error(f"Error uploading file: {e}")

    def action_download(
        self,
        path: Path,
        key: str,
        deployment: str | None = None,
    ) -> DgApiArtifactDownloadResult:
        try:
            content = self._client.download(key, deployment)
        except Exception as e:
            raise S3Error(f"Error downloading file: {e}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

        return DgApiArtifactDownloadResult(
            key=key,
            deployment=deployment,
            path=str(path),
        )
