import random
import string
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Optional

import dagster._check as check
from azure.storage.blob import BlobServiceClient
from dagster._core.pipes.client import PipesParams
from dagster._core.pipes.utils import PipesBlobStoreMessageReader, PipesLogReader
from dagster_pipes import PipesBlobStoreMessageWriter


class PipesAzureBlobStorageMessageReader(PipesBlobStoreMessageReader):
    """Message reader that reads messages by periodically reading message chunks from a specified AzureBlobStorage
    container.

    If `log_readers` is passed, this reader will also start the passed readers
    when the first message is received from the external process.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        container (str): The AzureBlobStorage container to read from.
        client (azure.storage.blob.BlobServiceClient): An azure BlobServiceClient.
        log_readers (Optional[Sequence[PipesLogReader]]): A set of log readers for logs on AzureBlobStorage.
        include_stdio_in_messages (bool): Whether to send stdout/stderr to Dagster via Pipes messages. Defaults to False.
    """

    def __init__(
        self,
        *,
        interval: float = 10,
        container: str,
        client: BlobServiceClient,
        log_readers: Optional[Sequence[PipesLogReader]] = None,
        include_stdio_in_messages: bool = False,
    ):
        super().__init__(
            interval=interval,
            log_readers=log_readers,
        )
        self.bucket = check.str_param(container, "container")
        self.include_stdio_in_messages = check.bool_param(
            include_stdio_in_messages, "include_stdio_in_messages"
        )
        self.client = client

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        yield {
            "bucket": self.bucket,
            "key_prefix": key_prefix,
            PipesBlobStoreMessageWriter.INCLUDE_STDIO_IN_MESSAGES_KEY: self.include_stdio_in_messages,
        }

    def messages_are_readable(self, params: PipesParams) -> bool:
        key_prefix = params.get("key_prefix")
        if key_prefix is not None:
            try:
                with self.client.get_blob_client(
                    self.bucket, f"{key_prefix}/1.json"
                ) as blob_client:
                    return blob_client.exists()
            except Exception:
                return False
        else:
            return False

    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]:
        key = f"{params['key_prefix']}/{index}.json"
        try:
            with self.client.get_blob_client(self.bucket, key) as blob_client:
                return blob_client.download_blob().readall().decode("utf-8")
        except Exception:
            return None

    def no_messages_debug_text(self) -> str:
        return (
            f"Attempted to read messages from Azure Blob Storage container "
            f"{self.bucket}. Expected PipesAzureBlobStorageMessageWriter to be "
            "explicitly passed to open_dagster_pipes in the external process."
        )
