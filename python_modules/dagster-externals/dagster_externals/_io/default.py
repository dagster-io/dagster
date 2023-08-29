import json

from .._protocol import (
    DAGSTER_EXTERNALS_ENV_KEYS,
    ExternalExecutionContextData,
    ExternalExecutionMessage,
)
from .._util import DagsterExternalsError, param_from_env_var
from .base import ExternalExecutionContextLoader, ExternalExecutionMessageWriter


class ExternalExecutionFileContextLoader(ExternalExecutionContextLoader):
    def load_context(self) -> ExternalExecutionContextData:
        path = self._get_path_from_env()
        with open(path, "r") as f:
            return json.load(f)

    def _get_path_from_env(self) -> str:
        try:
            context_injector_params = param_from_env_var("context")
            assert isinstance(context_injector_params, dict)
            assert isinstance(context_injector_params.get("path"), str)
            return context_injector_params["path"]
        except AssertionError:
            raise DagsterExternalsError(
                f"`{self.__class__.__name__}` requires a `path` key in the"
                f" {DAGSTER_EXTERNALS_ENV_KEYS['context_injector']} environment variable be a JSON"
                " object with a string `path` property."
            )


class ExternalExecutionFileMessageWriter(ExternalExecutionMessageWriter):
    def __init__(self):
        self._path = None

    def write_message(self, message: ExternalExecutionMessage) -> None:
        with open(self.path, "a") as f:
            f.write(json.dumps(message) + "\n")

    @property
    def path(self) -> str:
        if self._path is None:
            self._path = self._get_path_from_env()
        return self._path

    def _get_path_from_env(self) -> str:
        try:
            context_injector_params = param_from_env_var("messages")
            assert isinstance(context_injector_params, dict)
            assert isinstance(context_injector_params.get("path"), str)
            return context_injector_params["path"]
        except AssertionError:
            raise DagsterExternalsError(
                f"`{self.__class__.__name__}` requires a `path` key in the"
                f" {DAGSTER_EXTERNALS_ENV_KEYS['message_reader']} environment variable be a JSON"
                " object with a string `path` property."
            )
