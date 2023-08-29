import random
import string
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from dagster._core.external_execution.resource import (
    ExternalExecutionParams,
)
from dagster._core.external_execution.utils import ExternalExecutionBlobStoreMessageReader


class ExternalExecutionS3MessageReader(ExternalExecutionBlobStoreMessageReader):
    def __init__(self, *, interval: int = 10, bucket: str):
        super().__init__(interval=interval)
        self.bucket = bucket
        self.key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        self.client = boto3.client("s3")

    def get_params(self) -> ExternalExecutionParams:
        return {"bucket": self.bucket, "key_prefix": self.key_prefix}

    def download_messages_chunk(self, index: int) -> Optional[str]:
        key = f"{self.key_prefix}/{index}.json"
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"].read().decode("utf-8")
        except ClientError:
            return None
