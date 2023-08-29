from typing import IO, Any, Optional

from .._protocol import DAGSTER_EXTERNALS_ENV_KEYS, ExternalExecutionParams
from .._util import DagsterExternalsError
from .base import ExternalExecutionBlobStoreMessageWriter


class ExternalExecutionS3MessageWriter(ExternalExecutionBlobStoreMessageWriter):
    bucket: Optional[str] = None
    key_prefix: Optional[str] = None
    client: Any

    def set_params(
        self,
        params: ExternalExecutionParams,
    ) -> None:
        self._validate_params(params)
        self.bucket = params.get("bucket")
        self.key_prefix = params.get("key_prefix")

        try:
            import boto3

            self.client = boto3.client("s3")
        except ImportError:
            raise ImportError(
                "Missing boto3 library, required for S3 message writer. Install"
                " dagster-externals[s3]."
            )

    def _validate_params(self, params: ExternalExecutionParams) -> None:
        try:
            assert isinstance(params.get("bucket"), str)
            assert isinstance(params.get("key_prefix"), str)
        except AssertionError:
            raise DagsterExternalsError(
                f"`{self.__class__.__name__}` requires `bucket` and `key_prefix` keys in the"
                f" {DAGSTER_EXTERNALS_ENV_KEYS['messages']} environment variable."
            )

    def upload_messages_chunk(self, payload: IO, index: int) -> None:
        key = f"{self.key_prefix}/{index}.json" if self.key_prefix else f"{index}.json"
        self.client.put_object(
            Body=payload.read(),
            Bucket=self.bucket,
            Key=key,
        )
