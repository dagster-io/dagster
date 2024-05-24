### ORCHESTRATION PROCESS

import os
import string
from random import random
from typing import Iterator, Optional

import cloud_service  # type: ignore
from dagster_pipes import PipesParams

from dagster import PipesBlobStoreMessageReader


class MyCustomCloudServiceMessageReader(PipesBlobStoreMessageReader):
    def get_params(self) -> Iterator[PipesParams]:
        # generate a random key prefix to write message chunks under on the cloud service
        key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        yield {"key_prefix": key_prefix}

    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]:
        message_path = os.path.join(params["path"], f"{index}.json")
        raw_message = cloud_service.read(message_path)
        return raw_message

    def no_messages_debug_text(self) -> str:
        return (
            "Attempted to read messages from a `cloud_service`. Expected"
            " MyCustomCloudServiceMessageWriter to be explicitly passed to `open_dagster_pipes` in"
            " the external process."
        )
