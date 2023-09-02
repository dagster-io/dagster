import json
from contextlib import contextmanager
from typing import Iterator, Optional

from .._protocol import (
    ExtContextData,
    ExtMessage,
    ExtParams,
)
from .._util import assert_env_param_type, param_from_env_var
from .base import (
    ExtContextLoader,
    ExtMessageWriter,
    ExtMessageWriterChannel,
    ExtParamLoader,
)


class ExtFileContextLoader(ExtContextLoader):
    _path: Optional[str] = None

    @contextmanager
    def load_context(self, params: ExtParams) -> Iterator[ExtContextData]:
        path = assert_env_param_type(params, "path", str, self.__class__)
        with open(path, "r") as f:
            data = json.load(f)
        yield data


class ExtFileMessageWriter(ExtMessageWriter):
    _path: Optional[str] = None

    @contextmanager
    def open(self, params: ExtParams) -> Iterator["ExternalExecutionFileMessageChannel"]:
        path = assert_env_param_type(params, "path", str, self.__class__)
        yield ExternalExecutionFileMessageChannel(path)


class ExternalExecutionFileMessageChannel(ExtMessageWriterChannel):
    def __init__(self, path: str):
        self._path = path

    def write_message(self, message: ExtMessage) -> None:
        with open(self._path, "a") as f:
            f.write(json.dumps(message) + "\n")


class ExtEnvVarParamLoader(ExtParamLoader):
    def load_context_params(self) -> ExtParams:
        return param_from_env_var("context")

    def load_messages_params(self) -> ExtParams:
        return param_from_env_var("messages")
