import json
import os
import random
import string
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

import dagster._check as check
from dagster._core.pipes.client import PipesContextInjector, PipesParams
from dagster_pipes import PipesContextData
from google.cloud.storage import Client as GCSClient

_CONTEXT_FILENAME = "context.json"


class PipesGCSContextInjector(PipesContextInjector):
    """A context injector that injects context by writing to a temporary GCS location.

    Args:
        bucket (str): The GCS bucket to write to.
        client (google.cloud.storage.Client): A Google Cloud SDK client to use to write to GCS.
        key_prefix (Optional[str]): An optional prefix to use for the GCS key.
            Will be concatenated with a random string.

    """

    def __init__(self, *, bucket: str, client: GCSClient, key_prefix: Optional[str] = None):
        super().__init__()
        self.bucket = check.str_param(bucket, "bucket")
        self.key_prefix = check.opt_str_param(key_prefix, "key_prefix")
        self.client = client

    @contextmanager
    def inject_context(self, context: PipesContextData) -> Iterator[PipesParams]:  # pyright: ignore[reportIncompatibleMethodOverride]
        key_prefix = (self.key_prefix or "") + "".join(random.choices(string.ascii_letters, k=30))
        key = os.path.join(key_prefix, _CONTEXT_FILENAME)
        self.client.get_bucket(self.bucket).blob(key).upload_from_string(json.dumps(context))
        yield {"bucket": self.bucket, "key": key}
        self.client.get_bucket(self.bucket).blob(key).delete()

    def no_messages_debug_text(self) -> str:
        return (
            "Attempted to inject context via a temporary file in GCS. Expected"
            " PipesGCSContextLoader to be explicitly passed to open_dagster_pipes in the external"
            " process."
        )
