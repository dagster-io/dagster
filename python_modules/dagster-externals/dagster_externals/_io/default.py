import json
from contextlib import contextmanager
from typing import Iterator, Optional

from .._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionMessage,
    ExternalExecutionParams,
)
from .._util import assert_env_param_type, param_from_env_var
from .base import (
    ExternalExecutionContextLoader,
    ExternalExecutionMessageWriter,
    ExternalExecutionMessageWriterChannel,
    ExternalExecutionParamLoader,
)


class ExternalExecutionFileContextLoader(ExternalExecutionContextLoader):
    _path: Optional[str] = None

    @contextmanager
    def load_context(
        self, params: ExternalExecutionParams
    ) -> Iterator[ExternalExecutionContextData]:
        path = assert_env_param_type(params, "path", str, self.__class__)
        with open(path, "r") as f:
            data = json.load(f)
        yield data


class ExternalExecutionFileMessageWriter(ExternalExecutionMessageWriter):
    _path: Optional[str] = None

    @contextmanager
    def open(
        self, params: ExternalExecutionParams
    ) -> Iterator["ExternalExecutionFileMessageChannel"]:
        path = assert_env_param_type(params, "path", str, self.__class__)
        yield ExternalExecutionFileMessageChannel(path)


class ExternalExecutionFileMessageChannel(ExternalExecutionMessageWriterChannel):
    def __init__(self, path: str):
        self._path = path

    def write_message(self, message: ExternalExecutionMessage) -> None:
        with open(self._path, "a") as f:
            f.write(json.dumps(message) + "\n")


class ExternalExecutionEnvVarParamLoader(ExternalExecutionParamLoader):
    def load_context_params(self) -> ExternalExecutionParams:
        return param_from_env_var("context")

    def load_messages_params(self) -> ExternalExecutionParams:
        return param_from_env_var("messages")
