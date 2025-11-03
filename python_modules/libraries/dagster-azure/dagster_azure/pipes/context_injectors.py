import json
import os
import random
import string
from collections.abc import Iterator
from contextlib import contextmanager

import dagster._check as check
from azure.storage.blob import BlobServiceClient
from dagster._core.pipes.client import PipesContextInjector, PipesParams
from dagster_pipes import PipesContextData

_CONTEXT_FILENAME = "context.json"


class PipesAzureBlobStorageContextInjector(PipesContextInjector):
    """A context injector that injects context by writing to a temporary AzureBlobStorage location.

    Args:
        container (str): The AzureBlobStorage container to write to.
        client (azure.storage.blob.BlobServiceClient): An Azure Blob Storage client.
        key_prefix (Optional[str]): An optional prefix to use for the Azure Blob Storage key. Defaults to a random
            string.

    """

    def __init__(self, *, container: str, client: BlobServiceClient):
        super().__init__()
        self.bucket = check.str_param(container, "container")
        self.client = client

    @contextmanager
    def inject_context(self, context: PipesContextData) -> Iterator[PipesParams]:  # pyright: ignore[reportIncompatibleMethodOverride]
        key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        key = os.path.join(key_prefix, _CONTEXT_FILENAME)

        with self.client.get_blob_client(self.bucket, key) as blob_client:
            blob_client.upload_blob(json.dumps(context).encode("utf-8"))
            yield {"bucket": self.bucket, "key": key}
            blob_client.delete_blob()

    def no_messages_debug_text(self) -> str:
        return (
            "Attempted to inject context via a temporary file in AzureBlobStorage. Expected"
            " PipesAzureBlobStorageContextLoader to be explicitly passed to open_dagster_pipes in the external"
            " process."
        )
