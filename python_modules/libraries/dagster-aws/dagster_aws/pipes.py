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
from dagster._core.pipes.utils import PipesBlobStoreMessageReader


class PipesS3MessageReader(PipesBlobStoreMessageReader):
    def __init__(self, *, interval: float = 10, bucket: str, client: boto3.client):
        super().__init__(interval=interval)
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
