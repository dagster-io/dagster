import json
import os
import random
import string
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional

import boto3
import dagster._check as check
from botocore.exceptions import ClientError
from dagster._core.pipes.client import (
    PipesContextInjector,
    PipesParams,
)
from dagster._core.pipes.utils import PipesBlobStoreMessageReader, PipesBlobStoreStdioReader

if TYPE_CHECKING:
    from dagster_pipes import PipesContextData

_CONTEXT_FILENAME = "context.json"


class PipesS3ContextInjector(PipesContextInjector):
    """A context injector that injects context by writing to a temporary S3 location.

    Args:
        bucket (str): The S3 bucket to write to.
        client (boto3.client): A boto3 client to use to write to S3.
        key_prefix (Optional[str]): An optional prefix to use for the S3 key. Defaults to a random
            string.

    """

    def __init__(self, *, bucket: str, client: boto3.client):
        super().__init__()
        self.bucket = check.str_param(bucket, "bucket")
        self.client = client

    @contextmanager
    def inject_context(self, context: "PipesContextData") -> Iterator[PipesParams]:
        key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        key = os.path.join(key_prefix, _CONTEXT_FILENAME)
        self.client.put_object(
            Body=json.dumps(context).encode("utf-8"), Bucket=self.bucket, Key=key
        )
        yield {"bucket": self.bucket, "key": key}
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def no_messages_debug_text(self) -> str:
        return (
            "Attempted to inject context via a temporary file in s3. Expected"
            " PipesS3ContextLoader to be explicitly passed to open_dagster_pipes in the external"
            " process."
        )


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
        self.client = client

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        yield {"bucket": self.bucket, "key_prefix": key_prefix}

    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]:
        key = f"{params['key_prefix']}/{index}.json"
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
