"""Artifact endpoints - REST interface for upload/download via presigned S3 URLs."""

from dataclasses import dataclass
from pathlib import Path

import requests

from dagster_dg_cli.api_layer.schemas.artifact import ArtifactDownloadResult, ArtifactUploadResult


@dataclass(frozen=True)
class DgApiArtifactApi:
    base_url: str
    headers: dict[str, str]

    def upload(
        self,
        key: str,
        path: Path,
        deployment: str | None = None,
    ) -> ArtifactUploadResult:
        """Upload an artifact to Dagster Plus via presigned S3 URL."""
        if not path.exists():
            raise FileNotFoundError(f"Upload path does not exist: {path}")
        upload_file = path.resolve(strict=True)

        request_headers = {**self.headers}
        if deployment:
            request_headers["Dagster-Cloud-Deployment"] = deployment

        # Step 1: Get presigned POST URL
        response = requests.post(
            url=f"{self.base_url}/gen_artifact_post",
            headers=request_headers,
            json={"key": key},
        )
        response.raise_for_status()
        payload = response.json()

        # Step 2: Upload file to S3 via presigned POST
        with upload_file.open("rb") as f:
            s3_response = requests.post(
                payload["url"],
                data=payload["fields"],
                files={"file": f},
            )
        s3_response.raise_for_status()

        scope = "deployment" if deployment else "organization"
        return ArtifactUploadResult(key=key, scope=scope, deployment=deployment)

    def download(
        self,
        key: str,
        path: Path,
        deployment: str | None = None,
    ) -> ArtifactDownloadResult:
        """Download an artifact from Dagster Plus via presigned S3 URL."""
        request_headers = {**self.headers}
        if deployment:
            request_headers["Dagster-Cloud-Deployment"] = deployment

        # Step 1: Get presigned GET URL
        response = requests.post(
            url=f"{self.base_url}/gen_artifact_get",
            headers=request_headers,
            json={"key": key},
        )
        response.raise_for_status()
        payload = response.json()

        # Step 2: Download file from S3
        s3_response = requests.get(payload["url"])
        s3_response.raise_for_status()

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(s3_response.content)

        scope = "deployment" if deployment else "organization"
        return ArtifactDownloadResult(key=key, path=str(path), scope=scope, deployment=deployment)
