import json
import sys
from contextlib import contextmanager
from typing import Iterator, TextIO, cast

from .._protocol import (
    ExtContextData,
    ExtMessage,
    ExtParams,
)
from .._util import DagsterExtError, assert_env_param_type, param_from_env_var
from .base import (
    ExtContextLoader,
    ExtMessageWriter,
    ExtMessageWriterChannel,
    ExtParamLoader,
)


class ExtDefaultContextLoader(ExtContextLoader):
    FILE_PATH_KEY = "path"
    DIRECT_KEY = "data"

    @contextmanager
    def load_context(self, params: ExtParams) -> Iterator[ExtContextData]:
        if self.FILE_PATH_KEY in params:
            path = assert_env_param_type(params, self.FILE_PATH_KEY, str, self.__class__)
            with open(path, "r") as f:
                data = json.load(f)
                yield data
        elif self.DIRECT_KEY in params:
            data = assert_env_param_type(params, self.DIRECT_KEY, dict, self.__class__)
            yield cast(ExtContextData, data)
        else:
            raise DagsterExtError(
                f'Invalid params for {self.__class__.__name__}, expected key "{self.FILE_PATH_KEY}"'
                f' or "{self.DIRECT_KEY}", received {params}',
            )


class ExtDefaultMessageWriter(ExtMessageWriter):
    FILE_PATH_KEY = "path"
    STDIO_KEY = "stdio"
    STDERR = "stderr"
    STDOUT = "stdout"

    @contextmanager
    def open(self, params: ExtParams) -> Iterator[ExtMessageWriterChannel]:
        if self.FILE_PATH_KEY in params:
            path = assert_env_param_type(params, self.FILE_PATH_KEY, str, self.__class__)
            yield ExtFileMessageChannel(path)
        elif self.STDIO_KEY in params:
            stream = assert_env_param_type(params, self.STDIO_KEY, str, self.__class__)
            if stream == self.STDERR:
                yield ExtStreamMessageChannel(sys.stderr)
            elif stream == self.STDOUT:
                yield ExtStreamMessageChannel(sys.stdout)
            else:
                raise DagsterExtError(
                    f'Invalid value for key "std", expected "{self.STDERR}" or "{self.STDOUT}" but'
                    f" received {stream}"
                )
        else:
            raise DagsterExtError(
                f'Invalid params for {self.__class__.__name__}, expected key "path" or "std",'
                f" received {params}"
            )


class ExtFileMessageChannel(ExtMessageWriterChannel):
    def __init__(self, path: str):
        self._path = path

    def write_message(self, message: ExtMessage) -> None:
        with open(self._path, "a") as f:
            f.write(json.dumps(message) + "\n")


class ExtStreamMessageChannel(ExtMessageWriterChannel):
    def __init__(self, stream: TextIO):
        self._stream = stream

    def write_message(self, message: ExtMessage) -> None:
        self._stream.writelines((json.dumps(message), "\n"))


class ExtEnvVarParamLoader(ExtParamLoader):
    def load_context_params(self) -> ExtParams:
        return param_from_env_var("context")

    def load_messages_params(self) -> ExtParams:
        return param_from_env_var("messages")
