import json
from contextlib import contextmanager
from typing import Iterator, Optional

from .._protocol import (
    DAGSTER_EXTERNALS_ENV_KEYS,
    ExternalExecutionContextData,
    ExternalExecutionMessage,
    ExternalExecutionParams,
)
from .._util import DagsterExternalsError, param_from_env_var
from .base import (
    ExternalExecutionContextLoader,
    ExternalExecutionMessageWriter,
    ExternalExecutionParamLoader,
)


class ExternalExecutionFileContextLoader(ExternalExecutionContextLoader):
    _path: Optional[str] = None

    @contextmanager
    def setup(self, params: ExternalExecutionParams) -> Iterator[None]:
        self._validate_path_params(params)
        self._path = params["path"]
        yield

    def _validate_path_params(self, params: ExternalExecutionParams) -> None:
        try:
            assert isinstance(params.get("path"), str)
        except AssertionError:
            raise DagsterExternalsError(_validation_error_message(self, "context"))

    @property
    def path(self) -> str:
        assert self._path is not None
        return self._path

    def load_context(self) -> ExternalExecutionContextData:
        with open(self.path, "r") as f:
            return json.load(f)


class ExternalExecutionFileMessageWriter(ExternalExecutionMessageWriter):
    _path: Optional[str] = None

    @contextmanager
    def setup(self, params: ExternalExecutionParams) -> Iterator[None]:
        self._validate_path_params(params)
        self._path = params["path"]
        yield

    def _validate_path_params(self, params: ExternalExecutionParams) -> None:
        try:
            assert isinstance(params.get("path"), str)
        except AssertionError:
            raise DagsterExternalsError(_validation_error_message(self, "context"))

    @property
    def path(self) -> str:
        assert self._path is not None
        return self._path

    def write_message(self, message: ExternalExecutionMessage) -> None:
        with open(self.path, "a") as f:
            f.write(json.dumps(message) + "\n")


def _validation_error_message(obj: object, param: str) -> str:
    return (
        f"`{obj.__class__.__name__}` requires a `path` key in the"
        f" {DAGSTER_EXTERNALS_ENV_KEYS[param]} environment variable be a JSON"
        " object with a string `path` property."
    )


class ExternalExecutionEnvVarParamLoader(ExternalExecutionParamLoader):
    def load_context_params(self) -> ExternalExecutionParams:
        return param_from_env_var("context")

    def load_messages_params(self) -> ExternalExecutionParams:
        return param_from_env_var("messages")
