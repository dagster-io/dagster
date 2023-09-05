from typing import IO, Any, Optional

from .._protocol import ExtParams
from .._util import assert_env_param_type, assert_opt_env_param_type, assert_param_type
from .base import (
    ExtBlobStoreMessageWriter,
    ExtBlobStoreMessageWriterChannel,
)


class ExtS3MessageWriter(ExtBlobStoreMessageWriter):
    # client is a boto3.client("s3") object
    def __init__(self, client: Any, *, interval: float = 10):
        super().__init__(interval=interval)
        self._interval = assert_param_type(interval, float, self.__class__.__name__, "interval")
        # Not checking client type for now because it's a boto3.client object and we don't want to
        # depend on boto3.
        self._client = client

    def make_channel(
        self,
        params: ExtParams,
    ) -> "ExtS3MessageChannel":
        bucket = assert_env_param_type(params, "bucket", str, self.__class__)
        key_prefix = assert_opt_env_param_type(params, "key_prefix", str, self.__class__)
        return ExtS3MessageChannel(
            client=self._client,
            bucket=bucket,
            key_prefix=key_prefix,
            interval=self._interval,
        )


class ExtS3MessageChannel(ExtBlobStoreMessageWriterChannel):
    # client is a boto3.client("s3") object
    def __init__(
        self, client: Any, bucket: str, key_prefix: Optional[str], *, interval: float = 10
    ):
        super().__init__(interval=interval)
        self._client = client
        self._bucket = bucket
        self._key_prefix = key_prefix

    def upload_messages_chunk(self, payload: IO, index: int) -> None:
        key = f"{self._key_prefix}/{index}.json" if self._key_prefix else f"{index}.json"
        self._client.put_object(
            Body=payload.read(),
            Bucket=self._bucket,
            Key=key,
        )
