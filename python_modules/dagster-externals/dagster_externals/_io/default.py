import json

from .._protocol import (
    DAGSTER_EXTERNALS_ENV_KEYS,
    ExternalExecutionContextData,
    ExternalExecutionMessage,
)
from .._util import DagsterExternalsError, param_from_env
from .base import ExternalExecutionContextSource, ExternalExecutionMessageSink


class ExternalExecutionFileContextSource(ExternalExecutionContextSource):
    def load_context(self) -> ExternalExecutionContextData:
        path = self._get_path_from_env()
        with open(path, "r") as f:
            return json.load(f)

    def _get_path_from_env(self) -> str:
        try:
            context_source_params = param_from_env("context_source")
            assert isinstance(context_source_params, dict)
            assert isinstance(context_source_params.get("path"), str)
            return context_source_params["path"]
        except AssertionError:
            raise DagsterExternalsError(
                "`ExternalExecutionFileContextSource` requires a `path` key in the"
                f" {DAGSTER_EXTERNALS_ENV_KEYS['context_source']} environment variable be a JSON"
                " object with a string `path` property."
            )


class ExternalExecutionFileMessageSink(ExternalExecutionMessageSink):
    def __init__(self):
        self._path = None

    def send_message(self, message: ExternalExecutionMessage) -> None:
        with open(self.path, "a") as f:
            f.write(json.dumps(message) + "\n")

    @property
    def path(self) -> str:
        if self._path is None:
            self._path = self._get_path_from_env()
        return self._path

    def _get_path_from_env(self) -> str:
        try:
            context_source_params = param_from_env("message_sink")
            assert isinstance(context_source_params, dict)
            assert isinstance(context_source_params.get("path"), str)
            return context_source_params["path"]
        except AssertionError:
            raise DagsterExternalsError(
                "`ExternalExecutionFileMessageSink` requires a `path` key in the"
                f" {DAGSTER_EXTERNALS_ENV_KEYS['message_sink']} environment variable be a JSON"
                " object with a string `path` property."
            )
