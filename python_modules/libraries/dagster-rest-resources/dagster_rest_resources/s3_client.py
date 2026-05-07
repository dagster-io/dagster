from dataclasses import dataclass
from typing import BinaryIO

import httpx


@dataclass(frozen=True)
class S3Client:
    base_url: str
    headers: dict[str, str]

    def upload(self, key: str, deployment: str | None, f: BinaryIO) -> None:
        with httpx.Client() as client:
            # Step 1: Get presigned POST URL
            presigned_url_response = client.post(
                url=f"{self.base_url}/gen_artifact_post",
                headers=self.__add_deployment_header(deployment),
                json={"key": key},
            )
            presigned_url_response.raise_for_status()
            payload = presigned_url_response.json()

            # Step 2: Upload file to S3 via presigned POST
            upload_response = client.post(
                payload["url"],
                data=payload["fields"],
                files={"file": f},
            )
            upload_response.raise_for_status()

    def download(self, key: str, deployment: str | None) -> bytes:
        with httpx.Client() as client:
            # Step 1: Get presigned GET URL
            presigned_url_response = client.post(
                url=f"{self.base_url}/gen_artifact_get",
                headers=self.__add_deployment_header(deployment),
                json={"key": key},
            )
            presigned_url_response.raise_for_status()
            payload = presigned_url_response.json()

            # Step 2: Download file from S3
            download_response = client.get(url=payload["url"])
            download_response.raise_for_status()

        return download_response.content

    def __add_deployment_header(self, deployment: str | None) -> dict[str, str]:
        return self.headers | ({"Dagster-Cloud-Deployment": deployment} if deployment else {})
