import gzip
import os
import random
import string
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import IO, Callable, Optional

import dagster._check as check
from dagster._core.pipes.client import PipesParams
from dagster._core.pipes.utils import (
    PipesBlobStoreMessageReader,
    PipesChunkedLogReader,
    PipesLogReader,
)
from dagster_pipes import PipesBlobStoreMessageWriter
from google.cloud.storage import Client as GCSClient


def _can_read_from_gcs(client: GCSClient, bucket: Optional[str], key: Optional[str]):
    if not bucket or not key:
        return False
    else:
        try:
            client.get_bucket(bucket).blob(key).exists()
            return True
        except Exception:
            return False


def default_log_decode_fn(contents: bytes) -> str:
    return contents.decode("utf-8")


def gzip_log_decode_fn(contents: bytes) -> str:
    return gzip.decompress(contents).decode("utf-8")


class PipesGCSLogReader(PipesChunkedLogReader):
    def __init__(
        self,
        *,
        bucket: str,
        key: str,
        client: Optional[GCSClient] = None,
        interval: float = 10,
        target_stream: Optional[IO[str]] = None,
        # TODO: maybe move this parameter to a different scope
        decode_fn: Optional[Callable[[bytes], str]] = None,
        debug_info: Optional[str] = None,
    ):
        self.bucket = bucket
        self.key = key
        self.client: GCSClient = client or GCSClient()
        self.decode_fn = decode_fn or default_log_decode_fn

        self.log_position = 0

        super().__init__(
            interval=interval, target_stream=target_stream or sys.stdout, debug_info=debug_info
        )

    @property
    def name(self) -> str:
        return f"PipesGCSLogReader(gs://{os.path.join(self.bucket, self.key)})"

    def target_is_readable(self, params: PipesParams) -> bool:
        return _can_read_from_gcs(
            client=self.client,
            bucket=self.bucket,
            key=self.key,
        )

    def download_log_chunk(self, params: PipesParams) -> Optional[str]:
        text = self.decode_fn(
            self.client.get_bucket(self.bucket).blob(self.key).download_as_bytes()
        )
        current_position = self.log_position
        self.log_position += len(text)

        return text[current_position:]


class PipesGCSMessageReader(PipesBlobStoreMessageReader):
    """Message reader that reads messages by periodically reading message chunks from a specified GCS
    bucket.

    If `log_readers` is passed, this reader will also start the passed readers
    when the first message is received from the external process.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        bucket (str): The GCS bucket to read from.
        client (Optional[cloud.google.storage.Client]): The GCS client to use.
        log_readers (Optional[Sequence[PipesLogReader]]): A set of log readers for logs on GCS.
        include_stdio_in_messages (bool): Whether to send stdout/stderr to Dagster via Pipes messages. Defaults to False.
    """

    def __init__(
        self,
        *,
        interval: float = 10,
        bucket: str,
        client: Optional[GCSClient] = None,
        log_readers: Optional[Sequence[PipesLogReader]] = None,
        include_stdio_in_messages: bool = False,
    ):
        super().__init__(
            interval=interval,
            log_readers=log_readers,
        )
        self.bucket = check.str_param(bucket, "bucket")
        self.include_stdio_in_messages = check.bool_param(
            include_stdio_in_messages, "include_stdio_in_messages"
        )
        self.client = client or GCSClient()

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
                # just call head object on f"{key_prefix}/1.json" (no need to download it)
                self.client.get_bucket(self.bucket).blob(f"{key_prefix}/1.json").exists()
                return True
            except Exception:
                return False
        else:
            return False

    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]:
        key = f"{params['key_prefix']}/{index}.json"
        try:
            obj = self.client.get_bucket(self.bucket).blob(key).download_as_bytes()
            return obj.decode("utf-8")
        except Exception:
            return None

    def no_messages_debug_text(self) -> str:
        return (
            f"Attempted to read messages from GCS bucket {self.bucket}. Expected"
            " PipesGCSMessageWriter to be explicitly passed to open_dagster_pipes in the external"
            " process."
        )
