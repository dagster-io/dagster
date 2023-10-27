### EXTERNAL PROCESS

import json
from typing import IO

import cloud_service  # type: ignore
from dagster_pipes import (
    PipesBlobStoreMessageWriter,
    PipesBlobStoreMessageWriterChannel,
    PipesParams,
)


class MyCustomCloudServiceMessageWriter(PipesBlobStoreMessageWriter):
    def make_channel(
        self, params: PipesParams
    ) -> "MyCustomCloudServiceMessageWriterChannel":
        # params were yielded by the above message reader and sourced from the bootstrap payload
        key_prefix = params["key_prefix"]
        return MyCustomCloudServiceMessageWriterChannel(key_prefix=key_prefix)


class MyCustomCloudServiceMessageWriterChannel(PipesBlobStoreMessageWriterChannel):
    def __init__(self, key_prefix: str):
        super().__init__()
        self.key_prefix = key_prefix

    # This will be called periodically to upload any buffered messages
    def upload_messages_chunk(self, payload: IO, index: int) -> None:
        key = f"{self.key_prefix}/{index}.json"
        cloud_service.write(key, json.dumps(payload.read()))
