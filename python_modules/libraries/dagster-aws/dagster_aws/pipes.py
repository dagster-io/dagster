import random
import string
from contextlib import contextmanager
from typing import Iterator, Optional

import boto3
import dagster._check as check
from botocore.exceptions import ClientError
from dagster._core.pipes.client import (
    PipesParams,
)
from dagster._core.pipes.utils import PipesBlobStoreMessageReader, PipesBlobStoreStdioReader


class PipesS3MessageReader(PipesBlobStoreMessageReader):
    """Message reader that reads messages by periodically reading message chunks from a specified S3
    bucket.

    If `stdout_reader` or `stderr_reader` are passed, this reader will also start them when
    `read_messages` is called. If they are not passed, then the reader performs no stdout/stderr
    forwarding.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        bucket (str): The S3 bucket to read from.
        client (WorkspaceClient): A boto3 client.
        stdout_reader (Optional[PipesBlobStoreStdioReader]): A reader for reading stdout logs.
        stderr_reader (Optional[PipesBlobStoreStdioReader]): A reader for reading stderr logs.
    """

    def __init__(
        self,
        *,
        interval: float = 10,
        bucket: str,
        client: boto3.client,
        stdout_reader: Optional[PipesBlobStoreStdioReader] = None,
        stderr_reader: Optional[PipesBlobStoreStdioReader] = None,
    ):
        super().__init__(
            interval=interval, stdout_reader=stdout_reader, stderr_reader=stderr_reader
        )
        self.bucket = check.str_param(bucket, "bucket")
        self.key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        self.client = client

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        yield {"bucket": self.bucket, "key_prefix": self.key_prefix}

    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]:
        key = f"{self.key_prefix}/{index}.json"
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"].read().decode("utf-8")
        except ClientError:
            return None

    def no_messages_debug_text(self) -> str:
        return (
            f"Attempted to read messages from S3 bucket {self.bucket}. Expected"
            " PipesS3MessageWriter to be explicitly passed to open_dagster_pipes in the external"
            " process."
        )
