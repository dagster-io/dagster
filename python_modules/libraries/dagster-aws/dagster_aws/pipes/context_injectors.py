import json
import os
import random
import string
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

import boto3
import dagster._check as check
from dagster._core.pipes.client import PipesContextInjector, PipesParams
from dagster._core.pipes.utils import PipesEnvContextInjector

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

    def __init__(self, *, bucket: str, client: boto3.client):  # pyright: ignore (reportGeneralTypeIssues)
        super().__init__()
        self.bucket = check.str_param(bucket, "bucket")
        self.client = client

    @contextmanager
    def inject_context(self, context: "PipesContextData") -> Iterator[PipesParams]:  # pyright: ignore[reportIncompatibleMethodOverride]
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


class PipesLambdaEventContextInjector(PipesEnvContextInjector):
    """Injects context via AWS Lambda event input.
    Should be paired with :py:class`~dagster_pipes.PipesMappingParamsLoader` on the Lambda side.
    """

    def no_messages_debug_text(self) -> str:
        return "Attempted to inject context via the lambda event input."
